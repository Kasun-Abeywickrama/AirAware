import { useState } from "react";
import {
  BookOpen,
  Calculator,
  CheckCircle2,
  ExternalLink,
  FileText,
  Info,
  Scale,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { calculateAqi, getAqiCategory, CATEGORIES, EPA_AQI_SCALE } from "../../utils/aqi";

const REFERENCES = [
  {
    title: "U.S. EPA PM NAAQS Air Quality Index Fact Sheet (2024 Revision)",
    source: "United States Environmental Protection Agency (U.S. EPA)",
    description:
      "Final Rule updating the primary annual PM2.5 NAAQS from 12.0 µg/m³ to 9.0 µg/m³ and adjusting official AQI breakpoints (effective May 6, 2024).",
    url: "https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf",
    tag: "Primary Standard",
  },
  {
    title: "Technical Assistance Document for the Reporting of Daily Air Quality (AQI)",
    source: "U.S. EPA / AirNow Program",
    description:
      "Official technical guidelines specifying the linear interpolation mathematical formula, rounding criteria, and concentration truncation rules.",
    url: "https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf",
    tag: "Mathematical Formula",
  },
  {
    title: "EPA Air Quality System (AQS) AQI Breakpoints Reference Table",
    source: "U.S. EPA Office of Air Quality Planning & Standards (OAQPS)",
    description:
      "Official database codetables mapping ambient pollutant concentration ranges to index categories and sub-index values.",
    url: "https://aqs.epa.gov/aqsweb/documents/codetables/aqi_breakpoints.html",
    tag: "Data Reference",
  },
  {
    title: "IQAir 2024 U.S. EPA Air Quality Index Implementation",
    source: "IQAir Knowledge Base",
    description:
      "Documentation of how the world's leading ambient air monitoring platform adopted the 2024 revised EPA breakpoints for global reporting.",
    url: "https://www.iqair.com/support/knowledge-base/iqair-implements-2024-update-to-u-s-epa-air-quality-index-aqi",
    tag: "Global Adoption",
  },
  {
    title: "WHO Global Air Quality Guidelines (2021)",
    source: "World Health Organization (WHO)",
    description:
      "Global health benchmark thresholds (24-hour limit of 15 µg/m³ and annual limit of 5 µg/m³) developed to protect public health from particulate exposure.",
    url: "https://www.who.int/publications/i/item/9789240034228",
    tag: "Health Context",
  },
];

export function MethodologyPage() {
  const [calculatorInput, setCalculatorInput] = useState<number>(30.0);

  const truncatedC = Math.max(0, Math.floor(calculatorInput * 10) / 10);
  const calculatedAqi = calculateAqi(calculatorInput);
  const aqiInfo = getAqiCategory(calculatorInput);

  // Find the active band for step-by-step breakdown
  const activeBand =
    truncatedC <= 9.0
      ? { cLow: 0.0, cHigh: 9.0, iLow: 0, iHigh: 50, cat: "Good" }
      : truncatedC <= 35.4
        ? { cLow: 9.1, cHigh: 35.4, iLow: 51, iHigh: 100, cat: "Moderate" }
        : truncatedC <= 55.4
          ? { cLow: 35.5, cHigh: 55.4, iLow: 101, iHigh: 150, cat: "Unhealthy for Sensitive Groups" }
          : truncatedC <= 125.4
            ? { cLow: 55.5, cHigh: 125.4, iLow: 151, iHigh: 200, cat: "Unhealthy" }
            : truncatedC <= 225.4
              ? { cLow: 125.5, cHigh: 225.4, iLow: 201, iHigh: 300, cat: "Very Unhealthy" }
              : truncatedC <= 325.4
                ? { cLow: 225.5, cHigh: 325.4, iLow: 301, iHigh: 400, cat: "Hazardous" }
                : { cLow: 325.5, cHigh: 500.4, iLow: 401, iHigh: 500, cat: "Hazardous" };

  const deltaI = activeBand.iHigh - activeBand.iLow;
  const deltaC = +(activeBand.cHigh - activeBand.cLow).toFixed(1);
  const deltaCurrent = +(truncatedC - activeBand.cLow).toFixed(1);
  const rawStep = (deltaI / deltaC) * deltaCurrent + activeBand.iLow;

  return (
    <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-12">
      {/* Header */}
      <section className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700 sm:text-sm">Standards & Methodology</p>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl lg:text-4xl">
          US EPA Air Quality Index (AQI) Calculation & Standards
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600 sm:mt-3 sm:text-base sm:leading-7">
          How AirAware calculates the official Air Quality Index (AQI) from ambient PM2.5 concentrations using the
          latest 2024 U.S. Environmental Protection Agency (EPA) NAAQS breakpoints and official linear interpolation.
        </p>
      </section>

      {/* Interactive Calculator Section */}
      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:mt-10 sm:p-8" aria-labelledby="calculator-heading">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="rounded-xl bg-teal-50 p-2 text-teal-700 sm:p-2.5">
            <Calculator className="size-5 sm:size-6" aria-hidden="true" />
          </div>
          <div>
            <h2 id="calculator-heading" className="text-lg font-bold text-slate-950 sm:text-xl">
              PM2.5 to AQI Calculator
            </h2>
            <p className="mt-0.5 text-xs text-slate-600 sm:text-sm">
              Input any PM2.5 concentration (µg/m³) to inspect the live linear interpolation calculation.
            </p>
          </div>
        </div>

        <div className="mt-5 sm:mt-6 grid gap-5 sm:gap-6 lg:grid-cols-2">
          {/* Input & Result display */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 sm:p-5">
            <label htmlFor="calc-pm25-input" className="block text-xs font-semibold text-slate-800 sm:text-sm">
              Enter PM2.5 concentration:
            </label>
            <div className="mt-2 flex items-center gap-3">
              <input
                id="calc-pm25-input"
                type="number"
                min="0"
                max="1000"
                step="0.1"
                value={calculatorInput}
                onChange={(e) => setCalculatorInput(e.target.valueAsNumber || 0)}
                className="w-36 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-lg font-bold text-slate-950 shadow-sm focus:border-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-100 sm:w-40 sm:px-4 sm:py-2.5 sm:text-xl"
              />
              <span className="text-sm font-semibold text-slate-600 sm:text-base">µg/m³</span>
            </div>

            {/* Quick value presets */}
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Presets:</span>
              {[9.0, 30.0, 50.0, 100.0, 180.0, 260.0].map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setCalculatorInput(preset)}
                  className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${calculatorInput === preset
                      ? "bg-teal-700 text-white"
                      : "bg-white text-slate-700 border border-slate-200 hover:border-teal-500"
                    }`}
                >
                  {preset.toFixed(1)} µg/m³
                </button>
              ))}
            </div>

            {/* Calculated Output Card */}
            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Calculated US EPA AQI</p>
                  <p className="mt-1 text-4xl font-extrabold text-slate-950">{calculatedAqi}</p>
                </div>
                <span
                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${aqiInfo.colors.badge} ${aqiInfo.colors.text}`}
                >
                  <span className={`size-2 rounded-full ${aqiInfo.colors.dot}`} aria-hidden="true" />
                  {aqiInfo.label}
                </span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-600 border-t border-slate-100 pt-3">
                <span className="font-semibold text-slate-900">Health Advisory: </span>
                {aqiInfo.guidance}
              </p>
            </div>
          </div>

          {/* Mathematical Step-by-Step Breakdown */}
          <div className="flex flex-col justify-between rounded-xl border border-teal-100 bg-teal-50/40 p-5">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-teal-800">Mathematical Steps</p>
              <h3 className="mt-1 text-base font-semibold text-slate-900">Linear Interpolation Breakdown</h3>

              <div className="mt-4 space-y-3 text-sm text-slate-700">
                <div className="rounded-lg bg-white p-3 shadow-2xs font-mono text-xs">
                  <span className="text-slate-500">// 1. EPA Truncation rule:</span>
                  <br />
                  C = Math.floor({calculatorInput} × 10) / 10 = <span className="font-bold text-teal-700">{truncatedC.toFixed(1)} µg/m³</span>
                </div>

                <div className="rounded-lg bg-white p-3 shadow-2xs text-xs space-y-1">
                  <span className="font-semibold text-slate-900">2. Selected Breakpoint Band:</span>
                  <p className="text-slate-600">
                    Category: <span className="font-bold text-slate-900">{activeBand.cat}</span>
                  </p>
                  <p className="font-mono text-slate-600">
                    C<sub>low</sub> = {activeBand.cLow.toFixed(1)}, C<sub>high</sub> = {activeBand.cHigh.toFixed(1)}
                  </p>
                  <p className="font-mono text-slate-600">
                    I<sub>low</sub> = {activeBand.iLow}, I<sub>high</sub> = {activeBand.iHigh}
                  </p>
                </div>

                <div className="rounded-lg bg-white p-3 shadow-2xs font-mono text-xs leading-relaxed">
                  <span className="text-slate-500">// 3. Evaluation:</span>
                  <br />
                  I = [({activeBand.iHigh} - {activeBand.iLow}) / ({activeBand.cHigh.toFixed(1)} - {activeBand.cLow.toFixed(1)})] × ({truncatedC.toFixed(1)} - {activeBand.cLow.toFixed(1)}) + {activeBand.iLow}
                  <br />
                  I = [{deltaI} / {deltaC}] × {deltaCurrent} + {activeBand.iLow}
                  <br />
                  I = {rawStep.toFixed(3)}
                  <br />
                  <span className="text-slate-500">// 4. Round to nearest integer:</span>
                  <br />
                  AQI = <span className="font-bold text-teal-700 text-sm">{calculatedAqi}</span>
                </div>
              </div>
            </div>

            <p className="mt-3 text-[11px] text-teal-900/80">
              * Matches EPA Technical Assistance Document (TAD) specifications.
            </p>
          </div>
        </div>
      </section>

      {/* 2024 Breakpoints Table Section */}
      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:mt-12 sm:p-8" aria-labelledby="table-heading">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="size-4.5 text-teal-700 sm:size-5" aria-hidden="true" />
              <h2 id="table-heading" className="text-lg font-bold text-slate-950 sm:text-xl">
                Official 2024 US EPA PM2.5 AQI Breakpoints Table
              </h2>
            </div>
            <p className="mt-0.5 text-xs text-slate-600 sm:mt-1 sm:text-sm">
              National Ambient Air Quality Standards (NAAQS) revised under 89 FR 16202 (Effective May 6, 2024).
            </p>
          </div>
          <span className="hidden sm:inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 border border-emerald-200">
            2024 NAAQS Standard
          </span>
        </div>

        <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full text-left text-sm">
            <caption className="sr-only">2024 US EPA PM2.5 AQI Breakpoints Table</caption>
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
              <tr>
                <th className="px-4 py-3.5 font-semibold">AQI Category</th>
                <th className="px-4 py-3.5 font-semibold">Index Range (AQI)</th>
                <th className="px-4 py-3.5 font-semibold">PM2.5 24-hr Concentration (µg/m³)</th>
                <th className="px-4 py-3.5 font-semibold">Health Statement & Sensitive Groups</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {EPA_AQI_SCALE.map(({ category, label, range, colors }) => {
                const info = CATEGORIES[category];
                return (
                  <tr key={category} className="hover:bg-slate-50/50 transition">
                    <td className="px-4 py-3.5 font-medium text-slate-900 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${colors.badge} ${colors.text}`}>
                        <span className={`size-1.5 rounded-full ${colors.dot}`} aria-hidden="true" />
                        {label}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 font-semibold text-slate-900 whitespace-nowrap">
                      {info.aqiRange}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-xs font-bold text-teal-800 whitespace-nowrap">
                      {range} µg/m³
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-600 leading-relaxed max-w-md">
                      {info.guidance}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* 2024 Revision Note */}
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50/60 p-4 text-xs leading-relaxed text-amber-950 flex items-start gap-3">
          <Info className="size-4 shrink-0 text-amber-700 mt-0.5" aria-hidden="true" />
          <div>
            <span className="font-bold">What changed in the 2024 EPA revision?</span>
            <p className="mt-0.5 text-amber-900">
              On February 7, 2024, the U.S. EPA strengthened the primary annual PM2.5 NAAQS standard from 12.0 µg/m³ to 9.0 µg/m³. Consequently, the <strong>Good</strong> breakpoint upper limit was tightened from 12.0 µg/m³ down to <strong>9.0 µg/m³</strong>, and upper boundaries across Unhealthy (now 125.4 µg/m³), Very Unhealthy (225.4 µg/m³), and Hazardous were updated to reflect modern epidemiological research on health risks.
            </p>
          </div>
        </div>
      </section>

      {/* The Formula & Truncation Rules Section */}
      <section className="mt-12 grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
          <div className="flex items-center gap-2.5">
            <Scale className="size-5 text-teal-700" aria-hidden="true" />
            <h2 className="text-lg font-bold text-slate-950">The Linear Interpolation Equation</h2>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            The EPA computes the Air Quality Index for any pollutant concentration using standard piecewise linear interpolation:
          </p>

          <div className="my-5 overflow-x-auto py-3">
            <div className="flex items-center justify-center gap-2 font-serif text-lg text-slate-900 sm:text-xl py-2">
              <span className="italic font-bold">I</span>
              <span className="font-sans font-normal text-slate-500">=</span>

              {/* Fraction: (I_high - I_low) / (C_high - C_low) */}
              <div className="inline-flex flex-col items-center px-1">
                <span className="border-b-2 border-slate-800 px-2 pb-1 text-center leading-tight">
                  <span className="italic">I</span>
                  <sub className="font-sans text-xs font-normal">high</sub>
                  <span className="mx-1.5 font-sans font-normal text-slate-500">−</span>
                  <span className="italic">I</span>
                  <sub className="font-sans text-xs font-normal">low</sub>
                </span>
                <span className="px-2 pt-1 text-center leading-tight">
                  <span className="italic">C</span>
                  <sub className="font-sans text-xs font-normal">high</sub>
                  <span className="mx-1.5 font-sans font-normal text-slate-500">−</span>
                  <span className="italic">C</span>
                  <sub className="font-sans text-xs font-normal">low</sub>
                </span>
              </div>

              {/* Multiplication: × (C - C_low) */}
              <span className="font-sans font-normal text-slate-500">×</span>
              <span className="font-sans text-xl sm:text-2xl text-slate-400 font-light">(</span>
              <span>
                <span className="italic">C</span>
                <span className="mx-1.5 font-sans font-normal text-slate-500">−</span>
                <span className="italic">C</span>
                <sub className="font-sans text-xs font-normal">low</sub>
              </span>
              <span className="font-sans text-xl sm:text-2xl text-slate-400 font-light">)</span>

              {/* Addition: + I_low */}
              <span className="mx-0.5 font-sans font-normal text-slate-500">+</span>
              <span>
                <span className="italic">I</span>
                <sub className="font-sans text-xs font-normal">low</sub>
              </span>
            </div>
          </div>

          <ul className="space-y-2 text-xs text-slate-600">
            <li className="flex items-start gap-2">
              <span className="font-bold text-teal-700 italic font-serif">I:</span>
              <span>The computed Air Quality Index (rounded to the nearest integer).</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold text-teal-700 italic font-serif">C:</span>
              <span>The measured or forecasted PM2.5 concentration, truncated to 1 decimal place.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold text-teal-700 font-serif">
                <span className="italic">C</span><sub>low</sub> / <span className="italic">C</span><sub>high</sub>:
              </span>
              <span>The lower and upper concentration breakpoints bounding concentration C.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold text-teal-700 font-serif">
                <span className="italic">I</span><sub>low</sub> / <span className="italic">I</span><sub>high</sub>:
              </span>
              <span>The corresponding lower and upper index breakpoints for that category.</span>
            </li>
          </ul>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
          <div className="flex items-center gap-2.5">
            <Sparkles className="size-5 text-teal-700" aria-hidden="true" />
            <h2 className="text-lg font-bold text-slate-950">Standards Comparison: EPA vs WHO vs India NAQI</h2>
          </div>
          <div className="mt-4 space-y-3.5 text-xs leading-relaxed text-slate-600">
            <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
              <span className="font-bold text-slate-900">1. US EPA AQI (AirAware’s Standard):</span>
              <p className="mt-1">
                Provides a standardized 0–500 numeric index with 6 color-coded health risk tiers. Adopted globally by consumer platforms (IQAir, AirNow) for international comparability and strict health protection.
              </p>
            </div>
            <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
              <span className="font-bold text-slate-900">2. WHO Air Quality Guidelines (AQG):</span>
              <p className="mt-1">
                The World Health Organization publishes health thresholds (24-hr limit: 15 µg/m³, annual: 5 µg/m³), but does <em>not</em> publish a 0–500 index or "Good/Moderate" category system.
              </p>
            </div>
            <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
              <span className="font-bold text-slate-900">3. India CPCB National AQI (NAQI):</span>
              <p className="mt-1">
                India’s domestic standard uses a 0–500 scale with wider bands (e.g. Good extends up to 30 µg/m³). AirAware uses the more stringent 2024 US EPA standard to adhere to global research benchmarks.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Official References & Citations */}
      <section className="mt-12 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8" aria-labelledby="references-heading">
        <div className="flex items-center gap-2.5">
          <BookOpen className="size-5 text-teal-700" aria-hidden="true" />
          <h2 id="references-heading" className="text-xl font-bold text-slate-950">
            References & Technical Citations
          </h2>
        </div>
        <p className="mt-1 text-sm text-slate-600">
          Direct links to authoritative regulatory documentation, scientific reports, and technical manuals.
        </p>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {REFERENCES.map((ref) => (
            <a
              key={ref.url}
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50/50 p-4 transition hover:border-teal-400 hover:bg-white hover:shadow-sm"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded bg-teal-100 px-2 py-0.5 text-[10px] font-bold text-teal-800">
                    {ref.tag}
                  </span>
                  <ExternalLink className="size-3.5 text-slate-400 group-hover:text-teal-700 transition" aria-hidden="true" />
                </div>
                <h3 className="mt-2 text-sm font-bold text-slate-900 group-hover:text-teal-800 transition">
                  {ref.title}
                </h3>
                <p className="mt-1 text-xs font-semibold text-teal-700">{ref.source}</p>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">{ref.description}</p>
              </div>
              <div className="mt-3 flex items-center gap-1 text-[11px] font-semibold text-teal-700">
                View official document &rarr;
              </div>
            </a>
          ))}
        </div>
      </section>
    </main>
  );
}
