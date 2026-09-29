import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./client";

describe("activity-plan API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends the selected date and whole-hour duration to the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      status: "available", date: "2026-09-29", duration_minutes: 120, windows: [], disclaimer: "Guidance only.",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);

    await api.activityPlan("2026-09-29", 120);

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/activity-plans", expect.objectContaining({
      method: "POST", body: JSON.stringify({ date: "2026-09-29", duration_minutes: 120 }),
    }));
  });

  it("saves an anonymous alert preference with a PUT request", async () => {
    const browserId = "4d4a76a3-7c68-46ee-93b0-5ac2e3ef0c1e";
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      status: "configured", browser_id: browserId, threshold_ug_m3: 70, enabled: true, updated_at: "2026-09-28T08:00:00Z",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);

    await api.saveAlertPreference(browserId, 70, true);

    expect(fetchMock).toHaveBeenCalledWith(`/api/v1/alert-preferences/${browserId}`, expect.objectContaining({
      method: "PUT", body: JSON.stringify({ threshold_ug_m3: 70, enabled: true }),
    }));
  });
});
