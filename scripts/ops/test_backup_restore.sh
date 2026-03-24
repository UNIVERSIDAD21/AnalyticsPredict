#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_PATH="$($ROOT_DIR/scripts/ops/backup_sqlite.sh)"

# marca temporal para verificar restore
PAGOS_DB="${PAGOS_DB_PATH:-$ROOT_DIR/backend/data/pagos.db}"
python3 - <<PY
import sqlite3, os
p=os.path.abspath('$PAGOS_DB')
os.makedirs(os.path.dirname(p), exist_ok=True)
conn=sqlite3.connect(p)
conn.execute("CREATE TABLE IF NOT EXISTS c2_restore_probe(v TEXT)")
conn.execute("DELETE FROM c2_restore_probe")
conn.execute("INSERT INTO c2_restore_probe(v) VALUES ('modified_after_backup')")
conn.commit(); conn.close()
PY

$ROOT_DIR/scripts/ops/restore_sqlite.sh "$BACKUP_PATH" >/dev/null

python3 - <<PY
import sqlite3, os, sys
p=os.path.abspath('$PAGOS_DB')
conn=sqlite3.connect(p)
cur=conn.cursor()
try:
    cur.execute("SELECT COUNT(*) FROM c2_restore_probe")
    n=cur.fetchone()[0]
except Exception:
    n=0
conn.close()
print('restore_probe_rows', n)
if n != 0:
    sys.exit(1)
PY

echo "backup_restore_test_ok"
