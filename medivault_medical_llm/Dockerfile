FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/medivault_medical_llm

EXPOSE 8006

CMD ["uvicorn", "medivault_medical_llm.main:app", "--host", "0.0.0.0", "--port", "8006"]
