import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MethodologyPage } from "./MethodologyPage";

describe("MethodologyPage", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders page title and 2024 EPA breakpoints table", () => {
    render(<MethodologyPage />);

    expect(
      screen.getByRole("heading", {
        name: "US EPA Air Quality Index (AQI) Calculation & Standards",
      })
    ).toBeTruthy();

    expect(screen.getByText("Official 2024 US EPA PM2.5 AQI Breakpoints Table")).toBeTruthy();
    expect(screen.getByText("0–9.0 µg/m³")).toBeTruthy();
    expect(screen.getByText("9.1–35.4 µg/m³")).toBeTruthy();
    expect(screen.getByText("35.5–55.4 µg/m³")).toBeTruthy();
    expect(screen.getByText("55.5–125.4 µg/m³")).toBeTruthy();
    expect(screen.getByText("125.5–225.4 µg/m³")).toBeTruthy();
    expect(screen.getByText("≥ 225.5 µg/m³")).toBeTruthy();
  });

  it("calculates AQI dynamically in the interactive calculator", () => {
    render(<MethodologyPage />);

    const input = screen.getByLabelText("Enter PM2.5 concentration:");
    expect(input).toBeTruthy();

    // Default 30.0 should yield AQI 90 and Moderate
    expect(screen.getAllByText("90").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Moderate").length).toBeGreaterThan(0);

    // Change to 9.0 (Good upper bound)
    fireEvent.change(input, { target: { value: "9.0" } });
    expect(screen.getAllByText("50").length).toBeGreaterThan(0);

    // Change to 100.0 (Unhealthy)
    fireEvent.change(input, { target: { value: "100.0" } });
    expect(screen.getAllByText("182").length).toBeGreaterThan(0);
  });

  it("renders authoritative references with external links", () => {
    render(<MethodologyPage />);

    expect(screen.getByText("References & Technical Citations")).toBeTruthy();
    expect(
      screen.getByText("U.S. EPA PM NAAQS Air Quality Index Fact Sheet (2024 Revision)")
    ).toBeTruthy();
    expect(
      screen.getByText("Technical Assistance Document for the Reporting of Daily Air Quality (AQI)")
    ).toBeTruthy();
    expect(
      screen.getByText("IQAir 2024 U.S. EPA Air Quality Index Implementation")
    ).toBeTruthy();
  });
});
