"""
Usage Forecasting & Capacity Planning Module

Enterprise-only forecasting features:
- ML-powered usage prediction
- Budget forecasting and planning
- Capacity planning recommendations
- Trend analysis with seasonality detection
- What-if scenario modeling
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import requests


# =============================================================================
# Enums
# =============================================================================

class ForecastGranularity(Enum):
    """Forecast time granularity."""
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class TrendDirection(Enum):
    """Trend direction."""
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    CYCLICAL = "CYCLICAL"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class UsageForecast:
    """Usage forecast prediction."""
    metric: str
    granularity: str
    predictions: List[Dict[str, Any]]  # Each has timestamp, value, lower_bound, upper_bound
    confidence_interval: float  # e.g., 0.95 for 95% CI
    model_type: str  # ARIMA, Prophet, etc.
    training_data_points: int
    mape: float  # Mean Absolute Percentage Error
    created_at: str


@dataclass
class BudgetForecast:
    """Budget forecast with projections."""
    current_spend_usd: float
    projected_daily_usd: float
    projected_monthly_usd: float
    days_until_budget_exceeded: Optional[int]
    recommended_daily_limit: float
    cost_by_category: Dict[str, float]
    trend: str
    confidence: float
    scenarios: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CapacityRecommendation:
    """Capacity planning recommendation."""
    resource: str
    current_utilization: float
    projected_utilization: float
    projected_date: str
    recommendation: str
    urgency: str  # LOW, MEDIUM, HIGH, CRITICAL
    estimated_cost_impact_usd: float
    actions: List[str] = field(default_factory=list)


@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric: str
    direction: str
    slope: float  # Rate of change
    r_squared: float  # Goodness of fit
    seasonality_detected: bool
    seasonal_period: Optional[str] = None  # e.g., "daily", "weekly"
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    change_points: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ScenarioResult:
    """What-if scenario modeling result."""
    scenario_name: str
    assumptions: Dict[str, Any]
    projected_prompts: int
    projected_tokens: int
    projected_cost_usd: float
    projected_latency_ms: float
    comparison_to_baseline: Dict[str, float]
    risks: List[str] = field(default_factory=list)


# =============================================================================
# Usage Forecaster
# =============================================================================

class UsageForecaster:
    """
    ML-powered usage forecasting.

    Example:
        forecaster = client.analytics.enterprise.forecasting

        # Predict next week's usage
        forecast = forecaster.predict_usage(
            workspace_id="ws-123",
            metric="prompts",
            horizon_days=7
        )

        for point in forecast.predictions:
            print(f"{point['timestamp']}: {point['value']:.0f} prompts")
    """

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def predict_usage(
        self,
        workspace_id: str,
        metric: str = "prompts",  # prompts, tokens, cost, latency
        horizon_days: int = 7,
        granularity: str = "DAILY",
        include_confidence_intervals: bool = True,
        agent_id: Optional[str] = None,
    ) -> UsageForecast:
        """
        Predict future usage.

        Args:
            workspace_id: Workspace ID
            metric: Metric to forecast
            horizon_days: Days to forecast ahead
            granularity: Prediction granularity
            include_confidence_intervals: Include uncertainty bounds
            agent_id: Optional agent filter

        Returns:
            UsageForecast with predictions
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/usage"

        params = {
            "workspaceId": workspace_id,
            "metric": metric,
            "horizonDays": horizon_days,
            "granularity": granularity,
            "includeConfidenceIntervals": str(include_confidence_intervals).lower(),
        }
        if agent_id:
            params["agentId"] = agent_id

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return UsageForecast(
            metric=data.get("metric", metric),
            granularity=data.get("granularity", granularity),
            predictions=data.get("predictions", []),
            confidence_interval=data.get("confidenceInterval", 0.95),
            model_type=data.get("modelType", ""),
            training_data_points=data.get("trainingDataPoints", 0),
            mape=data.get("mape", 0.0),
            created_at=data.get("createdAt", ""),
        )

    def predict_growth(
        self,
        workspace_id: str,
        horizon_months: int = 3,
    ) -> Dict[str, Any]:
        """
        Predict usage growth trajectory.

        Args:
            workspace_id: Workspace ID
            horizon_months: Months to forecast

        Returns:
            Growth predictions with milestones
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/growth"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params={"workspaceId": workspace_id, "horizonMonths": horizon_months},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


# =============================================================================
# Budget Predictor
# =============================================================================

class BudgetPredictor:
    """
    Budget forecasting and cost projections.

    Example:
        budget = client.analytics.enterprise.budget

        forecast = budget.forecast(workspace_id="ws-123")
        print(f"Projected monthly: ${forecast.projected_monthly_usd:.2f}")

        if forecast.days_until_budget_exceeded:
            print(f"WARNING: Budget exceeded in {forecast.days_until_budget_exceeded} days")
    """

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def forecast(
        self,
        workspace_id: str,
        horizon_days: int = 30,
        include_scenarios: bool = True,
    ) -> BudgetForecast:
        """
        Forecast budget and spending.

        Args:
            workspace_id: Workspace ID
            horizon_days: Days to forecast
            include_scenarios: Include best/worst case scenarios

        Returns:
            BudgetForecast with projections
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/budget"

        params = {
            "workspaceId": workspace_id,
            "horizonDays": horizon_days,
            "includeScenarios": str(include_scenarios).lower(),
        }

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return BudgetForecast(
            current_spend_usd=data.get("currentSpendUsd", 0.0),
            projected_daily_usd=data.get("projectedDailyUsd", 0.0),
            projected_monthly_usd=data.get("projectedMonthlyUsd", 0.0),
            days_until_budget_exceeded=data.get("daysUntilBudgetExceeded"),
            recommended_daily_limit=data.get("recommendedDailyLimit", 0.0),
            cost_by_category=data.get("costByCategory", {}),
            trend=data.get("trend", "STABLE"),
            confidence=data.get("confidence", 0.0),
            scenarios=data.get("scenarios", []),
        )

    def what_if(
        self,
        workspace_id: str,
        scenario_name: str,
        assumptions: Dict[str, Any],
    ) -> ScenarioResult:
        """
        Run what-if scenario analysis.

        Args:
            workspace_id: Workspace ID
            scenario_name: Name for the scenario
            assumptions: Scenario assumptions, e.g.:
                - prompt_volume_change: 0.5 (50% increase)
                - model_switch: "gpt-4o-mini"
                - new_agent_count: 3

        Returns:
            ScenarioResult with projections
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/what-if"

        payload = {
            "workspaceId": workspace_id,
            "scenarioName": scenario_name,
            "assumptions": assumptions,
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return ScenarioResult(
            scenario_name=data.get("scenarioName", scenario_name),
            assumptions=data.get("assumptions", {}),
            projected_prompts=data.get("projectedPrompts", 0),
            projected_tokens=data.get("projectedTokens", 0),
            projected_cost_usd=data.get("projectedCostUsd", 0.0),
            projected_latency_ms=data.get("projectedLatencyMs", 0.0),
            comparison_to_baseline=data.get("comparisonToBaseline", {}),
            risks=data.get("risks", []),
        )


# =============================================================================
# Capacity Planner
# =============================================================================

class CapacityPlanner:
    """
    Capacity planning and resource recommendations.

    Example:
        planner = client.analytics.enterprise.capacity

        recs = planner.get_recommendations(workspace_id="ws-123")
        for rec in recs:
            if rec.urgency == "HIGH":
                print(f"URGENT: {rec.recommendation}")
    """

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def get_recommendations(
        self,
        workspace_id: str,
        horizon_days: int = 30,
    ) -> List[CapacityRecommendation]:
        """
        Get capacity planning recommendations.

        Args:
            workspace_id: Workspace ID
            horizon_days: Planning horizon

        Returns:
            List of CapacityRecommendation
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/capacity"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params={"workspaceId": workspace_id, "horizonDays": horizon_days},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        recommendations = []
        for item in response.json().get("recommendations", []):
            recommendations.append(CapacityRecommendation(
                resource=item.get("resource", ""),
                current_utilization=item.get("currentUtilization", 0.0),
                projected_utilization=item.get("projectedUtilization", 0.0),
                projected_date=item.get("projectedDate", ""),
                recommendation=item.get("recommendation", ""),
                urgency=item.get("urgency", "LOW"),
                estimated_cost_impact_usd=item.get("estimatedCostImpactUsd", 0.0),
                actions=item.get("actions", []),
            ))

        return recommendations

    def simulate_scaling(
        self,
        workspace_id: str,
        scale_factor: float,
    ) -> Dict[str, Any]:
        """
        Simulate scaling impact.

        Args:
            workspace_id: Workspace ID
            scale_factor: Scale multiplier (e.g., 2.0 for 2x)

        Returns:
            Scaling simulation results
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/scaling"

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json={"workspaceId": workspace_id, "scaleFactor": scale_factor},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


# =============================================================================
# Trend Analyzer
# =============================================================================

class TrendAnalyzer:
    """
    Advanced trend analysis with seasonality detection.

    Example:
        trends = client.analytics.enterprise.trends

        analysis = trends.analyze(
            workspace_id="ws-123",
            metric="latency_ms",
            period_days=30
        )

        if analysis.seasonality_detected:
            print(f"Seasonality: {analysis.seasonal_period}")
    """

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def analyze(
        self,
        workspace_id: str,
        metric: str,
        period_days: int = 30,
        detect_anomalies: bool = True,
        detect_change_points: bool = True,
        agent_id: Optional[str] = None,
    ) -> TrendAnalysis:
        """
        Analyze metric trends.

        Args:
            workspace_id: Workspace ID
            metric: Metric to analyze
            period_days: Analysis period
            detect_anomalies: Detect anomalous points
            detect_change_points: Detect trend changes
            agent_id: Optional agent filter

        Returns:
            TrendAnalysis with insights
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/trends"

        params = {
            "workspaceId": workspace_id,
            "metric": metric,
            "periodDays": period_days,
            "detectAnomalies": str(detect_anomalies).lower(),
            "detectChangePoints": str(detect_change_points).lower(),
        }
        if agent_id:
            params["agentId"] = agent_id

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return TrendAnalysis(
            metric=data.get("metric", metric),
            direction=data.get("direction", "STABLE"),
            slope=data.get("slope", 0.0),
            r_squared=data.get("rSquared", 0.0),
            seasonality_detected=data.get("seasonalityDetected", False),
            seasonal_period=data.get("seasonalPeriod"),
            anomalies=data.get("anomalies", []),
            change_points=data.get("changePoints", []),
        )

    def compare_periods(
        self,
        workspace_id: str,
        metric: str,
        period1_start: str,
        period1_end: str,
        period2_start: str,
        period2_end: str,
    ) -> Dict[str, Any]:
        """
        Compare metrics between two time periods.

        Args:
            workspace_id: Workspace ID
            metric: Metric to compare
            period1_start/end: First period dates
            period2_start/end: Second period dates

        Returns:
            Comparison results
        """
        url = f"{self._get_base_url()}/v1/analytics/enterprise/forecasting/compare"

        payload = {
            "workspaceId": workspace_id,
            "metric": metric,
            "period1": {"start": period1_start, "end": period1_end},
            "period2": {"start": period2_start, "end": period2_end},
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()
