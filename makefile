ENV_NAME := friendly-route
PYTHON_VERSION := 3.10

.PHONY: help env create install clean

help:
	@echo "Targets:"
	@echo "  make env      -> crea environment conda"
	@echo "  make install  -> install requirements"
	@echo "  make clean    -> clean environment"

env:
	conda create -y -n $(ENV_NAME) python=$(PYTHON_VERSION)

install:
	conda run -n $(ENV_NAME) pip install -r requirements.txt
	conda run -n $(ENV_NAME) pip install ruff

create: env install

clean:
	conda remove -y -n $(ENV_NAME) --all

lint:
	conda run -n $(ENV_NAME) ruff check .
	conda run -n $(ENV_NAME) ruff format .