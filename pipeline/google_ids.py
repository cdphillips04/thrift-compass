import csv
import json
import os
import urllib.request


def google_id(name, address, city):
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchText",
        data=json.dumps({"textQuery": f"{name} {address} {city}"}).encode(),
        headers={"Content-Type": "application/json",
                 "X-Goog-Api-Key": os.environ["GOOGLE_PLACES_KEY"],
                 "X-Goog-FieldMask": "places.id,places.formattedAddress"},
    )
    places = json.load(urllib.request.urlopen(req)).get("places")
    if not places:
        print("NOT FOUND:", name, "|", address)
        return ""
    google_address = places[0]["formattedAddress"]
    number = address.split(" ")[0]
    if number.isdigit() and number not in google_address:
        print("REJECTED:", name, "|", address, "| Google:", google_address)
        return ""
    return places[0]["id"]


# reuse IDs from the last run
saved = {}
if os.path.exists("data/google_ids.csv"):
    for row in csv.DictReader(open("data/google_ids.csv")):
        saved[row["id"]] = row["google_id"]

stores = list(csv.DictReader(open("data/raw/overture.csv")))
with open("data/google_ids.csv", "w") as f:
    f.write("id,google_id\n")
    for s in stores:
        gid = saved.get(s["id"]) or google_id(s["name"], s["address"], s["city"])
        f.write(f"{s['id']},{gid}\n")

print("Done")