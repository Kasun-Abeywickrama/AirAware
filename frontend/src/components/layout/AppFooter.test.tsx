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
    expect(screen.getByText(/New Delhi, India/)).toBeTruthy();

    // Feature navigation links
    expect(screen.getByRole("link", { name: /Live Dashboard/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Forecast & History/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Activity Planner/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Alert Preferences/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Research Methodology/i })).toBeTruthy();

    // Standards and specs
    expect(screen.getByText(/US EPA AQI Standard/i)).toBeTruthy();
    expect(screen.getByText(/WHO Air Quality Guidelines/i)).toBeTruthy();
    expect(screen.getByText(/LightGBM, XGBoost & CatBoost/i)).toBeTruthy();

    // Legal and disclaimer
    expect(screen.getByText(/AirAware\. Developed for air quality intelligence/i)).toBeTruthy();
  });
});
