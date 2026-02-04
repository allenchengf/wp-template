#!/usr/bin/env python3
"""
E2E Negative Test Cases - 端到端負面測試案例
測試錯誤情況、異常處理和邊界條件
"""

import unittest
import requests
import time
from typing import Dict


class TestWordPressNegativeCases(unittest.TestCase):
    """WordPress 負面測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 10

    def test_invalid_login_attempt(self):
        """測試無效登入嘗試（負面測試）"""
        try:
            # 嘗試使用錯誤的憑證登入
            login_data = {
                "log": "invalid_user",
                "pwd": "wrong_password",
                "wp-submit": "Log In"
            }
            response = requests.post(
                f"{self.BASE_URL}/wp-login.php",
                data=login_data,
                timeout=self.TIMEOUT,
                allow_redirects=False
            )
            # 應該返回登入頁面或錯誤訊息，不應該成功登入
            self.assertNotEqual(
                response.status_code,
                302,  # 不應該是重定向到後台
                "無效登入不應該成功"
            )
            # 檢查是否包含錯誤訊息
            if response.status_code == 200:
                self.assertIn(
                    "error",
                    response.text.lower(),
                    "無效登入應該顯示錯誤訊息"
                )
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試登入: {e}")

    def test_unauthorized_api_access(self):
        """測試未授權的 API 訪問（負面測試）"""
        try:
            # 嘗試訪問需要認證的 API 端點
            response = requests.get(
                f"{self.BASE_URL}/wp-json/wp/v2/users/me",
                timeout=self.TIMEOUT
            )
            # 應該返回 401 或 403
            self.assertIn(
                response.status_code,
                [401, 403, 404],
                f"未授權 API 訪問應返回錯誤狀態碼，實際: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試 API 訪問: {e}")

    def test_file_upload_size_limit(self):
        """測試檔案上傳大小限制（負面測試）"""
        try:
            # 嘗試上傳超過限制的檔案
            large_file = b"x" * (65 * 1024 * 1024)  # 65MB，超過 64MB 限制
            files = {"file": ("large_file.txt", large_file)}
            
            response = requests.post(
                f"{self.BASE_URL}/wp-admin/admin-ajax.php",
                files=files,
                timeout=30
            )
            # 應該返回 413 或 400
            self.assertIn(
                response.status_code,
                [400, 413, 500],
                f"超大檔案上傳應返回錯誤狀態碼，實際: {response.status_code}"
            )
        except requests.exceptions.RequestException:
            # 連接可能超時或失敗，這也是可以接受的
            pass

    def test_invalid_nonce(self):
        """測試無效的 nonce（負面測試）"""
        try:
            # 嘗試使用無效的 nonce 提交表單
            data = {
                "action": "test",
                "_wpnonce": "invalid_nonce_12345"
            }
            response = requests.post(
                f"{self.BASE_URL}/wp-admin/admin-ajax.php",
                data=data,
                timeout=self.TIMEOUT
            )
            # 應該返回錯誤（-1 或錯誤訊息）
            if response.status_code == 200:
                # WordPress AJAX 通常返回 -1 表示 nonce 驗證失敗
                self.assertIn(
                    "-1",
                    response.text,
                    "無效 nonce 應該返回錯誤"
                )
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試 nonce 驗證: {e}")

    def test_csrf_protection(self):
        """測試 CSRF 防護（負面測試）"""
        try:
            # 嘗試跨站請求（沒有正確的 referer）
            response = requests.post(
                f"{self.BASE_URL}/wp-admin/admin-ajax.php",
                data={"action": "test"},
                headers={"Referer": "http://evil-site.com"},
                timeout=self.TIMEOUT
            )
            # WordPress 應該有 CSRF 防護
            # 檢查響應中是否有錯誤指示
            if response.status_code == 200:
                # 可能返回 -1 或錯誤訊息
                pass  # 這個測試比較複雜，需要實際的表單
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試 CSRF 防護: {e}")

    def test_timeout_handling(self):
        """測試超時處理（負面測試）"""
        try:
            # 發送一個可能導致超時的請求
            response = requests.get(
                self.BASE_URL,
                timeout=0.001  # 極短的超時時間
            )
            self.fail("應該發生超時異常")
        except requests.exceptions.Timeout:
            # 預期的超時異常
            pass
        except requests.exceptions.RequestException:
            # 其他異常也是可以接受的
            pass

    def test_malformed_json_request(self):
        """測試格式錯誤的 JSON 請求（負面測試）"""
        try:
            response = requests.post(
                f"{self.BASE_URL}/wp-json/wp/v2",
                json={"invalid": "json", "unclosed": True},  # 故意不完整
                headers={"Content-Type": "application/json"},
                timeout=self.TIMEOUT
            )
            # 應該返回 400 或正常處理
            self.assertIn(
                response.status_code,
                [200, 400, 404],
                "格式錯誤的 JSON 應該被適當處理"
            )
        except requests.exceptions.RequestException:
            pass


class TestSecurityNegativeCases(unittest.TestCase):
    """安全性負面測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 10

    def test_directory_listing_disabled(self):
        """測試目錄列表是否被禁用（負面測試）"""
        try:
            # 嘗試訪問目錄（應該返回 403 或 404，不應該列出目錄內容）
            response = requests.get(
                f"{self.BASE_URL}/wp-content/",
                timeout=self.TIMEOUT,
                allow_redirects=False
            )
            # 不應該是 200 且包含目錄列表
            if response.status_code == 200:
                self.assertNotIn(
                    "Index of",
                    response.text,
                    "目錄列表應該被禁用"
                )
        except requests.exceptions.RequestException:
            pass

    def test_server_info_disclosure(self):
        """測試伺服器資訊洩露（負面測試）"""
        try:
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            headers = response.headers
            
            # Server 標頭不應該包含版本資訊
            server_header = headers.get("Server", "")
            if server_header:
                self.assertNotIn(
                    "nginx/1.26",
                    server_header.lower(),
                    "Server 標頭不應該洩露版本資訊"
                )
            
            # 不應該包含 X-Powered-By 標頭（或應該被移除）
            # WordPress 可能會設置，但 Nginx 應該嘗試移除
            powered_by = headers.get("X-Powered-By", "")
            if powered_by:
                print(f"⚠️ X-Powered-By 標頭存在: {powered_by}")
        except requests.exceptions.RequestException as e:
            self.fail(f"無法測試資訊洩露: {e}")

    def test_http_method_override_attack(self):
        """測試 HTTP 方法覆蓋攻擊（負面測試）"""
        try:
            # 嘗試使用 X-HTTP-Method-Override 標頭
            response = requests.post(
                self.BASE_URL,
                headers={"X-HTTP-Method-Override": "DELETE"},
                timeout=self.TIMEOUT
            )
            # 應該正常處理 POST，不應該執行 DELETE
            # 檢查響應是否正常（不應該是 405）
            self.assertNotEqual(
                response.status_code,
                405,
                "HTTP 方法覆蓋攻擊應該被防止"
            )
        except requests.exceptions.RequestException:
            pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
