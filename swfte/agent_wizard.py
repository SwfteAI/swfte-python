"""
Agent Wizard V2 resource client — generate, refine, and persist agents from
plain-English prompts or templates.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class AgentWizard(V2Resource):
    """Client for ``/v2/agents/wizard``."""

    _path_prefix = "/v2/agents/wizard"

    def generate(
        self,
        prompt: str,
        agent_type: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate an agent from a prompt (review-able draft)."""
        payload: Dict[str, Any] = {"prompt": prompt, **kwargs}
        if agent_type is not None:
            payload["agentType"] = agent_type
        if provider is not None:
            payload["provider"] = provider
        return self._request("POST", self._url("/generate"), data=payload)

    def generate_stream(self, prompt: str, **kwargs: Any) -> Any:
        """Open the SSE stream for agent generation; returns the underlying ``Response``."""
        params: Dict[str, Any] = {"prompt": prompt, **kwargs}
        return self._request("GET", self._url("/generate/stream"), params=params, stream=True)

    def quick(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate and immediately persist an agent (no review step)."""
        return self._request("POST", self._url("/quick"), data={"prompt": prompt, **kwargs})

    def review(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Review a draft and return suggestions."""
        return self._request("POST", self._url("/review"), data=draft)

    def refine(self, draft: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """Refine an existing draft using natural-language feedback."""
        return self._request(
            "POST",
            self._url("/refine"),
            data={"draft": draft, "feedback": feedback},
        )

    def create(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a generated agent."""
        return self._request("POST", self._url("/create"), data=draft)

    def link_tools(self, agent_id: str, tool_ids: List[str]) -> Dict[str, Any]:
        """Link MCP tools to a wizard-generated agent."""
        return self._request(
            "POST",
            self._url("/link-tools"),
            data={"agentId": agent_id, "toolIds": tool_ids},
        )

    def link_knowledge(self, agent_id: str, dataset_ids: List[str]) -> Dict[str, Any]:
        """Link knowledge bases (datasets) to a wizard-generated agent."""
        return self._request(
            "POST",
            self._url("/link-knowledge"),
            data={"agentId": agent_id, "datasetIds": dataset_ids},
        )

    def templates(self) -> List[Dict[str, Any]]:
        """List wizard templates."""
        return self._request("GET", self._url("/templates"))

    def template(self, name: str) -> Dict[str, Any]:
        """Get a wizard template by name."""
        return self._request("GET", self._url(f"/templates/{name}"))

    def agent_types(self) -> List[Dict[str, Any]]:
        """List supported agent types."""
        return self._request("GET", self._url("/agent-types"))

    def providers(self) -> List[Dict[str, Any]]:
        """List supported providers."""
        return self._request("GET", self._url("/providers"))

    def from_template(
        self,
        template_name: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create an agent from a named template."""
        return self._request(
            "POST",
            self._url(f"/from-template/{template_name}"),
            data=overrides or {},
        )
