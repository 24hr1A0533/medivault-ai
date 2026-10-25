# Production Dockerfile for MediVault Healthcare LLM vLLM GPU Server
FROM vllm/vllm-openai:v0.6.3

WORKDIR /app

ENV MODEL_NAME="/models/medivault-qwen-2.5-7b-merged"
ENV HOST="0.0.0.0"
ENV PORT="8000"
ENV MAX_MODEL_LEN="8192"
ENV GPU_MEMORY_UTILIZATION="0.92"

EXPOSE 8000

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
CMD ["--model", "/models/medivault-qwen-2.5-7b-merged", "--host", "0.0.0.0", "--port", "8000", "--gpu-memory-utilization", "0.92", "--max-model-len", "8192", "--enable-prefix-caching", "--trust-remote-code"]
