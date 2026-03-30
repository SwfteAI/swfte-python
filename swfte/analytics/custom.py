"""
Custom Metrics & Dimensions Module

Enterprise-only customization features:
- Define custom metrics from existing data
- Create custom dimensions for segmentation
- Build custom dashboards
- Computed metrics with formulas
- Metric aggregations and rollups
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import requests


# =============================================================================
# Enums
# =============================================================================

class MetricType(Enum):
    """Types of custom metrics."""
    COUNTER = "COUNTER"  # Cumulative count
    GAUGE = "GAUGE"  # Point-in-time value
    HISTOGRAM = "HISTOGRAM"  # Distribution
    RATE = "RATE"  # Rate of change
    COMPUTED = "COMPUTED"  # Derived from other metrics


class AggregationType(Enum):
    """Aggregation types for metrics."""
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    PERCENTILE_50 = "PERCENTILE_50"
    PERCENTILE_90 = "PERCENTILE_90"
    PERCENTILE_95 = "PERCENTILE_95"
    PERCENTILE_99 = "PERCENTILE_99"


class WidgetType(Enum):
    """Dashboard widget types."""
    LINE_CHART = "LINE_CHART"
    BAR_CHART = "BAR_CHART"
    PIE_CHART = "PIE_CHART"
    STAT = "STAT"
    TABLE = "TABLE"
    HEATMAP = "HEATMAP"
    GAUGE = "GAUGE"
    TEXT = "TEXT"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class MetricDefinition:
    """Custom metric definition."""
    id: str
    name: str
    description: str
    type: str
    unit: str  # e.g., "ms", "count", "USD", "percent"
    formula: Optional[str] = None  # For computed metrics
    source_metrics: List[str] = field(default_factory=list)
    aggregation: str = "AVG"
    dimensions: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    workspace_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class DimensionDefinition:
    """Custom dimension for segmentation."""
    id: str
    name: str
    description: str
    source_field: str  # Field to extract from
    extraction_pattern: Optional[str] = None  # Regex or JSONPath
    value_mapping: Dict[str, str] = field(default_factory=dict)
    default_value: str = "unknown"
    enabled: bool = True
    workspace_id: Optional[str] = None


@dataclass
class MetricAggregation:
    """Pre-computed metric aggregation."""
    id: str
    name: str
    source_metric: str
    aggregation_type: str
    granularity: str  # MINUTE, HOUR, DAY
    dimensions: List[str]
    retention_days: int = 90
    enabled: bool = True


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    id: str
    type: str
    title: str
    metrics: List[str]
    dimensions: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    time_range: str = "24h"
    refresh_interval_seconds: int = 60
    position: Dict[str, int] = field(default_factory=dict)  # x, y, w, h
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomDashboard:
    """Custom dashboard definition."""
    id: str
    name: str
    description: str
    widgets: List[DashboardWidget]
    workspace_id: Optional[str] = None
    is_default: bool = False
    is_shared: bool = False
    owner_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class MetricValue:
    """A metric value with timestamp and dimensions."""
    metric: str
    value: float
    timestamp: str
    dimensions: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Custom Metrics Manager
# =============================================================================

class CustomMetrics:
    """
    Custom metrics and dimensions management.

    Example:
        custom = client.analytics.custom

        # Define a custom metric
        metric = custom.metrics.create(
            name="cost_per_successful_response",
            description="Average cost for successful responses",
            type="COMPUTED",
            formula="cost_usd / (prompts - errors)",
            unit="USD"
        )

        # Create a dimension
        dimension = custom.dimensions.create(
            name="customer_tier",
            source_field="metadata.customer_tier",
            value_mapping={"enterprise": "Enterprise", "pro": "Pro"}
        )

        # Query custom metric
        values = custom.query(
            metrics=["cost_per_successful_response"],
            dimensions=["customer_tier"],
            time_range="7d"
        )
    """

    def __init__(self, client):
        self._client = client
        self._metrics_manager = None
        self._dimensions_manager = None
        self._aggregations_manager = None
        self._dashboards_manager = None

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    @property
    def metrics(self) -> "MetricsManager":
        """Manage custom metric definitions."""
        if self._metrics_manager is None:
            self._metrics_manager = MetricsManager(self._client)
        return self._metrics_manager

    @property
    def dimensions(self) -> "DimensionsManager":
        """Manage custom dimensions."""
        if self._dimensions_manager is None:
            self._dimensions_manager = DimensionsManager(self._client)
        return self._dimensions_manager

    @property
    def aggregations(self) -> "AggregationsManager":
        """Manage metric aggregations."""
        if self._aggregations_manager is None:
            self._aggregations_manager = AggregationsManager(self._client)
        return self._aggregations_manager

    @property
    def dashboards(self) -> "DashboardsManager":
        """Manage custom dashboards."""
        if self._dashboards_manager is None:
            self._dashboards_manager = DashboardsManager(self._client)
        return self._dashboards_manager

    def query(
        self,
        metrics: List[str],
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        time_range: str = "24h",
        granularity: str = "HOUR",
    ) -> List[MetricValue]:
        """
        Query custom metrics.

        Args:
            metrics: List of metric names
            workspace_id: Optional workspace filter
            agent_id: Optional agent filter
            dimensions: Dimensions to group by
            filters: Additional filters
            time_range: Time range (e.g., "1h", "24h", "7d", "30d")
            granularity: Data point granularity

        Returns:
            List of MetricValue objects
        """
        url = f"{self._get_base_url()}/v1/analytics/custom/query"

        payload = {
            "metrics": metrics,
            "timeRange": time_range,
            "granularity": granularity,
        }
        if workspace_id:
            payload["workspaceId"] = workspace_id
        if agent_id:
            payload["agentId"] = agent_id
        if dimensions:
            payload["dimensions"] = dimensions
        if filters:
            payload["filters"] = filters

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        values = []
        for item in response.json().get("values", []):
            values.append(MetricValue(
                metric=item.get("metric", ""),
                value=item.get("value", 0.0),
                timestamp=item.get("timestamp", ""),
                dimensions=item.get("dimensions", {}),
            ))

        return values

    def record(
        self,
        metric: str,
        value: float,
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Record a custom metric value.

        Args:
            metric: Metric name
            value: Metric value
            dimensions: Optional dimension values
            timestamp: Optional timestamp (defaults to now)

        Returns:
            True if successful
        """
        url = f"{self._get_base_url()}/v1/analytics/custom/record"

        payload = {
            "metric": metric,
            "value": value,
            "dimensions": dimensions or {},
        }
        if timestamp:
            payload["timestamp"] = timestamp

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )

        return response.status_code == 201


# =============================================================================
# Metrics Manager
# =============================================================================

class MetricsManager:
    """Manage custom metric definitions."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        description: str,
        type: str = "GAUGE",
        unit: str = "",
        formula: Optional[str] = None,
        source_metrics: Optional[List[str]] = None,
        aggregation: str = "AVG",
        dimensions: Optional[List[str]] = None,
    ) -> MetricDefinition:
        """Create a custom metric definition."""
        url = f"{self._get_base_url()}/v1/analytics/custom/metrics"

        payload = {
            "name": name,
            "description": description,
            "type": type,
            "unit": unit,
            "aggregation": aggregation,
            "dimensions": dimensions or [],
        }
        if formula:
            payload["formula"] = formula
        if source_metrics:
            payload["sourceMetrics"] = source_metrics

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_metric(response.json())

    def get(self, metric_id: str) -> MetricDefinition:
        """Get a metric definition."""
        url = f"{self._get_base_url()}/v1/analytics/custom/metrics/{metric_id}"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_metric(response.json())

    def list(self, type: Optional[str] = None) -> List[MetricDefinition]:
        """List all custom metrics."""
        url = f"{self._get_base_url()}/v1/analytics/custom/metrics"

        params = {}
        if type:
            params["type"] = type

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return [self._parse_metric(m) for m in response.json().get("metrics", [])]

    def update(self, metric_id: str, **updates) -> MetricDefinition:
        """Update a metric definition."""
        url = f"{self._get_base_url()}/v1/analytics/custom/metrics/{metric_id}"

        response = requests.patch(
            url,
            headers=self._client._get_headers(),
            json=updates,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_metric(response.json())

    def delete(self, metric_id: str) -> bool:
        """Delete a metric definition."""
        url = f"{self._get_base_url()}/v1/analytics/custom/metrics/{metric_id}"

        response = requests.delete(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )

        return response.status_code == 204

    def _parse_metric(self, data: Dict[str, Any]) -> MetricDefinition:
        return MetricDefinition(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            type=data.get("type", ""),
            unit=data.get("unit", ""),
            formula=data.get("formula"),
            source_metrics=data.get("sourceMetrics", []),
            aggregation=data.get("aggregation", "AVG"),
            dimensions=data.get("dimensions", []),
            filters=data.get("filters", {}),
            enabled=data.get("enabled", True),
            workspace_id=data.get("workspaceId"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


# =============================================================================
# Dimensions Manager
# =============================================================================

class DimensionsManager:
    """Manage custom dimensions."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        description: str,
        source_field: str,
        extraction_pattern: Optional[str] = None,
        value_mapping: Optional[Dict[str, str]] = None,
        default_value: str = "unknown",
    ) -> DimensionDefinition:
        """Create a custom dimension."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dimensions"

        payload = {
            "name": name,
            "description": description,
            "sourceField": source_field,
            "defaultValue": default_value,
        }
        if extraction_pattern:
            payload["extractionPattern"] = extraction_pattern
        if value_mapping:
            payload["valueMapping"] = value_mapping

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return DimensionDefinition(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            source_field=data.get("sourceField", ""),
            extraction_pattern=data.get("extractionPattern"),
            value_mapping=data.get("valueMapping", {}),
            default_value=data.get("defaultValue", "unknown"),
            enabled=data.get("enabled", True),
            workspace_id=data.get("workspaceId"),
        )

    def list(self) -> List[DimensionDefinition]:
        """List all custom dimensions."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dimensions"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        dimensions = []
        for data in response.json().get("dimensions", []):
            dimensions.append(DimensionDefinition(
                id=data.get("id", ""),
                name=data.get("name", ""),
                description=data.get("description", ""),
                source_field=data.get("sourceField", ""),
                extraction_pattern=data.get("extractionPattern"),
                value_mapping=data.get("valueMapping", {}),
                default_value=data.get("defaultValue", "unknown"),
                enabled=data.get("enabled", True),
                workspace_id=data.get("workspaceId"),
            ))

        return dimensions

    def delete(self, dimension_id: str) -> bool:
        """Delete a dimension."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dimensions/{dimension_id}"

        response = requests.delete(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )

        return response.status_code == 204


# =============================================================================
# Aggregations Manager
# =============================================================================

class AggregationsManager:
    """Manage pre-computed metric aggregations."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        source_metric: str,
        aggregation_type: str,
        granularity: str = "HOUR",
        dimensions: Optional[List[str]] = None,
        retention_days: int = 90,
    ) -> MetricAggregation:
        """Create a metric aggregation."""
        url = f"{self._get_base_url()}/v1/analytics/custom/aggregations"

        payload = {
            "name": name,
            "sourceMetric": source_metric,
            "aggregationType": aggregation_type,
            "granularity": granularity,
            "dimensions": dimensions or [],
            "retentionDays": retention_days,
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return MetricAggregation(
            id=data.get("id", ""),
            name=data.get("name", ""),
            source_metric=data.get("sourceMetric", ""),
            aggregation_type=data.get("aggregationType", ""),
            granularity=data.get("granularity", "HOUR"),
            dimensions=data.get("dimensions", []),
            retention_days=data.get("retentionDays", 90),
            enabled=data.get("enabled", True),
        )

    def list(self) -> List[MetricAggregation]:
        """List all aggregations."""
        url = f"{self._get_base_url()}/v1/analytics/custom/aggregations"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        aggregations = []
        for data in response.json().get("aggregations", []):
            aggregations.append(MetricAggregation(
                id=data.get("id", ""),
                name=data.get("name", ""),
                source_metric=data.get("sourceMetric", ""),
                aggregation_type=data.get("aggregationType", ""),
                granularity=data.get("granularity", "HOUR"),
                dimensions=data.get("dimensions", []),
                retention_days=data.get("retentionDays", 90),
                enabled=data.get("enabled", True),
            ))

        return aggregations


# =============================================================================
# Dashboards Manager
# =============================================================================

class DashboardsManager:
    """Manage custom dashboards."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        description: str = "",
        widgets: Optional[List[Dict[str, Any]]] = None,
        is_shared: bool = False,
    ) -> CustomDashboard:
        """Create a custom dashboard."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dashboards"

        payload = {
            "name": name,
            "description": description,
            "widgets": widgets or [],
            "isShared": is_shared,
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_dashboard(response.json())

    def get(self, dashboard_id: str) -> CustomDashboard:
        """Get a dashboard."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dashboards/{dashboard_id}"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_dashboard(response.json())

    def list(self, include_shared: bool = True) -> List[CustomDashboard]:
        """List all dashboards."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dashboards"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params={"includeShared": str(include_shared).lower()},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return [self._parse_dashboard(d) for d in response.json().get("dashboards", [])]

    def update(self, dashboard_id: str, **updates) -> CustomDashboard:
        """Update a dashboard."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dashboards/{dashboard_id}"

        response = requests.patch(
            url,
            headers=self._client._get_headers(),
            json=updates,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_dashboard(response.json())

    def add_widget(
        self,
        dashboard_id: str,
        widget_type: str,
        title: str,
        metrics: List[str],
        dimensions: Optional[List[str]] = None,
        position: Optional[Dict[str, int]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> DashboardWidget:
        """Add a widget to a dashboard."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dashboards/{dashboard_id}/widgets"

        payload = {
            "type": widget_type,
            "title": title,
            "metrics": metrics,
            "dimensions": dimensions or [],
            "position": position or {"x": 0, "y": 0, "w": 6, "h": 4},
            "options": options or {},
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return DashboardWidget(
            id=data.get("id", ""),
            type=data.get("type", ""),
            title=data.get("title", ""),
            metrics=data.get("metrics", []),
            dimensions=data.get("dimensions", []),
            filters=data.get("filters", {}),
            time_range=data.get("timeRange", "24h"),
            refresh_interval_seconds=data.get("refreshIntervalSeconds", 60),
            position=data.get("position", {}),
            options=data.get("options", {}),
        )

    def delete(self, dashboard_id: str) -> bool:
        """Delete a dashboard."""
        url = f"{self._get_base_url()}/v1/analytics/custom/dashboards/{dashboard_id}"

        response = requests.delete(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )

        return response.status_code == 204

    def _parse_dashboard(self, data: Dict[str, Any]) -> CustomDashboard:
        widgets = []
        for w in data.get("widgets", []):
            widgets.append(DashboardWidget(
                id=w.get("id", ""),
                type=w.get("type", ""),
                title=w.get("title", ""),
                metrics=w.get("metrics", []),
                dimensions=w.get("dimensions", []),
                filters=w.get("filters", {}),
                time_range=w.get("timeRange", "24h"),
                refresh_interval_seconds=w.get("refreshIntervalSeconds", 60),
                position=w.get("position", {}),
                options=w.get("options", {}),
            ))

        return CustomDashboard(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            widgets=widgets,
            workspace_id=data.get("workspaceId"),
            is_default=data.get("isDefault", False),
            is_shared=data.get("isShared", False),
            owner_id=data.get("ownerId"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )
