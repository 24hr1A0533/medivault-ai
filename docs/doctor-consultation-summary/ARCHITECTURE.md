# Doctor Consultation Summary Engine Architecture Specification

## 1. Overview & Clinical Objective

Before medical appointments, patients and physicians often struggle with fragmented records across different clinics, hospital stays, and diagnostic laboratories. 

The **MediVault Doctor Consultation Summary Engine** synthesizes all available patient health records into a concise, high-yield, citation-grounded clinical briefing note formatted specifically for physician consultations.

### Non-Negotiable Clinical Tenets:
1. **Concise & High-Yield**: Prioritizes actionable abnormal findings and active medications over boilerplate documentation.
2. **Medically Accurate**: Accurately reproduces test names, numerical values, units, and reference ranges without rounding errors.
3. **Source Grounded**: Every single condition, abnormal finding, medication, and follow-up item cites the specific source document: `[report_name, page_number, report_date]`.
4. **Patient-Empowering Questions**: Generates clinically pertinent questions for the patient to ask their physician based on their actual abnormal findings.

---

## 2. Required Clinical Briefing Format

```markdown
# Doctor Consultation Summary: [Patient ID]

## Patient Summary
[Concise executive overview of active conditions and overall trajectory]

## Abnormal Findings
- [Biomarker / Finding]: [Measured Value] (Ref: [Range]) - [Clinical Significance] [Source: Report Name, Page X, YYYY-MM-DD]
...

## Recent Reports
- [YYYY-MM-DD] - [Report Name] ([Category]): [Key Clinical Impression] [Source: Report Name, Page X, YYYY-MM-DD]
...

## Current Medications
- [Drug Name] [Dosage] [Frequency] (Indication: [Condition]) [Source: Report Name, Page X, YYYY-MM-DD]
...

## Upcoming Followups
- [Follow-up Target]: [Timeframe & Preparation] [Source: Report Name, Page X, YYYY-MM-DD]
...

## Questions To Discuss With Physician
1. [Targeted Question regarding abnormal biomarker or therapy response]
2. [Targeted Question regarding medication adherence/interactions]
3. [Targeted Question regarding upcoming screening/follow-up milestone]
```

---

## 3. Data Flow & Processing Pipeline

```
Patient Medical Records (Lab Reports, Discharge Summaries, Prescriptions, Clinical Notes)
                                      │
                                      ▼
                        [Clinical Record Normalizer]
                 (Extracts Conditions, Tests, Drugs, Dates)
                                      │
                                      ▼
                     [Abnormal Finding Detection Engine]
             (Flags out-of-range biomarkers vs standard ranges)
                                      │
                                      ▼
                      [Longitudinal Synthesis Prompt]
               (Structures findings into required clinical sections)
                                      │
                                      ▼
                         [Qwen / Clinical LLM Engine]
                 (Generates structured markdown consultation brief)
                                      │
                                      ▼
                      [Citation & Grounding Validator]
        (Verifies source attribution and enforces zero-hallucination policy)
                                      │
                                      ▼
                       Doctor Consultation Summary API
```
