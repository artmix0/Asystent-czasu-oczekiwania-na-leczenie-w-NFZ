import logging

import requests
import streamlit as st
from streamlit_js_eval import get_geolocation
from streamlit_local_storage import LocalStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Asystent czasu oczekiwania na leczenie w NFZ", page_icon="🏥"
)


@st.cache_resource
def get_chat_history():
    return []


if "messages" not in st.session_state:
    st.session_state.messages = get_chat_history()

local_storage = LocalStorage()

saved_geo = local_storage.getItem("geo_permission") == "true"

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.sidebar:
    st.header("Ustawienia")
    if st.button("Wyczyść czat"):
        st.session_state.messages = []
        st.rerun()

    geo = st.toggle(
        "Zezwolenie na użycie danych w celu lokalizacji",
        value="true" if saved_geo else False,
        help="Dzięki temu asystent będzie mógł automatycznie wykrywać "
        "Twoją lokalizację i dostarczać bardziej precyzyjne informacje "
        "o kolejkach w Twojej okolicy.",
        key="geo_toggle",
    )

if geo:
    local_storage.setItem("geo_permission", "true")
else:
    local_storage.setItem("geo_permission", "false")

loc = get_geolocation() if geo or saved_geo else None
print(loc)

prompt = st.chat_input("Np. Gdzie znajdę kardiologa w Poznaniu?")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        final_response = ""

        with st.spinner("Analizuję Twoje pytanie..."):
            payload = {"question": prompt}
            if loc:
                payload["localization"] = loc.get("coords")

            try:
                response = requests.post(
                    "http://backend:8000/zapytanie",
                    json=payload,
                    timeout=60,
                    stream=True,
                )
                response.raise_for_status()

                for chunk in response.iter_content(
                    chunk_size=None, decode_unicode=True
                ):
                    if chunk:
                        final_response += chunk
                        placeholder.markdown(final_response + "▌")

                placeholder.markdown(final_response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": final_response}
                )

            except Exception as e:
                logger.error(f"Błąd: {e}")
                error_msg = (
                    "Przepraszam, wystąpił problem. Spróbuj zadać pytanie ponownie."
                )
                placeholder.markdown(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

            st.rerun()

    # 3. Zapisujemy odpowiedź asystenta
    st.session_state.messages.append({"role": "assistant", "content": final_response})
