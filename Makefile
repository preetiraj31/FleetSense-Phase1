.PHONY: install lint test dashboard

install:
	pip install -r requirements.txt

lint:
	ruff check .

test:
	pytest tests/

dashboard:
	streamlit run dashboard.py