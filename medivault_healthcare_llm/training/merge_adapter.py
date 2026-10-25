"""
Adapter Weight Merger for Zero-Overhead vLLM Deployment.
Fuses fine-tuned LoRA adapters into base 16-bit model weights.
"""
import os
import argparse
import logging

logger = logging.getLogger("medivault.merge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def merge_lora_into_base(
    base_model_path: str,
    adapter_path: str,
    output_dir: str,
    device: str = "cpu",
):
    """
    Merges PEFT adapter into base model and saves full FP16 / BF16 weights.
    """
    logger.info(f"Loading base model from {base_model_path} onto {device}...")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as exc:
        logger.warning(f"Merge dependencies not loaded in test environment: {exc}")
        return False

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.bfloat16,
        device_map=device,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)

    logger.info(f"Loading LoRA adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(base_model, adapter_path)

    logger.info("Merging adapter weights into base model layers...")
    merged_model = model.merge_and_unload()

    logger.info(f"Saving standalone merged model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    merged_model.save_pretrained(output_dir, safe_serialization=True)
    tokenizer.save_pretrained(output_dir)

    logger.info("Model merge completed. Ready for vLLM deployment.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA weights into base model")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--adapter-path", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default="./models/medivault-qwen-2.5-7b-merged")
    args = parser.parse_args()

    merge_lora_into_base(
        base_model_path=args.base_model,
        adapter_path=args.adapter_path,
        output_dir=args.output_dir,
    )
