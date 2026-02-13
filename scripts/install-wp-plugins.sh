#!/usr/bin/env bash
# 依 docs/WORDPRESS_PLUGINS.md 清單，使用 WP-CLI 批次安裝 WordPress 外掛
# 在 VM 上執行：cd /opt/wp-template && bash scripts/install-wp-plugins.sh
# 或：./scripts/install-wp-plugins.sh（勿用 sh 執行）
# 需先啟動 docker compose（wordpress、db 在跑），且 .env 已設定

# 若被 sh 呼叫則改用 bash 重新執行（本腳本需 bash）
if [ -z "$BASH" ] || [ -n "$ZSH_VERSION" ]; then
  exec bash "$0" "$@"
fi

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# 從 docker-compose 取得專案名稱（用於 volume / network）
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-wp-template}"
VOLUME_NAME="${COMPOSE_PROJECT_NAME}_wp_data"
NETWORK_NAME="${COMPOSE_PROJECT_NAME}_wordpress-network"

# 載入 .env（若存在）
if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

# 必要變數（.env 內需有 MYSQL_PASSWORD）
if [ -z "${MYSQL_PASSWORD}" ]; then
  echo "錯誤：請在 $REPO_ROOT/.env 設定 MYSQL_PASSWORD"
  exit 1
fi
export WORDPRESS_DB_HOST="${WORDPRESS_DB_HOST:-db}"
export WORDPRESS_DB_USER="${MYSQL_USER:-wordpress}"
export WORDPRESS_DB_PASSWORD="${MYSQL_PASSWORD}"
export WORDPRESS_DB_NAME="${MYSQL_DATABASE:-wordpress}"

# 對應 docs/WORDPRESS_PLUGINS.md 的 WordPress.org 外掛 slug（不含「待選」）
PLUGINS=(
  seo-by-rank-math      # Rank Math SEO
  google-site-kit       # Site Kit by Google
  wp-super-cache        # WP Super Cache
  updraftplus           # UpdraftPlus
  wordfence             # Wordfence Security
  wps-hide-login        # WPS Hide Login
  google-captcha        # reCaptcha by BestWebSoft
  wp-mail-smtp          # WP Mail SMTP
)

echo "=== 使用 WP-CLI 安裝外掛（volume: $VOLUME_NAME）==="
for slug in "${PLUGINS[@]}"; do
  echo "安裝: $slug"
done

# 使用官方 wordpress:cli 映像，掛載同一 wp_data、加入同一 network
sudo docker run --rm \
  -v "$VOLUME_NAME:/var/www/html" \
  --network "$NETWORK_NAME" \
  -e WORDPRESS_DB_HOST="$WORDPRESS_DB_HOST" \
  -e WORDPRESS_DB_USER="$WORDPRESS_DB_USER" \
  -e WORDPRESS_DB_PASSWORD="$WORDPRESS_DB_PASSWORD" \
  -e WORDPRESS_DB_NAME="$WORDPRESS_DB_NAME" \
  wordpress:cli \
  plugin install "${PLUGINS[@]}" --allow-root

echo ""
echo "=== 安裝完成 ==="
echo "請至 WordPress 後台「外掛」啟用並設定各外掛。"
echo "社群分享、地圖嵌入、關閉留言等見 docs/WORDPRESS_PLUGINS.md 第六節。"
