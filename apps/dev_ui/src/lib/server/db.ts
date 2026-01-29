import Database from "better-sqlite3";
import fs from "fs";
import path from "path";

export const DB_PATH = path.resolve(process.cwd(), "..", "..", "db", "bandabi.sqlite");

let _db: Database.Database | null = null;

export function db() {
  if (_db) return _db;

  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
  _db = new Database(DB_PATH);

  // schema (자동 생성)
  _db.exec(`
    CREATE TABLE IF NOT EXISTS experiments (
      exp_id TEXT PRIMARY KEY,
      created_at TEXT NOT NULL,
      scenario_name TEXT,
      sweep_param_path TEXT,
      notes TEXT
    );

    CREATE TABLE IF NOT EXISTS variants (
      variant_id TEXT NOT NULL,
      exp_id TEXT NOT NULL,
      param_value REAL,
      config_hash TEXT,
      artifact_path TEXT,
      PRIMARY KEY (exp_id, variant_id),
      FOREIGN KEY (exp_id) REFERENCES experiments(exp_id)
    );

    CREATE TABLE IF NOT EXISTS kpis (
      exp_id TEXT NOT NULL,
      variant_id TEXT NOT NULL,
      metric TEXT NOT NULL,
      value REAL,
      PRIMARY KEY (exp_id, variant_id, metric),
      FOREIGN KEY (exp_id, variant_id) REFERENCES variants(exp_id, variant_id)
    );

    CREATE TABLE IF NOT EXISTS insights (
      insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
      exp_id TEXT NOT NULL,
      variant_id TEXT NOT NULL,
      type TEXT NOT NULL,
      payload_json TEXT NOT NULL
    );
  `);

  return _db;
}
