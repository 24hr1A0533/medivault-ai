# Healthcare LLM Engineering & Fine-Tuning Architecture Specification

## 1. Executive Summary & Model Selection

Healthcare clinical intelligence requires deep comprehension of physiological mechanisms, diagnostic criteria, pharmacology, and medical jargon, while strictly adhering to safety guardrails and source attribution.

This specification outlines the end-to-end production architecture for fine-tuning open-source foundation models (**Qwen 2.5 7B** / **Llama 3 8B**) using **QLoRA** on four gold-standard clinical datasets, paired with **vLLM** for low-latency, scalable GPU serving.

### Model Selection Rationale:
- **Primary: Qwen 2.5 7B (Instruction-Tuned)**
  - Native 128k context window (ideal for multi-page discharge summaries & longitudinal lab records).
  - Superior multilingual, reasoning, and structured JSON output adherence.
  - SOTA performance on MMLU-Medical and biomedical benchmarks among < 10B models.
- **Alternative: Meta Llama 3.1 8B Instruct**
  - RoPE scaling up to 128k context, strong English biomedical reasoning.

---

## 2. Dataset Synthesis Pipeline

The fine-tuning corpus balances real-world clinical documentation, biomedical literature, and multi-specialty clinical examinations across 4 core datasets:

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│     MIMIC-IV     │  │     PubMedQA     │  │      MedQA       │  │     MedMCQA      │
│ (Clinical Notes, │  │   (Biomedical    │  │  (USMLE Clinical │  │  (AIIMS / NEET  │
│  Discharge Sums) │  │ RAG & Reasoning) │  │ Decision Making) │  │ 21 Specialties) │
└─────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
          │                    │                     │                     │
          ▼                    ▼                     ▼                     ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    Healthcare Dataset Normalizer & Deduplicator                    │
│      - Formats into ChatML (<|im_start|>system...user...assistant<|im_end|>)       │
│      - Tags clinical tasks: EXPLAIN_REPORT, RAG_ANSWERING, MEDICAL_TERMINOLOGY     │
│      - Filters corrupted OCR artifacts & validates non-empty references            │
│      - Stratified split: 90% Training (180,000 pairs), 10% Validation (20,000)     │
└─────────────────────────────────────────┬──────────────────────────────────────────┘
                                          │
                                          ▼
                         [Tokenized Sequence Generator]
                       (Max Length = 4096 / 8192 tokens)
```

### Dataset Composition Breakdown:
| Dataset | Source Samples | Target Weight | Focus Optimization |
|---|---|---|---|
| **MIMIC-IV** | 70,000 de-identified records | 35% | Discharge summary synthesis, clinical entity extraction, report explanation. |
| **PubMedQA** | 45,000 biomedical Q&A | 25% | Context-grounded RAG answering, evidence citation, scientific literature reasoning. |
| **MedQA** | 40,000 USMLE exam cases | 20% | Clinical diagnostic evaluation, pathophysiological mechanisms, differential rationale. |
| **MedMCQA** | 45,000 multi-specialty items | 20% | Pharmacology, surgical principles, terminology definitions, laboratory normals. |

---

## 3. QLoRA Fine-Tuning Strategy

To achieve near-full fine-tuning accuracy with single/dual GPU constraints, we utilize **4-bit NormalFloat (NF4)** quantization with **Double Quantization (DQ)** and **LoRA Adapters** targeting all linear projection layers.

### Quantization Configuration:
- `load_in_4bit`: `True`
- `bnb_4bit_quant_type`: `"nf4"`
- `bnb_4bit_use_double_quant`: `True` (reduces memory footprint by 0.37 bits/param)
- `bnb_4bit_compute_dtype`: `torch.bfloat16`

### LoRA Hyperparameters:
- **Rank ($r$)**: `64`
- **Alpha ($\alpha$)**: `128` (scaling factor $\alpha / r = 2.0$)
- **Dropout**: `0.05`
- **Target Modules**: `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`
- **Trainable Parameters**: ~160M params (~2.2% of total 7.6B parameters)

### Training Hyperparameters:
```yaml
learning_rate: 2.0e-4
lr_scheduler_type: "cosine"
warmup_ratio: 0.03
per_device_train_batch_size: 4
gradient_accumulation_steps: 8  # Effective batch size = 32 (or 64 on multi-GPU)
max_seq_length: 4096
gradient_checkpointing: true
optim: "paged_adamw_8bit"
fp16: false
bf16: true
logging_steps: 10
eval_steps: 250
save_steps: 500
weight_decay: 0.01
max_grad_norm: 0.3
```

---

## 4. Serving Architecture with vLLM

After training, the LoRA adapter is merged into the base 16-bit model weights, enabling zero-latency serving via **vLLM** with PagedAttention:

```
Client Requests (FastAPI / RAG Microservices)
                    │
                    ▼
       ┌─────────────────────────┐
       │   HAProxy / Cloud LB    │ (SSL Termination, Rate Limiting)
       └────────────┬────────────┘
                    │
                    ▼
       ┌─────────────────────────┐
       │ Kubernetes Cluster (vLLM)
       │                         │
       │   Pod 1: vLLM Server    │ ──► [Continuous Batching + PagedAttention]
       │   (NVIDIA A100 / L40S)  │ ──► [KV-Cache Management, TP=1 or TP=2]
       │                         │ ──► [OpenAI-compatible /v1/chat/completions]
       │   Pod 2: vLLM Server    │
       │   (Auto-scaled via HPA) │
       └─────────────────────────┘
```

### Key vLLM Runtime Arguments:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /models/medivault-qwen-2.5-7b-merged \
    --tensor-parallel-size 1 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.92 \
    --enforce-eager false \
    --enable-prefix-caching \
    --trust-remote-code \
    --port 8000
```
