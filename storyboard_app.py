import streamlit as st
import fitz  # PyMuPDF
import json
import io
import zipfile
from openai import OpenAI

# --- UI ---
st.set_page_config(page_title="Storyboard Tag Generator", layout="wide")
st.title("🎬 Storyboard Generator with GPT-4o")

# API key input
api_key = st.text_input("🔑 Inserisci la tua OpenAI API Key", type="password")

# Upload PDF
uploaded_file = st.file_uploader("📄 Carica un trattamento o script in PDF", type=["pdf"])

# Bottone per avviare il processo
if st.button("🚀 Avvia Analisi GPT e Generazione Cartelle"):
    if not uploaded_file or not api_key:
        st.error("Devi caricare un PDF e inserire la tua API Key.")
        st.stop()

    # Estrai testo dal PDF
    with st.spinner("Estrazione testo dal PDF..."):
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = "\n".join([page.get_text() for page in pdf])

    # Prompt per GPT-4o
    prompt = f"""
Analizza il seguente documento e identifica un elenco di SCENE. Per ciascuna scena fornisci:
- Un TITOLO (breve)
- Una BREVE DESCRIZIONE (1 riga)
- Una lista di 5-7 TAG in inglese utili per cercare immagini su siti come ShotDeck, Flim o Pinterest.
Restituisci la risposta in formato JSON come questo:
[
  {{"title": "Beach Entry", "description": "Children running with paddleboards", "tags": ["beach kids", "paddle board", "sunlight", "vacation", "morning energy"]}},
  ...
]

TESTO:
""" + full_text[:12000]  # limitiamo la lunghezza per ora

    # Chiamata GPT-4o con nuova sintassi
    with st.spinner("💬 Chiamata a GPT-4o in corso..."):
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for film pre-production."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

    # Parsing della risposta
    try:
        gpt_output = response.choices[0].message.content
        data = json.loads(gpt_output)
    except Exception as e:
        st.error("Errore nel parsing della risposta GPT. Ecco il contenuto grezzo:")
        st.code(gpt_output)
        st.stop()

    # Genera ZIP in memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for scene in data:
            folder_name = scene['title'].replace(" ", "_").replace("/", "-")
            zip_file.writestr(f"{folder_name}/.keep", "")
    zip_buffer.seek(0)

    st.success("✅ Generazione completata!")
    st.download_button("⬇️ Scarica ZIP con cartelle delle scene", zip_buffer, "storyboard_folders.zip")

    # Mostra tag con copia-incolla
    st.markdown("### 🏷️ Tag per ogni scena")
    for scene in data:
        st.markdown(f"**🎬 {scene['title']}** – {scene['description']}")
        st.code(", ".join(scene['tags']), language="markdown")
