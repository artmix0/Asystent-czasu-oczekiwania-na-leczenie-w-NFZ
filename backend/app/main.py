import logging

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .api_client import NFZClient
from .geolocation import Geolocator
from .llm_logic import LLMExtractor, LLMResponder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

extractor = LLMExtractor()
responder = LLMResponder()
nfz_queues = NFZClient()
geolocator = Geolocator()


class UserRequest(BaseModel):
    question: str
    localization: dict = None


class GenerateAnswerRequest(BaseModel):
    question: str
    nfz_data: dict | list
    loc_data: dict = None


@app.post("/zapytanie")
async def ask_assistant(request: UserRequest):
    async def error_stream():
        yield (
            "Przepraszam, wystąpił problem przy przygotowywaniu odpowiedzi. "
            "Proszę spróbować ponownie."
        )

    try:
        criteria = await extractor.extract_criteria(request.question)
        benefit = criteria.get("benefit")
        city_name = criteria.get("city")
        province_name = criteria.get("province")
        needs_location = criteria.get("needs_location")

        loc_info = None
        if request.localization:
            loc_info = geolocator.get_geolocation_reverse(
                request.localization.get("latitude"),
                request.localization.get("longitude"),
            )

        if province_name and not city_name and not needs_location:
            logger.info(f"Szukanie ogólne w województwie: {province_name}")
            queues = await nfz_queues.get_queues(benefit, province=province_name)

        elif city_name or request.localization:
            origin_city = city_name or (loc_info.get("city") if loc_info else None)
            logger.info(f"Szukanie lokalne wokół: {origin_city}")

            city_loc = geolocator.get_city_coords(origin_city)
            province_name = geolocator.get_geolocation_reverse(
                city_loc[0], city_loc[1]
            )["province"]

            queues = await nfz_queues.get_queues(
                benefit, province=province_name, city=origin_city
            )

            if not any(queues.values()) if isinstance(queues, dict) else not queues:
                nearby_provinces = geolocator.get_nearby_provinces(origin_city)
                wider_data = await nfz_queues.get_queues(
                    benefit, province=nearby_provinces
                )

                all_providers = []
                for prov_list in (
                    wider_data.values()
                    if isinstance(wider_data, dict)
                    else [wider_data]
                ):
                    all_providers.extend(prov_list)

                cascade_res = geolocator.find_nearby_cascade(
                    origin_city, all_providers, 50
                )
                queues = cascade_res.get("results", [])

        else:
            return StreamingResponse(
                responder.generate_answer(
                    GenerateAnswerRequest(
                        question=request.question, nfz_data=[], loc_data=None
                    )
                ),
                media_type="text/plain",
            )

        return StreamingResponse(
            responder.generate_answer(
                GenerateAnswerRequest(
                    question=request.question, nfz_data=queues, loc_data=loc_info
                )
            ),
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Krytyczny błąd endpointu /zapytanie: {e}")
        return StreamingResponse(error_stream(), media_type="text/plain")
