"""
Import the fuel-price CSV into the FuelStation table.

Pipeline: parse -> dedup on OPIS id using LOWEST price ->
offline (city, state) geocode-join -> bulk insert.
Makes ZERO geocoding API calls. Run once; the request path
never geocodes.

    python manage.py import_fuel_prices fuel-prices-for-be-assessment.csv
"""

import csv
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction

from routing.models import FuelStation
from routing.services import cities


class Command(BaseCommand):
    help = "Load the fuel-price CSV into FuelStation (dedup by OPIS id using lowest price + offline geocode)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument(
            "--keep-unmatched",
            action="store_true",
            help="Report unmatched (city, state) pairs at the end.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        # Keep exactly one row per OPIS Truckstop ID:
        # the row with the lowest retail price.
        best_by_oid = {}

        unmatched = 0
        unmatched_keys = set()
        total = 0

        # utf-8-sig strips the BOM; csv handles quoted commas in Address.
        with open(
            opts["csv_path"],
            newline="",
            encoding="utf-8-sig",
        ) as f:
            for r in csv.DictReader(f):
                total += 1

                try:
                    oid = int(r["OPIS Truckstop ID"])
                    price = Decimal(r["Retail Price"].strip())
                except (ValueError, TypeError, InvalidOperation):
                    self.stderr.write(
                        f"Skipping invalid row {total}: "
                        f"invalid OPIS ID or Retail Price."
                    )
                    continue

                # Keep the cheapest price for each OPIS ID.
                existing = best_by_oid.get(oid)

                if existing is None or price < existing["price"]:
                    best_by_oid[oid] = {
                        "price": price,
                        "row": r,
                    }

        rows = []

        for oid, data in best_by_oid.items():
            r = data["row"]
            price = data["price"]

            city = r["City"].strip()
            state = r["State"].strip()

            coord = cities.lookup(city, state)

            if coord is None:
                unmatched += 1
                unmatched_keys.add(
                    (city.upper(), state.upper())
                )
                continue

            lat, lng = coord

            rows.append(
                FuelStation(
                    opis_id=oid,
                    name=r["Truckstop Name"].strip(),
                    address=r["Address"].strip(),
                    city=city,
                    state=state,
                    price=float(price),
                    lat=lat,
                    lng=lng,
                )
            )

        FuelStation.objects.all().delete()

        FuelStation.objects.bulk_create(
            rows,
            batch_size=1000,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(rows)} stations from {total} rows "
                f"({len(best_by_oid)} unique OPIS ids); "
                f"{unmatched} dropped for missing (city, state) geocode."
            )
        )

        if opts["keep_unmatched"] and unmatched_keys:
            self.stdout.write("Unmatched (city, state):")

            for city, state in sorted(unmatched_keys):
                self.stdout.write(
                    f"  {city}, {state}"
                )