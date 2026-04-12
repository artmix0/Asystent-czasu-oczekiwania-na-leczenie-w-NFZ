# Asystent czasu oczekiwania na leczenie w NFZ

Nowoczesna aplikacja webowa działająca jako asystent pacjenta w publicznej służbie zdrowia w Polsce.
Umożliwia wyszukiwanie dostępnych terminów leczenia i badań w NFZ na podstawie zapytań w języku naturalnym.

## Architektura

Aplikacja składa się z dwóch serwisów:

- **backend**: FastAPI, pobiera dane z API NFZ, analizuje zapytania użytkownika przy użyciu LLM i zwraca odpowiedź.
- **frontend**: Streamlit, interfejs czatu użytkownika, obsługa geolokalizacji i wyświetlanie odpowiedzi.

Komunikacja odbywa się przez `docker-compose`, gdzie frontend wywołuje backend pod endpointem `POST /zapytanie`.

## Funkcjonalność

- przyjmowanie zapytań naturalnych od użytkownika
- ekstrakcja kryteriów wyszukiwania: świadczenie, województwo, miasto
- pobieranie kolejek z API NFZ
- obsługa lokalizacji użytkownika przez geolokalizację przeglądarki
- wyszukiwanie wyników w pobliżu z wykorzystaniem dystansu i promienia wyszukiwania
- generowanie zwięzłych odpowiedzi użytkownikowi na podstawie wyników NFZ

## Struktura katalogów

- `backend/`
  - `Dockerfile`
  - `requirements.txt`
  - `app/`
    - `main.py` – punkt wejścia FastAPI
    - `api_client.py` – klient NFZ i pobieranie kolejek
    - `geolocation.py` – geokodowanie i obliczanie dystansów
    - `llm_logic.py` – ekstrakcja kryteriów i generowanie odpowiedzi

- `frontend/`
  - `Dockerfile`
  - `requirements.txt`
  - `app/`
    - `main.py` – UI Streamlit

- `docker-compose.yml` – kompozycja kontenerów backend i frontend

## Wymagania

- Docker i Docker Compose
- Python 3.13 (w kontenerach)
- klucz API dla modelu GROQ w backendzie: `GROQ_API_KEY`
- dostęp do internetu dla:
  - API NFZ
  - usługi geolokalizacji (geopy / Nominatim)
  - usługi LLM Groq

## Uruchomienie

1. W katalogu głównym projektu uruchom:

```bash
docker-compose up --build
```

2. Po uruchomieniu serwisów frontend będzie dostępny na:

- `http://localhost:8501`

3. Backend będzie dostępny na:

- `http://localhost:8000`

## Konfiguracja środowiska

W backendzie można ustawić zmienną środowiskową `GROQ_API_KEY`, aby dostęp do modelu Groq był możliwy.

Przykład pliku `backend/.env`:

```env
GROQ_API_KEY=twoj_klucz_groq
```

## API backendu

- `POST /zapytanie`
  - przyjmuje JSON z polami:
    - `question` (string)
    - `localization` (opcjonalnie, obiekt z `latitude` i `longitude`)
  - zwraca strumieniowaną odpowiedź tekstową wygenerowaną przez LLM

## Uwaga

Frontend używa `streamlit_js_eval` do pobrania lokalizacji użytkownika. Jeśli użytkownik odmówi uprawnień, aplikacja może wyszukiwać tylko po ręcznych kryteriach.

## Potencjalne ograniczenia

- Aplikacja wymaga działającego źródła danych NFZ.
- Generowanie odpowiedzi opiera się na modelu Groq i kluczu API.
- Brak testów automatycznych w repozytorium.

## Rozwój

Aby rozbudować projekt, warto:

- dodać testy jednostkowe i integracyjne
- obsłużyć błędy walidacji danych w backendzie bardziej szczegółowo
- dodać dokumentację API i przykładowe zapytania
- poprawić obsługę braku wyników i niepełnych kryteriów
