import streamlit as st
import fitz  # PyMuPDF
import json
import io
import zipfile
from openai import OpenAI
import os

# === CONFIG ===
DEFAULT_API_KEY = "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"

# --- UI ---
st.set_page_config(page_title="Scene_Gen_V3.2", layout="wide")
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            background-color: #0f0f0f;
            color: #00ffcc;
            font-family: 'Courier New', monospace;
        }
        .stButton>button {
            background-color: #00ffcc;
            color: black;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.5em 1.5em;
        }
        .stTextInput>div>div>input {
            background-color: #111;
            color: #00ffcc;
        }
        .stFileUploader>div>div {
            color: #00ffcc;
        }
        .stCodeBlock pre {
            background-color: #111;
            color: #33ff66;
        }
    </style>
    <h1 style='font-family:Courier New, monospace; color:#00ffcc;'>SCENE_GEN_V3.2</h1>
""", unsafe_allow_html=True)

# API key input o preinserita
if DEFAULT_API_KEY:
    api_key = DEFAULT_API_KEY
    st.text_input("OpenAI API Key (preloaded)", value=DEFAULT_API_KEY, type="password", disabled=True)
else:
    api_key = st.text_input("OpenAI API Key", type="password")

# Upload PDF
uploaded_file = st.file_uploader("Upload your treatment or script (PDF)", type=["pdf"])

# Bottone per avviare il processo
if st.button("ELABORATE"):
    if not uploaded_file or not api_key:
        st.error("Please upload a PDF and insert your API Key.")
        st.stop()

    with st.spinner("Extracting text from PDF..."):
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = "\n".join([page.get_text() for page in pdf])

    prompt = f"""
Analyze the following document and identify a list of SCENES. For each scene, provide:
- A TITLE (short)
- A BRIEF DESCRIPTION (1 line)
- A list of 5-7 TAGS in English useful for searching visual references online (e.g. ShotDeck, Flim, Pinterest).
Return the result in valid JSON format like this:
[
  {{"title": "Beach Entry", "description": "Children running with paddleboards", "tags": ["beach kids", "paddle board", "sunlight", "vacation", "morning energy"]}},
  ...
]

TEXT:
""" + full_text

    with st.spinner("Contacting GPT-4o..."):
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for film pre-production."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

    try:
        gpt_output = response.choices[0].message.content.strip()
        if gpt_output.startswith("```"):
            lines = gpt_output.strip("`").split("\n")
            if lines[0].strip().startswith("json"):
                lines = lines[1:]
            lines = [line for line in lines if not line.strip().startswith("```")]
            gpt_output = "\n".join(lines).strip()
        data = json.loads(gpt_output)
    except json.JSONDecodeError:
        st.error("⚠️ GPT returned an incomplete or broken JSON. Try simplifying your input or shorten the document.")
        st.code(response.choices[0].message.content)
        st.stop()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for scene in data:
            folder_name = scene['title'].replace(" ", "_").replace("/", "-")
            zip_file.writestr(f"{folder_name}/.keep", "")
    zip_buffer.seek(0)

    st.download_button("Download ZIP with scene folders", zip_buffer, "storyboard_folders.zip")

    st.markdown("<h3 style='font-family:Courier New, monospace; color:#00ffcc;'>Scene Tags</h3>", unsafe_allow_html=True)
    for scene in data:
        st.markdown(f"<b style='font-family:Courier New, monospace; color:#00ffcc;'>{scene['title']}</b> – {scene['description']}", unsafe_allow_html=True)
        st.code(", ".join(scene['tags']), language="markdown")
