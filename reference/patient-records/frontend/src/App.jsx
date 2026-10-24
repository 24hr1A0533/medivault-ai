import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import PatientList from './pages/PatientList';
import PatientDetail from './pages/PatientDetail';

function Nav() {
  const { user, logout } = useAuth();
  return (
    <nav className="bg-blue-900 text-white px-6 py-4 flex justify-between items-center shadow-md">
      <Link to="/" className="font-bold text-xl tracking-tight">MediVault - EHR Portal</Link>
      <div className="flex items-center space-x-4 text-sm">
        <Link to="/" className="hover:underline">Patients</Link>
        {user ? (
          <div className="flex items-center space-x-3">
            <span>Welcome, {user.username} ({user.role})</span>
            <button onClick={logout} className="bg-red-500 hover:bg-red-600 px-2 py-1 rounded">Logout</button>
          </div>
        ) : (
          <span>Not Logged In</span>
        )}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 text-gray-800">
          <Nav />
          <Routes>
            <Route path="/" element={<PatientList />} />
            <Route path="/patients/:id" element={<PatientDetail />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
