# Create a virtual environment and installs requirements
venv-setup: clean create-virtualenv install-requirements

clean: ## Remove the virtual environment directory
	@echo "Cleaning up virtual environment..."
	rm -rf venv

create-virtualenv:
	@echo "Creating virtual environment with python3.10..."
	test -d venv || python3.10 -m venv venv

install-requirements:
	@echo "Installing requirements..."
	source venv/bin/activate && pip3 install -r requirements.txt && pip install -e . && touch .env


# Initiate dbt project and run all models
dbt: validate-dbt-config run-dbt-models

validate-dbt-config:
	@echo "Validating dbt configuration..."
	dbt debug && dbt deps && dbt compile

run-dbt-models:
	@echo "Running dbt models..."
	dbt build
