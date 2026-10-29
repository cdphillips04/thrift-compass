import json
import urllib.request

import duckdb

# settings
CENTER = (37.2707, -76.7075)  # Williamsburg
RADIUS_MI = 30

# box around the 30-mile circle
S, N = 36.83, 37.71
W, E = -77.26, -76.16


def pull_overture():
    release = json.load(urllib.request.urlopen("https://stac.overturemaps.org/catalog.json"))["latest"]
    print("Overture release:", release)

    con = duckdb.connect()
    con.sql("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
    con.sql(f"""
    COPY (
        SELECT id, names.primary AS name, taxonomy.primary AS category,
               addresses[1].freeform AS address, addresses[1].locality AS city,
               addresses[1].postcode AS zip, phones[1] AS phone, websites[1] AS website,
               brand.names.primary AS brand, round(confidence, 2) AS confidence,
               operating_status, bbox.ymin AS lat, bbox.xmin AS lon
        FROM read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*', hive_partitioning=1)
        WHERE bbox.xmin BETWEEN {W} AND {E} AND bbox.ymin BETWEEN {S} AND {N}
          AND taxonomy.primary IN ('second_hand_store', 'second_hand_clothing_store')
          AND sqrt(power((bbox.ymin - ({CENTER[0]})) * 69, 2) + power((bbox.xmin - ({CENTER[1]})) * 55, 2)) <= {RADIUS_MI}
    ) TO 'data/raw/overture.csv' (HEADER)
    """)

    count = con.sql("SELECT count(*) FROM 'data/raw/overture.csv'").fetchall()[0][0]
    print("Overture stores:", count)


def pull_osm():
    query = f"""[out:csv(::type, ::id, name, shop, "addr:housenumber", "addr:street", "addr:city",
                     "addr:postcode", phone, website, opening_hours, ::lat, ::lon)];
    nwr["shop"~"^(second_hand|charity)$"](around:{RADIUS_MI * 1609},{CENTER[0]},{CENTER[1]});
    out center;"""
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=query.encode(),
        headers={"User-Agent": "thrift-compass (DATA 440 class project)"},
    )
    text = urllib.request.urlopen(req).read().decode()

    with open("data/raw/osm.tsv", "w") as f:
        f.write(text)
    print("OSM stores:", text.count("\n") - 1)


pull_overture()
pull_osm()