# FRONTEND GAP ANALYSIS: MEDIVAULT AI HOSPITAL OPERATING SYSTEM

**Audit Authority**: Principal Frontend Architect, Mayo Clinic Clinical UX Consultant  
**Target Codebase**: `d:\medivalutAI\medivault-ai\frontend\` and `d:\medivalutAI\apps\`

---

## 1. Executive Summary

| Frontend Domain | Audit Verdict | Severity |
| :--- | :--- | :--- |
| **Route Coverage** | Missing 4 core hospital console routes (`/emergency`, `/nurse`, `/caregiver`, `/fhir`) | **P0 (Blocker)** |
| **API Port Hardcoding** | Hardcoded to `localhost:8000` in `constants.js` instead of dynamic environment variable | **P1 (Critical)** |
| **Form Validation** | Missing client-side biometric format validation on Aadhaar / NPI fields | **P2 (High)** |
| **Accessibility (WCAG 2.1 AA)** | Missing `aria-live` regions on real-time vitals and alert monitors | **P2 (High)** |
| **Error & Empty States** | Generic alert fallback when claims or records fail to load | **P3 (Medium)** |

---

## 2. In-Depth Defect Breakdown

### Defect 1: Missing Routes for Clinical Hospital Consoles
* **Exact File**: [medivault-ai/frontend/src/App.jsx](file:///d:/medivalutAI/medivault-ai/frontend/src/App.jsx#L31-L170)
* **Lines**: Lines 31–170
* **Why Broken**: The master React router defines `/dashboard`, `/patient/dashboard`, `/doctor/dashboard`, and `/admin/dashboard`, but completely omits:
  * `/emergency`: Emergency Trauma Console
  * `/nurse`: Bedside Barcode Medication Administration (eMAR)
  * `/caregiver`: Caregiver & Legal Proxy Console
  Hospital staff navigating to `/emergency` hit the generic `NotFoundPage` (`404`) instead of trauma triage.
* **Production-Grade Fix**: Add explicit routes for `<EmergencyConsolePage />`, `<NurseConsolePage />`, and `<CaregiverPortalPage />` guarded with `allowedRoles={['doctor', 'triage_nurse', 'caregiver']}`.
* **Priority**: **P0 (Launch Blocker)**

### Defect 2: Hardcoded Backend Port in Frontend Constants
* **Exact File**: [medivault-ai/frontend/src/utils/constants.js](file:///d:/medivalutAI/medivault-ai/frontend/src/utils/constants.js#L6)
* **Lines**: Line 6: `export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';`
* **Why Broken**: The new Enterprise HOS API runs on port `8088`. In staging/production environments, requests attempt to connect to `localhost:8000`, causing `ERR_CONNECTION_REFUSED` on all clinical data operations if port 8000 is not running.
* **Production-Grade Fix**: Change fallback to relative path `/api/v1` so reverse proxy (Nginx) handles routing regardless of port:
  ```javascript
  export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  ```
* **Priority**: **P1 (Critical)**

### Defect 3: Missing ARIA Live Announcement for Acute Bedside Vitals
* **Exact File**: [packages/design-system/src/components/VitalsPanel.tsx](file:///d:/medivalutAI/packages/design-system/src/components/VitalsPanel.tsx#L18-L55)
* **Lines**: Lines 18–55
* **Why Broken**: Vital signs changes (e.g. Blood Pressure drop to 82/54) are visual only. Screen readers for impaired staff or audio monitors do not announce life-threatening telemetry updates.
* **Production-Grade Fix**: Wrap abnormal vitals displays in `<div role="alert" aria-live="assertive">` when thresholds exceed critical physiological bounds.
* **Priority**: **P2 (High)**

### Defect 4: Missing File Size Pre-Flight Guard on Document Upload Form
* **Exact File**: [medivault-ai/frontend/src/pages/DocumentStoragePage.jsx](file:///d:/medivalutAI/medivault-ai/frontend/src/pages/DocumentStoragePage.jsx#L142)
* **Lines**: Line 142: `const handleFileSelect = (e) => { setFile(e.target.files[0]); }`
* **Why Broken**: Upload inputs allow users to select 500MB+ ISO/video files. The frontend submits the entire stream before the backend rejects it with `413 Payload Too Large`, causing network thread starvation.
* **Production-Grade Fix**: Enforce pre-flight check in `handleFileSelect`:
  ```javascript
  if (selectedFile.size > 25 * 1024 * 1024) {
    setError('File exceeds maximum hospital document limit (25 MB).');
    return;
  }
  ```
* **Priority**: **P2 (High)**
