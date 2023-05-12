import io
import tempfile

import streamlit as st
from audiorecorder import audiorecorder

import openai

from search import get_top_k_matches, get_wines

openai.api_key = st.secrets["OPENAI_API_KEY"]


def transcribe(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmpfile:
        tmpfile.write(audio_bytes)
        tmpfile.seek(0)
        return openai.Audio.transcribe(
            "whisper-1",
            tmpfile,
            temperature=0.2,
            prompt="This transcript contains the name of a wine.",
        )["text"]


title = "Voice Search with OpenAI's Whisper, DuckDB, and the Metaphone Algorithm"

st.set_page_config(page_title=title, layout="wide")

st.title(title)
st.write("This is a demo that accompanies the following blog post: <link>.")
st.write("Code for the demo is available here: <link>")
st.divider()

audio = audiorecorder("Say a wine:", "Recording...")


if len(audio) > 0:
    with st.spinner("Transcribing..."):
        transcript = transcribe(audio.tobytes())

    st.write(f'**Transcript**: "{transcript}"')

    st.audio(audio.tobytes())
    results = get_top_k_matches(transcript, k=10)
    markdown = ""
    for i, result in enumerate(results):
        num = i + 1
        markdown += f"{num}. {result}\n"
    st.markdown(markdown)
    st.divider()

st.header("Inventory")
st.write("The following are all wines in inventory:")
st.table(get_wines())
