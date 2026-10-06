import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AppFooter } from "./AppFooter";

describe("AppFooter", () => {
  it("renders branding, station info, and feature links correctly", () => {
    render(
      <BrowserRouter>
        <AppFooter />
      </BrowserRouter>
    );

    // Brand and location
    expect(screen.getByAltText("AirAware")).toBeTruthy();
    expect(screen.getByText(/New Delhi · OpenAQ & NASA POWER/)).toBeTruthy();

    // Feature navigation links
    expect(screen.getByRole("link", { name: /Live Dashboard/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Forecast & History/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Activity Planner/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Alert Preferences/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Research Methodology/i })).toBeTruthy();

    // Standards and specs
    expect(screen.getByText(/US EPA 2024 PM2.5 Breakpoints/i)).toBeTruthy();
    expect(screen.getByText(/WHO 2021 Air Quality Target/i)).toBeTruthy();
    expect(screen.getByText(/Split-Conformal Prediction/i)).toBeTruthy();
    expect(screen.getByText(/TreeSHAP/i)).toBeTruthy();
    expect(screen.getByText(/Models: GRU & XGBoost\+GRU/i)).toBeTruthy();

    // Legal and research author attribution
    expect(screen.getByText(/A\.H\.K\. Thiwanka/i)).toBeTruthy();
  });
});
