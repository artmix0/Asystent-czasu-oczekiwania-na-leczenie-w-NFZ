import logging

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from geopy.geocoders import Nominatim
from pydantic import BaseModel

from .api_client import NFZClient
from .llm_logic import LLMExtractor, LLMResponder

geolocator = Nominatim(user_agent="nfz_assistant")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

extractor = LLMExtractor()
responder = LLMResponder()
nfz_queues = NFZClient()


class UserRequest(BaseModel):
    question: str
    localization: dict = None


class GenerateAnswerRequest(BaseModel):
    question: str
    nfz_data: list
    loc_data: dict = None


def get_geolocation_reverse(lat: float, lon: float):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="pl")
        if location and location.raw and "address" in location.raw:
            address = location.raw["address"]
            logger.info(address)
            return {
                "city": address.get("city", "") or address.get("village", ""),
                "province": address.get("state", "").replace("województwo", "").strip(),
            }
    except Exception as e:
        logger.error(f"Błąd podczas geolokalizacji: {e}")
    return None


@app.post("/zapytanie")
async def ask_assistant(request: UserRequest):
    try:
        criteria = await extractor.extract_criteria(request.question)
    except Exception as e:
        logger.error(f"LLM Extraction Error: {e}")
        return StreamingResponse(
            responder.generate_answer(
                request.question + " (Błąd ekstrakcji danych)", []
            ),
            media_type="text/plain",
        )

    if request.localization:
        logger.info(request.localization)
        try:
            loc_info = get_geolocation_reverse(
                request.localization.get("latitude"),
                request.localization.get("longitude"),
            )
            logger.info(f"Zidentyfikowana lokalizacja: {loc_info}")
        except Exception as e:
            logger.error(f"Błąd podczas geolokalizacji: {e}")

    benefit_search = criteria.get("benefit", "")

    if not benefit_search:
        return StreamingResponse(
            responder.generate_answer(request.question, []), media_type="text/plain"
        )

    province_name = criteria.get("province", None)

    if not province_name:
        logger.warning("Nie podano województwa, wyszukuje automatycznie")

        province_name = loc_info.get("province") if loc_info else ""

    city_name = criteria.get("city", None)

    if not city_name:
        logger.info("Nie podano miejscowości, wyszukuję automatycznie")

        city_name = loc_info.get("city") if loc_info else ""

    try:
        queues = await nfz_queues.get_queues(benefit_search, province_name, city_name)
    except Exception as e:
        logger.error(f"NFZ Queues Error: {e}")
        return StreamingResponse(
            responder.generate_answer(
                request.question + " (Błąd pobierania kolejek)", []
            ),
            media_type="text/plain",
        )

    return StreamingResponse(
        responder.generate_answer(
            GenerateAnswerRequest(
                question=request.question,
                nfz_data=queues,
                loc_data=request.localization,
            )
        ),
        media_type="text/plain",
    )
