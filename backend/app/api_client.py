import asyncio
import logging
import math

import httpx

PROVINCES = {
    "dolnośląskie": "01",
    "kujawsko-pomorskie": "02",
    "lubelskie": "03",
    "lubuskie": "04",
    "łódzkie": "05",
    "małopolskie": "06",
    "mazowieckie": "07",
    "opolskie": "08",
    "podkarpackie": "09",
    "podlaskie": "10",
    "pomorskie": "11",
    "śląskie": "12",
    "świętokrzyskie": "13",
    "warmińsko-mazurskie": "14",
    "wielkopolskie": "15",
    "zachodniopomorskie": "16",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NFZClient:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(3)
        self.BASE_URL = "https://api.nfz.gov.pl/app-itl-api/queues"

    async def get_queues(self, user_input: str, province: str | list, city: str = ""):
        print(
            f"""Przetwarzanie zapytania: '{user_input}'
            dla województwa: '{province}' i miejscowości: {city}"""
        )

        if isinstance(province, str):
            province_code = PROVINCES.get(province.lower())
        else:
            province_code = []
            for prov in province:
                province_code.append(PROVINCES.get(prov.lower()))

        locality = city.strip().lower()

        if not province_code:
            print(f"Nieznany kod województwa: {province}")
            return "Nieznane województwo"

        benefit = user_input[:5]

        if isinstance(province_code, str):
            province_code = [province_code]

        async with self.semaphore:
            async with httpx.AsyncClient() as client:
                tasks = [
                    self.fetch_province_data(client, prov, benefit, locality)
                    for prov in province_code
                ]

                responses = await asyncio.gather(*tasks)

                final_results = {prov: res for prov, res in responses}
            await asyncio.sleep(0.5)

        return final_results

    async def fetch_province_data(self, client, prov, benefit, locality):
        params = {
            "format": "json",
            "case": 1,
            "benefit": benefit,
            "province": prov,
            "locality": locality,
            "page": 1,
            "limit": 25,
        }
        try:
            res = await client.get(self.BASE_URL, params=params, timeout=5.0)
            res.raise_for_status()
            data = res.json()
            results = data.get("data", [])
            count = data.get("meta", {}).get("count", 0)

            if count > 25:
                total_pages = min(math.ceil(count / 25), 5)
                for i in range(2, total_pages + 1):
                    params["page"] = i
                    try:
                        p_res = await client.get(
                            self.BASE_URL, params=params, timeout=5.0
                        )
                        p_res.raise_for_status()
                        results.extend(p_res.json().get("data", []))
                    except Exception:
                        break
            return prov, results
        except Exception as e:
            logger.error(f"Błąd dla {prov}: {e}")
            return prov, []
