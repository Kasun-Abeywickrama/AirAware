"""
API Routes Package.

Contains FastAPI route modules for all public REST API endpoints:
- status.py: System health and component availability (/api/v1/status).
- conditions.py: Latest real-time PM2.5 conditions (/api/v1/current-conditions).
- forecasts.py: Latest 1h/6h/24h ML forecasts and history (/api/v1/forecasts/latest, /api/v1/forecasts/history).
- activity_plans.py: Exposure-aware outdoor activity planner (/api/v1/activity-plans).
- alert_preferences.py: Anonymous threshold alerts (/api/v1/alert-preferences/{browser_id}).
"""
