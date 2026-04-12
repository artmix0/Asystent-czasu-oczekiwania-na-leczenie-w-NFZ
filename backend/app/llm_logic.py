import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchCriteria(BaseModel):
    benefit: str = Field(description="Specjalizacja/badanie (np. kardiolog)")

    city: str | None = Field(None, description="Miejscowość")

    province: str | None = Field(None, description="Województwo")

    needs_location: bool = Field(
        False,
        description="Ustaw True, jeżeli użytkownik pyta o terminy w obrębie np 50km",
    )


class GenerateAnswerRequest(BaseModel):
    question: str
    nfz_data: list
    loc_data: dict = None


class LLMExtractor:
    def __init__(self):
        self.model = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="openai/gpt-oss-120b",
            temperature=0,
        )
        self.parser = JsonOutputParser(pydantic_object=SearchCriteria)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Jesteś precyzyjnym parserem danych.
                    Twoim zadaniem jest wyciągnięcie informacji
                    o świadczeniu medycznym, województwie, miejscowości
                    oraz odczytanie intencji użytkownika w celu
                    wykrycia w jakim obrębie chce on szukać terminów.
                    W przypadku braku jednej z tych informacji,
                    zwróć None w adekwatnym polu.
                    Poprawiaj błędy ortograficzne i literówki użytkownika
                    aby dopasować je do polskiego języka.
                    {format_instructions}""",
                ),
                ("user", "{question}"),
            ]
        )
        self.chain = self.prompt | self.model | self.parser

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        reraise=True,
    )
    async def extract_criteria(self, question: str):
        try:
            response = await self.chain.ainvoke(
                {
                    "question": question,
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )

            print(f"LLM zwrócił surową odpowiedź: '{response}'")

            if isinstance(response, str):
                logger.warning(
                    "Parser zwrócił string, próbuję ręcznego rzutowania na JSON"
                )
                return json.loads(response)

            return response

        except Exception as e:
            logger.error(f"Krytyczny błąd ekstrakcji: {e}")
            return {"benefit": question, "province": "", "city": ""}


class LLMResponder:
    def __init__(self):
        self.model = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="openai/gpt-oss-120b",
            temperature=0.2,
            max_tokens=4096,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Jesteś pomocnym asystentem NFZ.
                    Twoim celem jest uprzejme poinformowanie pacjenta o terminach.
                    ZASADY:
                    1. Odpowiadaj miło, ale bądź zwięzły.
                    2. Dla każdej placówki NAJPIERW podaj nazwę świadczenia
                    ('benefit' w danych).
                    3. Sortuj odpowiedź według daty, odległości (jesli podana)
                    oraz kategorii świadczeń
                    (twórz sekcje jeżeli występuje więcej niż
                    jedno świadczenie o tej samej nazwie).
                    4. NIE pisz o telefonie, jeśli go nie ma w danych.
                    5. NIE pisz o dacie aktualizacji, jeśli jej nie ma.
                    6. Jeśli brak danych, odpisz uprzejmie,
                    że obecnie nie znaleziono wolnych terminów.
                    7. NIE podawaj informacji spoza danych NFZ.
                    8. W przypadku gdy podany jest dystans do placówki masz
                    obowiązek go podać oraz zaznaczyć że jest to dystans przybliżony.
                    9. W przypadku braku danych o beneficie poproś
                    o doprecyzowanie pytania.
                    10. ZAWSZE odpowiadaj wyłącznie za pomocą tabeli Markdown jeśli
                    w danych są placówki.""",
                ),
                ("user", "Pacjent pyta: {question}\nDane z NFZ:\n{context}"),
            ]
        )

        self.chain = self.prompt | self.model | StrOutputParser()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _get_stream(self, question, context):
        return self.chain.astream({"question": question, "context": context})

    async def generate_answer(self, request: GenerateAnswerRequest):
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            all_items = []

            if isinstance(request.nfz_data, dict):
                for prov_list in request.nfz_data.values():
                    all_items.extend(prov_list)
            else:
                all_items = request.nfz_data

            all_items.sort(
                key=lambda x: (
                    x.get("distance_km", 999),
                    x.get("attributes", {}).get("dates", {}).get("date", "9999-12-31"),
                )
            )

            simplified_data = []
            for item in all_items:
                attr = item.get("attributes", {})
                dates = attr.get("dates", {})
                termin = dates.get("date")

                if not termin or termin < today_str:
                    continue

                simplified_data.append(
                    {
                        "b": attr.get("benefit", "")[:50],
                        "p": attr.get("provider", "")[:70],
                        "a": f"{attr.get('address', '')}, {attr.get('locality', '')}",
                        "t": termin,
                        "d": item.get("distance_km"),
                    }
                )

                if len(simplified_data) >= 10:
                    break
        except Exception as e:
            logger.warning(f"Błąd podczas upraszczania danych NFZ: {e}")
            simplified_data = request.nfz_data

        try:
            simplified_data.append({"ip_info": request.loc_data})
        except Exception as e:
            logger.warning(f"Błąd podczas dodawania danych geolokalizacyjnych: {e}")

        try:
            stream = await self._get_stream(request.question, str(simplified_data))

            async for chunk in stream:
                content = getattr(chunk, "content", str(chunk))
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Responder Error: {e}")
            yield (
                "Przepraszam, wystąpił problem przy przygotowywaniu odpowiedzi. "
                "Proszę spróbować ponownie."
            )
