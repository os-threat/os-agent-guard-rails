"use strict";

const crypto = require("crypto");

function sendProblem(res, status, title, detail) {
  res.status(status).type("application/problem+json").json({
    type: "about:blank",
    title,
    status,
    detail,
    trace_id: crypto.randomUUID()
  });
}

module.exports = { sendProblem };
