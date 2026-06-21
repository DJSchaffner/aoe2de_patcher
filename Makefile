# Variables
VENV=.venv
SCRIPTS=$(VENV)/$(shell if [ -f .venv/bin/pip ]; then echo bin; else echo Scripts; fi)
PYTHON=$(SCRIPTS)/python
PIP=$(SCRIPTS)/pip
FLAKE8=$(SCRIPTS)/flake8

# Default target
.PHONY: all help venv install lint clean build

all: clean install lint build

help:
	@echo Makefile commands:
	@echo   make venv      - Create virtual environment
	@echo   make install   - Install dependencies
	@echo   make lint      - Run lint checks \(flake8\)
	@echo   make clean     - Remove temporary files
	@echo   make build     - Build into standalone executable

venv:
	python -m pip install virtualenv
	python -m venv $(VENV)

install:
	$(PIP) install -r requirements.txt

lint:
	$(FLAKE8) src/

clean:
	rm -rf *.pyc __pycache__ build/ dist/ manifests/ download/ backup/ log.txt

build: clean
	$(PYTHON) -m pip install cx-Freeze
	$(PYTHON) setup.py build
