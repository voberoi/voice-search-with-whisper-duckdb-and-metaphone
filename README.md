# Voice search with OpenAI Whisper, DuckDB, and Metaphone

This repository is a companion to [Helping sommeliers inventory wines faster with Whisper, DuckDB, and Metaphone](https://vikramoberoi.com/helping-sommeliers-inventory-wine-faster-with-whisper-duckdb-and-metaphone/). Read the blog post for an explanation of how this code works.

This a Streamlit app. You can check it out on [Streamlit Cloud](https://voice-search-with-whisper-duckdb-and-metaphone.streamlit.app/).

## Running the Streamlit app locally

You'll need to place your OpenAI API key in `.streamlit/secrets.toml`:

```
OPENAI_API_KEY = "<your-openai-api-key>"
```

Then run `poetry run streamlit run main.py`.

This demo uses OpenAI whisper, which [costs $0.006/minute as of May 2023](https://openai.com/pricing). It's cheap.


## Navigating this codebase

* `index.py` prepares all the indexes in `wines.duckdb`.
* `search.py` implements querying our indexes.
* `main.py` is our Streamlit app.

The blog post walks through our search indexes and how we query them in detail.

## Contributing

This codebase is purely educational. If you see errors, please open a PR. If you want to make improvements, I encourage you to fork it and talk about your changes -- [let me know if you do](https://twitter.com/voberoi)!
