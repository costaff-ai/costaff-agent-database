---
name: cross-db-extraction
description: >
  Multi-database extraction: pull related data from two or more database
  aliases into separate CSV files plus explicit join notes for downstream
  agents. Use when asked to 跨資料庫/合併不同系統的資料/對照兩個庫, or when one
  question needs tables that live in different connected databases.
---

# Cross-Database Extraction Playbook

## Steps

1. **Map the question to sources** — `get_connected_databases()`; decide which
   alias owns which part of the question. If one alias covers everything,
   fall back to the simpler data-extraction playbook.
2. **Verify schemas on every side** — `inspect_database(db_alias)` then
   `inspect_table(db_alias, table_name)` for each table involved. Identify the
   join keys and check their formats match across DBs (e.g. zero-padded codes
   vs integers) using the sample rows.
3. **Extract per database** — one `query(db_alias, sql, output_filename)` per
   source. SQL can only see tables inside its own alias — **never write a
   single SQL statement that references tables from two aliases**; there is no
   cross-DB join engine. Include the join-key column in every SELECT.
4. **Name files by source** — prefix filenames with the alias, e.g.
   `salesdb_orders.csv`, `hrdb_employees.csv`, so downstream agents can tell
   them apart.
5. **Verify and document** — `list_data_files(path="/app/data/shared/costaff-agent-database")`
   to confirm all files exist, then report: each file's absolute path, which
   alias it came from, row count, and exactly which columns join to which
   (e.g. `salesdb_orders.emp_id = hrdb_employees.id`). The actual merge is the
   downstream agent's job (coding/BA), not yours.

## Gates & failure handling

- Same read-only rule as everywhere: SELECT only; refuse any cross-DB "sync"
  or "copy table A into database B" request — that is data modification.
- If one source fails (connection or SQL error), still deliver the successful
  files, and report the failing alias's error verbatim — do not silently drop
  the failed side or substitute data from another alias.
- Do not attempt the join yourself by re-querying with values pasted from the
  other database's result unless the key list is tiny (≤ ~20 values) and the
  task explicitly needs a filtered pull.
- Key-format mismatch you cannot resolve via SQL casts is reported as a
  finding with examples, not "fixed" by guessing a transformation.
