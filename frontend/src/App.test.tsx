import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { api } from "./api/client";

vi.mock("./api/client", () => ({
  api: {
    status: vi.fn(),
    currentConditions: vi.fn(),
    latestForecasts: vi.fn(),
    forecastHistory: vi.fn(),
    activityPlan: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

function renderDashboard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><App /></QueryClientProvider>);
}

describe("dashboard data states", () => {
  beforeEach(() => vi.resetAllMocks());

  it("shows loading placeholders while data is being fetched", () => {
    const pending = new Promise<never>(() => undefined);
    mockedApi.status.mockReturnValue(pending);
    mockedApi.currentConditions.mockReturnValue(pending);
    mockedApi.latestForecasts.mockReturnValue(pending);
    mockedApi.forecastHistory.mockReturnValue(pending);

    renderDashboard();

    expect(screen.getByLabelText("Loading current PM2.5")).toBeTruthy();
    expect(screen.getByLabelText("Loading PM2.5 trend")).toBeTruthy();
  });

  it("keeps the dashboard informative when every data request is unavailable", async () => {
    const unavailable = Promise.reject(new Error("Data is temporarily unavailable."));
    mockedApi.status.mockReturnValue(unavailable);
    mockedApi.currentConditions.mockReturnValue(unavailable);
    mockedApi.latestForecasts.mockReturnValue(unavailable);
    mockedApi.forecastHistory.mockReturnValue(unavailable);

    renderDashboard();

    expect(await screen.findByText("Current PM2.5 is unavailable")).toBeTruthy();
    expect(screen.getByText("Forecasts are unavailable")).toBeTruthy();
    expect(screen.getByText("Chart data is unavailable")).toBeTruthy();
  });
});
