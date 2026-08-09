#!/bin/sh
# Entrypoint pgAdmin: generate servers.json + .pgpass dari env vars,
# lalu jalankan entrypoint asli image (yang meng-import keduanya).
set -e

DB_HOST="${PGADMIN_DB_HOST:-db}"
DB_PORT="${PGADMIN_DB_PORT:-5432}"
DB_NAME="${PGADMIN_DB_NAME:-rsud}"
DB_USER="${PGADMIN_DB_USER:-rsud}"
DB_PASSWORD="${POSTGRES_PASSWORD:-rsud_secret}"

# Server definition — di-import pgAdmin saat start (PGADMIN_REPLACE_SERVERS_ON_STARTUP=True)
SERVERS_JSON="$(mktemp)"
cat > "${SERVERS_JSON}" <<EOF
{
  "Servers": {
    "1": {
      "Name": "rsud",
      "Group": "Servers",
      "Host": "${DB_HOST}",
      "Port": ${DB_PORT},
      "MaintenanceDB": "${DB_NAME}",
      "Username": "${DB_USER}",
      "SSLMode": "prefer"
    }
  }
}
EOF
export PGADMIN_SERVER_JSON_FILE="${SERVERS_JSON}"

# .pgpass agar koneksi ke Postgres tidak meminta password manual
PGPASS_FILE="$(mktemp)"
printf '%s:%s:%s:%s:%s\n' \
  "${DB_HOST}" "${DB_PORT}" "${DB_NAME}" "${DB_USER}" "${DB_PASSWORD}" \
  > "${PGPASS_FILE}"
chmod 600 "${PGPASS_FILE}"
export PGPASS_FILE

exec /entrypoint.sh "$@"
