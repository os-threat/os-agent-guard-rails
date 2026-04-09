const { Pool } = require("pg");

const connectionString =
  process.env.DATABASE_URL ||
  `postgresql://${process.env.POSTGRES_USER || "medical_app"}:${process.env.POSTGRES_PASSWORD || "medical_app_dev_pw"}@${process.env.POSTGRES_HOST || "localhost"}:${process.env.POSTGRES_PORT || "5433"}/${process.env.POSTGRES_DB || "medical_mini_app"}`;

const pool = new Pool({ connectionString });

async function query(text, params = []) {
  return pool.query(text, params);
}

async function withTransaction(work) {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const result = await work(client);
    await client.query("COMMIT");
    return result;
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

module.exports = {
  pool,
  query,
  withTransaction,
};
