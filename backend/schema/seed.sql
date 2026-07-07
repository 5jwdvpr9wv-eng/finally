-- Default seed data for a fresh FinAlly database.
--
-- Run only when the database is empty (see the lazy-init logic in
-- app/db/connection.py). INSERT OR IGNORE keeps it safe to re-run: existing
-- rows are never clobbered, so a user's edited cash balance or curated
-- watchlist survives restarts.
--
-- Timestamps use ISO-8601 UTC (strftime) to match the format the Python
-- repository layer writes.

-- One user profile: default, $10,000 cash.
INSERT OR IGNORE INTO users_profile (id, cash_balance, created_at)
VALUES ('default', 10000.0, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));

-- Ten default watchlist tickers.
INSERT OR IGNORE INTO watchlist (user_id, ticker, added_at) VALUES
    ('default', 'AAPL',  strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'GOOGL', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'MSFT',  strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'AMZN',  strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'TSLA',  strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'NVDA',  strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'META',  strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'JPM',   strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'V',     strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('default', 'NFLX',  strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));
