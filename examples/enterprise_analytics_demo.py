#!/usr/bin/env python3
"""
Swfte Enterprise Analytics Demo

Demonstrates all enterprise-grade analytics features that differentiate
the official SDK from the open-source version.

Features demonstrated:
1. Team Analytics
2. Anomaly Detection
3. A/B Testing
4. Compliance Reporting
5. Cost Optimization
6. Model Comparison
7. User Journey Tracking
8. RAG Quality Metrics
9. Real-time Streaming
10. Custom Alerts
11. Usage Forecasting
12. Custom Metrics & Dashboards
"""

import os
from datetime import datetime, timedelta

# Swfte SDK imports
from swfte import SwfteClient
from swfte.analytics import (
    # Core
    Analytics,
    PromptInsight,
    PromptPatternSummary,

    # Enterprise
    EnterpriseAnalytics,
    TeamAnalytics,
    AnomalyDetection,
    ABTestingAnalytics,
    ComplianceReporting,
    CostOptimization,
    ModelComparison,
    UserJourneyAnalytics,
    RAGQualityMetrics,

    # Real-time
    RealtimeAnalytics,
    AnalyticsStream,
    LiveDashboard,

    # Alerts
    AlertManager,
    AlertRule,
    AlertPolicy,

    # Forecasting
    UsageForecaster,
    BudgetPredictor,
    CapacityPlanner,
    TrendAnalyzer,

    # Custom Metrics
    CustomMetrics,
    MetricDefinition,
)

from swfte.analytics.alerts import AlertCondition


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    # Initialize client
    client = SwfteClient(
        api_key=os.environ.get("SWFTE_API_KEY", "sk-swfte-demo"),
        workspace_id=os.environ.get("SWFTE_WORKSPACE_ID", "workspace-demo"),
    )

    print_section("SWFTE ENTERPRISE ANALYTICS DEMO")
    print("Demonstrating enterprise-grade features not available in OSS version")

    # =========================================================================
    # 1. TEAM ANALYTICS
    # =========================================================================
    print_section("1. Team Analytics")
    print("Track usage across teams and users")

    try:
        # Get team summary
        team = client.analytics.enterprise.teams.summary("team-123")
        print(f"\nTeam: {team.team_id}")
        print(f"  Members: {team.total_members}")
        print(f"  Total Prompts: {team.total_prompts:,}")
        print(f"  Total Cost: ${team.total_cost_usd:.2f}")
        print(f"  Avg Cost/User: ${team.avg_cost_per_user:.2f}")
        print(f"  Cost Trend: {team.cost_trend}")

        # Top users
        print("\n  Top Users:")
        for user in team.top_users[:3]:
            print(f"    - {user.name}: ${user.total_cost_usd:.2f} ({user.total_prompts} prompts)")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 2. ANOMALY DETECTION
    # =========================================================================
    print_section("2. ML-Powered Anomaly Detection")
    print("Automatically detect unusual patterns")

    try:
        anomalies = client.analytics.enterprise.anomalies.detect(
            workspace_id="workspace-123",
            lookback_hours=24,
            sensitivity="medium"
        )
        print(f"\n  Anomalies detected: {len(anomalies)}")
        for anomaly in anomalies[:3]:
            print(f"\n  [{anomaly.severity}] {anomaly.type}")
            print(f"    Metric: {anomaly.metric}")
            print(f"    Expected: {anomaly.expected_value:.2f}")
            print(f"    Actual: {anomaly.actual_value:.2f}")
            print(f"    Deviation: {anomaly.deviation_percent:.1f}%")
            if anomaly.recommendations:
                print(f"    Recommendation: {anomaly.recommendations[0]}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 3. A/B TESTING FRAMEWORK
    # =========================================================================
    print_section("3. A/B Testing Framework")
    print("Run experiments on prompts, models, and configurations")

    try:
        # Create an A/B test
        test = client.analytics.enterprise.ab_testing.create_test(
            name="GPT-4 vs GPT-4o-mini Cost Test",
            agent_id="agent-123",
            variant_a_config={"model": "gpt-4o"},
            variant_b_config={"model": "gpt-4o-mini"},
            traffic_split=0.5,
            metrics=["latency_ms", "cost_usd", "satisfaction"],
            min_sample_size=1000
        )
        print(f"\n  Test Created: {test.test_name}")
        print(f"  Status: {test.status}")
        print(f"  Variant A: {test.variant_a}")
        print(f"  Variant B: {test.variant_b}")

        # Get test results
        if test.status == "COMPLETED":
            print(f"\n  Results:")
            print(f"    Winner: {test.winner}")
            print(f"    Confidence: {test.confidence:.1%}")
            print(f"    Lift: {test.lift:.1%}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 4. COMPLIANCE REPORTING
    # =========================================================================
    print_section("4. Compliance Reporting (SOC2, GDPR, HIPAA)")
    print("Generate audit-ready compliance reports")

    try:
        report = client.analytics.enterprise.compliance.generate_report(
            framework="SOC2",
            workspace_id="workspace-123"
        )
        print(f"\n  Report: {report.report_id}")
        print(f"  Framework: {report.framework}")
        print(f"  Overall Score: {report.overall_score:.1f}/100")
        print(f"  Status: {report.status}")
        print(f"\n  Compliance Checks:")
        print(f"    Data Retention: {'✓' if report.data_retention_compliant else '✗'}")
        print(f"    PII Handling: {'✓' if report.pii_handling_compliant else '✗'}")
        print(f"    Access Control: {'✓' if report.access_control_compliant else '✗'}")
        print(f"    Audit Logging: {'✓' if report.audit_log_compliant else '✗'}")
        print(f"    Encryption: {'✓' if report.encryption_compliant else '✗'}")

        if report.recommendations:
            print(f"\n  Recommendations:")
            for rec in report.recommendations[:3]:
                print(f"    • {rec}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 5. COST OPTIMIZATION
    # =========================================================================
    print_section("5. AI-Powered Cost Optimization")
    print("Get recommendations to reduce LLM spending")

    try:
        recommendations = client.analytics.enterprise.cost_optimization.get_recommendations(
            workspace_id="workspace-123",
            min_savings_usd=10.0
        )
        print(f"\n  Recommendations found: {len(recommendations)}")
        for rec in recommendations[:3]:
            print(f"\n  [{rec.category}] {rec.title}")
            print(f"    Estimated Savings: ${rec.estimated_savings_usd:.2f}/month ({rec.estimated_savings_percent:.1f}%)")
            print(f"    Effort: {rec.effort} | Impact: {rec.impact}")
            if rec.implementation_steps:
                print(f"    First Step: {rec.implementation_steps[0]}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 6. MODEL COMPARISON
    # =========================================================================
    print_section("6. Model Benchmarking & Comparison")
    print("Compare model performance across your workload")

    try:
        benchmarks = client.analytics.enterprise.model_comparison.benchmark(
            workspace_id="workspace-123"
        )
        print(f"\n  Models benchmarked: {len(benchmarks)}")
        print(f"\n  {'Model':<25} {'Latency':<12} {'P95':<10} {'Cost/Req':<12} {'Quality'}")
        print("  " + "-" * 70)
        for b in benchmarks:
            quality = f"{b.quality_score:.1f}" if b.quality_score else "N/A"
            print(f"  {b.model:<25} {b.avg_latency_ms:>8.0f}ms {b.p95_latency_ms:>6.0f}ms ${b.avg_cost_per_request:>9.4f} {quality:>7}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 7. USER JOURNEY TRACKING
    # =========================================================================
    print_section("7. User Journey & Lifecycle Analytics")
    print("Track user progression and predict churn")

    try:
        journey = client.analytics.enterprise.user_journeys.get_journey("user-123")
        print(f"\n  User: {journey.user_id}")
        print(f"  Current Stage: {journey.current_stage}")
        print(f"  Total Sessions: {journey.total_sessions}")
        print(f"  Total Prompts: {journey.total_prompts:,}")
        print(f"  Lifetime Value: ${journey.lifetime_value:.2f}")
        print(f"  Churn Risk: {journey.churn_risk:.1%}")
        print(f"  Satisfaction Trend: {journey.satisfaction_trend}")

        # Churn prediction
        at_risk = client.analytics.enterprise.user_journeys.churn_prediction(
            workspace_id="workspace-123",
            threshold=0.7
        )
        print(f"\n  Users at risk of churning: {len(at_risk)}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 8. RAG QUALITY METRICS
    # =========================================================================
    print_section("8. RAG Quality Metrics")
    print("Measure and improve RAG pipeline quality")

    try:
        rag_metrics = client.analytics.enterprise.rag_quality.get_metrics(
            agent_id="rag-agent-123"
        )
        print(f"\n  Agent: {rag_metrics.agent_id}")
        print(f"  Total Queries: {rag_metrics.total_queries:,}")
        print(f"\n  Quality Scores:")
        print(f"    Retrieval Accuracy: {rag_metrics.retrieval_accuracy:.1%}")
        print(f"    Answer Relevance: {rag_metrics.answer_relevance:.1%}")
        print(f"    Faithfulness: {rag_metrics.faithfulness:.1%}")
        print(f"    Context Precision: {rag_metrics.context_precision:.1%}")
        print(f"    Context Recall: {rag_metrics.context_recall:.1%}")
        print(f"\n  Performance:")
        print(f"    Retrieval Latency: {rag_metrics.latency_retrieval_ms:.0f}ms")
        print(f"    Generation Latency: {rag_metrics.latency_generation_ms:.0f}ms")
        print(f"    Fallback Rate: {rag_metrics.fallback_rate:.1%}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 9. REAL-TIME STREAMING
    # =========================================================================
    print_section("9. Real-time Analytics Streaming")
    print("Stream events via WebSocket for live dashboards")

    print("""
    # Example: Stream live events
    for event in client.analytics.realtime.stream(
        event_types=["ANOMALY_DETECTED", "BUDGET_WARNING"],
        timeout=60
    ):
        print(f"{event.event_type}: {event.data}")

    # Example: Subscribe with callback
    def on_anomaly(event):
        send_slack_alert(event.data)

    stream = client.analytics.realtime.subscribe(
        event_types=["ANOMALY_DETECTED"],
        callback=on_anomaly
    )
    stream.start()
    """)

    # =========================================================================
    # 10. CUSTOM ALERTS
    # =========================================================================
    print_section("10. Enterprise Alert Management")
    print("Create custom alert rules with webhook integrations")

    try:
        # Create an alert rule
        rule = client.analytics.alerts.create_rule(
            name="High Latency Alert",
            conditions=[
                AlertCondition(
                    metric="latency_ms",
                    operator="GREATER_THAN",
                    threshold=5000,
                    duration_seconds=300,  # 5 minutes
                    aggregation="avg"
                )
            ],
            severity="WARNING",
            notification_channels=["slack-ops", "pagerduty"],
            labels={"team": "platform", "env": "production"}
        )
        print(f"\n  Rule Created: {rule.name}")
        print(f"  ID: {rule.id}")
        print(f"  Severity: {rule.severity}")
        print(f"  Channels: {', '.join(rule.notification_channels)}")

        # Create Slack integration
        slack = client.analytics.alerts.slack.create(
            name="Ops Channel",
            webhook_url="https://hooks.slack.com/services/...",
            channel="#ops-alerts"
        )
        print(f"\n  Slack Integration: {slack.name}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 11. USAGE FORECASTING
    # =========================================================================
    print_section("11. ML-Powered Usage Forecasting")
    print("Predict future usage and costs")

    try:
        # Usage forecast
        usage = client.analytics.enterprise.forecasting.predict_usage(
            workspace_id="workspace-123",
            metric="prompts",
            horizon_days=30
        )
        print(f"\n  Usage Forecast (next 30 days):")
        print(f"    Model: {usage.model_type}")
        print(f"    MAPE: {usage.mape:.1%}")
        for pred in usage.predictions[:7]:
            print(f"    {pred['timestamp']}: {pred['value']:.0f} prompts")

        # Budget forecast
        budget = client.analytics.enterprise.budget.forecast(
            workspace_id="workspace-123"
        )
        print(f"\n  Budget Forecast:")
        print(f"    Current Spend: ${budget.current_spend_usd:.2f}")
        print(f"    Projected Daily: ${budget.projected_daily_usd:.2f}")
        print(f"    Projected Monthly: ${budget.projected_monthly_usd:.2f}")
        if budget.days_until_budget_exceeded:
            print(f"    ⚠️  Budget exceeded in: {budget.days_until_budget_exceeded} days")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # 12. CUSTOM METRICS & DASHBOARDS
    # =========================================================================
    print_section("12. Custom Metrics & Dashboards")
    print("Define your own metrics and build custom dashboards")

    try:
        # Create custom metric
        metric = client.analytics.custom.metrics.create(
            name="cost_per_successful_response",
            description="Average cost per successful (non-error) response",
            type="COMPUTED",
            formula="sum(cost_usd) / (count(prompts) - count(errors))",
            unit="USD"
        )
        print(f"\n  Custom Metric: {metric.name}")
        print(f"    Type: {metric.type}")
        print(f"    Formula: {metric.formula}")

        # Create dimension
        dimension = client.analytics.custom.dimensions.create(
            name="customer_tier",
            description="Customer subscription tier",
            source_field="metadata.customer.tier",
            value_mapping={
                "enterprise": "Enterprise",
                "pro": "Professional",
                "free": "Free Tier"
            }
        )
        print(f"\n  Custom Dimension: {dimension.name}")

        # Create dashboard
        dashboard = client.analytics.custom.dashboards.create(
            name="Executive Summary",
            description="High-level metrics for leadership",
            is_shared=True
        )
        print(f"\n  Dashboard Created: {dashboard.name}")

        # Add widget
        widget = client.analytics.custom.dashboards.add_widget(
            dashboard_id=dashboard.id,
            widget_type="LINE_CHART",
            title="Cost per Response by Tier",
            metrics=["cost_per_successful_response"],
            dimensions=["customer_tier"],
            position={"x": 0, "y": 0, "w": 12, "h": 6}
        )
        print(f"  Widget Added: {widget.title}")
    except Exception as e:
        print(f"  [Demo mode - API not connected: {e}]")

    # =========================================================================
    # COMPARISON: OSS vs Enterprise
    # =========================================================================
    print_section("Feature Comparison: OSS vs Enterprise")
    print("""
    +-----------------------------------+------------+------------+
    | Feature                           | OSS        | Enterprise |
    +-----------------------------------+------------+------------+
    | PII Detection                     | Regex      | ML-Powered |
    | Intent Classification             | Rules      | ML-Powered |
    | Sentiment Analysis                | Keywords   | ML-Powered |
    | Cost Tracking                     | Local      | Cloud+Local|
    | Storage                           | SQLite     | DynamoDB   |
    | Dashboard                         | Terminal   | Web UI     |
    +-----------------------------------+------------+------------+
    | Team Analytics                    |     ✗      |     ✓      |
    | Anomaly Detection                 |     ✗      |     ✓      |
    | A/B Testing                       |     ✗      |     ✓      |
    | Compliance Reporting              |     ✗      |     ✓      |
    | Cost Optimization                 |     ✗      |     ✓      |
    | Model Comparison                  |     ✗      |     ✓      |
    | User Journey Tracking             |     ✗      |     ✓      |
    | RAG Quality Metrics               |     ✗      |     ✓      |
    | Real-time Streaming               |     ✗      |     ✓      |
    | Custom Alerts + Webhooks          |     ✗      |     ✓      |
    | Usage Forecasting                 |     ✗      |     ✓      |
    | Custom Metrics & Dashboards       |     ✗      |     ✓      |
    | Embedding Analytics               |     ✗      |     ✓      |
    | Escalation Policies               |     ✗      |     ✓      |
    | Data Retention Policies           |     ✗      |     ✓      |
    | SSO / SAML Integration            |     ✗      |     ✓      |
    +-----------------------------------+------------+------------+
    | Price                             | FREE       | Usage-based|
    +-----------------------------------+------------+------------+
    """)

    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("  Get started: https://swfte.com/enterprise")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
