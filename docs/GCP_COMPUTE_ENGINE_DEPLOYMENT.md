# 在 GCP Compute Engine 部署 WordPress Docker 環境（gcloud 操作）

本文件以 **gcloud CLI** 為主，提供在 GCP Compute Engine 上建立 VM、設定防火牆、安裝 Docker，並部署本專案（WordPress + Nginx + MySQL）的完整指令流程。

---

## 前置需求

- 已擁有 Google 帳號
- 本機已安裝 [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)
- （僅建立新專案時）專案需連結帳單；既有專案請在 Console 確認已啟用計費

---

## 變數說明（請依環境替換）

以下流程會用到這些變數，建議先設好再複製貼上指令：

```bash
# 專案 ID（若為新專案，會一併建立）
export PROJECT_ID="your-project-id"          # 例如：wordpress-prod
export PROJECT_NAME="WordPress Prod"         # 專案顯示名稱（僅建立新專案時用）

# VM 與區域
export INSTANCE_NAME="wordpress-vm"
export ZONE="asia-east1-b"                   # 台灣 asia-east1，可選 a/b/c
export MACHINE_TYPE="e2-medium"              # 2 vCPU, 4GB；可改 e2-standard-2 等
```

---

## 一、gcloud 登入與專案

### 步驟 1.1：登入並設定應用程式預設憑證

```bash
gcloud auth login
gcloud auth application-default login
```

### 步驟 1.2：建立新專案 或 使用既有專案

**若你要用「新專案」**（且專案 ID 尚未被使用）：

```bash
# 建立專案（PROJECT_ID 需全網唯一，且建立後無法變更）
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# 連結帳單：請到 Console https://console.cloud.google.com/billing 手動連結
# 連結完成後再執行後續步驟
```

**若出現「Project ID is already in use」**：

- **可能是你自己已有的專案**：直接改用該專案，不需再建立。請略過 `projects create`，從「選定專案並啟用 API」開始：

```bash
# 查看你帳號下已有的專案（確認 PROJECT_ID 是否在清單中）
gcloud projects list

# 直接選定該專案並繼續後續步驟
gcloud config set project $PROJECT_ID
gcloud services enable compute.googleapis.com
```

- **若要建立「全新」專案**：請換一個**全網唯一**的專案 ID（例如加上數字或代碼：`wordpress-prod-2024`、`my-company-wp`），再執行 `gcloud projects create`。

### 步驟 1.3：選定專案並啟用 API

```bash
gcloud config set project $PROJECT_ID

# 啟用 Compute Engine API（建立 VM 必要）
gcloud services enable compute.googleapis.com

# 可選：若之後要用 Cloud Storage 備份
# gcloud services enable storage-api.googleapis.com
```

---

## 二、用 gcloud 建立 Compute Engine VM

一鍵建立 VM：Ubuntu 22.04、開機磁碟 30GB、並加上 HTTP/HTTPS 標籤（供下方防火牆規則使用）。

```bash
gcloud compute instances create $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server \
  --metadata=startup-script='#!/bin/bash
apt-get -y update && apt-get -y install docker.io docker-compose-plugin
systemctl enable docker && systemctl start docker'
```

> **說明**：  
> - `--tags=http-server,https-server` 會讓預設的「允許 HTTP/HTTPS」防火牆規則套用到此 VM；若專案沒有該預設規則，請用下一節手動建立。  
> - 使用 startup-script 時，首次 SSH 登入後若希望免 sudo 執行 docker，請執行：`sudo usermod -aG docker $USER`，再登出並重新 SSH 登入。

**不帶 startup-script、僅建立空白 VM（手動裝 Docker）**：

```bash
gcloud compute instances create $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server
```

建立完成後，記下輸出中的 `EXTERNAL_IP`，或執行：

```bash
gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

## 三、防火牆規則（gcloud）

若 VM 未使用 `http-server,https-server` 標籤，或專案沒有預設 HTTP/HTTPS 規則，可手動建立：

```bash
# 允許 HTTP (80) 與 HTTPS (443) 入站
gcloud compute firewall-rules create allow-http-https \
  --project=$PROJECT_ID \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0
```

僅允許特定 IP（例如你的辦公室）時，將 `--source-ranges` 改為你的 IP，例如：

```bash
--source-ranges=203.0.113.0/24
```

---

## 四、SSH 連線與取得外部 IP（gcloud）

### 取得 VM 外部 IP

```bash
gcloud compute instances list --filter="name=$INSTANCE_NAME" --format='table(name,zone,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)'
```

或單一值（方便寫進腳本）：

```bash
export EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo $EXTERNAL_IP
```

### SSH 連線

```bash
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID
```

連線後終端機提示會變成 `username@instance-name:~$`，表示已進入 VM。

### （可選）保留靜態外部 IP

```bash
# 先查詢目前使用中的 IP 名稱
gcloud compute addresses list

# 將目前 VM 的臨時 IP 升格為靜態（需先停止 VM 或保留其臨時 IP 後再升格）
# 建議做法：建立具名靜態 IP，再建立/更新 VM 時指定
gcloud compute addresses create wordpress-ip --region=asia-east1 --project=$PROJECT_ID
# 建立 VM 時可改為：--address=$(gcloud compute addresses describe wordpress-ip --region=asia-east1 --format='get(address)')
```

---

## 四之一、進入 VM 後完整設定（root SSH、Docker、專案安裝）

以下依序在 **VM 內**執行。建議專案放在 **`/opt/wp-template`**。

### 1. 設定 root SSH（讓本機可用 root 登入）

先以**一般使用者**連線進入 VM，再執行：

```bash
# 複製目前使用者的 SSH 公鑰到 root，讓 gcloud 可指定 --login-user=root 登入
sudo mkdir -p /root/.ssh
sudo cp ~/.ssh/authorized_keys /root/.ssh/authorized_keys
sudo chown -R root:root /root/.ssh
sudo chmod 700 /root/.ssh
sudo chmod 600 /root/.ssh/authorized_keys

# 允許 root 以金鑰登入（禁止密碼，較安全）
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

之後在**本機**可用 root 登入：

```bash
gcloud compute ssh wordpress-vm --zone=asia-east1-b --project=ubiqservices -- --login-user=root
```

### 2. 安裝 Docker、Docker Compose 並設定權限

在 VM 內執行（可用 root 或一般使用者 + sudo）：

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable docker && sudo systemctl start docker
```

- **若用 root 操作**：無需額外權限，直接執行 `docker` / `docker compose` 即可。
- **若用一般使用者**：加入 docker 群組後登出再登入一次：

```bash
sudo usermod -aG docker $USER
# 登出後重新 SSH 登入，或執行：newgrp docker
```

驗證：

```bash
sudo docker --version
sudo docker compose version
```

### 3. 將專案安裝到正確位置（/opt/wp-template）

**3.1 本機打包並上傳**

在**本機**執行（專案父目錄、變數請替換）：

```bash
cd /Users/allenchen/project/tony
tar czf /tmp/wp-template.tar.gz --exclude='wp-template/.git' wp-template

gcloud compute scp /tmp/wp-template.tar.gz wordpress-vm:/tmp/wp-template.tar.gz \
  --zone=asia-east1-b --project=ubiqservices
```

**3.2 在 VM 上解壓到 /opt/wp-template**

在 **VM 內**執行：

```bash
sudo mkdir -p /opt/wp-template
sudo tar xzf /tmp/wp-template.tar.gz -C /opt
# 若解壓後是 /opt/wp-template（目錄名正確），無需搬移；若解壓到 /opt 底下多個檔案，請：sudo mv /opt/docker-compose.yml /opt/config /opt/env.example /opt/wp-template/ 等
ls -la /opt/wp-template/docker-compose.yml
```

確認有 `docker-compose.yml`、`config/`、`env.example` 後，設定環境變數並啟動：

```bash
cd /opt/wp-template
sudo cp env.example .env
sudo nano .env
```

在 `.env` 中至少修改：

- `MYSQL_ROOT_PASSWORD=強密碼`
- `MYSQL_PASSWORD=強密碼`

存檔後啟動服務：

```bash
sudo docker compose up -d
sudo docker compose ps
```

之後從瀏覽器開啟 `http://<VM 外部 IP>` 完成 WordPress 安裝。

---

## 五、在 VM 上安裝 Docker 與 Docker Compose（未用 startup-script 時）

若建立 VM 時**沒有**使用上面的 `startup-script`，需手動在 VM 內安裝 Docker。先以 gcloud SSH 進入 VM，再執行：

```bash
# 在 VM 內執行
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker $USER
```

登出 SSH 再登入後，可免 sudo 執行 `docker` / `docker compose`。驗證：

```bash
docker --version
docker compose version
```

---

## 五、在 VM 上安裝 Docker 與 Docker Compose

以下在 **VM 的 SSH 終端機** 中執行（Ubuntu 22.04）。

### 步驟 5.1：更新系統

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 步驟 5.2：安裝必要套件

```bash
sudo apt-get install -y ca-certificates curl gnupg lsb-release
```

### 步驟 5.3：加入 Docker 官方 GPG 與 repository

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 步驟 5.4：安裝 Docker Engine 與 Compose 外掛

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### 步驟 5.5：啟動並設定開機自動啟動

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 步驟 5.6：驗證安裝

```bash
sudo docker --version
sudo docker compose version
```

（可選）讓目前使用者免 sudo 執行 docker：

```bash
sudo usermod -aG docker $USER
# 登出 SSH 再登入後生效；或先執行：newgrp docker
```

---

## 六、將專案放到 VM 並設定環境變數（gcloud scp）

### 步驟 6.1：從本機上傳專案到 VM

在**本機**（含專案目錄的電腦）執行，使用 gcloud 上傳：

```bash
# 在本機：從專案「上層」目錄打包，解壓後會得到 wp-template 目錄
cd /Users/allenchen/project/tony   # 專案所在父目錄
tar czf /tmp/wp-template.tar.gz --exclude='wp-template/.git' wp-template

# 上傳到 VM
gcloud compute scp /tmp/wp-template.tar.gz $INSTANCE_NAME:~ \
  --zone=$ZONE \
  --project=$PROJECT_ID
```

在 **VM 上**（先 `gcloud compute ssh $INSTANCE_NAME --zone=$ZONE` 進入）：

```bash
cd ~
tar xzf wp-template.tar.gz
cd wp-template
```

**方式 B：VM 上從 Git 複製（若 VM 可連到你的 Git repo）**

```bash
# 在 VM 內
sudo apt-get install -y git
git clone https://github.com/your-org/wp-template.git ~/wp-template
cd ~/wp-template
```

### 步驟 6.2：建立並編輯 .env

```bash
cp env.example .env
nano .env
```

至少修改以下為**強密碼**（勿使用範例值）：

```env
MYSQL_ROOT_PASSWORD=你的_root_密碼
MYSQL_PASSWORD=你的_wordpress_資料庫密碼
```

其餘可維持預設（如 `MYSQL_DATABASE=wordpress`, `NGINX_HTTP_PORT=80`）。儲存後離開（nano: `Ctrl+O`  Enter, `Ctrl+X`）。

---

## 七、啟動 WordPress 服務

### 步驟 7.1：啟動容器

在專案目錄（含 `docker-compose.yml`）執行：

```bash
sudo docker compose up -d
```

### 步驟 7.2：確認服務狀態

```bash
sudo docker compose ps
```

三個服務（db、wordpress、nginx）應為 **Up** 或 **healthy**。若有異常：

```bash
sudo docker compose logs -f
```

### 步驟 7.3：開放 VM 本機 80 埠（若需要）

一般 GCP 已允許 VM 對外 80 埠，若本機有防火牆可檢查：

```bash
sudo ufw status
# 若 ufw 為 active 且未放行 80：
# sudo ufw allow 80/tcp
# sudo ufw allow 443/tcp
# sudo ufw reload
```

---

## 八、完成 WordPress 安裝與存取

### 步驟 8.1：從瀏覽器存取

在瀏覽器開啟：

- `http://<VM 的外部 IP>`

例如：`http://34.80.xxx.xxx`

### 步驟 8.2：執行 WordPress 五分鐘安裝

1. 選擇語言
2. 填寫網站標題、管理員帳號、密碼、電子郵件
3. 點「安裝 WordPress」
4. 登入後即可開始使用

### 步驟 8.3：網域與 HTTPS（見下方第九節）

---

## 九、網域與 Let's Encrypt（HTTPS）

### 9.0 網域已在 GoDaddy 指好：WordPress 與 Nginx 要改什麼？

DNS 已指向 VM（例如 `www.ubiqservices.net` → 34.81.156.56）後，需改兩處。**無法用 gcloud 直接改**，但可用 **gcloud 連進 VM** 後用指令或後台完成。

| 項目 | 要改的內容 | 方式 |
|------|------------|------|
| **Nginx** | `server_name` 改為你的網域，Nginx 才會用這個站點回應 | 改設定檔後重啟 nginx 容器 |
| **WordPress** | 後台「網址」：WordPress 位址、網站位址改為 `https://www.ubiqservices.net`（或先 `http://`） | 後台 **設定 → 一般**，或下方指令 |

**一、Nginx 設定（在 VM 上）**

專案裡已將 `config/nginx/default.conf` 的 `server_name` 設為 `www.ubiqservices.net ubiqservices.net`。若 VM 上的專案已更新，只需重啟 Nginx：

```bash
# 在 VM 上（先 gcloud compute ssh wordpress-vm --zone=asia-east1-b --project=ubiqservices）
cd /opt/wp-template
sudo docker compose restart nginx
```

若 VM 上的設定檔仍是 `server_name localhost;`，可手動改為網域後再重啟：

```bash
sudo sed -i 's/server_name localhost;/server_name www.ubiqservices.net ubiqservices.net localhost;/' /opt/wp-template/config/nginx/default.conf
sudo docker compose restart nginx
```

或從本機把已改好的設定檔傳上 VM 再重啟：

```bash
# 本機執行
gcloud compute scp /Users/allenchen/project/tony/wp-template/config/nginx/default.conf wordpress-vm:/opt/wp-template/config/nginx/default.conf --zone=asia-east1-b --project=ubiqservices
# 再 SSH 進 VM 執行
sudo docker compose -f /opt/wp-template/docker-compose.yml restart nginx
```

**二、WordPress 網址（兩種方式擇一）**

- **方式 A：後台**  
  登入 WordPress 後台 → **設定 → 一般** → 將「WordPress 位址 (URL)」與「網站位址 (URL)」改為 `https://www.ubiqservices.net`（若尚未啟用 HTTPS，先改為 `http://www.ubiqservices.net`）→ 儲存。

- **方式 B：在 VM 上用指令（透過 gcloud SSH 進去後執行）**

```bash
# 在 VM 上，先 cd /opt/wp-template
# 將 YOUR_MYSQL_PASSWORD 換成 .env 裡的 MYSQL_PASSWORD；若尚未啟用 HTTPS 請改用 http://
sudo docker compose exec -T db mysql -u wordpress -pYOUR_MYSQL_PASSWORD wordpress -e "UPDATE wp_options SET option_value = 'https://www.ubiqservices.net' WHERE option_name IN ('siteurl', 'home');"
sudo docker compose restart wordpress
```

完成後用瀏覽器開 **https://www.ubiqservices.net/**（或先 http）應可正常進入網站。

---

**順序：先設定 Domain Name（DNS），再設定 Let's Encrypt。**

Let's Encrypt 會驗證「網域是否指向你的主機」，所以必須先讓網域指到 VM 的 IP，憑證才能核發。

### 9.1 先做：Domain Name（網域與 DNS）

**1. 固定 VM 的外部 IP（建議）**

若 VM 重開機，預設會換 IP，DNS 就會指錯。建議先保留靜態 IP：

```bash
# 本機執行
gcloud compute addresses create wordpress-ip --region=asia-east1 --project=ubiqservices
# 查詢剛建立的靜態 IP
gcloud compute addresses describe wordpress-ip --region=asia-east1 --project=ubiqservices --format='get(address)'
```

接著在 GCP Console：**Compute Engine → VM 執行個體 → 點 wordpress-vm → 編輯 → 網路介面 → 外部 IP 改為「wordpress-ip」** 並儲存。或刪除現有 VM 後用 `--address=上述IP` 重建（需先備份 /opt/wp-template 與資料）。

**2. 在網域註冊商設定 DNS**

到購買網域的地方（Cloudflare、GoDaddy、Gandi、Google Domains 等）新增一筆 **A 記錄**：

| 類型 | 名稱（host） | 內容（指向） | TTL |
|------|--------------|--------------|-----|
| A    | @ 或 www     | VM 的外部 IP（例如 34.81.156.56） | 300 或預設 |

- **@** = 根網域（例如 `example.com`）
- **www** = `www.example.com`

等幾分鐘後，在本機測試是否已指到 VM：

```bash
dig +short 你的網域
# 或
nslookup 你的網域
```

應回傳你的 VM 外部 IP。

**3. 確認 80 已對外開放**

GCP 防火牆需允許 80（以及之後 443）。若尚未開，本機執行：

```bash
gcloud compute firewall-rules create allow-http-https \
  --project=ubiqservices --direction=INGRESS --priority=1000 --network=default \
  --action=ALLOW --rules=tcp:80,tcp:443 --source-ranges=0.0.0.0/0
```

完成以上後，用瀏覽器開 `http://你的網域` 應能看到 WordPress。

---

### 9.2 再做：Let's Encrypt（HTTPS 憑證）

DNS 已指到 VM、且 **http:// 你的網域** 可連線後，在 VM 上依序執行以下步驟。專案已內建 Nginx 443 設定（`config/nginx/default-ssl.conf`）與 `docker-compose` 的 443 埠、憑證掛載。

**步驟 1：在 VM 上安裝 Certbot 並取得憑證**

```bash
# 先 SSH 進 VM
gcloud compute ssh wordpress-vm --zone=asia-east1-b --project=ubiqservices

# 在 VM 內
sudo apt-get update && sudo apt-get install -y certbot
cd /opt/wp-template
sudo docker compose stop nginx
sudo certbot certonly --standalone -d www.ubiqservices.net -d ubiqservices.net --email 你的信箱@example.com --agree-tos --non-interactive
```

**步驟 2：把專案最新檔同步到 VM（含 docker-compose 與 default-ssl.conf）**

若 VM 上的專案是從 Git 拉的：

```bash
cd /opt/wp-template && sudo git pull
```

若為本機上傳，在本機執行後再回 VM 解壓或覆蓋：

```bash
# 本機
cd /Users/allenchen/project/tony
tar czf /tmp/wp-template.tar.gz --exclude='wp-template/.git' wp-template
gcloud compute scp /tmp/wp-template.tar.gz wordpress-vm:/tmp/ --zone=asia-east1-b --project=ubiqservices
# VM 上
cd /opt/wp-template && sudo tar xzf /tmp/wp-template.tar.gz --strip-components=1 -C .
```

**步驟 3：啟動 Nginx（會載入 443 與憑證）**

```bash
cd /opt/wp-template
sudo docker compose up -d nginx
sudo docker compose ps
```

用瀏覽器開 **https://www.ubiqservices.net** 應可看到網站（可能需接受憑證警告一次）。

**步驟 4（可選）：HTTP 自動導向 HTTPS**

讓 `http://` 自動跳轉到 `https://`：

```bash
sudo cp /opt/wp-template/config/nginx/default-80-redirect.conf /opt/wp-template/config/nginx/default.conf
sudo docker compose restart nginx
```

**步驟 5：WordPress 後台改為 HTTPS 網址**

登入 WordPress → **設定 → 一般** → 將「WordPress 位址 (URL)」「網站位址 (URL)」改為 **https://www.ubiqservices.net** → 儲存。或 VM 上執行（替換密碼）：

```bash
cd /opt/wp-template
sudo docker compose exec -T db mysql -u wordpress -p你的MYSQL密碼 wordpress -e "UPDATE wp_options SET option_value = 'https://www.ubiqservices.net' WHERE option_name IN ('siteurl', 'home');"
sudo docker compose restart wordpress
```

**步驟 6：憑證自動續期（cron）**

```bash
sudo crontab -e
# 加入一行（每月 1 日 00:00 續期並重載 Nginx）
0 0 1 * * certbot renew --quiet && (cd /opt/wp-template && sudo docker compose exec -T nginx nginx -s reload)
```

---

**總結順序**

| 步驟 | 項目 | 說明 |
|------|------|------|
| 1 | Domain Name | 靜態 IP（可選）→ DNS A 記錄指到 VM → 確認 `http://你的網域` 可連 |
| 2 | Let's Encrypt | 在 VM 上執行 certbot 取得憑證 → 設定 Nginx 使用 443 與憑證 |

---

## 十、日後維運常用指令（在 VM 上）

在專案目錄下：

```bash
# 進入專案目錄
cd ~/wp-template

# 查看狀態
sudo docker compose ps

# 查看日誌
sudo docker compose logs -f

# 停止服務
sudo docker compose down

# 再次啟動
sudo docker compose up -d

# 重啟單一服務（例如 nginx）
sudo docker compose restart nginx
```

---

## 十一、gcloud 指令速查（依序執行）

以下為**本機**可一次複製貼上的 gcloud 流程（變數請先設好：`PROJECT_ID`、`ZONE`、`INSTANCE_NAME`、`MACHINE_TYPE`）。

```bash
# 1) 登入與專案
gcloud auth login
gcloud auth application-default login
gcloud config set project $PROJECT_ID
gcloud services enable compute.googleapis.com

# 2) 建立 VM（含 HTTP/HTTPS 標籤）
gcloud compute instances create $INSTANCE_NAME \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server

# 3) 防火牆（若專案尚無預設 http-server 規則）
gcloud compute firewall-rules create allow-http-https \
  --direction=INGRESS --priority=1000 --network=default \
  --action=ALLOW --rules=tcp:80,tcp:443 --source-ranges=0.0.0.0/0

# 4) 查 VM 外部 IP
gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# 5) SSH 連線
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE
```

進入 VM 後：安裝 Docker（見第五節）、上傳專案（見第六節）、設定 `.env`、執行 `docker compose up -d`。

---

## 十二、建議步驟順序總覽

| 順序 | 階段 | gcloud / 操作 |
|------|------|----------------|
| 1 | 專案與 API | `gcloud auth login` → `gcloud config set project` → `gcloud services enable compute.googleapis.com` |
| 2 | 建立 VM | `gcloud compute instances create ... --tags=http-server,https-server` |
| 3 | 防火牆 | `gcloud compute firewall-rules create allow-http-https ...`（無預設規則時） |
| 4 | 連線與 IP | `gcloud compute ssh`、`gcloud compute instances describe ... format=EXTERNAL_IP` |
| 5 | 安裝 Docker | VM 內手動安裝或使用建立 VM 時的 startup-script |
| 6 | 部署專案 | 本機 `gcloud compute scp` 上傳 → VM 解壓、`cp env.example .env` 並編輯 |
| 7 | 啟動服務 | VM 內 `docker compose up -d`、`docker compose ps` |
| 8 | 存取網站 | 瀏覽 `http://<EXTERNAL_IP>` 完成 WordPress 安裝 |
| 9 | 網域與 HTTPS | 先設 DNS A 記錄（與靜態 IP）→ 再設 Let's Encrypt（見第九節） |

---

## 參考

- 專案一般安裝說明：[INSTALLATION.md](INSTALLATION.md)
- 故障排除：[TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [GCP Compute Engine 文件](https://cloud.google.com/compute/docs)
- [Docker 安裝（Ubuntu）](https://docs.docker.com/engine/install/ubuntu/)
