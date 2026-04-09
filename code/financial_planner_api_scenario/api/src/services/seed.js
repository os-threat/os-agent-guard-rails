"use strict";

const crypto = require("crypto");
const { getDb } = require("./db");

const FIRST_NAMES = [
  "Ava", "Noah", "Mia", "Liam", "Sophia", "Ethan", "Isla", "Lucas", "Chloe", "Mason",
  "Grace", "Elijah", "Zoe", "Oliver", "Ruby", "James", "Amelia", "Henry", "Ella", "Jack"
];
const LAST_NAMES = [
  "Nguyen", "Patel", "Smith", "Johnson", "Chen", "Taylor", "Brown", "Williams", "Singh", "Martin",
  "Wilson", "Anderson", "Thompson", "Moore", "Thomas", "Khan", "White", "Lee", "Walker", "Clark"
];
const STREETS = [
  "King St", "George St", "Collins St", "Queen St", "Oxford St", "High St", "Station Rd", "Bridge Rd"
];
const SUBURBS = [
  "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Hobart", "Newcastle"
];
const STATES = ["NSW", "VIC", "QLD", "WA", "SA", "ACT", "TAS"];
const COMM_PREFS = ["email", "sms", "phone"];
const INS_TYPES = ["general", "household", "death_life", "business"];
const DATE_TYPES = ["birthday", "review_anniversary", "policy_anniversary", "tax_planning_window"];

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pick(arr) {
  return arr[randomInt(0, arr.length - 1)];
}

function isoDate(y, m, d) {
  return new Date(Date.UTC(y, m - 1, d)).toISOString().slice(0, 10);
}

function futureDate(days) {
  const dt = new Date(Date.now() + days * 24 * 60 * 60 * 1000);
  return dt.toISOString().slice(0, 10);
}

function makeAddress(i) {
  return `${10 + (i % 190)} ${pick(STREETS)}, ${pick(SUBURBS)} ${pick(STATES)} ${2000 + (i % 799)}`;
}

async function generateRichDataset() {
  const db = getDb();

  const collections = [
    "clients",
    "households",
    "profiles",
    "important_dates",
    "addresses",
    "recommendations",
    "investment_accounts",
    "investment_holdings",
    "savings_accounts",
    "super_accounts",
    "super_contributions",
    "super_beneficiaries",
    "insurance_policies",
    "insurance_coverages",
    "insurance_renewals",
    "insurance_claims",
    "tasks",
    "communications",
    "campaigns",
    "anniversary_triggers",
    "tax_planning_checkpoints",
    "admin_jobs",
    "audit_events"
  ];

  for (const c of collections) {
    await db.collection(c).deleteMany({});
  }

  const clients = [];
  const households = [];
  const profiles = [];
  const importantDates = [];
  const addresses = [];
  const recommendations = [];
  const investmentAccounts = [];
  const investmentHoldings = [];
  const savingsAccounts = [];
  const superAccounts = [];
  const superContributions = [];
  const superBeneficiaries = [];
  const insurancePolicies = [];
  const insuranceCoverages = [];
  const insuranceRenewals = [];
  const insuranceClaims = [];
  const tasks = [];
  const communications = [];
  const campaigns = [];
  const anniversaryTriggers = [];
  const taxCheckpoints = [];

  const clientCount = 420;
  const householdCount = 190;

  for (let i = 0; i < householdCount; i++) {
    households.push({
      id: `HH-${i + 1}`,
      household_name: `Household ${i + 1}`,
      primary_client_id: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
  }

  for (let i = 0; i < clientCount; i++) {
    const id = `C-${i + 1}`;
    const hh = households[i % households.length];
    if (!hh.primary_client_id) hh.primary_client_id = id;
    const first = pick(FIRST_NAMES);
    const last = pick(LAST_NAMES);
    const dobYear = randomInt(1958, 2001);
    const dobMonth = randomInt(1, 12);
    const dobDay = randomInt(1, 28);

    clients.push({
      id,
      first_name: first,
      last_name: last,
      date_of_birth: isoDate(dobYear, dobMonth, dobDay),
      address: makeAddress(i),
      communication_preference: pick(COMM_PREFS),
      household_id: hh.id,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    addresses.push({
      id: `ADDR-${id}`,
      client_id: id,
      line1: `${10 + (i % 190)} ${pick(STREETS)}`,
      suburb: pick(SUBURBS),
      state: pick(STATES),
      postcode: String(2000 + (i % 799)),
      country: "AU",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    profiles.push({
      id: `P-${id}`,
      client_id: id,
      risk_tier: pick(["conservative", "balanced", "growth"]),
      communication_consent: Math.random() > 0.15,
      social_opt_in: Math.random() > 0.35,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    for (const dt of DATE_TYPES) {
      importantDates.push({
        id: crypto.randomUUID(),
        client_id: id,
        date_type: dt,
        date_value: futureDate(randomInt(1, 365)),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }

    const invId = `INV-${id}`;
    investmentAccounts.push({
      id: invId,
      client_id: id,
      product_name: pick(["Core Growth", "Balanced Income", "Sustainable Mix"]),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    for (let h = 0; h < 3; h++) {
      investmentHoldings.push({
        id: crypto.randomUUID(),
        client_id: id,
        investment_account_id: invId,
        symbol: pick(["VTI", "BND", "VEU", "VAS", "VGS", "IEM"]),
        allocation_pct: randomInt(10, 60),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }

    savingsAccounts.push({
      id: `SAV-${id}`,
      client_id: id,
      goal_name: pick(["Emergency Fund", "Holiday", "Home Deposit"]),
      target_amount: randomInt(8000, 70000),
      current_amount: randomInt(1000, 60000),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    const superId = `SUP-${id}`;
    superAccounts.push({
      id: superId,
      client_id: id,
      fund_name: pick(["Future Super", "Secure Retirement", "Balanced Super"]),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    superContributions.push({
      id: crypto.randomUUID(),
      client_id: id,
      super_account_id: superId,
      annual_amount: randomInt(6000, 32000),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    superBeneficiaries.push({
      id: crypto.randomUUID(),
      client_id: id,
      super_account_id: superId,
      beneficiary_name: `${pick(FIRST_NAMES)} ${pick(LAST_NAMES)}`,
      beneficiary_pct: randomInt(25, 100),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    const policyCount = randomInt(1, 3);
    for (let p = 0; p < policyCount; p++) {
      const policyId = `POL-${id}-${p + 1}`;
      const insType = pick(INS_TYPES);
      insurancePolicies.push({
        id: policyId,
        client_id: id,
        insurance_type: insType,
        insurer: pick(["Acme Insurance", "Harbor Cover", "Summit Mutual"]),
        premium_annual: randomInt(500, 12000),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
      insuranceCoverages.push({
        id: crypto.randomUUID(),
        client_id: id,
        policy_id: policyId,
        coverage_name: `${insType}_core`,
        sum_insured: randomInt(20000, 900000),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
      insuranceRenewals.push({
        id: crypto.randomUUID(),
        client_id: id,
        policy_id: policyId,
        renewal_date: futureDate(randomInt(15, 360)),
        status: pick(["upcoming", "quoted", "completed"]),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
      if (Math.random() > 0.8) {
        insuranceClaims.push({
          id: crypto.randomUUID(),
          client_id: id,
          policy_id: policyId,
          claim_status: pick(["lodged", "under_review", "paid"]),
          claim_amount: randomInt(500, 50000),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
      }
    }

    // communications and tasks richness
    for (let c = 0; c < 6; c++) {
      communications.push({
        id: crypto.randomUUID(),
        client_id: id,
        channel: pick(["email", "sms", "phone"]),
        outcome: pick(["sent", "opened", "replied", "no_answer"]),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }
    for (let t = 0; t < 4; t++) {
      tasks.push({
        id: crypto.randomUUID(),
        client_id: id,
        task_type: pick(["review_call", "renewal_outreach", "tax_prep", "beneficiary_check"]),
        status: pick(["pending", "in_progress", "done"]),
        due_date: futureDate(randomInt(3, 90)),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }
    anniversaryTriggers.push({
      id: crypto.randomUUID(),
      client_id: id,
      trigger_type: pick(["policy_anniversary", "birthday", "review_anniversary"]),
      trigger_date: futureDate(randomInt(5, 330)),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    taxCheckpoints.push({
      id: crypto.randomUUID(),
      client_id: id,
      checkpoint_type: "one_month_pre_tax",
      checkpoint_date: futureDate(randomInt(20, 110)),
      status: pick(["pending", "contacted", "completed"]),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    if (Math.random() > 0.25) {
      recommendations.push({
        id: crypto.randomUUID(),
        client_id: id,
        title: pick([
          "Rebalance growth tilt",
          "Super co-contribution window",
          "Insurance gap vs household debt",
          "Tax-loss harvesting review",
          "Consolidate duplicate super accounts"
        ]),
        rationale: "cross_product_suitability",
        products_touched: pick([
          ["investment", "super"],
          ["insurance", "savings"],
          ["super", "insurance"],
          ["investment", "insurance", "super"]
        ]),
        status: pick(["draft", "presented", "accepted", "deferred"]),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }
  }

  for (let k = 0; k < 25; k++) {
    campaigns.push({
      id: `CAM-${k + 1}`,
      campaign_name: pick(["Spring Insurance Review", "Tax Prep Outreach", "Super Health Check"]),
      segment_id: `SEG-${(k % 8) + 1}`,
      channel: pick(["email", "sms", "social"]),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
  }

  await db.collection("households").insertMany(households);
  await db.collection("clients").insertMany(clients);
  await db.collection("profiles").insertMany(profiles);
  await db.collection("important_dates").insertMany(importantDates);
  await db.collection("addresses").insertMany(addresses);
  if (recommendations.length) await db.collection("recommendations").insertMany(recommendations);
  await db.collection("investment_accounts").insertMany(investmentAccounts);
  await db.collection("investment_holdings").insertMany(investmentHoldings);
  await db.collection("savings_accounts").insertMany(savingsAccounts);
  await db.collection("super_accounts").insertMany(superAccounts);
  await db.collection("super_contributions").insertMany(superContributions);
  await db.collection("super_beneficiaries").insertMany(superBeneficiaries);
  await db.collection("insurance_policies").insertMany(insurancePolicies);
  await db.collection("insurance_coverages").insertMany(insuranceCoverages);
  await db.collection("insurance_renewals").insertMany(insuranceRenewals);
  if (insuranceClaims.length) await db.collection("insurance_claims").insertMany(insuranceClaims);
  await db.collection("tasks").insertMany(tasks);
  await db.collection("communications").insertMany(communications);
  await db.collection("campaigns").insertMany(campaigns);
  await db.collection("anniversary_triggers").insertMany(anniversaryTriggers);
  await db.collection("tax_planning_checkpoints").insertMany(taxCheckpoints);

  const job = {
    id: crypto.randomUUID(),
    job_type: "seed_rich_dataset",
    status: "completed",
    created_at: new Date().toISOString(),
    details: {
      clients: clients.length,
      households: households.length,
      tasks: tasks.length,
      communications: communications.length,
      policies: insurancePolicies.length
    }
  };
  await db.collection("admin_jobs").insertOne(job);
  await db.collection("audit_events").insertOne({
    id: crypto.randomUUID(),
    event_type: "seed_completed",
    created_at: new Date().toISOString(),
    payload: job.details
  });

  return job.details;
}

module.exports = { generateRichDataset };
