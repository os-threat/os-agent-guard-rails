const state = {
  options: null,
  enrollments: [],
  /** @type {{ enrollments: Array<Record<string, unknown>>, blocksTrialRelatedRx: boolean } | null} */
  rxTrialGuard: null,
};

async function api(path, init) {
  const res = await fetch(path, init);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.error || body.detail || `Request failed: ${res.status}`);
  }
  return body;
}

function selectValues(selectEl) {
  return Array.from(selectEl.selectedOptions).map((o) => o.value);
}

function fillSelect(el, items, valueKey, labelFn, allowBlank = false) {
  el.innerHTML = "";
  if (allowBlank) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "(none)";
    el.appendChild(opt);
  }
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = String(item[valueKey]);
    opt.textContent = labelFn(item);
    el.appendChild(opt);
  }
}

function switchTab(tabId) {
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".panel");
  tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === tabId));
  panels.forEach((p) => p.classList.toggle("active", p.id === tabId));
}

function wireTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });
}

function findPatientId(firstName, lastName) {
  if (!state.options?.patients) return null;
  const p = state.options.patients.find((x) => x.first_name === firstName && x.last_name === lastName);
  return p ? p.id : null;
}

function findEnrollmentForPatient(firstName, lastName) {
  return state.enrollments.find((e) => e.first_name === firstName && e.last_name === lastName);
}

function firstPhysicianLicense() {
  const d = state.options?.doctors?.find((x) => x.role === "physician" || x.role === "investigator");
  return d?.license_id || state.options?.doctors?.[0]?.license_id || "";
}

function pickBetaLactamMedication() {
  const meds = state.options?.medications || [];
  return (
    meds.find((m) => /penicillin/i.test(m.name)) ||
    meds.find((m) => /amoxicillin/i.test(m.name)) ||
    meds[0]
  );
}

function pickNonPenicillinMedication() {
  const meds = state.options?.medications || [];
  const bad = (m) => /penicillin|amoxicillin|clavul/i.test(m.name);
  return meds.find((m) => !bad(m)) || meds[0];
}

/**
 * @type {Record<string, { tab: string, hint: string, apply: () => Promise<void> | void }>}
 */
const DEMO_SCENARIOS = {
  M1: {
    tab: "prescription-form",
    hint: "M1: Safe outpatient path — Jordan Hayes, non–β-lactam med, not trial-related. Guard focus: MED-R01/R02 if you pick a conflicting med.",
    apply: async () => {
      const id = findPatientId("Jordan", "Hayes");
      if (!id) throw new Error("Seed patient Jordan Hayes not found");
      document.getElementById("rxPatient").value = String(id);
      document.getElementById("rxTrialRelated").checked = false;
      await refreshRxTrialGuard();
      document.getElementById("rxPrescriber").value = firstPhysicianLicense();
      const med = pickNonPenicillinMedication();
      if (med) document.getElementById("rxMedication").value = String(med.id);
      document.getElementById("rxDose").value = "10mg";
      document.getElementById("rxFrequency").value = "daily";
      updateRxSubmitState();
    },
  },
  M2: {
    tab: "prescription-form",
    hint: "M2: Allergy DENY — Riley Chen with verified penicillin allergy; pick a β-lactam med for MED-R01 demo.",
    apply: async () => {
      const id = findPatientId("Riley", "Chen");
      if (!id) throw new Error("Seed patient Riley Chen not found");
      document.getElementById("rxPatient").value = String(id);
      document.getElementById("rxTrialRelated").checked = false;
      await refreshRxTrialGuard();
      document.getElementById("rxPrescriber").value = firstPhysicianLicense();
      const med = pickBetaLactamMedication();
      if (med) document.getElementById("rxMedication").value = String(med.id);
      document.getElementById("rxDose").value = "500mg";
      document.getElementById("rxFrequency").value = "tid";
      updateRxSubmitState();
    },
  },
  M3: {
    tab: "prescription-form",
    hint: "M3: Trial concomitant — Sam Okonkwo. Check trial allowed list in patient detail; choose a med NOT on allowed list + mark trial-related.",
    apply: async () => {
      const id = findPatientId("Sam", "Okonkwo");
      if (!id) throw new Error("Seed patient Sam Okonkwo not found");
      document.getElementById("rxPatient").value = String(id);
      document.getElementById("rxTrialRelated").checked = true;
      await refreshRxTrialGuard();
      document.getElementById("rxPrescriber").value = firstPhysicianLicense();
      const meds = state.options?.medications || [];
      document.getElementById("rxMedication").value = String(meds[0]?.id || "");
      updateRxSubmitState();
    },
  },
  M4: {
    tab: "patients",
    hint: "M4: Open severe AE — search Avery Morrison; timeline shows G3+ open AE blocking new rx per MED-R04.",
    apply: async () => {
      document.getElementById("patientSearch").value = "Avery Morrison";
      await loadPatients("Avery Morrison");
    },
  },
  M5: {
    tab: "prescription-form",
    hint: "M5: Pending review gate — Nico Harper: trial-related rx is blocked until review approved (MED-R06). Approve pending review on Enrollment Review tab.",
    apply: async () => {
      const id = findPatientId("Nico", "Harper");
      if (!id) throw new Error("Seed patient Nico Harper not found");
      document.getElementById("rxPatient").value = String(id);
      document.getElementById("rxTrialRelated").checked = true;
      await refreshRxTrialGuard();
      document.getElementById("rxPrescriber").value = firstPhysicianLicense();
      const med = pickNonPenicillinMedication();
      if (med) document.getElementById("rxMedication").value = String(med.id);
      updateRxSubmitState();
    },
  },
  M6: {
    tab: "adverse-event-form",
    hint: "M6: Reporter vs prescriber junction — Lake Kim; link AE to enrollment and pick a reporter not on enrollment prescriber list for MED-R08.",
    apply: async () => {
      const id = findPatientId("Lake", "Kim");
      if (!id) throw new Error("Seed patient Lake Kim not found");
      document.getElementById("aePatient").value = String(id);
      const en = findEnrollmentForPatient("Lake", "Kim");
      const sel = document.getElementById("aeEnrollment");
      if (en) sel.value = String(en.id);
      document.getElementById("aeReporter").value = firstPhysicianLicense();
      document.getElementById("aeType").value = "AE-R";
      document.getElementById("aeSeverity").value = "3";
    },
  },
};

function wireScenarioButtons() {
  document.querySelectorAll("[data-scenario]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const key = btn.getAttribute("data-scenario");
      const scenario = DEMO_SCENARIOS[key];
      const hintEl = document.getElementById("scenarioHint");
      if (!scenario) return;
      try {
        switchTab(scenario.tab);
        await scenario.apply();
        hintEl.textContent = scenario.hint;
      } catch (err) {
        hintEl.textContent = String(err);
      }
    });
  });
}

async function refreshRxTrialGuard() {
  const banner = document.getElementById("rxTrialGuardBanner");
  const patientId = document.getElementById("rxPatient").value;
  if (!patientId) {
    state.rxTrialGuard = null;
    banner.className = "banner";
    banner.textContent = "Select a patient to evaluate trial enrollment and review status.";
    updateRxSubmitState();
    return;
  }
  try {
    const data = await api(`/patients/${patientId}/trial-guard`);
    state.rxTrialGuard = data;
    if (!data.enrollments?.length) {
      banner.className = "banner";
      banner.textContent = "No active or screening trial enrollment for this patient.";
      updateRxSubmitState();
      return;
    }
    const pending = data.enrollments.filter((x) => x.hasPendingReview);
    if (pending.length) {
      banner.className = "banner block";
      banner.textContent = `MED-R06 gate: ${pending.length} enrollment(s) have PENDING review. Trial-related prescribing is blocked until committee approval.`;
    } else {
      const parts = data.enrollments.map(
        (e) => `${e.trialId} (review: ${e.latestReviewStatus})`
      );
      banner.className = "banner warn";
      banner.textContent = `Active trial enrollment(s): ${parts.join("; ")}. If prescribing is trial-related, ensure prescriber is on enrollment (MED-R12).`;
    }
  } catch (err) {
    banner.className = "banner block";
    banner.textContent = `Could not load trial guard: ${err}`;
    state.rxTrialGuard = null;
  }
  updateRxSubmitState();
}

function updateRxSubmitState() {
  const trialRelated = document.getElementById("rxTrialRelated").checked;
  const blocked = Boolean(trialRelated && state.rxTrialGuard?.blocksTrialRelatedRx);
  document.getElementById("rxSubmitBtn").disabled = blocked;
}

async function loadDashboard() {
  const dash = await api("/dashboard");
  document.getElementById("activeTrials").textContent = String(dash.activeTrials);
  document.getElementById("openAes").textContent = String(dash.openAdverseEvents);
  document.getElementById("pendingReviews").textContent = String(dash.pendingReviews);
}

async function loadPatients(search = "") {
  const rows = await api(`/patients?search=${encodeURIComponent(search)}`);
  const list = document.getElementById("patientList");
  list.innerHTML = "";
  rows.forEach((p) => {
    const li = document.createElement("li");
    li.textContent = `${p.last_name}, ${p.first_name} (${p.patient_id})`;
    li.style.cursor = "pointer";
    li.addEventListener("click", async () => {
      const detail = await api(`/patients/${p.id}`);
      document.getElementById("patientDetail").textContent = JSON.stringify(detail, null, 2);
    });
    list.appendChild(li);
  });
}

async function loadTrials() {
  const rows = await api("/trials");
  const list = document.getElementById("trialList");
  list.innerHTML = "";
  rows.forEach((t) => {
    const li = document.createElement("li");
    li.style.cursor = "pointer";
    li.textContent = `${t.trial_id} - ${t.title} (${t.enrollment_count} enrollments)`;
    li.addEventListener("click", async () => {
      const detail = await api(`/trials/${t.id}`);
      document.getElementById("trialDetail").textContent = JSON.stringify(detail, null, 2);
    });
    list.appendChild(li);
  });
}

async function loadOptionsAndForms() {
  state.options = await api("/options");
  state.enrollments = await api("/enrollments");

  const patientLabel = (p) => `${p.last_name}, ${p.first_name} (${p.patient_id})`;
  fillSelect(document.getElementById("enrollPatient"), state.options.patients, "id", patientLabel);
  fillSelect(document.getElementById("rxPatient"), state.options.patients, "id", patientLabel);
  fillSelect(document.getElementById("aePatient"), state.options.patients, "id", patientLabel);

  fillSelect(
    document.getElementById("enrollTrial"),
    state.options.trials,
    "id",
    (t) => `${t.trial_id} - ${t.title}`
  );
  fillSelect(
    document.getElementById("enrollSite"),
    state.options.hospitals,
    "id",
    (h) => `${h.hospital_id} - ${h.name}`
  );
  fillSelect(
    document.getElementById("rxSite"),
    state.options.hospitals,
    "id",
    (h) => `${h.hospital_id} - ${h.name}`
  );

  fillSelect(
    document.getElementById("enrollPrescribers"),
    state.options.doctors,
    "license_id",
    (d) => `${d.license_id} - ${d.last_name}, ${d.first_name} [${d.role}]`
  );
  fillSelect(
    document.getElementById("rxPrescriber"),
    state.options.doctors,
    "license_id",
    (d) => `${d.license_id} - ${d.last_name}, ${d.first_name} [${d.role}]`
  );
  fillSelect(
    document.getElementById("aeReporter"),
    state.options.doctors,
    "license_id",
    (d) => `${d.license_id} - ${d.last_name}, ${d.first_name} [${d.role}]`
  );
  fillSelect(
    document.getElementById("reviewer"),
    state.options.doctors,
    "license_id",
    (d) => `${d.license_id} - ${d.last_name}, ${d.first_name} [${d.role}]`
  );

  fillSelect(
    document.getElementById("enrollMeds"),
    state.options.medications,
    "id",
    (m) => `${m.drug_code} - ${m.name}`
  );
  fillSelect(
    document.getElementById("rxMedication"),
    state.options.medications,
    "id",
    (m) => `${m.drug_code} - ${m.name}`
  );

  fillSelect(
    document.getElementById("aeEnrollment"),
    state.enrollments,
    "id",
    (e) => `${e.enrollment_id} - ${e.last_name}, ${e.first_name}`,
    true
  );
  fillSelect(
    document.getElementById("reviewEnrollment"),
    state.enrollments,
    "id",
    (e) => `${e.enrollment_id} - ${e.last_name}, ${e.first_name}`
  );

  await refreshRxTrialGuard();
}

function wireForms() {
  document.getElementById("enrollmentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const prescribers = selectValues(document.getElementById("enrollPrescribers"));
      const meds = selectValues(document.getElementById("enrollMeds")).map(Number);
      if (prescribers.length < 1) {
        document.getElementById("enrollmentResult").textContent = "Select at least one prescriber.";
        return;
      }
      if (meds.length < 1) {
        document.getElementById("enrollmentResult").textContent = "Select at least one trial medication.";
        return;
      }
      const payload = {
        patientId: Number(document.getElementById("enrollPatient").value),
        trialId: Number(document.getElementById("enrollTrial").value),
        siteId: Number(document.getElementById("enrollSite").value),
        prescriberLicenses: prescribers,
        medicationIds: meds,
      };
      const out = await api("/enrollments", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      document.getElementById("enrollmentResult").textContent = JSON.stringify(out, null, 2);
      await loadDashboard();
      await loadOptionsAndForms();
      await loadPendingReviews();
    } catch (err) {
      document.getElementById("enrollmentResult").textContent = String(err);
    }
  });

  document.getElementById("rxPatient").addEventListener("change", () => {
    refreshRxTrialGuard();
  });
  document.getElementById("rxTrialRelated").addEventListener("change", () => {
    updateRxSubmitState();
  });

  document.getElementById("prescriptionForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const trialRelated = document.getElementById("rxTrialRelated").checked;
    if (trialRelated && state.rxTrialGuard?.blocksTrialRelatedRx) {
      document.getElementById("rxResult").textContent =
        "Blocked: trial-related prescribing requires no pending enrollment review (MED-R06). Approve on Enrollment Review tab first.";
      return;
    }
    try {
      const out = await api("/prescriptions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          patientId: Number(document.getElementById("rxPatient").value),
          prescriberLicense: document.getElementById("rxPrescriber").value,
          hospitalId: Number(document.getElementById("rxSite").value),
          medicationId: Number(document.getElementById("rxMedication").value),
          dose: document.getElementById("rxDose").value,
          frequency: document.getElementById("rxFrequency").value,
          route: "oral",
          status: "active",
          isTrialRelated: trialRelated,
        }),
      });
      document.getElementById("rxResult").textContent = JSON.stringify(out, null, 2);
      await loadDashboard();
    } catch (err) {
      document.getElementById("rxResult").textContent = String(err);
    }
  });

  document.getElementById("aeForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const sev = Number(document.getElementById("aeSeverity").value);
      if (sev < 1 || sev > 5) {
        document.getElementById("aeResult").textContent = "Severity must be 1–5.";
        return;
      }
      const enrollmentValue = document.getElementById("aeEnrollment").value;
      const out = await api("/adverse-events", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          patientId: Number(document.getElementById("aePatient").value),
          eventTypeCode: document.getElementById("aeType").value,
          reportingPhysicianLicense: document.getElementById("aeReporter").value,
          enrollmentId: enrollmentValue ? Number(enrollmentValue) : null,
          severity: sev,
          status: "open",
          details: "Created from UI form",
        }),
      });
      document.getElementById("aeResult").textContent = JSON.stringify(out, null, 2);
      await loadDashboard();
    } catch (err) {
      document.getElementById("aeResult").textContent = String(err);
    }
  });

  document.getElementById("reviewForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const out = await api("/enrollment-reviews", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          enrollmentId: Number(document.getElementById("reviewEnrollment").value),
          reviewerLicense: document.getElementById("reviewer").value,
          approvalStatus: document.getElementById("reviewStatus").value,
          reviewNotes: "Created from UI form",
        }),
      });
      document.getElementById("reviewResult").textContent = JSON.stringify(out, null, 2);
      await loadDashboard();
      await loadPendingReviews();
      await refreshRxTrialGuard();
    } catch (err) {
      document.getElementById("reviewResult").textContent = String(err);
    }
  });

  document.getElementById("reseedBtn").addEventListener("click", async () => {
    try {
      const out = await api("/admin/reseed", { method: "POST" });
      document.getElementById("adminResult").textContent = JSON.stringify(out, null, 2);
      await Promise.all([loadDashboard(), loadPatients(), loadTrials(), loadOptionsAndForms(), loadPendingReviews()]);
    } catch (err) {
      document.getElementById("adminResult").textContent = String(err);
    }
  });
}

async function loadPendingReviews() {
  const rows = await api("/enrollment-reviews?status=pending");
  const list = document.getElementById("pendingReviewList");
  list.innerHTML = "";
  rows.forEach((r) => {
    const li = document.createElement("li");
    const head = document.createElement("div");
    head.textContent = `${r.id} | ${r.first_name} ${r.last_name} | ${r.trial_id} | ${r.enrollment_code || r.enrollment_pk} | ${r.approval_status}`;
    li.appendChild(head);
    const actions = document.createElement("div");
    actions.className = "review-actions";
    const approve = document.createElement("button");
    approve.type = "button";
    approve.textContent = "Approve";
    approve.addEventListener("click", async () => {
      try {
        await api(`/enrollment-reviews/${r.id}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ approvalStatus: "approved", reviewNotes: "Approved from UI pending list" }),
        });
        await loadDashboard();
        await loadPendingReviews();
        await refreshRxTrialGuard();
      } catch (err) {
        document.getElementById("reviewResult").textContent = String(err);
      }
    });
    const reject = document.createElement("button");
    reject.type = "button";
    reject.textContent = "Reject";
    reject.className = "danger";
    reject.addEventListener("click", async () => {
      try {
        await api(`/enrollment-reviews/${r.id}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ approvalStatus: "rejected", reviewNotes: "Rejected from UI pending list" }),
        });
        await loadDashboard();
        await loadPendingReviews();
        await refreshRxTrialGuard();
      } catch (err) {
        document.getElementById("reviewResult").textContent = String(err);
      }
    });
    actions.appendChild(approve);
    actions.appendChild(reject);
    li.appendChild(actions);
    list.appendChild(li);
  });
}

function wireSearch() {
  document.getElementById("patientSearchBtn").addEventListener("click", async () => {
    await loadPatients(document.getElementById("patientSearch").value);
  });
}

async function init() {
  wireTabs();
  wireScenarioButtons();
  wireSearch();
  wireForms();
  await Promise.all([loadDashboard(), loadPatients(), loadTrials(), loadOptionsAndForms(), loadPendingReviews()]);
}

init().catch((err) => {
  console.error(err);
});
