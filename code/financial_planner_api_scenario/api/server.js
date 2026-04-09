"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const express = require("express");
const cors = require("cors");
const yaml = require("js-yaml");
const swaggerUi = require("swagger-ui-express");
const { config } = require("./src/config");
const { initDb } = require("./src/services/db");
const { sendProblem } = require("./src/problem");
const { coreRouter } = require("./src/routes/core");
const { productsRouter } = require("./src/routes/products");
const { workflowsRouter } = require("./src/routes/workflows");
const { adminRouter } = require("./src/routes/admin");

const app = express();
const PORT = config.apiPort;

function resolveOpenApiPath() {
  if (process.env.OPENAPI_PATH && fs.existsSync(process.env.OPENAPI_PATH)) {
    return process.env.OPENAPI_PATH;
  }
  const fallback = path.join(__dirname, "..", "openapi", "financial-services.yaml");
  if (fs.existsSync(fallback)) return fallback;
  return null;
}

let openapiSpec = null;
const openApiPath = resolveOpenApiPath();
if (openApiPath) {
  try {
    openapiSpec = yaml.load(fs.readFileSync(openApiPath, "utf8"));
    console.log(`OpenAPI loaded from ${openApiPath}`);
  } catch (e) {
    console.warn("Failed to parse OpenAPI:", e.message);
  }
} else {
  console.warn("OpenAPI file not found; /docs will be unavailable.");
}

app.use(cors());
app.use(express.json());
app.use((req, res, next) => {
  const correlationId = req.header("x-correlation-id") || crypto.randomUUID();
  req.correlationId = correlationId;
  res.setHeader("x-correlation-id", correlationId);

  const originalJson = res.json.bind(res);
  res.json = (body) => {
    if (body && typeof body === "object" && !Array.isArray(body)) {
      return originalJson({
        ...body,
        _meta: {
          correlation_id: correlationId
        }
      });
    }
    return originalJson(body);
  };
  next();
});

app.get("/", (_req, res) => {
  res.json({
    app: "financial-services-mini-app",
    version: "0.2",
    message: "Financial services v2 API (OpenAPI: openapi/financial-services.yaml).",
    docs: {
      swagger_ui: openapiSpec ? "/docs/" : null,
      openapi_json: openapiSpec ? "/openapi.json" : null,
      health: "/admin/health",
      integration_contract: "/admin/integration-contract",
      openapi_file: openApiPath || "openapi/financial-services.yaml"
    },
    env: config.env
  });
});

if (openapiSpec) {
  app.use("/docs", swaggerUi.serve, swaggerUi.setup(openapiSpec, { customSiteTitle: "Financial Services API" }));
  app.get("/openapi.json", (_req, res) => {
    res.type("application/json").send(JSON.stringify(openapiSpec));
  });
}

app.use(coreRouter);
app.use(productsRouter);
app.use(workflowsRouter);
app.use(adminRouter);

app.use((err, _req, res, _next) => {
  console.error(err);
  sendProblem(res, 500, "Internal Server Error", err.message || "Unexpected error");
});

async function start() {
  await initDb();
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`financial-services-api listening on port ${PORT}`);
  });
}

start().catch((err) => {
  console.error(err);
  process.exit(1);
});
