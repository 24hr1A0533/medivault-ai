export interface PatientRecord {
  id: string;
  name: string;
  dob: string;
  mrn: string;
  allergies: string[];
  medications: Array<{ name: string; dosage: string; frequency: string }>;
  recentLabs: Array<{ marker: string; value: string; unit: string; range: string; isAbnormal: boolean }>;
}

export const fetchPatientProfile = async (patientId: string): Promise<PatientRecord> => {
  return {
    id: patientId,
    name: "John Alexander Doe",
    dob: "1968-04-12",
    mrn: "MRN-8920192",
    allergies: ["Penicillin", "Latex"],
    medications: [
      { name: "Atorvastatin", dosage: "20mg", frequency: "Once daily at bedtime" },
      { name: "Metformin HCl", dosage: "500mg", frequency: "Twice daily with meals" },
    ],
    recentLabs: [
      { marker: "Glucose (Fasting)", value: "104", unit: "mg/dL", range: "70-99", isAbnormal: true },
      { marker: "HbA1c", value: "6.3", unit: "%", range: "< 5.7", isAbnormal: true },
      { marker: "eGFR", value: "84", unit: "mL/min", range: "> 60", isAbnormal: false },
    ],
  };
};
