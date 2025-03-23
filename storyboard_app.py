import streamlit as st
import fitz  # PyMuPDF
import openai
import io
import zipfile

# --- UI ---
st.set_page_config(page_title="Storyboard Tag Generator", layout="wide")
st.title("🎬 Storyboard Generator with GPT-4o")

# API key input
api_key = st.text_input("🔑 Inserisci la tua OpenAI API Key", type="password")

uploaded_file = st.file_uploader("📄 Carica un trattamento o script in PDF", type=["pdf"])

if uploaded_file and api_key:
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

    # Chiamata API OpenAI
    with st.spinner("💬 Invio a GPT-4o per l'elaborazione..."):
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for film pre-production."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

    # Parsing della risposta
    import json
    try:
        data = json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error("Errore nel parsing della risposta GPT:")
        st.code(response.choices[0].message.content)
        st.stop()

    # Genera file ZIP con cartelle
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for scene in data:
            folder_name = scene['title'].replace(" ", "_").replace("/", "-")
            zip_file.writestr(f"{folder_name}/.keep", "")
    zip_buffer.seek(0)

    st.success("✅ Generazione completata!")
    st.download_button("⬇️ Scarica ZIP con cartelle delle scene", zip_buffer, "storyboard_folders.zip")

    # Mostra tabella tag
    st.markdown("### 🏷️ Tag per ogni scena")
    for scene in data:
        st.markdown(f"**🎬 {scene['title']}** – {scene['description']}")
        st.code(", ".join(scene['tags']), language="markdown")
