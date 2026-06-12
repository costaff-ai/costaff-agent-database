---
name: database-discovery
description: >
  Survey connected databases and explore their schemas before any query:
  list DB aliases, list tables, inspect columns/types/sample rows. Use when
  asked to 查資料庫/有哪些資料庫/看資料表/欄位有什麼/schema 長怎樣, or whenever
  the target table or column for an extraction task is not yet known.
---

# Database Discovery Playbook

## Steps

1. **List sources** — `get_connected_databases()` (no arguments). It returns
   each configured alias with its `type` and `description`. Pick the alias
   whose description matches the task; never invent an alias.
2. **List tables** — `inspect_database(db_alias)` returns the table names of
   that database. If the alias is wrong it returns
   `Error: Database alias '<x>' not found.` — go back to step 1, do not guess
   alternative spellings.
3. **Inspect candidates** — for each plausible table, call
   `inspect_table(db_alias, table_name)`. It returns `columns`
   (name/type/nullable) and up to 3 `sample_rows`. Use the samples to confirm
   value formats (date strings, codes, enums) before writing any SQL.
4. **Report findings** — summarise: alias, relevant tables, the exact column
   names to be used downstream. Quote column names exactly as returned —
   downstream `query` SQL must match them character for character.

## Gates & failure handling

- This skill is **inspection only** — never call `query` from here except via
  the data-extraction playbook after the schema is confirmed.
- `get_connected_databases()` returning "No databases configured" means the
  `DATABASE_CONFIG` env is missing: report that verbatim and stop; there is
  nothing to retry.
- Connection errors (`Error connecting to '<alias>': ...`) are reported
  verbatim. Do not retry more than once and never switch to a different alias
  hoping it is "the same data".
- `inspect_table` validates the table name against the live table list; a
  "Table not found" reply means re-run `inspect_database` — do not pluralise,
  snake-case, or otherwise mutate the name and retry blindly.
