import React, { useState, useEffect } from 'react';
import { getPatients, createPatient } from '../services/api';
import { Link } from 'react-router-dom';

export default function PatientList() {
  const [patients, setPatients] = useState([]);
  const [name, setName] = useState('');
  const [aadhaar, setAadhaar] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('Male');

  useEffect(() => {
    getPatients().then((res) => setPatients(res.data)).catch(console.error);
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    // Insecure practice: Submits raw Aadhaar directly without validation or masking
    const res = await createPatient({ name, aadhaar_number: aadhaar, dob, gender });
    setPatients([...patients, res.data]);
    setName('');
    setAadhaar('');
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Patient Directory</h1>
      <form onSubmit={handleCreate} className="mb-6 p-4 border rounded bg-white shadow-sm space-y-3">
        <h2 className="font-semibold">Register New Patient</h2>
        <input
          type="text"
          placeholder="Patient Full Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="border p-2 w-full rounded"
          required
        />
        <input
          type="text"
          placeholder="Aadhaar Number (12 digits)"
          value={aadhaar}
          onChange={(e) => setAadhaar(e.target.value)}
          className="border p-2 w-full rounded"
          required
        />
        <input
          type="date"
          value={dob}
          onChange={(e) => setDob(e.target.value)}
          className="border p-2 w-full rounded"
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
          Add Patient
        </button>
      </form>

      <div className="grid gap-4">
        {patients.map((p) => (
          <div key={p.id} className="p-4 border rounded shadow-sm bg-white flex justify-between items-center">
            <div>
              <p className="font-bold">{p.name}</p>
              {/* Unsafe exposure of raw Aadhaar in UI */}
              <p className="text-sm text-gray-500">Aadhaar: {p.aadhaar_number} | DOB: {p.dob}</p>
            </div>
            <Link to={`/patients/${p.id}`} className="text-blue-500 hover:underline">
              View Records &rarr;
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
