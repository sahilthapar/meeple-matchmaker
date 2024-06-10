install:
	pip install -r requirements.txt

lint:
	ruff check
	mypy src
	mypy test

start_bot:
	python ./src/bot.py