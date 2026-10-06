import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ActivityPlannerPage, newDelhiDate } from "./ActivityPlannerPage";
import { api } from "../../api/client";
import type { ActivityPlan } from "../../api/types";

vi.mock("../../api/client", () => ({
  api: {
    activityPlan: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

const mockPlan: ActivityPlan = {
  status: "available",
  date: "2026-10-06",
  duration_minutes: 60,
  windows: [
    {
      start_at: "2026-10-06T06:00:00+05:30",
      end_at: "2026-10-06T07:00:00+05:30",
      mean_predicted_value_ug_m3: 32.5,
      mean_upper_bound_ug_m3: 45.0,
      comparative_score: 45.0,
      rationale: "Ranked by lowest mean upper forecast bound.",
    },
    {
      start_at: "2026-10-06T07:00:00+05:30",
      end_at: "2026-10-06T08:00:00+05:30",
      mean_predicted_value_ug_m3: 65.0,
      mean_upper_bound_ug_m3: 80.0,
      comparative_score: 80.0,
      rationale: "Ranked by lowest mean upper forecast bound.",
    },
  ],
  disclaimer: "Forecasts are indicative and subject to atmospheric changes.",
};

function renderPlanner() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ActivityPlannerPage />
    </QueryClientProvider>
  );
}

describe("ActivityPlannerPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("calculates New Delhi dates with correct offset", () => {
    const today = newDelhiDate(0);
    const tomorrow = newDelhiDate(1);
    expect(today).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(tomorrow).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(today).not.toEqual(tomorrow);
  });

  it("renders with min and max date set to today and tomorrow", () => {
    mockedApi.activityPlan.mockResolvedValue(mockPlan);
    renderPlanner();

    const dateInput = screen.getByLabelText(/^Date/);
    expect(dateInput.getAttribute("min")).toEqual(newDelhiDate(0));
    expect(dateInput.getAttribute("max")).toEqual(newDelhiDate(1));
  });

  it("automatically loads the activity plan on mount and displays AQI badges", async () => {
    mockedApi.activityPlan.mockResolvedValue(mockPlan);
    renderPlanner();

    expect(screen.getByText("Finding optimal outdoor windows…")).toBeTruthy();

    await waitFor(() => {
      expect(mockedApi.activityPlan).toHaveBeenCalledWith(newDelhiDate(0), 60);
    });

    expect(await screen.findByText("Moderate")).toBeTruthy();
    expect(screen.getByText("Unhealthy")).toBeTruthy();
    expect(screen.getByText("Option 1")).toBeTruthy();
  });

  it("switches date when Tomorrow quick button is clicked", async () => {
    mockedApi.activityPlan.mockResolvedValue(mockPlan);
    renderPlanner();

    const tomorrowBtn = screen.getByRole("button", { name: "Tomorrow" });
    fireEvent.click(tomorrowBtn);

    await waitFor(() => {
      expect(mockedApi.activityPlan).toHaveBeenCalledWith(newDelhiDate(1), 60);
    });
  });

  it("displays unavailable panel when no plan is available", async () => {
    mockedApi.activityPlan.mockRejectedValue(new Error("No complete forecast window is available for this date."));
    renderPlanner();

    expect(await screen.findByText("No complete plan is available")).toBeTruthy();
    expect(screen.getByText("No complete forecast window is available for this date.")).toBeTruthy();
  });
});
