"use strict";

const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../../.env") });

function asNumber(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

const config = {
  env: process.env.NODE_ENV || "development",
  apiPort: asNumber(process.env.API_PORT, 8082),
  webPort: asNumber(process.env.WEB_PORT, 8083),
  mongoPort: asNumber(process.env.MONGO_PORT, 27017),
  mongodbUri: process.env.MONGODB_URI || "mongodb://mongo:27017/financial_services"
};

module.exports = { config };
