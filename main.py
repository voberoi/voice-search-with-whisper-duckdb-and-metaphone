import streamlit as st

from search import get_top_k_matches, get_wines

title = "Voice Search with OpenAI's Whisper, DuckDB, and the Metaphone Algorithm"

st.set_page_config(page_title=title, layout="wide")

st.title(title)
st.write("This is a demo that accompanies the following blog post: <link>.")
st.write("Code for the demo is available here: <link>")
st.divider()

transcript = st.text_input("Enter your transcript")
button_clicked = st.button("Search")

if button_clicked:
    results = get_top_k_matches(transcript)
    markdown = ""
    for result in results:
        markdown += f"* {result}\n"
    st.markdown(markdown)

st.write("The following are all wines in inventory:")
st.table(get_wines())
