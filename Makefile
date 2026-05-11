include .env
export

.PHONY: run sync

run:
	uv run python bot.py

sync:
	uv sync
