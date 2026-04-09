"use strict";

const crypto = require("crypto");
const { getDb } = require("./db");

async function seedScenarioFixtures() {
  const db = getDb();

  const fixtureClientIds = [
    "C-FIX-RENEWAL",
    "C-FIX-TAX",
    "C-FIX-CAMPAIGN",
    "C-FIX-COMPLAINT"
  ];

  await db.collection("clients").deleteMany({ id: { $in: fixtureClientIds } });
  await db.collection("profiles").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("insurance_policies").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("insurance_renewals").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("tax_planning_checkpoints").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("tasks").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("communications").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("anniversary_triggers").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("addresses").deleteMany({ client_id: { $in: fixtureClientIds } });
  await db.collection("recommendations").deleteMany({ client_id: { $in: fixtureClientIds } });

  const nowIso = new Date().toISOString();

  const clients = [
    {
      id: "C-FIX-RENEWAL",
      first_name: "Harper",
      last_name: "Davis",
      date_of_birth: "1986-03-12",
      address: "40 Collins St, Melbourne VIC 3000",
      communication_preference: "email",
      fixture_cohort: "renewal_30_day",
      created_at: nowIso,
      updated_at: nowIso
    },
    {
      id: "C-FIX-TAX",
      first_name: "Ethan",
      last_name: "Lopez",
      date_of_birth: "1981-11-21",
      address: "88 George St, Sydney NSW 2000",
      communication_preference: "phone",
      fixture_cohort: "tax_one_month",
      created_at: nowIso,
      updated_at: nowIso
    },
    {
      id: "C-FIX-CAMPAIGN",
      first_name: "Sofia",
      last_name: "Khan",
      date_of_birth: "1990-07-05",
      address: "22 Queen St, Brisbane QLD 4000",
      communication_preference: "sms",
      fixture_cohort: "campaign_opt_in",
      created_at: nowIso,
      updated_at: nowIso
    },
    {
      id: "C-FIX-COMPLAINT",
      first_name: "Liam",
      last_name: "Turner",
      date_of_birth: "1978-02-10",
      address: "10 King St, Perth WA 6000",
      communication_preference: "email",
      fixture_cohort: "complaint_holdout",
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  const profiles = [
    { id: crypto.randomUUID(), client_id: "C-FIX-RENEWAL", communication_consent: true, social_opt_in: true, created_at: nowIso, updated_at: nowIso },
    { id: crypto.randomUUID(), client_id: "C-FIX-TAX", communication_consent: true, social_opt_in: false, created_at: nowIso, updated_at: nowIso },
    { id: crypto.randomUUID(), client_id: "C-FIX-CAMPAIGN", communication_consent: true, social_opt_in: true, created_at: nowIso, updated_at: nowIso },
    { id: crypto.randomUUID(), client_id: "C-FIX-COMPLAINT", communication_consent: true, social_opt_in: true, created_at: nowIso, updated_at: nowIso }
  ];

  const insurancePolicies = [
    {
      id: "POL-FIX-1",
      client_id: "C-FIX-RENEWAL",
      insurance_type: "household",
      insurer: "Acme Insurance",
      premium_annual: 2100,
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  const in30Days = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const in31Days = new Date(Date.now() + 31 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

  const renewals = [
    {
      id: crypto.randomUUID(),
      client_id: "C-FIX-RENEWAL",
      policy_id: "POL-FIX-1",
      renewal_date: in30Days,
      status: "upcoming",
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  const taxCheckpoints = [
    {
      id: crypto.randomUUID(),
      client_id: "C-FIX-TAX",
      checkpoint_type: "one_month_pre_tax",
      checkpoint_date: in31Days,
      status: "pending",
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  const tasks = [
    {
      id: crypto.randomUUID(),
      client_id: "C-FIX-COMPLAINT",
      task_type: "complaint_resolution",
      status: "in_progress",
      notes: "Do not send promotional outreach until resolved",
      created_at: nowIso,
      updated_at: nowIso
    },
    {
      id: crypto.randomUUID(),
      client_id: "C-FIX-CAMPAIGN",
      task_type: "social_personalized_outreach",
      status: "pending",
      segment_id: "SEG-OPT-IN-A",
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  const comms = [
    {
      id: crypto.randomUUID(),
      client_id: "C-FIX-COMPLAINT",
      channel: "email",
      outcome: "complaint_logged",
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  const anniversaries = [
    {
      id: crypto.randomUUID(),
      client_id: "C-FIX-RENEWAL",
      trigger_type: "policy_anniversary",
      trigger_date: in30Days,
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  const fixtureAddresses = clients.map((c) => ({
    id: `ADDR-${c.id}`,
    client_id: c.id,
    line1: c.address.split(",")[0]?.trim() || "1 Demo St",
    suburb: c.address.includes("Melbourne")
      ? "Melbourne"
      : c.address.includes("Sydney")
        ? "Sydney"
        : c.address.includes("Brisbane")
          ? "Brisbane"
          : "Perth",
    state: c.address.includes("VIC") ? "VIC" : c.address.includes("NSW") ? "NSW" : c.address.includes("QLD") ? "QLD" : "WA",
    postcode: c.address.match(/\d{4}/)?.[0] || "3000",
    country: "AU",
    created_at: nowIso,
    updated_at: nowIso
  }));

  const fixtureRecommendations = [
    {
      id: "REC-FIX-RENEWAL",
      client_id: "C-FIX-RENEWAL",
      title: "Bundle renewal outreach with household review",
      rationale: "cross_product_demo",
      products_touched: ["insurance", "investment"],
      status: "presented",
      created_at: nowIso,
      updated_at: nowIso
    },
    {
      id: "REC-FIX-TAX",
      client_id: "C-FIX-TAX",
      title: "Tax-window super and savings coordination",
      rationale: "cross_product_demo",
      products_touched: ["super", "savings"],
      status: "draft",
      created_at: nowIso,
      updated_at: nowIso
    }
  ];

  await db.collection("clients").insertMany(clients);
  await db.collection("profiles").insertMany(profiles);
  await db.collection("insurance_policies").insertMany(insurancePolicies);
  await db.collection("insurance_renewals").insertMany(renewals);
  await db.collection("tax_planning_checkpoints").insertMany(taxCheckpoints);
  await db.collection("tasks").insertMany(tasks);
  await db.collection("communications").insertMany(comms);
  await db.collection("anniversary_triggers").insertMany(anniversaries);
  await db.collection("addresses").insertMany(fixtureAddresses);
  await db.collection("recommendations").insertMany(fixtureRecommendations);

  const summary = {
    fixture_clients: clients.length,
    renewal_fixture: "C-FIX-RENEWAL",
    tax_fixture: "C-FIX-TAX",
    campaign_fixture: "C-FIX-CAMPAIGN",
    complaint_fixture: "C-FIX-COMPLAINT"
  };

  await db.collection("admin_jobs").insertOne({
    id: crypto.randomUUID(),
    job_type: "seed_demo_fixtures",
    status: "completed",
    created_at: nowIso,
    details: summary
  });

  await db.collection("audit_events").insertOne({
    id: crypto.randomUUID(),
    event_type: "fixtures_seeded",
    created_at: nowIso,
    payload: summary
  });

  return summary;
}

module.exports = { seedScenarioFixtures };
