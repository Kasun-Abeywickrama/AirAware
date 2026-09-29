export type Availability = "available" | "limited" | "unavailable" | "not_started";

export interface SystemStatus {
  status: "available" | "limited";
  database: "connected" | "unreachable";
  pm25: { status: Availability; last_completed_at: string | null };
  weather: { status: Availability; last_completed_at: string | null };
  forecast: { status: Availability; last_completed_at: string | null };
}

export interface CurrentConditions {
  status: "available";
  pm25: {
    value_ug_m3: number;
    unit: string;
    observed_at: string;
    received_at: string;
  };
  source: { provider: string; location_name: string };
}

export interface ForecastItem {
  horizon_hours: 1 | 6 | 24;
  target_at: string;
  predicted_value_ug_m3: number;
  lower_bound_ug_m3: number;
  upper_bound_ug_m3: number;
  explanation?: ForecastExplanation | null;
}

export interface ForecastExplanationFactor {
  key: string;
  label: string;
  contribution_ug_m3: number;
  direction: "increased" | "decreased" | "neutral";
  absolute_share_percent: number;
  rank: number | null;
  is_top_3: boolean;
  used_by_model: boolean;
}

export interface ForecastExplanation {
  factors: ForecastExplanationFactor[];
  notice: string;
}

export interface LatestForecasts {
  status: "available";
  issued_at: string;
  model_version: string;
  forecasts: ForecastItem[];
}

export interface ForecastHistory {
  status: "available";
  hours: number;
  observations: Array<{ observed_at: string; value_ug_m3: number; unit: string }>;
  forecasts: Array<ForecastItem & { issued_at: string }>;
}

export interface ActivityPlanWindow {
  start_at: string;
  end_at: string;
  mean_predicted_value_ug_m3: number;
  mean_upper_bound_ug_m3: number;
  comparative_score: number;
  rationale: string;
}

export interface ActivityPlan {
  status: "available";
  date: string;
  duration_minutes: number;
  windows: ActivityPlanWindow[];
  disclaimer: string;
}

export interface AlertPreference {
  status: "configured" | "not_configured";
  browser_id: string;
  threshold_ug_m3: number | null;
  enabled: boolean;
  updated_at: string | null;
}

export interface ApiUnavailable {
  status: "unavailable";
  message: string;
  code: string;
}
