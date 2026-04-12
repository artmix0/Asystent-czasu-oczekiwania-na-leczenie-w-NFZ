import logging

from geopy.distance import geodesic
from geopy.geocoders import Nominatim

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

geolocator = Nominatim(user_agent="nfz_assistant")


class Geolocator:
    def get_geolocation_reverse(self, lat: float, lon: float):
        try:
            location = geolocator.reverse(f"{lat}, {lon}", language="pl")
            if location and location.raw and "address" in location.raw:
                address = location.raw["address"]
                logger.info(address)
                return {
                    "city": address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or "",
                    "province": address.get("state", "")
                    .replace("województwo", "")
                    .strip(),
                }
        except Exception as e:
            logger.error(f"Błąd podczas geolokalizacji: {e}")
        return None

    def get_city_coords(self, city_name: str):
        try:
            location = geolocator.geocode(f"{city_name}, Polska")
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.error(f"Błąd podczas pobierania współrzędnych: {e}")
        return None

    def find_nearby_cascade(
        self, city_name: str, all_providers: dict | list, max_radius_km: int = 50
    ):
        origin = self.get_city_coords(city_name)
        if not origin:
            return {"error": "Nie znaleziono miejscowości", "results": []}

        flat_list = []
        if isinstance(all_providers, dict):
            for prov_list in all_providers.values():
                if isinstance(prov_list, list):
                    flat_list.extend(prov_list)
        else:
            flat_list = all_providers

        results_with_dist = []

        for item in flat_list:
            try:
                attr = item.get("attributes", item)
                p_lat = attr.get("latitude")
                p_lon = attr.get("longitude")

                if p_lat is not None and p_lon is not None:
                    dist = geodesic(origin, (float(p_lat), float(p_lon))).km
                    item["distance_km"] = round(dist, 1)

                    if dist <= max_radius_km:
                        results_with_dist.append(item)
            except Exception as e:
                logger.warning(f"Pominięto placówkę przy liczeniu dystansu: {e}")
                continue

        results_with_dist.sort(key=lambda x: x.get("distance_km", 999))

        return {
            "search_radius": max_radius_km,
            "city_origin": origin,
            "results": results_with_dist,
        }

    def get_nearby_provinces(self, city_name: str, radius_km: int = 50):
        origin = self.get_city_coords(city_name)
        if not origin:
            return []

        lat, lon = origin

        offset = radius_km / 111.0

        points_to_check = [
            (lat, lon),
            (lat + offset, lon),
            (lat - offset, lon),
            (lat, lon + offset),
            (lat, lon - offset),
        ]

        found_provinces = set()
        for p_lat, p_lon in points_to_check:
            info = self.get_geolocation_reverse(p_lat, p_lon)
            if info and info["province"]:
                found_provinces.add(info["province"])

        return list(found_provinces)
