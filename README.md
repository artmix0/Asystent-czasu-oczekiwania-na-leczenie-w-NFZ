# Asystent czasu oczekiwania na leczenie w NFZ

Nowoczesna aplikacja webowa asystenta pacjenta w publicznej służbie zdrowia w Polsce. Umożliwia wyszukiwanie dostępnych terminów leczenia i badań w NFZ na podstawie zapytań w języku naturalnym, z automatycznym wykrywaniem lokalizacji użytkownika.

---

## Spis treści

- [O projekcie](#o-projekcie)
- [Wymagania](#wymagania)
- [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
- [Jak używać aplikację](#jak-używać-aplikację)
- [Konfiguracja zmiennych środowiskowych](#konfiguracja-zmiennych-środowiskowych)
- [Architektura](#architektura)
- [API backendu](#api-backendu)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## O projekcie

**Asystent czasu oczekiwania na leczenie w NFZ** to inteligentna aplikacja, która:

- Przyjmuje oraz analizuje pytania pacjentów w języku naturalnym
- Automatycznie wykrywa lokalizację użytkownika i wyszukuje placówki medyczne w pobliżu
- Pobiera dane o kolejkach i dostępnych terminach z API NFZ
- Generuje spersonalizowane odpowiedzi przy użyciu modelów LLM (Groq)
- Wyświetla wyniki w intuicyjnym interfejsie czatowego

Aplikacja jest gotowa do wdrożenia za pomocą Docker i wspiera wdrażanie lokalne oraz na serwerach produkcyjnych.

---

## Wymagania

Przed uruchomieniem projektu upewnij się, że posiadasz:

- **Docker Desktop** (dla Windows/Mac) lub **Docker + Docker Compose** (dla Linux)
  - [Pobierz Docker](https://www.docker.com/products/docker-desktop)
- **Git** (do klonowania repozytorium)
  - [Pobierz Git](https://git-scm.com/downloads)
- **Klucz API Groq** – wymagany do działania logiki LLM
  - [Zarejestruj się na Groq Console](https://console.groq.com)
- **Połączenie internetowe** – do komunikacji z:
  - API NFZ
  - Usługi geolokalizacji (OpenStreetMap/Nominatim)
  - Usługi LLM Groq

---

## Instalacja i uruchomienie

### Krok 1: Klonowanie repozytorium

```bash
git clone https://github.com/twoj-uzytkownik/Asystent-czasu-oczekiwania-na-leczenie-w-NFZ.git
cd Asystent-czasu-oczekiwania-na-leczenie-w-NFZ
```

### Krok 2: Konfiguracja zmiennych środowiskowych

**Opcja A: Wersja testowa**

Jeśli pobierasz projekt już skonfigurowany do testów, plik `backend/.env` powinien być już obecny. Sprawdź, czy plik istnieje w katalogu `backend/`:

```bash
# Windows (PowerShell)
Test-Path backend\.env

# Linux/Mac
ls backend/.env
```

Jeśli plik istnieje, możesz go użyć od razu do uruchomienia.

**Opcja B: Włastny klucz API Groq**

Jeśli chcesz użyć własnego klucza API (wymagane do wydania produkcyjnego), postępuj poniżej:

1. Utwórz lub edytuj plik `.env` w katalogu `backend/`:

```bash
# Windows (PowerShell)
New-Item -Path backend\.env -ItemType File

# Linux/Mac
touch backend/.env
```

2. Otwórz ten plik w edytorze tekstowym i dodaj:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

3. **Jak znaleźć klucz Groq API:**
   - Przejdź na https://console.groq.com
   - Zaloguj się lub utwórz konto
   - Przejdź do sekcji "API Keys"
   - Kliknij "Create New API Key"
   - Skopiuj wygenerowany klucz
   - Wklej go do pliku `backend/.env`

> **Ważne:** Wklej tutaj swój rzeczywisty klucz API z [Groq Console](https://console.groq.com)

### Krok 3: Uruchomienie aplikacji za pomocą Docker Compose

```bash
docker-compose up --build
```

Użyj tego polecenia za pierwszym razem lub gdy zmienisz dependency w `requirements.txt`.

Jeśli aplikacja już jest zbudowana i chcesz ją tylko uruchomić:

```bash
docker-compose up
```

### Krok 4: Dostęp do aplikacji

Po pomyślnym uruchomieniu otwórz przeglądarkę i przejdź do:

- **Frontend (UI):** http://localhost:8501
- **Backend (API):** http://localhost:8000

---

## Jak używać aplikację

### Interfejs użytkownika

1. **Otwórz aplikację**  
   Przejdź do http://localhost:8501 w przeglądarce

2. **Włącz lokalizację (opcjonalnie)**  
   - Na pasku bocznym ("Ustawienia") zaznacz opcję "Zezwolenie na użycie danych w celu lokalizacji"
   - Potwierdź dostęp do lokalizacji w oknie przeglądarki
   - Dzięki temu asystent będzie wyszukiwać placówki w Twojej okolicy

3. **Zadaj pytanie**  
   W polu "Np. Gdzie znajdę kardiologa w Poznaniu?" wpisz swoje pytanie, np.:
   - "Gdzie mogę znaleźć kardiologa w moim mieście?"
   - "Jakie są najbliższe kolejki do dentysty?"
   - "Gdzie leczyć oczy we Wrocławiu?"

4. **Przeczytaj odpowiedź**  
   Asystent wyświetli dostępne placówki, specjalizacje i przybliżone czasy oczekiwania

### Przykładowe pytania

```
- Jakie są dostępne terminy u ginekologa w Krakowie?
- Gdzie w mojej okolicy leczyć depresję?
- Ile wynosi średni czas oczekiwania na endokrynologa?
- Gdzie znaleźć laryngologa?
- Jaki jest najbliższy termin na rezonans w promieniu 50 km od Warszawy?
```

### Czyszczenie historii czatu

Kliknij przycisk "Wyczyść czat" w ustawieniach, aby usunąć historię rozmów.

---

## Konfiguracja zmiennych środowiskowych

### Plik `.env` dla backendu

Plik `backend/.env` zawiera wrażliwe dane konfiguracyjne. 

#### Wymagane zmienne

| Zmienna | Opis | Przykład |
|---------|------|---------|
| `GROQ_API_KEY` | Klucz API do usługi Groq (LLM) | `gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

### Gdzie znaleźć poufne dane

| Dane | Źródło | Gdzie |
|------|--------|-------|
| GROQ_API_KEY | Groq Console | https://console.groq.com/keys |

### Bezpieczeństwo

- **Nie dodawaj `.env` do Git** – plik jest na `.gitignore`
- **Nigdy nie sharej kluczy publicznych** – traktuj je jak hasła
- **Regularnie regeneruj klucze** – jeśli podejrzewasz wycieki
- **Używaj różnych kluczy** dla różnych środowisk (dev, test, prod)

---

## Architektura

Aplikacja składa się z dwóch niezależnych serwisów działających w kontenerach Docker:

```
┌─────────────────────────────────────────────────┐
│           FRONTEND (Streamlit)                   │
│         http://localhost:8501                    │
│  - Interfejs czatu                              │
│  - Geolokalizacja przeglądarki                  │
│  - Komunikacja z backendem                      │
└──────────────┬──────────────────────────────────┘
               │ POST /zapytanie
               │ (JSON)
┌──────────────▼──────────────────────────────────┐
│           BACKEND (FastAPI)                      │
│         http://localhost:8000                    │
│  - Ekstrakcja kryteriów (LLM)                   │
│  - Pobieranie danych z API NFZ                  │
│  - Geokodowanie adresów                         │
│  - Generowanie odpowiedzi (LLM)                │
└──────────────┬──────────────────────────────────┘
               │
        ┌──────┴──────┬──────────────┐
        │             │              │
   ┌────▼───┐  ┌──────▼───┐  ┌──────▼─────┐
   │ API NFZ │  │ Nominatim│  │   Groq     │
   │ (kolejki)   │(geoloc) │  │   (LLM)    │
   └────────┘  └──────────┘  └────────────┘
```

### Komponenty backendu

| Moduł | Funkcja |
|-------|---------|
| `main.py` | Punkt wejścia FastAPI, routing |
| `api_client.py` | Klient API NFZ, pobieranie kolejek |
| `geolocation.py` | Geokodowanie, obliczanie dystansów |
| `llm_logic.py` | Ekstrakcja kryteriów, generowanie odpowiedzi |

---

## API backendu

### Endpoint: POST /zapytanie

**Opis:**  
Przyjmuje pytanie użytkownika i opcjonalną lokalizację, zwraca streamed tekst odpowiedzi.

**URL:**  
```
http://backend:8000/zapytanie
```

**Metoda:** `POST`

**Nagłówki:**
```
Content-Type: application/json
```

## Narzędzia developerskie

### Zastavienie aplikacji

```bash
# Zatrzymaj kontenery, ale zachowaj dane
docker-compose stop

# Zastavowi kontenery i usuń je
docker-compose down

# Usuń wszystkie dane (kontenery, obrazy, wolumeny)
docker-compose down -v
```

### Podgląd logów

```bash
# Wszystkie logi
docker-compose logs -f

# Logi backendu
docker-compose logs -f backend

# Logi frontendu
docker-compose logs -f frontend
```

### Przebudowanie obrazów

```bash
# Przebuduj bez cache
docker-compose build --no-cache

# Uruchom z przebudową
docker-compose up --build
```

---

## Rozwiązywanie problemów

### Problem: "Connection refused" na porcie 8000

**Przyczyna:** Backend nie został uruchomiony.

**Rozwiązanie:**
```bash
docker-compose logs backend
docker-compose restart backend
```

### Problem: "Invalid API Key" przy pytaniu

**Przyczyna:** Klucz Groq jest niepoprawny lub wygasł.

**Rozwiązanie:**
1. Przejdź na https://console.groq.com/keys
2. Sprawdź, czy klucz jest aktywny
3. Jeśli trzeba, utwórz nowy klucz
4. Zaktualizuj plik `backend/.env`
5. Przebuduj kontenery: `docker-compose up --build`

### Problem: "Permission denied" przy pliku .env

**Przyczyna:** Brak uprawnień do odczytu pliku.

**Rozwiązanie (Linux/Mac):**
```bash
chmod 644 backend/.env
```

### Problem: Lokalizacja nie działa

**Przyczyna:** Przeglądarki odmówiła dostępu.

**Rozwiązanie:**
1. Sprawdź ustawienia lokalizacji przeglądarki
2. Wyznacz pozwolenie dla localhost:8501
3. Zaznacz "Zezwolenie na użycie danych w celu lokalizacji" w aplikacji
4. Odśwież stronę (F5)

### Problem: Brak odpowiedzi od API NFZ

**Przyczyna:** NFZ API może być niedostępne.

**Rozwiązanie:**
1. Sprawdź połączenie internetowe
2. Poczekaj kilka minut i spróbuj ponownie
3. Sprawdź logami: `docker-compose logs backend`

### Problem: "ModuleNotFoundError" w backendzie

**Przyczyna:** Zmieniły się zależności w `requirements.txt`.

**Rozwiązanie:**
```bash
docker-compose build --no-cache
docker-compose up
```

---

## Licencja

Projekt jest dostępny na licencji określonej w pliku [LICENSE](LICENSE).

---

## Kontakt

W przypadku pytań lub problemów, proszę otworzyć **Issue** w repozytorium:  
https://github.com/artmix0/Asystent-czasu-oczekiwania-na-leczenie-w-NFZ/issues

---

**Ostatnia aktualizacja:** Kwiecień 2026
