import streamlit as st
import os
import zipfile
import io

# Titolo app
st.title("📂 Storyboard Folder & Tag Generator")

st.markdown("""
Carica un PDF (es. un trattamento), inserisci le scene, e ottieni:
1. Uno ZIP con le cartelle per ogni scena
2. Una lista di tag generati automaticamente per la ricerca reference
""")

# Upload del file PDF (placeholder per futuro parsing automatico)
uploaded_file = st.file_uploader("Carica il trattamento in PDF", type=["pdf"])

# Inserimento manuale delle scene
titles_input = st.text_area("Inserisci i titoli delle scene, una per riga:",
                           placeholder="01 Beach – Kids with SUP\n02 Promenade – Family restaurant\n...")

# Funzione per generare tag (mock semplice per ora)
def generate_tags(title):
    keywords = title.lower().replace("–", "").replace("-", "").split()
    extra = ["cinematic", "natural light", "POV", "reference", "emotion"]
    return ", ".join(keywords[:4] + extra[:3])

# Quando premi il pulsante:
if st.button("📦 Genera ZIP e mostra i tag"):
    if not titles_input.strip():
        st.warning("Inserisci almeno una scena per continuare.")
    else:
        scene_titles = titles_input.strip().split("\n")

        # Crea file ZIP in memoria
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for title in scene_titles:
                folder_name = title.strip().replace(" ", "_").replace("/", "-")
                zip_file.writestr(f"{folder_name}/.keep", "")  # File segnaposto per tenere la cartella

        zip_buffer.seek(0)
        st.download_button("⬇️ Scarica ZIP con cartelle", zip_buffer, "storyboard_folders.zip")

        st.markdown("---")
        st.markdown("### 🏷️ Tag generati automaticamente")

        for title in scene_titles:
            tag_text = generate_tags(title)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{title}**")
            with col2:
                st.code(tag_text, language="markdown")
                st.button(f"📋 Copia tag – {title}", key=title)

        st.info("I tag sono generati automaticamente a partire dai titoli delle scene. Puoi personalizzarli nel codice se vuoi risultati più avanzati.")
