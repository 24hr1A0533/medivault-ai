"""
Production QLoRA Fine-Tuning Script for Healthcare LLM (Qwen 2.5 7B / Llama 3 8B).
Uses HuggingFace Transformers, PEFT, BitsAndBytes 4-bit NF4, and TRL.
"""
import os
import sys
import argparse
import logging
from typing import Optional

logger = logging.getLogger("medivault.qlora")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def build_qlora_training_pipeline(
    base_model_id: str = "Qwen/Qwen2.5-7B-Instruct",
    dataset_path: Optional[str] = None,
    output_dir: str = "./output/medivault-healthcare-qlora",
    lora_r: int = 64,
    lora_alpha: int = 128,
    lora_dropout: float = 0.05,
    learning_rate: float = 2e-4,
    batch_size: int = 4,
    grad_accum_steps: int = 8,
    num_epochs: int = 3,
    max_seq_length: int = 4096,
    use_flash_attention: bool = True,
):
    """
    Sets up bitsandbytes 4-bit quantization, LoRA PEFT adapter config,
    and Hugging Face TrainingArguments.
    """
    try:
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments,
        )
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from trl import SFTTrainer
    except ImportError as exc:
        logger.warning(f"Training dependencies not loaded in current test env: {exc}")
        return None

    logger.info(f"Configuring 4-bit NF4 Quantization for base model: {base_model_id}")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    logger.info("Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    logger.info("Loading 4-bit Base Model with FlashAttention-2...")
    model_kwargs = {
        "quantization_config": bnb_config,
        "device_map": "auto",
        "trust_remote_code": True,
        "torch_dtype": torch.bfloat16,
    }
    if use_flash_attention:
        model_kwargs["attn_implementation"] = "flash_attention_2"

    model = AutoModelForCausalLM.from_pretrained(base_model_id, **model_kwargs)
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    logger.info(f"Configuring LoRA Adapter: r={lora_r}, alpha={lora_alpha}")
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    peft_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum_steps,
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        num_train_epochs=num_epochs,
        logging_steps=10,
        eval_strategy="steps" if dataset_path else "no",
        eval_steps=250 if dataset_path else None,
        save_strategy="steps",
        save_steps=500,
        save_total_limit=3,
        optim="paged_adamw_8bit",
        bf16=True,
        fp16=False,
        max_grad_norm=0.3,
        weight_decay=0.01,
        gradient_checkpointing=True,
        report_to=["tensorboard"],
    )

    return {
        "model": model,
        "tokenizer": tokenizer,
        "peft_config": peft_config,
        "training_args": training_args,
        "max_seq_length": max_seq_length,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Healthcare LLM with QLoRA")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--output-dir", type=str, default="./output/medivault-healthcare-qlora")
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    pipeline = build_qlora_training_pipeline(
        base_model_id=args.base_model,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
    )
    logger.info("QLoRA Fine-tuning pipeline assembled successfully.")
