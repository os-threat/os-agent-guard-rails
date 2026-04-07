"use strict";

/**
 * Pure rule helpers for FP-R01–FP-R12 (mini-app enforcement + unit tests).
 * Thresholds match plan/financial_planner_api_scenario/SCENARIO.md.
 */

const KYC_RANK = { retail: 0, accredited: 1, qualified: 2 };

const DAILY_TRADE_CAP = 20;
const WASH_SALE_DAYS = 30;
const FEE_DISCLOSURE_WINDOW_DAYS = 90;
const CONCENTRATION_PCT = 0.15;
const SECTOR_PCT_MODERATE = 0.4;
const NEAR_GOAL_YEARS = 5;

function kycMeets(required, actual) {
  return KYC_RANK[actual] >= KYC_RANK[required];
}

/** FP-R02: dominant asset class vs risk tier (see openapi appendix). */
function dominantAllowedForRisk(riskTier, dominant) {
  if (riskTier === "aggressive") return true;
  if (riskTier === "conservative") {
    return ["fixed_income", "short_duration", "cash"].includes(dominant);
  }
  if (riskTier === "moderate") {
    return ["equity", "fixed_income", "alternatives", "short_duration", "cash"].includes(dominant);
  }
  return false;
}

/** Max single-equity % of account value from holdings. */
function maxSingleEquityShare(holdings) {
  const bySymbol = new Map();
  let total = 0;
  for (const h of holdings) {
    const mv = Number(h.market_value_usd) || 0;
    total += mv;
    bySymbol.set(h.symbol, (bySymbol.get(h.symbol) || 0) + mv);
  }
  if (total <= 0) return { maxPct: 0, symbol: null, bySymbol };
  let maxPct = 0;
  let symbol = null;
  for (const [sym, val] of bySymbol) {
    const p = val / total;
    if (p > maxPct) {
      maxPct = p;
      symbol = sym;
    }
  }
  return { maxPct, symbol, bySymbol, total };
}

/** Max sector % of account value. */
function maxSectorShare(holdings) {
  const bySector = new Map();
  let total = 0;
  for (const h of holdings) {
    const mv = Number(h.market_value_usd) || 0;
    total += mv;
    const s = h.sector || "Unknown";
    bySector.set(s, (bySector.get(s) || 0) + mv);
  }
  if (total <= 0) return { maxPct: 0, sector: null };
  let maxPct = 0;
  let sector = null;
  for (const [sec, val] of bySector) {
    const p = val / total;
    if (p > maxPct) {
      maxPct = p;
      sector = sec;
    }
  }
  return { maxPct, sector };
}

/**
 * Simulate adding a small notional to proposed_symbol for concentration checks.
 * Uses 5% of account total as hypothetical add to proposed symbol.
 */
function projectedMaxSingleEquity(holdings, proposedSymbol) {
  const { maxPct, symbol, bySymbol, total } = maxSingleEquityShare(holdings);
  if (total <= 0) return { maxPct: 0, symbol: null };
  const add = total * 0.05;
  const newTotal = total + add;
  const newSymVal = (bySymbol.get(proposedSymbol) || 0) + add;
  const projected = newSymVal / newTotal;
  const others = [...bySymbol.entries()]
    .filter(([s]) => s !== proposedSymbol)
    .map(([, v]) => v / newTotal);
  const maxOther = others.length ? Math.max(...others) : 0;
  const newMax = Math.max(projected, maxOther);
  return { maxPct: newMax, symbol: projected >= maxOther ? proposedSymbol : symbol };
}

function projectedMaxSector(holdings, proposedSymbol, proposedSector) {
  const bySector = new Map();
  let total = 0;
  for (const h of holdings) {
    const mv = Number(h.market_value_usd) || 0;
    total += mv;
    const s = h.sector || "Unknown";
    bySector.set(s, (bySector.get(s) || 0) + mv);
  }
  const add = total > 0 ? total * 0.05 : 1;
  const newTotal = total + add;
  const targetSector =
    proposedSector ||
    holdings.find((h) => h.symbol === proposedSymbol)?.sector ||
    "Unknown";
  bySector.set(targetSector, (bySector.get(targetSector) || 0) + add);
  let maxP = 0;
  let maxS = null;
  for (const [s, v] of bySector) {
    const p = v / newTotal;
    if (p > maxP) {
      maxP = p;
      maxS = s;
    }
  }
  return { maxPct: maxP, sector: maxS };
}

function hasGoalWithinYears(goals, years) {
  const now = new Date();
  const cutoff = new Date(now);
  cutoff.setFullYear(cutoff.getFullYear() + years);
  return goals.some((g) => {
    const d = new Date(g.target_date);
    return d <= cutoff;
  });
}

/**
 * @param {object} input
 * @param {object} input.client
 * @param {object[]} input.holdingsForAccounts - all holdings across client's accounts
 * @param {object[]} input.goals
 * @param {object} input.body - RecommendationRequest
 */
function evaluateRecommendation(input) {
  const { client, holdingsForAccounts, goals, body } = input;
  const risk = client.risk_tier;
  const kyc = client.kyc_tier;

  if (body.instrument_requires_accredited && !kycMeets("accredited", kyc)) {
    return {
      guard_status: "DENY",
      rule_id: "FP-R03",
      witness: { kyc_tier: kyc, required: "accredited" },
    };
  }

  if (!dominantAllowedForRisk(risk, body.dominant_asset_class)) {
    return {
      guard_status: "DENY",
      rule_id: "FP-R02",
      witness: { risk_tier: risk, dominant_asset_class: body.dominant_asset_class },
    };
  }

  if (hasGoalWithinYears(goals, NEAR_GOAL_YEARS) && body.long_duration_only_stance) {
    return {
      guard_status: "DENY",
      rule_id: "FP-R09",
      witness: { horizon: "within_5y", stance: "long_duration_only" },
    };
  }

  if (risk === "moderate" || risk === "conservative") {
    const proj = projectedMaxSingleEquity(holdingsForAccounts, body.proposed_symbol);
    if (proj.maxPct > CONCENTRATION_PCT) {
      return {
        guard_status: "DENY",
        rule_id: "FP-R01",
        witness: {
          max_single_equity_pct: Number((proj.maxPct * 100).toFixed(2)),
          symbol: proj.symbol,
          threshold_pct: CONCENTRATION_PCT * 100,
        },
      };
    }
  }

  if (risk === "moderate") {
    const sectorTag = body.proposed_sector || holdingsForAccounts.find((h) => h.symbol === body.proposed_symbol)?.sector;
    const sec = projectedMaxSector(holdingsForAccounts, body.proposed_symbol, sectorTag);
    if (sec.maxPct > SECTOR_PCT_MODERATE) {
      return {
        guard_status: "DENY",
        rule_id: "FP-R12",
        witness: {
          max_sector_pct: Number((sec.maxPct * 100).toFixed(2)),
          sector: sec.sector,
          threshold_pct: SECTOR_PCT_MODERATE * 100,
        },
      };
    }
  }

  return { guard_status: "ALLOW" };
}

function accountFlagsForSymbol(holdings, accountId, symbol) {
  const h = holdings.find((x) => x.account_id === accountId && x.symbol === symbol);
  return new Set(h?.flags || []);
}

function daysBetween(a, b) {
  return Math.abs(a - b) / (1000 * 60 * 60 * 24);
}

module.exports = {
  evaluateRecommendation,
  dominantAllowedForRisk,
  maxSingleEquityShare,
  maxSectorShare,
  projectedMaxSingleEquity,
  KYC_RANK,
  DAILY_TRADE_CAP,
  WASH_SALE_DAYS,
  FEE_DISCLOSURE_WINDOW_DAYS,
  CONCENTRATION_PCT,
  SECTOR_PCT_MODERATE,
  NEAR_GOAL_YEARS,
  accountFlagsForSymbol,
  daysBetween,
};
