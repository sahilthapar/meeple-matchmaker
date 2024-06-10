install:
	pip install -r requirements.txt

lint:
	ruff check
	mypy src
	mypy tests

test:
	pytest

start_bot:
	python ./src/bot.py