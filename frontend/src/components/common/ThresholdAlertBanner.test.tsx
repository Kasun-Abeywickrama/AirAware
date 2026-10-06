import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import { ThresholdAlertBanner } from "./ThresholdAlertBanner";
import type { AlertPreference } from "../../api/types";

function renderBanner(currentPm25: number, preference?: AlertPreference | null) {
  return render(
    <MemoryRouter>
      <ThresholdAlertBanner currentPm25={currentPm25} preference={preference} />
    </MemoryRouter>
  );
}

describe("ThresholdAlertBanner", () => {
  afterEach(() => {
    cleanup();
  });

  it("does not render when preference is undefined or null", () => {
    const { container } = renderBanner(80, null);
    expect(container.firstChild).toBeNull();
  });

  it("does not render when preference is disabled", () => {
    const pref: AlertPreference = {
      status: "configured",
      browser_id: "test-id",
      threshold_ug_m3: 50,
      enabled: false,
      updated_at: "2026-03-30T10:00:00Z",
    };
    const { container } = renderBanner(80, pref);
    expect(container.firstChild).toBeNull();
  });

  it("does not render when threshold_ug_m3 is null", () => {
    const pref: AlertPreference = {
      status: "not_configured",
      browser_id: "test-id",
      threshold_ug_m3: null,
      enabled: true,
      updated_at: null,
    };
    const { container } = renderBanner(80, pref);
    expect(container.firstChild).toBeNull();
  });

  it("does not render when current PM2.5 is less than or equal to threshold", () => {
    const pref: AlertPreference = {
      status: "configured",
      browser_id: "test-id",
      threshold_ug_m3: 55,
      enabled: true,
      updated_at: "2026-03-30T10:00:00Z",
    };
    const { container } = renderBanner(55, pref);
    expect(container.firstChild).toBeNull();

    cleanup();
    const { container: containerLower } = renderBanner(42, pref);
    expect(containerLower.firstChild).toBeNull();
  });

  it("renders active alert when current PM2.5 exceeds threshold", () => {
    const pref: AlertPreference = {
      status: "configured",
      browser_id: "test-id",
      threshold_ug_m3: 50,
      enabled: true,
      updated_at: "2026-03-30T10:00:00Z",
    };
    renderBanner(75.4, pref);

    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText("Air Quality Alert")).toBeTruthy();
    expect(screen.getByText("Current PM2.5 exceeds your personal alert limit")).toBeTruthy();
    expect(screen.getByText("+25.4 µg/m³ higher")).toBeTruthy();
    expect(screen.getByText("Adjust Alert Threshold")).toBeTruthy();
  });

  it("dismisses the banner when close button or dismiss action is clicked", () => {
    const pref: AlertPreference = {
      status: "configured",
      browser_id: "test-id",
      threshold_ug_m3: 35,
      enabled: true,
      updated_at: "2026-03-30T10:00:00Z",
    };
    renderBanner(60, pref);

    expect(screen.getByRole("alert")).toBeTruthy();

    const dismissButton = screen.getByLabelText("Dismiss alert for now");
    fireEvent.click(dismissButton);

    expect(screen.queryByRole("alert")).toBeNull();
  });
});
