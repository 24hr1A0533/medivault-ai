# Patient Records Management Prototype (EHR Service)

> [!WARNING]
> Prototype status: This codebase is an early-stage hackathon prototype for patient record management.

## Advertised Features
- "Fully HIPAA and GDPR compliant electronic medical records" (Unverified claim)
- "Zero-knowledge encryption for medical PDFs" (Unverified claim)
- Real-time medical history and doctor notes
- Automated AI discharge summary generation via OpenAI API
- React 18 frontend with React Router v6

## Stack
- Frontend: React 18, Vite, Tailwind CSS, Axios
- Backend: Python Flask, Flask-SQLAlchemy, SQLite
- Authentication: JWT (HS256)

## Setup Instructions (Reference only)
Do not execute in production.
```bash
cd backend && pip install -r requirements.txt && python app.py
cd frontend && npm install && npm run dev
```
