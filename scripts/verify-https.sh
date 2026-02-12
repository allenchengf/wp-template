#!/usr/bin/env bash
# 驗證 HTTPS 是否正常（可在 Let's Encrypt 設定完成後執行）
set -e
PROJECT_ID="${GCP_PROJECT:-ubiqservices}"
ZONE="${GCP_ZONE:-asia-east1-b}"
INSTANCE_NAME="${GCP_INSTANCE:-wordpress-vm}"

EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "VM 外部 IP: $EXTERNAL_IP"
echo ""
echo "--- https://www.ubiqservices.net ---"
curl -sS -w "\nHTTP 狀態: %{http_code}\n" --connect-timeout 10 "https://www.ubiqservices.net/" -o /dev/null -k 2>/dev/null || echo "連線失敗（請確認 DNS 與防火牆）"
echo ""
echo "--- 憑證資訊 ---"
echo | openssl s_client -connect "www.ubiqservices.net:443" -servername www.ubiqservices.net 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null || echo "無法取得憑證資訊"
