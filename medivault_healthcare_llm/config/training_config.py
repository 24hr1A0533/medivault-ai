"""
Configuration parameters for Healthcare LLM Fine-Tuning and Inference.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    base_model_name_or_path: str = Field(default="Qwen/Qwen2.5-7B-Instruct", description="Base model name on Hugging Face")
    alternative_base_model: str = Field(default="meta-llama/Meta-Llama-3.1-8B-Instruct")
    model_max_length: int = Field(default=4096, description="Maximum context window length")
    torch_dtype: str = Field(default="bfloat16")
    trust_remote_code: bool = Field(default=True)
    use_flash_attention_2: bool = Field(default=True)

class QLoRAConfig(BaseModel):
    r: int = Field(default=64, description="LoRA rank")
    lora_alpha: int = Field(default=128, description="LoRA alpha scaling factor")
    lora_dropout: float = Field(default=0.05, description="LoRA dropout rate")
    target_modules: List[str] = Field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )
    bias: str = Field(default="none")
    task_type: str = Field(default="CAUSAL_LM")

class QuantizationConfig(BaseModel):
    load_in_4bit: bool = Field(default=True)
    bnb_4bit_quant_type: str = Field(default="nf4")
    bnb_4bit_use_double_quant: bool = Field(default=True)
    bnb_4bit_compute_dtype: str = Field(default="bfloat16")

class TrainingHyperparameters(BaseModel):
    output_dir: str = Field(default="./output/medivault-qwen-2.5-7b-qlora")
    learning_rate: float = Field(default=2e-4)
    per_device_train_batch_size: int = Field(default=4)
    per_device_eval_batch_size: int = Field(default=4)
    gradient_accumulation_steps: int = Field(default=8)
    warmup_ratio: float = Field(default=0.03)
    num_train_epochs: int = Field(default=3)
    lr_scheduler_type: str = Field(default="cosine")
    weight_decay: float = Field(default=0.01)
    max_grad_norm: float = Field(default=0.3)
    optim: str = Field(default="paged_adamw_8bit")
    logging_steps: int = Field(default=10)
    eval_steps: int = Field(default=250)
    save_steps: int = Field(default=500)
    save_total_limit: int = Field(default=3)
    gradient_checkpointing: bool = Field(default=True)
    bf16: bool = Field(default=True)
    fp16: bool = Field(default=False)

class DatasetMixtureConfig(BaseModel):
    mimic_iv_weight: float = Field(default=0.35, description="Clinical notes & summaries")
    pubmedqa_weight: float = Field(default=0.25, description="Biomedical RAG reasoning")
    medqa_weight: float = Field(default=0.20, description="USMLE clinical decision cases")
    medmcqa_weight: float = Field(default=0.20, description="21-specialty clinical items")

class VLLMServingConfig(BaseModel):
    model_path: str = Field(default="./models/medivault-qwen-2.5-7b-merged")
    tensor_parallel_size: int = Field(default=1)
    max_model_len: int = Field(default=8192)
    gpu_memory_utilization: float = Field(default=0.92)
    enforce_eager: bool = Field(default=False)
    enable_prefix_caching: bool = Field(default=True)
    port: int = Field(default=8000)
    host: str = Field(default="0.0.0.0")
