"""
Deployment management for the Swfte SDK.
Handles RunPod GPU deployments and model serving.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import requests
import time


class DeploymentState(Enum):
    """Deployment state enumeration."""
    PENDING = "PENDING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


@dataclass
class Deployment:
    """Represents a model deployment."""
    id: str
    model_name: str
    model_type: str
    state: DeploymentState
    workspace_id: Optional[str] = None
    environment: Optional[str] = None
    pod_id: Optional[str] = None
    runpod_instance_id: Optional[str] = None
    endpoint_url: Optional[str] = None
    health_check_url: Optional[str] = None
    status_message: Optional[str] = None
    enabled: bool = True
    parameters: Optional[Dict] = None
    serving_framework: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_health_check: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deployment":
        """Create a Deployment from a dictionary."""
        state_str = data.get("state", "PENDING")
        try:
            state = DeploymentState(state_str)
        except ValueError:
            state = DeploymentState.PENDING
        
        return cls(
            id=data.get("id", data.get("deploymentId", "")),
            model_name=data.get("modelName", data.get("model_name", "")),
            model_type=data.get("modelType", data.get("model_type", "")),
            state=state,
            workspace_id=data.get("workspaceId", data.get("workspace_id")),
            environment=data.get("environment"),
            pod_id=data.get("podId", data.get("pod_id")),
            runpod_instance_id=data.get("runpodInstanceId", data.get("runpod_instance_id")),
            endpoint_url=data.get("endpoint", data.get("endpointUrl")),
            health_check_url=data.get("healthCheckUrl", data.get("health_check_url")),
            status_message=data.get("statusMessage", data.get("status_message")),
            enabled=data.get("enabled", True),
            parameters=data.get("parameters"),
            serving_framework=data.get("servingFramework", data.get("serving_framework")),
            created_at=data.get("createdAt", data.get("created_at")),
            updated_at=data.get("updatedAt", data.get("updated_at")),
            last_health_check=data.get("lastHealthCheck", data.get("last_health_check")),
        )


@dataclass
class HealthStatus:
    """Represents deployment health status."""
    healthy: bool
    status: str
    message: Optional[str] = None
    last_check: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthStatus":
        """Create HealthStatus from a dictionary."""
        return cls(
            healthy=data.get("healthy", False),
            status=data.get("status", "UNKNOWN"),
            message=data.get("message"),
            last_check=data.get("lastCheck", data.get("last_check")),
        )


class Deployments:
    """
    Deployment management API for RunPod GPU model deployments.
    
    Example:
        client = SwfteClient(api_key="sk-swfte-...")
        
        # Deploy a model
        deployment = client.deployments.create(
            model_name="meta-llama/Llama-3.2-8B-Instruct",
            model_type="chat",
            use_spot=True
        )
        
        # Wait for deployment to be ready
        deployment = client.deployments.wait_for_ready(deployment.id)
        
        # Check health
        health = client.deployments.health(deployment.id)
        
        # Terminate deployment
        client.deployments.terminate(deployment.id)
    """
    
    def __init__(self, client):
        self._client = client
    
    def _get_base_url(self) -> str:
        """Get the base URL for deployment endpoints."""
        base = self._client.base_url
        # Remove /gateway if present to get the service root
        if "/gateway" in base:
            base = base.replace("/v2/gateway", "").replace("/v1/gateway", "")
        return f"{base}/v1/inference"
    
    def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make an HTTP request."""
        headers = self._client._get_headers()
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=self._client.timeout,
        )
        
        response.raise_for_status()
        
        if response.content:
            return response.json()
        return {}
    
    def create(
        self,
        model_name: str,
        model_type: str = "chat",
        use_spot: bool = True,
        gpu_type: str = "NVIDIA RTX A5000",
        max_model_len: Optional[int] = None,
        gpu_memory_utilization: float = 0.9,
        container_disk_size: Optional[int] = None,
        **kwargs,
    ) -> Deployment:
        """
        Deploy a model on RunPod GPU infrastructure.
        
        Args:
            model_name: The HuggingFace model name (e.g., "meta-llama/Llama-3.2-8B-Instruct").
            model_type: Type of model - "chat", "image-generation", "embedding", or "audio".
            use_spot: Whether to use spot instances (cheaper but interruptible).
            gpu_type: GPU type (e.g., "NVIDIA RTX A5000", "NVIDIA RTX A6000").
            max_model_len: Maximum model context length.
            gpu_memory_utilization: GPU memory utilization (0.0-1.0).
            container_disk_size: Container disk size in GB.
            **kwargs: Additional deployment parameters.
        
        Returns:
            The created Deployment.
        """
        parameters = {
            "use_spot": str(use_spot).lower(),
            "gpu_type": gpu_type,
            "gpu_memory_utilization": str(gpu_memory_utilization),
            **kwargs,
        }
        
        if max_model_len is not None:
            parameters["max_model_len"] = str(max_model_len)
        if container_disk_size is not None:
            parameters["container_disk_size"] = str(container_disk_size)
        
        payload = {
            "modelName": model_name,
            "modelType": model_type,
            "parameters": parameters,
        }
        
        url = f"{self._get_base_url()}/models/deploy"
        response = self._make_request("POST", url, data=payload)
        return Deployment.from_dict(response)
    
    def get(self, deployment_id: str) -> Deployment:
        """
        Get deployment details.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            The Deployment.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}"
        response = self._make_request("GET", url)
        return Deployment.from_dict(response)
    
    def list(
        self,
        page: int = 0,
        size: int = 20,
    ) -> List[Deployment]:
        """
        List all deployments.
        
        Args:
            page: Page number (0-based).
            size: Number of deployments per page.
        
        Returns:
            List of deployments.
        """
        params = {"page": page, "size": size}
        url = f"{self._get_base_url()}/deployments"
        response = self._make_request("GET", url, params=params)
        
        deployments_data = response.get("deployments", [])
        return [Deployment.from_dict(d) for d in deployments_data]
    
    def health(self, deployment_id: str) -> HealthStatus:
        """
        Check deployment health.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Health status.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/health"
        response = self._make_request("GET", url)
        return HealthStatus.from_dict(response)
    
    def terminate(self, deployment_id: str) -> None:
        """
        Terminate a deployment.
        
        Args:
            deployment_id: The ID of the deployment to terminate.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}"
        self._make_request("DELETE", url)
    
    def stop(self, deployment_id: str) -> Dict:
        """
        Stop a running deployment pod.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Response with status.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/stop"
        return self._make_request("POST", url)
    
    def start(self, deployment_id: str) -> Dict:
        """
        Start a stopped deployment pod.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Response with status.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/start"
        return self._make_request("POST", url)
    
    def restart(self, deployment_id: str) -> Dict:
        """
        Restart a deployment pod.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Response with status.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/restart"
        return self._make_request("POST", url)
    
    def wait_for_ready(
        self,
        deployment_id: str,
        timeout: int = 600,
        poll_interval: int = 30,
    ) -> Deployment:
        """
        Wait for a deployment to become ready.
        
        Args:
            deployment_id: The ID of the deployment.
            timeout: Maximum time to wait in seconds.
            poll_interval: Time between status checks in seconds.
        
        Returns:
            The Deployment once ready.
        
        Raises:
            TimeoutError: If deployment doesn't become ready within timeout.
            RuntimeError: If deployment fails.
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Deployment {deployment_id} did not become ready within {timeout}s"
                )
            
            deployment = self.get(deployment_id)
            
            if deployment.state == DeploymentState.RUNNING:
                return deployment
            elif deployment.state == DeploymentState.FAILED:
                raise RuntimeError(
                    f"Deployment {deployment_id} failed: {deployment.status_message}"
                )
            elif deployment.state in (DeploymentState.TERMINATED, DeploymentState.STOPPED):
                raise RuntimeError(
                    f"Deployment {deployment_id} was terminated or stopped"
                )
            
            time.sleep(poll_interval)
    
    def get_uptime(self, deployment_id: str) -> Dict:
        """
        Get deployment uptime metrics.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Uptime metrics dictionary.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/uptime"
        return self._make_request("GET", url)
    
    def get_circuit_breaker(self, deployment_id: str) -> Dict:
        """
        Get circuit breaker status for a deployment.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Circuit breaker status.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/circuit-breaker"
        return self._make_request("GET", url)
    
    def reset_circuit_breaker(self, deployment_id: str) -> Dict:
        """
        Reset circuit breaker for a deployment.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Response with status.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/circuit-breaker/reset"
        return self._make_request("POST", url)
    
    def trigger_recovery(self, deployment_id: str) -> Dict:
        """
        Manually trigger recovery for a deployment.
        
        Args:
            deployment_id: The ID of the deployment.
        
        Returns:
            Response with status.
        """
        url = f"{self._get_base_url()}/deployments/{deployment_id}/recover"
        return self._make_request("POST", url)
    
    def get_monitoring_health(self) -> Dict:
        """
        Get health monitoring statistics.
        
        Returns:
            Health monitoring statistics.
        """
        url = f"{self._get_base_url()}/monitoring/health"
        return self._make_request("GET", url)
    
    def get_monitoring_recovery(self) -> Dict:
        """
        Get auto-recovery statistics.
        
        Returns:
            Recovery statistics.
        """
        url = f"{self._get_base_url()}/monitoring/recovery"
        return self._make_request("GET", url)
    
    def get_monitoring_dashboard(self) -> Dict:
        """
        Get comprehensive monitoring dashboard data.
        
        Returns:
            Dashboard data.
        """
        url = f"{self._get_base_url()}/monitoring/dashboard"
        return self._make_request("GET", url)
    
    def generate_image(
        self,
        model: str,
        prompt: str,
        size: str = "1024x1024",
        n: int = 1,
        quality: str = "standard",
        style: str = "vivid",
        negative_prompt: Optional[str] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> Dict:
        """
        Generate images using a deployed image generation model.
        
        Args:
            model: The model name.
            prompt: The prompt for image generation.
            size: Image size (e.g., "1024x1024").
            n: Number of images to generate.
            quality: Quality setting ("standard" or "hd").
            style: Style setting ("vivid" or "natural").
            negative_prompt: Negative prompt for generation.
            steps: Number of inference steps.
            guidance_scale: Guidance scale for generation.
            seed: Random seed for reproducibility.
        
        Returns:
            Image generation response.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n,
            "quality": quality,
            "style": style,
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if steps:
            payload["steps"] = steps
        if guidance_scale:
            payload["guidance_scale"] = guidance_scale
        if seed:
            payload["seed"] = seed
        
        url = f"{self._get_base_url()}/images/generate"
        return self._make_request("POST", url, data=payload)







