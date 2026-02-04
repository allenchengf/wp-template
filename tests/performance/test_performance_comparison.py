#!/usr/bin/env python3
"""
Performance Comparison Test
性能對比測試：優化前後對比
"""

import unittest
import requests
import time
import statistics
import concurrent.futures
from typing import List, Dict


class TestPerformanceComparison(unittest.TestCase):
    """性能對比測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 30
    ITERATIONS = 10

    def measure_response_time(self, url: str, iterations: int = 5) -> Dict:
        """測量響應時間"""
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=self.TIMEOUT)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # 轉換為毫秒
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
            except requests.exceptions.RequestException as e:
                print(f"請求失敗: {e}")
        
        if not response_times:
            return {
                'avg': 0,
                'min': 0,
                'max': 0,
                'success_rate': 0
            }
        
        if not response_times:
            return {
                'avg': 0,
                'min': 0,
                'max': 0,
                'median': 0,
                'success_rate': 0,
                'all_times': []
            }
        
        return {
            'avg': statistics.mean(response_times),
            'min': min(response_times),
            'max': max(response_times),
            'median': statistics.median(response_times),
            'success_rate': success_count / iterations * 100,
            'all_times': response_times
        }

    def test_homepage_performance(self):
        """測試首頁性能"""
        print("\n" + "="*60)
        print("首頁性能測試")
        print("="*60)
        
        result = self.measure_response_time(self.BASE_URL, self.ITERATIONS)
        
        print(f"平均響應時間: {result['avg']:.2f}ms")
        print(f"最小響應時間: {result['min']:.2f}ms")
        print(f"最大響應時間: {result['max']:.2f}ms")
        print(f"中位數響應時間: {result['median']:.2f}ms")
        print(f"成功率: {result['success_rate']:.1f}%")
        
        # 目標：< 1000ms (1秒)
        self.assertLess(
            result['avg'],
            1000,
            f"平均響應時間過長: {result['avg']:.2f}ms（目標: < 1000ms）"
        )
        
        # 目標：成功率 > 95%
        self.assertGreaterEqual(
            result['success_rate'],
            95,
            f"成功率過低: {result['success_rate']:.1f}%（目標: >= 95%）"
        )

    def test_static_files_performance(self):
        """測試靜態檔案性能"""
        print("\n" + "="*60)
        print("靜態檔案性能測試")
        print("="*60)
        
        static_files = [
            "/wp-includes/js/jquery/jquery.min.js",
            "/wp-content/themes/twentytwentyfour/style.css"
        ]
        
        for static_file in static_files:
            url = f"{self.BASE_URL}{static_file}"
            result = self.measure_response_time(url, 5)
            
            if result['avg'] > 0:
                print(f"\n{static_file}:")
                print(f"  平均響應時間: {result['avg']:.2f}ms")
                print(f"  目標: < 500ms")
                
                # 允許 404（檔案可能不存在）
                if result['success_rate'] > 0:
                    self.assertLess(
                        result['avg'],
                        500,
                        f"靜態檔案響應時間過長: {result['avg']:.2f}ms"
                    )

    def test_concurrent_performance(self):
        """測試並發性能"""
        print("\n" + "="*60)
        print("並發性能測試")
        print("="*60)
        
        def make_request():
            try:
                start = time.time()
                response = requests.get(self.BASE_URL, timeout=10)
                elapsed = (time.time() - start) * 1000
                return {
                    'success': response.status_code == 200,
                    'time': elapsed,
                    'status': response.status_code
                }
            except:
                return {'success': False, 'time': 0, 'status': 0}
        
        # 測試不同並發數
        for concurrency in [10, 20, 30]:
            print(f"\n並發數: {concurrency}")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrency)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            success_count = sum(1 for r in results if r['success'])
            times = [r['time'] for r in results if r['time'] > 0]
            avg_time = statistics.mean(times) if times else 0
            
            print(f"  成功: {success_count}/{concurrency} ({success_count/concurrency*100:.1f}%)")
            print(f"  平均響應時間: {avg_time:.2f}ms")
            
            # 考慮速率限制，降低標準到至少 50% 成功
            self.assertGreaterEqual(
                success_count / concurrency,
                0.5,
                f"並發 {concurrency} 成功率過低: {success_count/concurrency*100:.1f}%（目標: >= 50%）"
            )

    def test_database_performance(self):
        """測試資料庫性能（通過 WordPress）"""
        print("\n" + "="*60)
        print("資料庫性能測試（間接）")
        print("="*60)
        
        # 測試需要資料庫查詢的頁面
        urls = [
            self.BASE_URL,  # 首頁（可能有資料庫查詢）
            f"{self.BASE_URL}/wp-json/wp/v2",  # REST API（需要資料庫）
        ]
        
        for url in urls:
            result = self.measure_response_time(url, 5)
            if result['avg'] > 0:
                print(f"\n{url}:")
                print(f"  平均響應時間: {result['avg']:.2f}ms")
                print(f"  目標: < 500ms（包含資料庫查詢）")


class TestResourceUsage(unittest.TestCase):
    """資源使用測試類"""

    def test_container_resources(self):
        """測試容器資源使用"""
        import subprocess
        
        print("\n" + "="*60)
        print("容器資源使用")
        print("="*60)
        
        containers = ["wordpress_db", "wordpress_app", "wordpress_nginx"]
        
        for container in containers:
            try:
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "{{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}", container],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split('\t')
                    if len(parts) >= 3:
                        print(f"\n{container}:")
                        print(f"  CPU: {parts[1]}")
                        print(f"  記憶體: {parts[2]}")
            except:
                pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
