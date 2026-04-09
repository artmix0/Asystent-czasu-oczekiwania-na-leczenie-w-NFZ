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


class NFZClient:
    BASE_URL = "https://api.nfz.gov.pl/app-itl-api/queues"

    async def get_queues(self, user_input: str, province: str, city: str):
        print(
            f"""Przetwarzanie zapytania: '{user_input}'
            dla województwa: '{province}' i miejscowości: {city}"""
        )

        province_code = PROVINCES.get(province.lower())
        locality = city.strip().lower()

        if not province_code:
            print(f"Nieznany kod województwa: {province}")
            return "Nieznane województwo"

        benefit = user_input[:5]

        params = {
            "format": "json",
            "case": 1,
            "benefit": benefit,
            "province": province_code,
            "locality": locality,
            "page": 1,
            "limit": 10,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                print(f"Otrzymano dane z NFZ: {data}")

                results = [data for data in data.get("data", [])]

                return results
            except Exception as e:
                print(f"Błąd NFZ: {e}")
                return []
