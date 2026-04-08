import httpx

PROVINCES = {
    "dolnośląskie": "01", "kujawsko-pomorskie": "02", "lubelskie": "03",
    "lubuskie": "04", "łódzkie": "05", "małopolskie": "06",
    "mazowieckie": "07", "opolskie": "08", "podkarpackie": "09",
    "podlaskie": "10", "pomorskie": "11", "śląskie": "12",
    "świętokrzyskie": "13", "warmińsko-mazurskie": "14",
    "wielkopolskie": "15", "zachodniopomorskie": "16"
}

class NFZBenefits:
    BASE_URL = "https://api.nfz.gov.pl/app-itl-api/benefits"
    
    async def get_benefits(self, user_input: str = ""):
        search_input = user_input[:5]  # Bierzemy tylko pierwsze 5 znaków, żeby zwiększyć szansę na trafienie

        print(f"Sprawdzanie świadczeń zawierających: {search_input}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params={"format": "json", "name": search_input}, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                            
                print(f"Otrzymano dane z NFZ: {data}")

                # Wyciągamy tylko nazwy świadczeń
                benefits = [item for item in data.get("data", [])]
                return benefits
            except Exception as e:
                print(f"Błąd NFZ: {e}")
                return []


class NFZClient:
    BASE_URL = "https://api.nfz.gov.pl/app-itl-api/queues"

    async def get_queues(self, benefit: str, province: str):
        province_code = PROVINCES.get(province.lower())
        if not province_code:
            print(f"Nieznany kod województwa: {province}")
            return []
        params = {
            "format": "json",
            "case": 1,
            "benefit": benefit,
            "province": province_code,
            "page": 1,
            "limit": 10 
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                print(f"Otrzymano dane z NFZ: {data}")

                # Wyciągamy tylko to, co nas interesuje
                results = []
                for item in data.get("data", []):
                    attr = item.get("attributes", {})
                    results.append({
                        "hospital": attr.get("provider"),
                        "city": attr.get("locality"),
                        "date": attr.get("dates", {}).get("first-available-day"),
                        "phone": attr.get("phone"),
                        "address": attr.get("address")
                    })
                return results
            except Exception as e:
                print(f"Błąd NFZ: {e}")
                return []
            