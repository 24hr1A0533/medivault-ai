import axios from 'axios';

// Hardcoded backend URL without environment variable fallback or HTTPS enforcement
const API = axios.create({
  baseURL: 'http://localhost:5000/api',
});

// Attaches token from localStorage directly
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const getPatients = () => API.get('/patients');
export const getPatientById = (id) => API.get(`/patients/${id}`);
export const createPatient = (data) => API.post('/patients', data);
export const getRecords = (patientId) => API.get(`/patients/${patientId}/records`);
export const uploadRecord = (patientId, formData) =>
  API.post(`/patients/${patientId}/records/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const generateAISummary = (patientId) => API.post(`/patients/${patientId}/ai-summary`);

export default API;
