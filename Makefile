install:
	pip install -r requirements.txt

lint:
	ruff check

test:
	pytest

start_bot:
	python ./src/bot.py