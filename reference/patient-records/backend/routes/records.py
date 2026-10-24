import os
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from models import db, MedicalRecord, Patient

records_bp = Blueprint('records', __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@records_bp.route('/<int:patient_id>/records', methods=['GET'])
def get_patient_records(patient_id):
    # Flaw: No role verification (any logged-in or anonymous user can query any patient's records)
    records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'category': r.category,
        'file_path': r.file_path,
        'notes': r.notes,
        'created_at': r.created_at.isoformat()
    } for r in records])

@records_bp.route('/<int:patient_id>/records/upload', methods=['POST'])
def upload_record(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    title = request.form.get('title', 'Untitled')
    category = request.form.get('category', 'General')

    # Security Vulnerability: No file extension whitelist, no MIME magic byte check, no size limit check
    filename = secure_filename(file.filename)
    # File overwrite vulnerability if two patients upload the same file name
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    rec = MedicalRecord(
        patient_id=patient.id,
        title=title,
        category=category,
        file_path=filename
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({
        'id': rec.id,
        'title': rec.title,
        'category': rec.category,
        'file_path': rec.file_path,
        'created_at': rec.created_at.isoformat()
    }), 201

# Vulnerability: Arbitrary file download without authorization check
@records_bp.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
