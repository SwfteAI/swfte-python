#!/usr/bin/env python3
"""
Deploy Qwen 2.5, TTS, and STT models on RunPod using the Swfte SDK.
"""
import os
import sys
import time

# Add parent directory to path to use local SDK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swfte import SwfteClient

# Configure client for local service
client = SwfteClient(
    api_key="test-api-key",
    base_url="http://localhost:3388/v2/gateway",
    workspace_id="test-workspace"
)

print("=" * 60)
print("RunPod Model Deployment Script")
print("=" * 60)

# List existing deployments first
print("\n=== Existing Deployments ===")
try:
    existing = client.deployments.list()
    for dep in existing:
        print(f"  - {dep.model_name} ({dep.model_type}): {dep.state.value} [ID: {dep.id}]")
    if not existing:
        print("  (No existing deployments)")
except Exception as e:
    print(f"  Error listing deployments: {e}")

# Define models to deploy
models_to_deploy = [
    {
        "name": "Qwen 2.5 Chat",
        "model_name": "Qwen/Qwen2.5-7B-Instruct",
        "model_type": "chat",
        "gpu_type": "NVIDIA RTX A5000",
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.9,
    },
    {
        "name": "TTS (Text-to-Speech)",
        "model_name": "tts-1",  # Uses openedai-speech container
        "model_type": "tts",
        "gpu_type": "NVIDIA RTX A4000",
    },
    {
        "name": "STT (Whisper Large)",
        "model_name": "Systran/faster-whisper-large-v3",
        "model_type": "stt",
        "gpu_type": "NVIDIA RTX A5000",
    },
]

deployments = {}

for model in models_to_deploy:
    print(f"\n=== Deploying {model['name']} ===")
    print(f"  Model: {model['model_name']}")
    print(f"  Type: {model['model_type']}")
    print(f"  GPU: {model['gpu_type']}")

    try:
        # Build deployment parameters
        params = {
            "model_name": model["model_name"],
            "model_type": model["model_type"],
            "gpu_type": model["gpu_type"],
            "use_spot": True,
        }

        if "max_model_len" in model:
            params["max_model_len"] = model["max_model_len"]
        if "gpu_memory_utilization" in model:
            params["gpu_memory_utilization"] = model["gpu_memory_utilization"]

        deployment = client.deployments.create(**params)

        print(f"  [SUCCESS] Deployment created!")
        print(f"  Deployment ID: {deployment.id}")
        print(f"  State: {deployment.state.value}")

        deployments[model["name"]] = deployment

    except Exception as e:
        print(f"  [ERROR] Failed to deploy: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Deployment Summary")
print("=" * 60)

for name, dep in deployments.items():
    print(f"\n{name}:")
    print(f"  ID: {dep.id}")
    print(f"  Model: {dep.model_name}")
    print(f"  Type: {dep.model_type}")
    print(f"  State: {dep.state.value}")
    if dep.endpoint_url:
        print(f"  Endpoint: {dep.endpoint_url}")

print("\n" + "=" * 60)
print("Next Steps")
print("=" * 60)
print("""
1. Wait for deployments to reach RUNNING state (5-15 minutes)

   Monitor status with:
   curl -s "http://localhost:3388/v1/runpod/deployments" -H "X-Workspace-Id: test-workspace" | jq

2. Update the test scripts with deployment IDs:

   Python: /sdks/python/examples/test_gateway.py
   - Set QWEN_DEPLOYMENT_ID = "<qwen-id>"
   - Set TTS_DEPLOYMENT_ID = "<tts-id>"
   - Set STT_DEPLOYMENT_ID = "<stt-id>"

3. Run the comprehensive tests:
   cd /sdks/python && python examples/test_gateway.py
""")

# Optional: Wait for deployments
if deployments:
    print("\nWould you like to wait for deployments to be ready?")
    print("Waiting for deployments... (Ctrl+C to skip)")

    try:
        for name, dep in deployments.items():
            print(f"\nWaiting for {name} (ID: {dep.id})...")
            try:
                ready_dep = client.deployments.wait_for_ready(
                    dep.id,
                    timeout=900,  # 15 minutes
                    poll_interval=30
                )
                print(f"  [READY] {name} is now running!")
                print(f"  Endpoint: {ready_dep.endpoint_url}")
            except TimeoutError:
                print(f"  [TIMEOUT] {name} did not become ready in time")
            except RuntimeError as e:
                print(f"  [FAILED] {name}: {e}")
    except KeyboardInterrupt:
        print("\n\nSkipped waiting. Deployments will continue in background.")

print("\nDone!")
