.PHONY: all
all: environment code_style run

.PHONY: environment
environment:
	python3 -m venv eleicoes_2024
	eleicoes_2024/bin/pip install --upgrade pip
	eleicoes_2024/bin/pip install -r requirements.txt

.PHONY: code_style
code_style:
	eleicoes_2024/bin/black --exclude '/(venv|env|build|dist|eleicoes_2024)/' .
	eleicoes_2024/bin/isort . --skip venv --skip env --skip eleicoes_2024

.PHONY: run
run:
	shiny run shiny_app/app.py

.PHONY: build_shinylive
build_shinylive:
	shinylive export shiny_app docs
	sed -i '' 's/<title>Shiny App<\/title>/<title>Eleições - 2024<\/title>/' docs/index.html
	python3 -m http.server --directory docs --bind 127.0.0.1 8080

.PHONY: clean
clean:
	rm -rf eleicoes_2024
	find . -name '*.pyc' -delete

.PHONY: clear
clear: clean
	eleicoes_2024/bin/pip uninstall -y -r requirements.txt