ROOT_PYTHON := ./src/.venv/bin/python

.PHONY: run test test-fast benchmark data docker-up docker-down

run:
	cd src && ./.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8501

test:
	cd src && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -m pytest -q ../tests/test_core.py ../tests/test_solver.py ../tests/test_integration.py ../tests/test_models.py ../tests/test_live_sync.py

test-fast:
	cd src && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -m pytest -q ../tests/test_core.py ../tests/test_solver.py

benchmark:
	cd src && ./.venv/bin/python -c "from analytics.model_benchmark import model_benchmarker; from api.main import state; import json; print(json.dumps(model_benchmarker.benchmark_models(state.df), ensure_ascii=False, indent=2))"

data:
	cd src && ./.venv/bin/python generator/produce_mega_dataset.py --days 7 --output ../data/raw/aviation_scenario_7d_latest.csv

docker-up:
	cp -n .env.example .env || true
	docker compose up --build

docker-down:
	docker compose down
