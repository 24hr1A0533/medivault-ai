"""
Epic Hyperspace Launch Context Model.
Captures clinical EHR launch parameters passed when MediVault AI is invoked
inside an Epic Hyperspace iframe or Cerner PowerChart view.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class EpicLaunchContext(BaseModel):
    launch_token: str
    iss: str = Field(..., description="FHIR Server Base URL of the EHR (e.g. Epic FHIR Endpoint)")
    patient_id: Optional[str] = Field(None, description="Active Patient ID in context")
    encounter_id: Optional[str] = Field(None, description="Active Encounter ID in context")
    user_id: Optional[str] = Field(None, description="Clinician EHR User ID")
    need_patient_banner: bool = Field(True, description="Whether EHR renders the patient header banner")
    smart_style_url: Optional[str] = Field(None, description="Stylesheet provided by Epic for seamless theming")
    tenant_id: str = "mayo-clinic-system"

    def to_claims(self) -> Dict[str, Any]:
        return {
            "patient": self.patient_id,
            "encounter": self.encounter_id,
            "user": self.user_id,
            "need_patient_banner": self.need_patient_banner,
            "iss": self.iss,
            "tenant_id": self.tenant_id,
        }
