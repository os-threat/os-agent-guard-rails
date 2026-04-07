"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const rules = require("../mock/lib/rules.js");

describe("FP-R02 dominant vs risk tier", () => {
  it("denies equity dominant for conservative", () => {
    assert.equal(rules.dominantAllowedForRisk("conservative", "equity"), false);
    assert.equal(rules.dominantAllowedForRisk("conservative", "fixed_income"), true);
  });
  it("allows equity for aggressive", () => {
    assert.equal(rules.dominantAllowedForRisk("aggressive", "equity"), true);
  });
});

describe("evaluateRecommendation", () => {
  const baseClient = { kyc_tier: "accredited", risk_tier: "moderate" };
  const diversified = [
    { symbol: "S1", market_value_usd: 3000, sector: "Technology" },
    { symbol: "S2", market_value_usd: 3000, sector: "Health Care" },
    { symbol: "S3", market_value_usd: 3000, sector: "Financials" },
    { symbol: "S4", market_value_usd: 3000, sector: "Consumer" },
    { symbol: "S5", market_value_usd: 3000, sector: "Industrials" },
    { symbol: "S6", market_value_usd: 3000, sector: "Energy" },
    { symbol: "S7", market_value_usd: 3000, sector: "Materials" },
    { symbol: "S8", market_value_usd: 3000, sector: "Utilities" },
    { symbol: "S9", market_value_usd: 3000, sector: "Real Estate" },
    { symbol: "S10", market_value_usd: 3000, sector: "Communication" },
  ];

  it("ALLOW for diversified moderate client", () => {
    const r = rules.evaluateRecommendation({
      client: baseClient,
      holdingsForAccounts: diversified,
      goals: [],
      body: {
        proposed_symbol: "S1",
        dominant_asset_class: "equity",
        instrument_requires_accredited: false,
        long_duration_only_stance: false,
        horizon_years: 15,
      },
    });
    assert.equal(r.guard_status, "ALLOW");
  });

  it("DENY FP-R03 retail + accredited instrument", () => {
    const r = rules.evaluateRecommendation({
      client: { kyc_tier: "retail", risk_tier: "moderate" },
      holdingsForAccounts: diversified,
      goals: [],
      body: {
        proposed_symbol: "REGD",
        dominant_asset_class: "equity",
        instrument_requires_accredited: true,
        long_duration_only_stance: false,
        horizon_years: 10,
      },
    });
    assert.equal(r.guard_status, "DENY");
    assert.equal(r.rule_id, "FP-R03");
  });

  it("DENY FP-R01 high concentration", () => {
    const concentrated = [
      { symbol: "AAPL", market_value_usd: 120000, sector: "Technology" },
      { symbol: "CASH", market_value_usd: 30000, sector: "Cash" },
    ];
    const r = rules.evaluateRecommendation({
      client: baseClient,
      holdingsForAccounts: concentrated,
      goals: [],
      body: {
        proposed_symbol: "AAPL",
        dominant_asset_class: "equity",
        instrument_requires_accredited: false,
        long_duration_only_stance: false,
        horizon_years: 10,
      },
    });
    assert.equal(r.guard_status, "DENY");
    assert.equal(r.rule_id, "FP-R01");
  });
});
