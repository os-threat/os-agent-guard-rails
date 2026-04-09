"use strict";

const { MongoClient } = require("mongodb");
const { config } = require("../config");

let db;
let client;

async function initDb() {
  if (db) return db;
  client = new MongoClient(config.mongodbUri);
  await client.connect();
  db = client.db();
  return db;
}

function getDb() {
  if (!db) {
    throw new Error("Database is not initialized.");
  }
  return db;
}

module.exports = { initDb, getDb };
