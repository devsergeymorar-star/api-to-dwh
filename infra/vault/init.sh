#!/bin/sh
# Seeds the dev-mode Vault: KV mount for Airflow, the DWH connection, and a read-only token.
set -eu

until vault status >/dev/null 2>&1; do sleep 1; done

if ! vault secrets list -format=json | grep -q '"airflow/"'; then
  vault secrets enable -path=airflow kv-v2
fi

# Airflow VaultBackend reads airflow/connections/<conn_id>
vault kv put airflow/connections/clickhouse_dwh \
  conn_type=generic \
  host=clickhouse \
  port=8123 \
  login="$CH_USER" \
  password="$CH_PASSWORD" \
  schema=raw >/dev/null

# API keys of sources. An empty CoinGecko key means "use the public rate limit".
vault kv put airflow/connections/coingecko \
  conn_type=http \
  host=api.coingecko.com \
  password="${COINGECKO_API_KEY:-}" >/dev/null

vault policy write airflow-read - <<'EOF' >/dev/null
path "airflow/data/*"     { capabilities = ["read"] }
path "airflow/metadata/*" { capabilities = ["read", "list"] }
EOF

if ! vault token lookup "$AIRFLOW_VAULT_TOKEN" >/dev/null 2>&1; then
  vault token create -id="$AIRFLOW_VAULT_TOKEN" -policy=airflow-read -orphan -period=768h >/dev/null
fi

echo "vault seeded: connections clickhouse_dwh, coingecko; policy airflow-read"
