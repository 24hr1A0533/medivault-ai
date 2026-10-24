import React, { useState } from 'react';
import { uploadRecord } from '../services/api';

export default function RecordUploadModal({ patientId, onClose, onUploadSuccess }) {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Prescription');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return alert('Select a file first');
    setUploading(true);
    const data = new FormData();
    data.append('title', title);
    data.append('category', category);
    data.append('file', file);

    try {
      const res = await uploadRecord(patientId, data);
      onUploadSuccess(res.data);
    } catch (err) {
      alert('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white p-6 rounded-lg max-w-md w-full shadow-lg">
        <h2 className="text-lg font-bold mb-4">Upload Medical Document</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Document Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border p-2 rounded text-sm"
            required
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full border p-2 rounded text-sm"
          >
            <option>Prescription</option>
            <option>Lab Report</option>
            <option>Scan / Imaging</option>
            <option>Discharge Summary</option>
          </select>
          {/* No client-side file extension or size verification */}
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm"
            required
          />
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 border rounded text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
