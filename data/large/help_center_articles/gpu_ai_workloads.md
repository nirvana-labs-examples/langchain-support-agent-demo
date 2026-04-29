# GPU Instances for AI Workloads

## Available GPU Configurations

| Instance | GPUs | VRAM | vCPUs | RAM | Best For |
|----------|------|------|-------|-----|----------|
| gpu-small | 1x A10G | 16 GB | 8 | 32 GB | Fine-tuning small models, inference |
| gpu-medium | 2x A10G | 32 GB | 16 | 64 GB | Fine-tuning medium models |
| gpu-large | 8x A100 | 320 GB | 96 | 768 GB | Pre-training, large model inference |
| gpu-xl | 16x H100 | 640 GB | 192 | 2 TB | Frontier model training |

Note: 1.5 GB of VRAM is reserved per GPU for ECC error correction and driver overhead.

## Setting Up CUDA

GPU instances come with NVIDIA drivers pre-installed on CUDA-enabled images:

```bash
# Verify GPU is visible
nvidia-smi

# Check CUDA version
nvcc --version
```

Use the `ubuntu-22-04-cuda-12` image when creating your VM for a pre-configured
CUDA environment.

## Running Inference with Ollama

```bash
docker run --gpus all -p 11434:11434 ollama/ollama
docker exec -it ollama ollama pull llama3.2:8b
```

Ollama automatically detects and uses all available GPUs.

## Running Inference with vLLM

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server   --model meta-llama/Meta-Llama-3-8B-Instruct   --tensor-parallel-size 2
```

## Persistent Model Storage

Store model weights on an ABS NVMe volume (not the root disk):

```bash
# Mount volume at /models
sudo mkfs.ext4 /dev/vdb
sudo mount /dev/vdb /models
```

Download weights once; reload from disk on subsequent starts — no repeated downloads.

## GPU Monitoring

GPU metrics (utilization, VRAM, temperature) are available in **Monitoring → Dashboards**
for any GPU instance. Set alerts on `gpu_utilization > 95%` to detect training stalls.

## Cost

GPU instances are billed per second. Spot GPU instances are available at up to 70%
discount for interruptible training jobs.
