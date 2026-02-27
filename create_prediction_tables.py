#!/usr/bin/env python
"""One-off: create prediction tables and record migration (when migration order is broken)."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_ai.settings')
django.setup()

from django.db import connection

# SQLite-compatible SQL for prediction.0001_initial (no "integer unsigned")
SQL = """
CREATE TABLE IF NOT EXISTS "prediction_ai_models" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "version" varchar(20) NOT NULL, "description" text NOT NULL, "accuracy_score" decimal NOT NULL, "total_predictions" integer NOT NULL, "correct_predictions" integer NOT NULL, "is_active" bool NOT NULL, "created_at" datetime NOT NULL);
CREATE TABLE IF NOT EXISTS "prediction_stocks" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "symbol" varchar(10) NOT NULL UNIQUE, "name" varchar(200) NOT NULL, "sector" varchar(100) NOT NULL DEFAULT '', "current_price" decimal NOT NULL, "previous_close" decimal NOT NULL, "market_cap" bigint NULL, "volume" bigint NULL, "pe_ratio" decimal NULL, "fifty_two_week_high" decimal NULL, "fifty_two_week_low" decimal NULL, "last_updated" datetime NOT NULL);
CREATE TABLE IF NOT EXISTS "prediction_predictions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_prediction" varchar(4) NOT NULL, "ai_prediction" varchar(4) NOT NULL, "ai_confidence" decimal NOT NULL, "ai_explanation" text NOT NULL, "actual_result" varchar(4) NULL, "is_correct" bool NULL, "price_at_prediction" decimal NOT NULL, "predicted_for_date" date NOT NULL, "created_at" datetime NOT NULL, "resolved_at" datetime NULL, "stock_id" bigint NOT NULL REFERENCES "prediction_stocks" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE IF NOT EXISTS "prediction_market_indicators" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "indicator_type" varchar(20) NOT NULL, "value" decimal NOT NULL, "period" integer NOT NULL DEFAULT 14, "calculated_at" datetime NOT NULL, "stock_id" bigint NOT NULL REFERENCES "prediction_stocks" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE IF NOT EXISTS "prediction_price_history" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "date" date NOT NULL, "open_price" decimal NOT NULL, "high_price" decimal NOT NULL, "low_price" decimal NOT NULL, "close_price" decimal NOT NULL, "volume" bigint NOT NULL, "stock_id" bigint NOT NULL REFERENCES "prediction_stocks" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX IF NOT EXISTS "prediction_predictions_stock_id_77ea4c2e" ON "prediction_predictions" ("stock_id");
CREATE INDEX IF NOT EXISTS "prediction_predictions_user_id_9a50e4db" ON "prediction_predictions" ("user_id");
CREATE INDEX IF NOT EXISTS "prediction_market_indicators_stock_id_deb4b161" ON "prediction_market_indicators" ("stock_id");
CREATE UNIQUE INDEX IF NOT EXISTS "prediction_price_history_stock_id_date_45c87952_uniq" ON "prediction_price_history" ("stock_id", "date");
CREATE INDEX IF NOT EXISTS "prediction_price_history_stock_id_843c4d4a" ON "prediction_price_history" ("stock_id");
"""

def main():
    with connection.cursor() as cur:
        for stmt in SQL.strip().split(';'):
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt)
            except Exception as e:
                if 'already exists' in str(e).lower():
                    continue
                raise
    # Record migration as applied
    with connection.cursor() as cur:
        cur.execute(
            "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES ('prediction', '0001_initial', datetime('now'))"
        )
    print("Prediction tables created and migration recorded.")

if __name__ == '__main__':
    main()
