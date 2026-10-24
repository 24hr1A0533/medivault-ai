from flask import Blueprint, request, jsonify
from models import db, Patient

patients_bp = Blueprint('patients', __name__)

# Vulnerability: Missing authentication decorator on patient list / read (Broken Object Level Authorization / IDOR)
@patients_bp.route('', methods=['GET'])
def list_patients():
    patients = Patient.query.all()
    # Unsafe exposure of raw Aadhaar numbers to all callers
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'aadhaar_number': p.aadhaar_number,
        'dob': p.dob,
        'gender': p.gender
    } for p in patients])

@patients_bp.route('/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({'error': 'Patient not found'}), 404
    return jsonify({
        'id': p.id,
        'name': p.name,
        'aadhaar_number': p.aadhaar_number,
        'dob': p.dob,
        'gender': p.gender
    })

@patients_bp.route('', methods=['POST'])
def create_patient():
    data = request.get_json() or {}
    # Flaw: No Aadhaar Verhoeff algorithm check, no OTP verification, accepts any 12 digit string
    p = Patient(
        name=data.get('name'),
        aadhaar_number=data.get('aadhaar_number'),
        dob=data.get('dob'),
        gender=data.get('gender')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id, 'name': p.name, 'aadhaar_number': p.aadhaar_number}), 201
