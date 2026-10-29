import duckdb

duckdb.sql("""
COPY (
    SELECT name, address, city, category, lat, lon
    FROM 'data/raw/overture.csv'
    WHERE operating_status IS DISTINCT FROM 'permanently_closed'
) TO 'web/data/stores.json' (FORMAT json, ARRAY true)
""")
print("Wrote web/data/stores.json")