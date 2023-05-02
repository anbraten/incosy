all:
	streamlit run --server.headless=true index.py

install:
	pip install -r requirements.txt