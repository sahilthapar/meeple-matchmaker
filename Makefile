install:
	pip install -r requirements.txt

lint:
	pylint tests src

test:
	pytest

start_bot:
	python ./src/bot.py