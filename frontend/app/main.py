import requests
import streamlit as st

st.set_page_config(
    page_title="Asystent czasu oczekiwania na leczenie w NFZ", page_icon="🏥"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Ustawienia")
    if st.button("Wyczyść czat"):
        st.session_state.messages = []
        st.rerun()

    geo = st.toggle("Zezwolenie na użycie danych w celu lokalizacji", value=False)

    if geo:
        st.info(
            "Dzięki temu asystent będzie mógł automatycznie "
            "wykrywać Twoją lokalizację i dostarczać bardziej "
            "precyzyjne informacje o kolejkach w Twojej okolicy."
        )
    else:
        st.info(
            "Nie udostępniając danych lokalizacyjnych, nadal "
            "możesz zadawać pytania, ale wyniki mogą być mniej "
            "precyzyjne, zwłaszcza jeśli nie podasz województwa "
            "lub miejscowości w swoim pytaniu."
        )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Np. Gdzie znajdę kardiologa w Poznaniu?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Analizuję Twoje pytanie..."):
            response = requests.post(
                "http://backend:8000/zapytanie", params={"question": prompt}, timeout=15
            )
            final_response = response.json().get(
                "ai_answer", "Nie udało się uzyskać odpowiedzi."
            )
            st.markdown(final_response)

    # 3. Zapisujemy odpowiedź asystenta
    st.session_state.messages.append({"role": "assistant", "content": final_response})
