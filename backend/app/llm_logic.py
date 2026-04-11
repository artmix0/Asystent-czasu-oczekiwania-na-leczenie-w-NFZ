import json
import logging
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchCriteria(BaseModel):
    benefit: str = Field(
        description="Nazwa specjalizacji medycznej lub badania "
        "(np. kardiolog, rtg, okulista)"
    )

    city: str = Field(
        description="Nazwa miejscowości w Polsce " "(np. Warszawa, Kraków, Gdańsk)"
    )

    province: str = Field(
        description="Nazwa województwa w Polsce " "(np. mazowieckie, śląskie)"
    )


class GenerateAnswerRequest(BaseModel):
    question: str
    nfz_data: list
    loc_data: dict = None


class LLMExtractor:
    def __init__(self):
        self.model = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            temperature=0,
        )
        self.parser = JsonOutputParser(pydantic_object=SearchCriteria)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Jesteś precyzyjnym parserem danych.
                    Twoim zadaniem jest wyciągnięcie informacji
                    o świadczeniu medycznym, województwie i miejscowości.
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
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
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
                    3. Sortuj odpowiedź według daty oraz kategorii świadczeń
                    (twórz sekcje jeżeli występuje więcej niż
                    jedno świadczenie o tej samej nazwie).
                    4. NIE pisz o telefonie, jeśli go nie ma w danych.
                    5. NIE pisz o dacie aktualizacji, jeśli jej nie ma.
                    6. Jeśli brak danych, odpisz uprzejmie,
                    że obecnie nie znaleziono wolnych terminów.
                    7. NIE podawaj informacji spoza danych NFZ.
                    8. W przypadku braku danych o beneficie poproś
                    o doprecyzowanie pytania.""",
                ),
                ("user", "Pacjent pyta: {question}\nDane z NFZ:\n{context}"),
            ]
        )

        self.chain = self.prompt | self.model | StrOutputParser()

    async def generate_answer(self, request: GenerateAnswerRequest):
        try:
            simplified_data = []
            for d in request.nfz_data:
                attr = d.get("attributes", {})
                dates = attr.get("dates", {})
                simplified_data.append(
                    {
                        "benefit": attr.get("benefit"),
                        "miejsce": attr.get("place"),
                        "placowka": attr.get("provider"),
                        "adres": f"{attr.get('address')}, {attr.get('locality')}",
                        "phone": attr.get("phone"),
                        "pierwszy termin": dates.get("date"),
                        "aktualizacja": attr.get("updated_at"),
                    }
                )
        except Exception as e:
            logger.warning(f"Błąd podczas upraszczania danych NFZ: {e}")
            simplified_data = request.nfz_data

        try:
            simplified_data.append({"ip_info": request.loc_data})
        except Exception as e:
            logger.warning(f"Błąd podczas dodawania danych geolokalizacyjnych: {e}")

        try:
            async for chunk in self.chain.astream(
                {"question": request.question, "context": str(simplified_data)}
            ):
                content = getattr(chunk, "content", str(chunk))
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Responder Error: {e}")
            yield "Wystąpił problem podczas generowania odpowiedzi."
