import logging

from fastapi import FastAPI, HTTPException

from .api_client import NFZClient
from .llm_logic import LLMExtractor, LLMResponder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

extractor = LLMExtractor()
responder = LLMResponder()
nfz_queues = NFZClient()


@app.get("/zapytanie")
async def ask_assistant(question: str):
    try:
        criteria = await extractor.extract_criteria(question)
    except Exception as e:
        logger.error(f"LLM Extraction Error: {e}")
        raise HTTPException(status_code=500, detail="Błąd analizy pytania przez AI")

    benefit_search = criteria.get("benefit", "")
    province_name = criteria.get("province", "")

    try:
        queues = await nfz_queues.get_queues(benefit_search, province_name)
    except Exception as e:
        logger.error(f"NFZ Queues Error: {e}")
        raise HTTPException(status_code=502, detail="Błąd pobierania kolejek z NFZ")

    try:
        final_answer = await responder.generate_answer(question, queues)
    except Exception as e:
        logger.error(f"LLM Responder Error: {e}")
        return {
            "ai_answer": "Pobrałem dane, ale wystąpił "
            "błąd przy generowaniu odpowiedzi.",
            "raw_data": queues[:3],
        }

    return {
        "ai_answer": final_answer,
        "details": {"benefit": benefit_search, "province": province_name},
    }
