install:
	pip install -r requirements.txt

lint:
	ruff check

typecheck:
	mypy src/

test:
	pytest

check: lint typecheck test

start_bot:
	python ./src/bot.py