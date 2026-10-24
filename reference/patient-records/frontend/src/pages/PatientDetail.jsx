import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getPatientById, getRecords, generateAISummary } from '../services/api';
import RecordUploadModal from '../components/RecordUploadModal';

export default function PatientDetail() {
  const { id } = useParams();
  const [patient, setPatient] = useState(null);
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loadingAI, setLoadingAI] = useState(false);

  useEffect(() => {
    getPatientById(id).then((r) => setPatient(r.data));
    getRecords(id).then((r) => setRecords(r.data));
  }, [id]);

  const handleAISummary = async () => {
    setLoadingAI(true);
    try {
      const res = await generateAISummary(id);
      setSummary(res.data.summary);
    } catch (err) {
      alert('AI generation failed: ' + err.message);
    } finally {
      setLoadingAI(false);
    }
  };

  if (!patient) return <div className="p-6">Loading patient record...</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="border p-4 rounded bg-white shadow-sm">
        <h1 className="text-2xl font-bold">{patient.name}</h1>
        <p className="text-gray-600">Aadhaar: {patient.aadhaar_number} | Gender: {patient.gender}</p>
        <button
          onClick={handleAISummary}
          disabled={loadingAI}
          className="mt-3 bg-purple-600 text-white px-3 py-1.5 rounded text-sm hover:bg-purple-700"
        >
          {loadingAI ? 'Generating with OpenAI...' : 'Generate AI Clinical Summary'}
        </button>
        {summary && (
          <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded">
            <h3 className="font-semibold text-purple-900">AI Summary</h3>
            <p className="text-sm text-purple-800 whitespace-pre-line">{summary}</p>
          </div>
        )}
      </div>

      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Medical Documents & Lab Reports</h2>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-green-600 text-white px-3 py-1.5 rounded text-sm"
        >
          + Upload Document
        </button>
      </div>

      <div className="space-y-3">
        {records.length === 0 ? (
          <p className="text-gray-500">No records found for this patient.</p>
        ) : (
          records.map((rec) => (
            <div key={rec.id} className="p-3 border rounded bg-white flex justify-between">
              <div>
                <p className="font-semibold">{rec.title}</p>
                <p className="text-xs text-gray-500">Category: {rec.category} | Date: {rec.created_at}</p>
              </div>
              <a
                href={`http://localhost:5000/uploads/${rec.file_path}`}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 text-sm hover:underline"
              >
                Download File
              </a>
            </div>
          ))
        )}
      </div>

      {isModalOpen && (
        <RecordUploadModal
          patientId={id}
          onClose={() => setIsModalOpen(false)}
          onUploadSuccess={(newRec) => {
            setRecords([newRec, ...records]);
            setIsModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
