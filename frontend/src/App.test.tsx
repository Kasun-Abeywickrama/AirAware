import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>
  );
}

describe("dashboard and routing", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.history.pushState({}, "", "/");
  });

  afterEach(() => {
    cleanup();
  });

  it("shows loading placeholders while data is being fetched", () => {
    const pending = new Promise<never>(() => undefined);
    mockedApi.status.mockReturnValue(pending);
    mockedApi.currentConditions.mockReturnValue(pending);
    mockedApi.latestForecasts.mockReturnValue(pending);
    mockedApi.forecastHistory.mockReturnValue(pending);

    renderApp();

    expect(screen.getByLabelText("Loading current PM2.5")).toBeTruthy();
    expect(screen.getByLabelText("Loading PM2.5 trend")).toBeTruthy();
  });

  it("keeps the dashboard informative when every data request is unavailable", async () => {
    const unavailable = Promise.reject(new Error("Data is temporarily unavailable."));
    mockedApi.status.mockReturnValue(unavailable);
    mockedApi.currentConditions.mockReturnValue(unavailable);
    mockedApi.latestForecasts.mockReturnValue(unavailable);
    mockedApi.forecastHistory.mockReturnValue(unavailable);

    renderApp();

    expect(await screen.findByText("Current PM2.5 is unavailable")).toBeTruthy();
    expect(screen.getByText("Forecasts are unavailable")).toBeTruthy();
    expect(screen.getByText("Chart data is unavailable")).toBeTruthy();
  });

  it("renders clean path-based navigation links without hash symbols", () => {
    const pending = new Promise<never>(() => undefined);
    mockedApi.status.mockReturnValue(pending);
    mockedApi.currentConditions.mockReturnValue(pending);
    mockedApi.latestForecasts.mockReturnValue(pending);
    mockedApi.forecastHistory.mockReturnValue(pending);

    renderApp();

    const dashboardLink = screen.getByRole("link", { name: "Dashboard" });
    const forecastLink = screen.getByRole("link", { name: "Forecast" });
    const plannerLink = screen.getByRole("link", { name: "Planner" });
    const alertsLink = screen.getByRole("link", { name: "Alerts" });
    const methodologyLink = screen.getByRole("link", { name: "Methodology" });

    expect(dashboardLink.getAttribute("href")).toBe("/");
    expect(forecastLink.getAttribute("href")).toBe("/forecast");
    expect(plannerLink.getAttribute("href")).toBe("/planner");
    expect(alertsLink.getAttribute("href")).toBe("/alerts");
    expect(methodologyLink.getAttribute("href")).toBe("/methodology");
  });

  it("navigates cleanly when clicking navigation links", () => {
    const pending = new Promise<never>(() => undefined);
    mockedApi.status.mockReturnValue(pending);
    mockedApi.currentConditions.mockReturnValue(pending);
    mockedApi.latestForecasts.mockReturnValue(pending);
    mockedApi.forecastHistory.mockReturnValue(pending);

    renderApp();

    const methodologyLink = screen.getByRole("link", { name: "Methodology" });
    fireEvent.click(methodologyLink);

    expect(window.location.pathname).toBe("/methodology");
  });
});
