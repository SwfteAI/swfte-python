"""
Workflow management for the Swfte SDK.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests
import time


class ExecutionStatus(Enum):
    """Workflow execution status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class WorkflowNode:
    """Represents a workflow node."""
    id: str
    type: str
    name: Optional[str] = None
    position: Optional[Dict] = None
    config: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowNode":
        """Create a WorkflowNode from a dictionary."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            name=data.get("name"),
            position=data.get("position"),
            config=data.get("config", data.get("configuration")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert WorkflowNode to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "position": self.position,
            "config": self.config,
        }


@dataclass
class WorkflowEdge:
    """Represents a workflow edge (connection between nodes)."""
    id: str
    source: str
    target: str
    condition: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowEdge":
        """Create a WorkflowEdge from a dictionary."""
        return cls(
            id=data.get("id", ""),
            source=data.get("source", ""),
            target=data.get("target", ""),
            condition=data.get("condition"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert WorkflowEdge to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "condition": self.condition,
        }


@dataclass
class Workflow:
    """Represents a workflow."""
    id: str
    name: str
    description: Optional[str] = None
    workspace_id: Optional[str] = None
    active: bool = True
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    variables: Optional[Dict] = None
    version: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create a Workflow from a dictionary."""
        nodes_data = data.get("nodes", [])
        edges_data = data.get("edges", [])
        
        # Handle nodes as list or dict
        if isinstance(nodes_data, dict):
            nodes = [WorkflowNode.from_dict({**v, "id": k}) for k, v in nodes_data.items()]
        elif isinstance(nodes_data, list):
            nodes = [WorkflowNode.from_dict(n) for n in nodes_data]
        else:
            nodes = []
        
        edges = [WorkflowEdge.from_dict(e) for e in edges_data] if edges_data else []
        
        return cls(
            id=data.get("workflowId", data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description"),
            workspace_id=data.get("workspaceId", data.get("workspace_id")),
            active=data.get("active", True),
            nodes=nodes,
            edges=edges,
            variables=data.get("variables"),
            version=data.get("version"),
            created_at=data.get("createdAt", data.get("created_at")),
            updated_at=data.get("updatedAt", data.get("updated_at")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Workflow to dictionary."""
        return {
            "workflowId": self.id,
            "name": self.name,
            "description": self.description,
            "workspaceId": self.workspace_id,
            "active": self.active,
            "nodes": [n.to_dict() for n in (self.nodes or [])],
            "edges": [e.to_dict() for e in (self.edges or [])],
            "variables": self.variables,
            "version": self.version,
        }


@dataclass
class WorkflowExecution:
    """Represents a workflow execution."""
    id: str
    workflow_id: str
    status: ExecutionStatus
    progress: int = 0
    inputs: Optional[Dict] = None
    outputs: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowExecution":
        """Create a WorkflowExecution from a dictionary."""
        status_str = data.get("status", "PENDING")
        try:
            status = ExecutionStatus(status_str)
        except ValueError:
            status = ExecutionStatus.PENDING
        
        return cls(
            id=data.get("executionId", data.get("id", "")),
            workflow_id=data.get("workflowId", data.get("workflow_id", "")),
            status=status,
            progress=data.get("progress", 0),
            inputs=data.get("inputs"),
            outputs=data.get("outputs"),
            error=data.get("error"),
            started_at=data.get("startedAt", data.get("started_at")),
            completed_at=data.get("completedAt", data.get("completed_at")),
        )


@dataclass
class ValidationResult:
    """Represents workflow validation result."""
    valid: bool
    errors: List[Dict]
    warnings: List[Dict]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        """Create ValidationResult from a dictionary."""
        return cls(
            valid=data.get("valid", False),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
        )


class Workflows:
    """
    Workflow management API for creating, executing, and managing workflows.
    
    Example:
        client = SwfteClient(api_key="sk-swfte-...")
        
        # Create a workflow
        workflow = client.workflows.create(
            name="My Workflow",
            nodes=[
                {"id": "start", "type": "TRIGGER", "config": {"triggerType": "MANUAL"}},
                {"id": "llm", "type": "LLM", "config": {"model": "gpt-4"}},
                {"id": "end", "type": "END", "config": {}}
            ],
            edges=[
                {"id": "e1", "source": "start", "target": "llm"},
                {"id": "e2", "source": "llm", "target": "end"}
            ]
        )
        
        # Execute workflow
        execution = client.workflows.execute(workflow.id, {"message": "Hello"})
        
        # Wait for completion
        execution = client.workflows.wait_for_completion(execution.id)
    """
    
    def __init__(self, client):
        self._client = client
    
    def _get_base_url(self) -> str:
        """Get the base URL for workflow endpoints."""
        base = self._client.base_url
        # Remove /gateway if present to get the service root
        if "/gateway" in base:
            base = base.replace("/v1/gateway", "")
        return f"{base}/v2/workflows"
    
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
        name: str,
        nodes: List[Dict],
        edges: Optional[List[Dict]] = None,
        description: Optional[str] = None,
        active: bool = True,
        variables: Optional[Dict] = None,
        **kwargs,
    ) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: The name of the workflow.
            nodes: List of workflow nodes.
            edges: List of workflow edges (connections).
            description: Workflow description.
            active: Whether the workflow is active.
            variables: Workflow variables.
            **kwargs: Additional workflow properties.
        
        Returns:
            The created Workflow.
        """
        payload = {
            "name": name,
            "nodes": nodes,
            "edges": edges or [],
            "description": description,
            "active": active,
            "variables": variables or {},
            "workspaceId": self._client.workspace_id,
            **kwargs,
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        response = self._make_request("POST", self._get_base_url(), data=payload)
        return Workflow.from_dict(response)
    
    def get(self, workflow_id: str) -> Workflow:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: The ID of the workflow.
        
        Returns:
            The Workflow.
        """
        url = f"{self._get_base_url()}/{workflow_id}"
        response = self._make_request("GET", url)
        return Workflow.from_dict(response)
    
    def update(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[List[Dict]] = None,
        edges: Optional[List[Dict]] = None,
        active: Optional[bool] = None,
        variables: Optional[Dict] = None,
        **kwargs,
    ) -> Workflow:
        """
        Update an existing workflow.
        
        Args:
            workflow_id: The ID of the workflow to update.
            name: New name for the workflow.
            description: New description.
            nodes: New nodes list.
            edges: New edges list.
            active: New active status.
            variables: New variables.
            **kwargs: Additional properties to update.
        
        Returns:
            The updated Workflow.
        """
        # First get the current workflow
        current = self.get(workflow_id)
        
        # Merge updates
        payload = current.to_dict()
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if nodes is not None:
            payload["nodes"] = nodes
        if edges is not None:
            payload["edges"] = edges
        if active is not None:
            payload["active"] = active
        if variables is not None:
            payload["variables"] = variables
        
        payload.update(kwargs)
        
        url = f"{self._get_base_url()}/{workflow_id}"
        response = self._make_request("PUT", url, data=payload)
        return Workflow.from_dict(response)
    
    def patch(self, workflow_id: str, **updates) -> Workflow:
        """
        Partially update a workflow.
        
        Args:
            workflow_id: The ID of the workflow to update.
            **updates: Fields to update.
        
        Returns:
            The updated Workflow.
        """
        url = f"{self._get_base_url()}/{workflow_id}"
        response = self._make_request("PATCH", url, data=updates)
        return Workflow.from_dict(response)
    
    def delete(self, workflow_id: str, force: bool = False) -> None:
        """
        Delete a workflow.
        
        Args:
            workflow_id: The ID of the workflow to delete.
            force: Force delete even with active executions.
        """
        url = f"{self._get_base_url()}/{workflow_id}"
        params = {"force": force} if force else None
        self._make_request("DELETE", url, params=params)
    
    def list(
        self,
        page: int = 0,
        size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Workflow]:
        """
        List all workflows.
        
        Args:
            page: Page number (0-based).
            size: Number of workflows per page.
            status: Filter by status.
            search: Search term.
        
        Returns:
            List of workflows.
        """
        params = {"page": page, "size": size}
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        
        response = self._make_request("GET", self._get_base_url(), params=params)
        
        workflows_data = response.get("content", response.get("workflows", []))
        return [Workflow.from_dict(w) for w in workflows_data]
    
    def validate(
        self,
        name: str,
        nodes: List[Dict],
        edges: Optional[List[Dict]] = None,
        **kwargs,
    ) -> ValidationResult:
        """
        Validate a workflow definition.
        
        Args:
            name: The name of the workflow.
            nodes: List of workflow nodes.
            edges: List of workflow edges.
            **kwargs: Additional workflow properties.
        
        Returns:
            Validation result.
        """
        payload = {
            "name": name,
            "nodes": nodes,
            "edges": edges or [],
            **kwargs,
        }
        
        url = f"{self._get_base_url()}/validate"
        response = self._make_request("POST", url, data=payload)
        return ValidationResult.from_dict(response)
    
    def execute(
        self,
        workflow_id: str,
        inputs: Optional[Dict] = None,
        skip_validation: bool = False,
    ) -> WorkflowExecution:
        """
        Execute a workflow.
        
        Args:
            workflow_id: The ID of the workflow to execute.
            inputs: Input data for the workflow.
            skip_validation: Skip validation before execution.
        
        Returns:
            The workflow execution.
        """
        url = f"{self._get_base_url()}/{workflow_id}/execute"
        params = {"skipValidation": skip_validation} if skip_validation else None
        response = self._make_request("POST", url, data=inputs or {}, params=params)
        return WorkflowExecution.from_dict(response)
    
    def get_execution_status(self, execution_id: str) -> WorkflowExecution:
        """
        Get execution status.
        
        Args:
            execution_id: The ID of the execution.
        
        Returns:
            The execution status.
        """
        url = f"{self._get_base_url()}/executions/{execution_id}/status"
        response = self._make_request("GET", url)
        return WorkflowExecution.from_dict(response)
    
    def pause_execution(self, execution_id: str) -> WorkflowExecution:
        """
        Pause a running execution.
        
        Args:
            execution_id: The ID of the execution.
        
        Returns:
            The updated execution.
        """
        url = f"{self._get_base_url()}/executions/{execution_id}/pause"
        response = self._make_request("POST", url)
        return WorkflowExecution.from_dict(response)
    
    def resume_execution(self, execution_id: str) -> WorkflowExecution:
        """
        Resume a paused execution.
        
        Args:
            execution_id: The ID of the execution.
        
        Returns:
            The updated execution.
        """
        url = f"{self._get_base_url()}/executions/{execution_id}/resume"
        response = self._make_request("POST", url)
        return WorkflowExecution.from_dict(response)
    
    def get_execution_history(self, workflow_id: str) -> List[WorkflowExecution]:
        """
        Get execution history for a workflow.
        
        Args:
            workflow_id: The ID of the workflow.
        
        Returns:
            List of executions.
        """
        url = f"{self._get_base_url()}/{workflow_id}/executions"
        response = self._make_request("GET", url)
        
        if isinstance(response, list):
            return [WorkflowExecution.from_dict(e) for e in response]
        return []
    
    def wait_for_completion(
        self,
        execution_id: str,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> WorkflowExecution:
        """
        Wait for a workflow execution to complete.
        
        Args:
            execution_id: The ID of the execution.
            timeout: Maximum time to wait in seconds.
            poll_interval: Time between status checks in seconds.
        
        Returns:
            The completed execution.
        
        Raises:
            TimeoutError: If execution doesn't complete within timeout.
            RuntimeError: If execution fails.
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Execution {execution_id} did not complete within {timeout}s"
                )
            
            execution = self.get_execution_status(execution_id)
            
            if execution.status == ExecutionStatus.COMPLETED:
                return execution
            elif execution.status == ExecutionStatus.FAILED:
                raise RuntimeError(
                    f"Execution {execution_id} failed: {execution.error}"
                )
            elif execution.status == ExecutionStatus.CANCELLED:
                raise RuntimeError(f"Execution {execution_id} was cancelled")
            
            time.sleep(poll_interval)
    
    def clone(
        self,
        workflow_id: str,
        new_name: str,
        include_history: bool = False,
    ) -> Workflow:
        """
        Clone a workflow.
        
        Args:
            workflow_id: The ID of the workflow to clone.
            new_name: Name for the cloned workflow.
            include_history: Include execution history.
        
        Returns:
            The cloned workflow.
        """
        url = f"{self._get_base_url()}/{workflow_id}/clone"
        params = {"newName": new_name, "includeHistory": include_history}
        response = self._make_request("POST", url, params=params)
        return Workflow.from_dict(response)
    
    def export(
        self,
        workflow_id: str,
        format: str = "json",
        include_metadata: bool = True,
    ) -> Union[Dict, str]:
        """
        Export a workflow.
        
        Args:
            workflow_id: The ID of the workflow.
            format: Export format ("json" or "yaml").
            include_metadata: Include metadata in export.
        
        Returns:
            Exported workflow data.
        """
        url = f"{self._get_base_url()}/{workflow_id}/export"
        params = {"format": format, "includeMetadata": include_metadata}
        return self._make_request("GET", url, params=params)
    
    def get_analytics(
        self,
        workflow_id: str,
        days: int = 30,
        detailed: bool = False,
    ) -> Dict:
        """
        Get workflow analytics.
        
        Args:
            workflow_id: The ID of the workflow.
            days: Number of days to analyze.
            detailed: Include detailed metrics.
        
        Returns:
            Analytics data.
        """
        url = f"{self._get_base_url()}/{workflow_id}/analytics"
        params = {"days": days, "detailed": detailed}
        return self._make_request("GET", url, params=params)
    
    def search(
        self,
        query: str,
        page: int = 0,
        size: int = 20,
    ) -> List[Workflow]:
        """
        Search workflows.
        
        Args:
            query: Search query.
            page: Page number (0-based).
            size: Number of results per page.
        
        Returns:
            List of matching workflows.
        """
        url = f"{self._get_base_url()}/search"
        params = {"query": query, "page": page, "size": size}
        response = self._make_request("GET", url, params=params)
        
        workflows_data = response.get("content", [])
        return [Workflow.from_dict(w) for w in workflows_data]
    
    def link_agent(self, workflow_id: str, agent_id: str) -> None:
        """
        Link an agent to a workflow.
        
        Args:
            workflow_id: The ID of the workflow.
            agent_id: The ID of the agent to link.
        """
        url = f"{self._get_base_url()}/{workflow_id}/agent/{agent_id}"
        self._make_request("POST", url)
    
    def unlink_agent(self, workflow_id: str, agent_id: str) -> None:
        """
        Unlink an agent from a workflow.
        
        Args:
            workflow_id: The ID of the workflow.
            agent_id: The ID of the agent to unlink.
        """
        url = f"{self._get_base_url()}/{workflow_id}/agent/{agent_id}"
        self._make_request("DELETE", url)







