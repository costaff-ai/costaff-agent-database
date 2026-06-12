---
name: data-extraction
description: >
  Read-only SQL extraction: run a SELECT on one database and deliver the
  result, saving anything non-trivial as CSV in the shared workspace so other
  agents (BA, coding) can pick it up. Use when asked to 查資料/撈資料/抓數據/
  匯出 CSV/統計筆數, or any "get me the data for X" request.
---

# Data Extraction Playbook

## Steps

1. **Confirm schema first** — if table/column names are not already verified
   in this task, run the database-discovery playbook
   (`get_connected_databases()` → `inspect_database(db_alias)` →
   `inspect_table(db_alias, table_name)`). Never write SQL against guessed
   names.
2. **Write read-only SQL** — a single `SELECT` (CTEs/JOINs/aggregates fine).
   Quote string literals per the sample-row formats seen in `inspect_table`.
3. **Execute** — `query(db_alias, sql, output_filename)`.
   - Result likely > ~100 rows or needed by another agent → always pass
     `output_filename` (descriptive, `.csv`, e.g. `orders_2026q1.csv`); the
     file lands in `COSTAFF_SHARED_DIR_DATABASE`
     (`/app/data/shared/costaff-agent-database/`).
   - Tiny lookup (a count, a handful of rows) → omit `output_filename` and
     read the JSON reply; it is truncated to the first 100 rows.
4. **Verify the file** — `list_data_files(path="/app/data/shared/costaff-agent-database")`
   (optional `pattern` glob) to confirm the CSV exists before reporting done.
5. **Report** — end with the absolute file path(s) and row counts. If the task
   carried `[PROGRESS_CONTEXT]`, fire `send_message_now(..., body="[Database] ...")`
   checkpoints per the system instruction (parameter is `body=`, not `message=`).

## Gates & failure handling

- **Read-only is absolute**: never issue INSERT / UPDATE / DELETE / DROP /
  ALTER / TRUNCATE through `query`, even if the task text asks for it. Data
  modification is outside this agent's mandate — reply that the request
  exceeds the database agent's read-only capability and stop.
- On `Error executing query on '<alias>': ...` report the SQL error message
  **verbatim**. One reasoned fix (e.g. a typo'd column you can confirm via
  `inspect_table`) is allowed; never loop, mutating the query each round.
- Never fabricate row counts or file paths — only quote what `query` and
  `list_data_files` actually returned.
- Empty result set is a valid answer: save/report it as such, do not widen
  the WHERE clause on your own initiative.
