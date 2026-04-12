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
        self, city_name: str, all_providers: dict, max_radius_km: int = 50
    ):
        origin = self.get_city_coords(city_name)
        if not origin:
            return {"error": "Nie znaleziono miejscowości", "results": []}

        results_with_dist = []
        logger.info(all_providers)
        for p in all_providers:
            for i in range(len(all_providers[p])):
                logger.info(all_providers[p])

                p_lat = all_providers[p][i].get("attributes").get("latitude")
                p_lon = all_providers[p][i].get("attributes").get("longitude")

                if p_lat is not None and p_lon is not None:
                    dist = geodesic(origin, (float(p_lat), float(p_lon))).km
                    all_providers[p][i]["distance_km"] = round(dist, 1)
                    results_with_dist.append(all_providers[p][i])

        logger.info(results_with_dist)

        filtered = [p for p in results_with_dist if p["distance_km"] <= max_radius_km]

        logger.info(filtered)
        return {
            "search_radius": max_radius_km,
            "city_origin": origin,
            "results": filtered,
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
