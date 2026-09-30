import { describe, expect, it } from "vitest";
import { buildChartData } from "./AirQualityChart";
import type { ForecastHistory } from "../../api/types";

describe("buildChartData", () => {
  it("keeps observed values and forecast ranges in timestamp order", () => {
    const history: ForecastHistory = {
      status: "available",
      hours: 72,
      observations: [{ observed_at: "2026-09-28T01:00:00Z", value_ug_m3: 32, unit: "ug/m3" }],
      forecasts: [
        {
          issued_at: "2026-09-28T01:00:00Z",
          target_at: "2026-09-28T02:00:00Z",
          horizon_hours: 1,
          predicted_value_ug_m3: 35,
          lower_bound_ug_m3: 20,
          upper_bound_ug_m3: 50,
        },
      ],
    };
    expect(buildChartData(history)).toEqual([
      { timestamp: "2026-09-28T01:00:00Z", observation: 32 },
      { timestamp: "2026-09-28T02:00:00Z", forecast: 35, lower: 20, upper: 50 },
    ]);
  });
});
