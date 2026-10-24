import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, Patient, MedicalRecord
from routes.auth import auth_bp
from routes.patients import patients_bp
from routes.records import records_bp
import openai

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patient_records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(patients_bp, url_prefix='/api/patients')
app.register_blueprint(records_bp, url_prefix='/api/patients')

# Unverified AI Feature: Direct unvalidated prompt injection into OpenAI API
@app.route('/api/patients/<int:patient_id>/ai-summary', methods=['POST'])
def generate_ai_summary(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
    record_titles = [f"- {r.title} ({r.category})" for r in records]
    
    # Flaw: Hardcoded or unvalidated API key handling, prompt injection risk
    openai.api_key = os.getenv("OPENAI_API_KEY", "sk-mock-key-123456789")
    
    prompt = f"Summarize medical condition for patient {patient.name}, DOB {patient.dob}, with records:\n" + "\n".join(record_titles)

    try:
        # Mock/Unverified external dependency
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        summary = response.choices[0].message.content
    except Exception as e:
        # Fallback simulation if OpenAI is unreachable
        summary = f"Simulated AI Summary for {patient.name}: Patient presented with {len(records)} active records. Vital metrics stable."

    return jsonify({'patient_id': patient_id, 'summary': summary})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5000, debug=True)
