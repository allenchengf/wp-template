#!/usr/bin/env bash
# Let's Encrypt 設定腳本（透過 gcloud 在 VM 上執行）
# 使用方式：先 gcloud auth login，再執行
#   CERTBOT_EMAIL=your@email.com ./scripts/setup-letsencrypt-gcloud.sh

set -e
if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -1 >/dev/null; then
  echo "請先在本機執行: gcloud auth login"
  exit 1
fi
PROJECT_ID="${GCP_PROJECT:-ubiqservices}"
ZONE="${GCP_ZONE:-asia-east1-b}"
INSTANCE_NAME="${GCP_INSTANCE:-wordpress-vm}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@ubiqservices.net}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 1. 上傳 HTTPS 設定檔到 VM ==="
gcloud compute scp \
  "$REPO_ROOT/docker-compose.yml" \
  "$REPO_ROOT/config/nginx/default-ssl.conf" \
  "$REPO_ROOT/config/nginx/default-80-redirect.conf" \
  "$INSTANCE_NAME:/tmp/" \
  --zone="$ZONE" \
  --project="$PROJECT_ID"

echo "=== 2. 在 VM 上：複製設定、安裝 certbot、取得憑證、啟動 Nginx ==="
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --command="
set -e
sudo cp /tmp/docker-compose.yml /opt/wp-template/
sudo cp /tmp/default-ssl.conf /tmp/default-80-redirect.conf /opt/wp-template/config/nginx/

sudo apt-get update -qq && sudo apt-get install -y -qq certbot > /dev/null

cd /opt/wp-template
sudo docker compose stop nginx || true

# 僅先申請 www.ubiqservices.net（根網域 ubiqservices.net 須在 GoDaddy 設 A 記錄指到 VM 後再一起申請）
sudo certbot certonly --standalone \
  -d www.ubiqservices.net \
  --email '$CERTBOT_EMAIL' \
  --agree-tos --non-interactive

sudo docker compose up -d nginx
sudo docker compose ps
"

echo "=== 3. 啟用 HTTP 導向 HTTPS ==="
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --command="
sudo cp /opt/wp-template/config/nginx/default-80-redirect.conf /opt/wp-template/config/nginx/default.conf
cd /opt/wp-template && sudo docker compose restart nginx
"

echo "=== 4. 取得 VM 外部 IP 並測試 HTTPS ==="
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "VM 外部 IP: $EXTERNAL_IP"

echo ""
echo "--- 測試 HTTPS (www.ubiqservices.net) ---"
curl -sS --connect-timeout 10 -o /dev/null -w "HTTP 狀態: %{http_code}\n" "https://www.ubiqservices.net/" -k 2>/dev/null || echo "（若本機無法解析網域，可改用 IP 測 443）"

echo ""
echo "--- 測試 443 埠 (by IP) ---"
curl -sS --connect-timeout 10 -o /dev/null -w "HTTP 狀態: %{http_code}\n" "https://$EXTERNAL_IP/" -k -H "Host: www.ubiqservices.net" 2>/dev/null || echo "連線逾時或失敗"

echo ""
echo "--- 檢查憑證資訊 (若 openssl 可用) ---"
echo | openssl s_client -connect "www.ubiqservices.net:443" -servername www.ubiqservices.net 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null || true

echo ""
echo "=== 完成 ==="
echo "請在瀏覽器開啟: https://www.ubiqservices.net"
echo "WordPress 後台請將網址改為 https://www.ubiqservices.net（設定 → 一般）"
echo ""
echo "若要在憑證中加入根網域 ubiqservices.net："
echo "  1. 在 GoDaddy 為 ubiqservices.net（@）新增 A 記錄指到 VM 外部 IP"
echo "  2. 等 DNS 生效後，在 VM 上執行："
echo "     sudo certbot certonly --standalone -d www.ubiqservices.net -d ubiqservices.net --expand --email $CERTBOT_EMAIL --agree-tos --non-interactive"
echo "     cd /opt/wp-template && sudo docker compose restart nginx"
