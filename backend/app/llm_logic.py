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
    province: str = Field(
        description="Nazwa województwa w Polsce " "(np. mazowieckie, śląskie)"
    )


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
                    o świadczeniu medycznym i województwie.
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
            return {"benefit": question, "province": ""}


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
            3. Format: [Nazwa Benefitu] | Placówka | Adres |
            Termin | nr Telefonu | (Aktualizacja: Data)
            4. NIE pisz o telefonie, jeśli go nie ma w danych.
            5. NIE pisz o dacie aktualizacji, jeśli jej nie ma.
            6. Jeśli brak danych, odpisz uprzejmie,
            że obecnie nie znaleziono wolnych terminów.""",
                ),
                ("user", "Pacjent pyta: {question}\nDane z NFZ:\n{context}"),
            ]
        )

        self.chain = self.prompt | self.model | StrOutputParser()

    async def generate_answer(self, question: str, nfz_data: list):
        if not nfz_data:
            return (
                "Dzień dobry! Przykro mi, ale nie znalazłem o"
                "becnie żadnych wolnych terminów dla wskazanego świadczenia."
            )

        simplified_data = []
        for d in nfz_data:
            print(f"Przetwarzanie rekordu NFZ: {d}")
            attr = d.get("attributes", {})
            dates = attr.get("dates", {})

            simplified_data.append(
                {
                    "benefit": attr.get("benefit"),
                    "miejsce": attr.get("place"),
                    "placowka": attr.get("provider"),
                    "adres": f"{attr.get('address')}, {attr.get('locality')}",
                    "phone": attr.get("phone"),
                    "date": dates.get("date"),
                    "date-situation-as-at": dates.get("date-situation-as-at"),
                }
            )

        try:
            return await self.chain.ainvoke(
                {"question": question, "context": str(simplified_data)}
            )
        except Exception as e:
            logger.error(f"Responder Error: {e}")
            return (
                "Pobrałem dane z NFZ, ale mam problem "
                "z ich przetworzeniem. Spróbuj za chwilę."
            )
