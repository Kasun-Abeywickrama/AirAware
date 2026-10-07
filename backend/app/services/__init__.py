"""
Services Package.

Contains business logic and application service modules for AirAware:
- validation.py: Ingestion data validation and physical boundary constraints.
- public_data.py: Read models for current conditions and multi-horizon forecasts.
- forecast_inputs.py: ML model input readiness evaluation (168h lags and 24h weather).
- forecasting.py: GRU/XGBoost inference, conformal prediction bounds, and XAI explainability.
- status.py: Subsystem health monitoring and pipeline availability aggregation.
- user_features.py: Interactive history charts, activity planning sliding windows, and alert preferences.
"""
