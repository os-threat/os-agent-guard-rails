"use strict";

const crypto = require("crypto");

function problem(res, status, title, detail, extra = {}) {
  const trace_id = crypto.randomUUID();
  const body = {
    type: "about:blank",
    title,
    status,
    detail: detail ?? title,
    trace_id,
    ...extra,
  };
  res.type("application/problem+json");
  res.status(status).json(body);
  return body;
}

module.exports = { problem };
