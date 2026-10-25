.PHONY: help install test dev prod docker-up docker-down seed clean

help:
	@echo "MediVault AI Hospital OS Commands:"
	@echo "  make install     Install all backend and frontend dependencies"
	@echo "  make test        Execute complete 82-test enterprise test suite"
	@echo "  make dev         Run backend server on port 8088"
	@echo "  make frontend    Run Vite frontend development server on port 5173"
	@echo "  make docker-up   Start production container cluster via Docker Compose"
	@echo "  make docker-down Stop container cluster"
	@echo "  make seed        Seed initial hospital tenants and FHIR resources"

install:
	pip install -r requirements.txt
	pip install pytest pydantic fastapi uvicorn cryptography
	cd medivault-ai/frontend && npm install

test:
	python -m pytest tests/ medivault_medical_llm/tests/ medivault_healthcare_llm/tests/ medivault_doctor_summary/tests/ medivault_trend_engine/tests/ medivault_guardrails/tests/ medivault_patient_rag/tests/ medivault_document_intelligence/tests/ -v

dev:
	python -m uvicorn main_enterprise:app --host 127.0.0.1 --port 8088 --reload

frontend:
	cd medivault-ai/frontend && npm run dev -- --host 127.0.0.1 --port 5173

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v

seed:
	python scripts/seed_db.py
