#!/usr/bin/env python3
"""
PHI 去識別化工具 — 完整使用流程功能驗證腳本
============================================================

依照使用說明頁面的 8 個步驟，逐一驗證後端 API 是否正常。
使用真實 HTTP 請求，不需 Mock。

執行方式:
    cd /path/to/medical-deidentification
    python scripts/check_workflow.py [--url http://localhost:8000] [--verbose]
    python scripts/check_workflow.py --url http://localhost:5173 --frontend-proxy
"""

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("❌ 需要安裝 requests: uv pip install requests")
    sys.exit(1)

# ─── 顏色輸出 ────────────────────────────────────────────────────────────────

STRICT_WARNINGS = False
API_HEADERS: dict[str, str] = {}
API_SESSION = requests.Session()

def green(s: str) -> str:
    return f"\033[32m{s}\033[0m"

def red(s: str) -> str:
    return f"\033[31m{s}\033[0m"

def yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"

def blue(s: str) -> str:
    return f"\033[34m{s}\033[0m"

def bold(s: str) -> str:
    return f"\033[1m{s}\033[0m"

# ─── 測試結果追蹤 ─────────────────────────────────────────────────────────────

class CheckResult:
    def __init__(self, name: str):
        self.name = name
        self.steps: list[tuple[str, bool, str]] = []  # (desc, passed, detail)

    def ok(self, desc: str, detail: str = ""):
        self.steps.append((desc, True, detail))
        print(f"  {green('✓')} {desc}" + (f"  {yellow(detail)}" if detail else ""))

    def fail(self, desc: str, detail: str = ""):
        self.steps.append((desc, False, detail))
        print(f"  {red('✗')} {desc}" + (f"  {red(detail)}" if detail else ""))

    def warn(self, desc: str, detail: str = ""):
        self.steps.append((desc, not STRICT_WARNINGS, detail))
        print(f"  {yellow('⚠')} {desc}" + (f"  {yellow(detail)}" if detail else ""))

    @property
    def passed(self) -> bool:
        return all(ok for _, ok, _ in self.steps)

    @property
    def counts(self) -> tuple[int, int]:
        """Returns (passed, total)"""
        total = len(self.steps)
        passed = sum(1 for _, ok, _ in self.steps if ok)
        return passed, total


def step_header(num: int, title: str):
    print(f"\n{bold(blue(f'[步驟 {num}]'))} {bold(title)}")
    print("─" * 50)


# ─── API 輔助 ─────────────────────────────────────────────────────────────────

def api(base_url: str, method: str, path: str, **kwargs) -> requests.Response:
    url = f"{base_url}{path}"
    kwargs.setdefault("timeout", 30)
    headers = dict(API_HEADERS)
    headers.update(kwargs.pop("headers", {}) or {})
    if headers:
        kwargs["headers"] = headers
    return API_SESSION.request(method, url, **kwargs)


def default_frontend_origin(base_url: str, frontend_proxy: bool = False) -> str | None:
    """Derive the likely frontend origin from the backend URL."""
    if frontend_proxy:
        return None
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.hostname:
        return None
    if parsed.port in {80, 443, 5173}:
        return None
    return f"{parsed.scheme}://{parsed.hostname}:5173"


# ─── 各步驟驗證 ───────────────────────────────────────────────────────────────

def check_step0_server(base_url: str, verbose: bool, frontend_origin: str | None) -> CheckResult:
    """前置：確認 server 可連線"""
    r = CheckResult("Server 連線")
    step_header(0, "確認 API Server 可連線")
    try:
        resp = api(base_url, "GET", "/api/live")
        if resp.status_code == 200:
            r.ok("GET /api/live → 200 (API 啟動中)")
        else:
            docs_resp = api(base_url, "GET", "/docs")
            if docs_resp.status_code == 200:
                r.ok("GET /docs → 200 (FastAPI 啟動中)")
            else:
                r.fail(f"GET /api/live → {resp.status_code}")
    except requests.exceptions.ConnectionError:
        r.fail(f"無法連線至 {base_url}", "請確認服務已啟動：systemctl status medical-deid-frontend medical-deid-backend")

    if frontend_origin:
        try:
            resp = api(
                base_url,
                "OPTIONS",
                "/api/auth/login",
                headers={
                    "Origin": frontend_origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            allowed_origin = resp.headers.get("access-control-allow-origin")
            if resp.status_code == 200 and allowed_origin == frontend_origin:
                r.ok("CORS preflight 正常", f"origin={frontend_origin}")
            else:
                r.fail(
                    f"CORS preflight → {resp.status_code}",
                    f"origin={frontend_origin}, allow-origin={allowed_origin}",
                )
        except Exception as e:
            r.fail(f"CORS preflight 例外: {e}")
    return r


def authenticate(base_url: str, username: str | None, password: str | None) -> CheckResult:
    """Optional password-mode login for production smoke tests."""
    r = CheckResult("登入/session")
    step_header(0, "建立登入 session")
    if not username and not password:
        r.ok("未提供帳密，使用既有匿名 session 或 service token")
        return r
    if not username or not password:
        r.fail("帳號與密碼需同時提供")
        return r

    try:
        resp = api(
            base_url,
            "POST",
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        if resp.status_code == 200:
            user = resp.json().get("user", {})
            r.ok("登入成功", f"user={user.get('username')}, role={user.get('role')}")
        else:
            r.fail(f"登入失敗 HTTP {resp.status_code}", resp.text[:200])
    except Exception as e:
        r.fail(f"登入例外: {e}")
    return r


def check_step1_health(base_url: str, verbose: bool) -> CheckResult:
    """步驟 1：確認 LLM 連線"""
    r = CheckResult("LLM 連線")
    step_header(1, "確認 LLM 連線 (GET /api/health)")
    try:
        resp = api(base_url, "GET", "/api/health")
        if resp.status_code != 200:
            r.fail(f"HTTP {resp.status_code}", resp.text[:200])
            return r
        data = resp.json()
        r.ok("API 回應正常", f"status={data.get('status')}")

        llm = data.get("llm", {})
        llm_status = llm.get("status", "unknown")
        if llm_status == "online":
            r.ok(f"LLM 在線", f"model={llm.get('model')}")
        elif llm_status == "offline":
            r.warn("LLM 離線", "將使用模擬處理，PHI 偵測能力受限")
        else:
            r.warn(f"LLM 狀態: {llm_status}")

        engine = data.get("engine_available", False)
        if engine:
            r.ok("PHI 引擎已載入")
        else:
            r.warn("PHI 引擎未載入", "使用模擬處理")

        if verbose:
            print(f"    {yellow('Detail:')} {json.dumps(data, ensure_ascii=False)}")
    except Exception as e:
        r.fail(f"例外: {e}")
    return r


def check_step2_upload(base_url: str, verbose: bool) -> tuple[CheckResult, str | None]:
    """步驟 2：上傳檔案"""
    r = CheckResult("上傳檔案")
    step_header(2, "上傳檔案 (POST /api/upload)")
    file_id = None

    # 建立測試用 CSV
    csv_content = (
        "姓名,出生日期,電話,病歷號,備註\n"
        "王小明,1980/03/15,0912-345-678,MR001234,患者於 2024/01/15 回診\n"
        "李美華,1975/08/22,02-2345-6789,MR005678,請電 user@example.com 確認\n"
        "陳大偉,1990/12/01,0987-654-321,MR009999,地址：台北市信義區忠孝路1號\n"
    )
    test_file = io.BytesIO(csv_content.encode("utf-8"))

    try:
        resp = api(
            base_url, "POST", "/api/upload",
            files={"file": ("test_phi_data.csv", test_file, "text/csv")},
        )
        if resp.status_code == 200:
            data = resp.json()
            file_id = data.get("id") or data.get("file_id")
            filename = data.get("filename", "?")
            size = data.get("size", 0)
            r.ok(f"上傳成功", f"file_id={file_id}, filename={filename}, size={size}B")
        else:
            r.fail(f"HTTP {resp.status_code}", resp.text[:300])
    except Exception as e:
        r.fail(f"例外: {e}")
    return r, file_id


def check_step3_preview(base_url: str, file_id: str | None, verbose: bool) -> CheckResult:
    """步驟 3：預覽資料"""
    r = CheckResult("資料預覽")
    step_header(3, "預覽資料 (GET /api/preview)")

    if not file_id:
        r.fail("略過（無可用 file_id）")
        return r

    try:
        resp = api(base_url, "GET", f"/api/preview/{file_id}", params={"page": 1, "page_size": 10})
        if resp.status_code == 200:
            data = resp.json()
            rows = data.get("rows") or data.get("data", [])
            columns = data.get("columns", [])
            total = data.get("total_rows") or data.get("totalRows", 0)
            r.ok("預覽 API 正常")
            r.ok(f"欄位: {columns}" if columns else "欄位可讀")
            r.ok(f"總列數: {total}, 本頁: {len(rows)} 筆")
        elif resp.status_code == 404:
            r.fail(f"找不到檔案 {file_id}")
        else:
            r.fail(f"HTTP {resp.status_code}", resp.text[:300])
    except Exception as e:
        r.fail(f"例外: {e}")
    return r


def check_step4_settings(base_url: str, verbose: bool) -> CheckResult:
    """步驟 4：PHI 設定"""
    r = CheckResult("PHI 設定")
    step_header(4, "PHI 設定 (GET /api/settings/)")

    try:
        # 取得 PHI 類型
        resp = api(base_url, "GET", "/api/settings/phi-types")
        if resp.status_code == 200:
            types = resp.json()
            r.ok(f"PHI 類型列表正常", f"共 {len(types)} 種類型")
        else:
            r.fail(f"GET /api/settings/phi-types → {resp.status_code}")

        # 取得目前設定
        resp2 = api(base_url, "GET", "/api/settings/config")
        if resp2.status_code == 200:
            config = resp2.json()
            r.ok("設定 API 正常", f"masking={config.get('default_masking', '?')}")
        else:
            r.fail(f"GET /api/settings/config → {resp2.status_code}")
    except Exception as e:
        r.fail(f"例外: {e}")
    return r


def check_step5_process(
    base_url: str, file_id: str | None, verbose: bool, process_timeout: int
) -> tuple[CheckResult, str | None]:
    """步驟 5：執行去識別化"""
    r = CheckResult("去識別化處理")
    step_header(5, "執行去識別化 (POST /api/process)")
    task_id = None

    if not file_id:
        r.fail("略過（無可用 file_id）")
        return r, None

    try:
        resp = api(
            base_url, "POST", "/api/process",
            json={"file_ids": [file_id], "job_name": "workflow-check-test"},
        )
        if resp.status_code == 200:
            data = resp.json()
            task_id = data.get("task_id")
            status = data.get("status", "?")
            r.ok(f"任務建立成功", f"task_id={task_id}, status={status}")
        else:
            r.fail(f"HTTP {resp.status_code}", resp.text[:300])
            return r, None

        # 輪詢等待完成
        r.ok(f"等待任務完成（最多 {process_timeout} 秒）...")
        start = time.time()
        final_status = None
        while time.time() - start < process_timeout:
            try:
                resp2 = api(base_url, "GET", f"/api/tasks/{task_id}")
            except requests.exceptions.Timeout:
                # LLM 呼叫期間 server 可能忙，等待後重試
                time.sleep(3)
                continue
            if resp2.status_code == 200:
                task = resp2.json()
                final_status = task.get("status")
                progress = task.get("progress", 0)
                if verbose:
                    print(f"    {yellow('...')} status={final_status}, progress={progress:.0%}")
                if final_status in ("completed", "completed_with_errors", "failed"):
                    break
            time.sleep(3)

        if final_status == "completed":
            r.ok(f"任務完成", f"耗時 {time.time()-start:.1f} 秒")
        elif final_status == "completed_with_errors":
            r.warn("任務部分完成", "請檢查單檔錯誤")
        elif final_status == "failed":
            r.fail("任務失敗")
        else:
            r.warn(f"任務超時（狀態: {final_status}）", "後端仍在處理，可前往 UI 查看")
    except Exception as e:
        r.fail(f"例外: {e}")
    return r, task_id


def check_step6_results(base_url: str, task_id: str | None, verbose: bool) -> CheckResult:
    """步驟 6：查看結果"""
    r = CheckResult("處理結果")
    step_header(6, "查看處理結果 (GET /api/results)")

    try:
        # 列表
        resp = api(base_url, "GET", "/api/results")
        if resp.status_code == 200:
            results = resp.json()
            r.ok(f"結果列表正常", f"共 {len(results)} 筆")
        else:
            r.fail(f"GET /api/results → {resp.status_code}")
            return r

        # 詳情
        if task_id:
            resp2 = api(base_url, "GET", f"/api/results/{task_id}")
            if resp2.status_code == 200:
                detail = resp2.json()
                total_phi = detail.get("total_phi_found")
                if total_phi is None:
                    total_phi = sum(r.get("phi_found", 0) for r in detail.get("results", []))
                r.ok(f"結果詳情正常", f"偵測到 {total_phi} 個 PHI")
                # 驗證 PHI 是否有偵測到（CSV 中有明顯 PHI）
                if total_phi > 0:
                    r.ok(f"PHI 偵測有效（> 0）")
                else:
                    r.warn("PHI 偵測結果為 0", "可能使用模擬引擎或 LLM 離線")
            elif resp2.status_code == 404:
                r.warn(f"結果尚未產生", f"task_id={task_id}")
            else:
                r.fail(f"GET /api/results/{task_id} → {resp2.status_code}")
    except Exception as e:
        r.fail(f"例外: {e}")
    return r


def check_step7_reports(base_url: str, task_id: str | None, verbose: bool) -> CheckResult:
    """步驟 7：查看報告"""
    r = CheckResult("報告")
    step_header(7, "查看報告 (GET /api/reports)")

    try:
        resp = api(base_url, "GET", "/api/reports")
        if resp.status_code == 200:
            reports = resp.json()
            r.ok(f"報告列表正常", f"共 {len(reports)} 份報告")
        else:
            r.fail(f"GET /api/reports → {resp.status_code}")
            return r

        if task_id:
            resp2 = api(base_url, "GET", f"/api/reports/{task_id}")
            if resp2.status_code == 200:
                report = resp2.json()
                summary = report.get("summary", {})
                r.ok("報告詳情正常", f"total_phi={summary.get('total_phi_found', 0)}")
            elif resp2.status_code == 404:
                r.warn("報告尚未產生", f"task_id={task_id}")
            else:
                r.fail(f"GET /api/reports/{task_id} → {resp2.status_code}")
    except Exception as e:
        r.fail(f"例外: {e}")
    return r


def check_step8_download(base_url: str, task_id: str | None, verbose: bool) -> CheckResult:
    """步驟 8：下載去識別化資料"""
    r = CheckResult("下載資料")
    step_header(8, "下載去識別化資料 (GET /api/download)")

    if not task_id:
        r.fail("略過（無可用 task_id）")
        return r

    try:
        # 下載 result excel
        resp = api(
            base_url, "GET", f"/api/download/{task_id}",
            params={"file_type": "result", "format": "xlsx"},
        )
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            content_len = len(resp.content)
            r.ok("下載 Excel 成功", f"size={content_len}B, content-type={content_type}")
        elif resp.status_code == 404:
            r.warn("下載檔案 404", f"task_id={task_id} 結果可能尚未產生")
        else:
            r.fail(f"HTTP {resp.status_code}", resp.text[:200])

        # 下載 report json
        resp2 = api(
            base_url, "GET", f"/api/download/{task_id}",
            params={"file_type": "report", "format": "json"},
        )
        if resp2.status_code == 200:
            r.ok("下載報告(JSON)成功", f"size={len(resp2.content)}B")
        elif resp2.status_code == 404:
            r.warn("報告檔案 404，可能尚未產生")
        else:
            r.fail(f"下載報告 HTTP {resp2.status_code}")
    except Exception as e:
        r.fail(f"例外: {e}")
    return r


# ─── 清理測試資料 ─────────────────────────────────────────────────────────────

def cleanup_test_data(base_url: str, file_id: str | None, verbose: bool):
    """清除本次測試產生的資料（可選）"""
    print(f"\n{bold(blue('[清理]'))} 清除測試資料...")
    try:
        if file_id:
            resp = api(base_url, "DELETE", f"/api/files/{file_id}")
            if resp.status_code == 200:
                print(f"  {green('✓')} 已刪除測試檔案 {file_id}")
            else:
                print(f"  {yellow('⚠')} 刪除檔案失敗: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  {yellow('⚠')} 清理時發生例外: {e}")


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PHI 去識別化工具 — 完整使用流程功能驗證"
    )
    parser.add_argument("--url", default="http://localhost:8000", help="後端 API base URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="顯示詳細資訊")
    parser.add_argument("--skip-cleanup", action="store_true", help="跳過清除測試資料")
    parser.add_argument("--skip-process", action="store_true", help="跳過去識別化（僅測試 API 可用性）")
    parser.add_argument("--process-timeout", type=int, default=120, help="等待處理任務完成的秒數")
    parser.add_argument("--ci", action="store_true", help="CI 模式：warning 也視為失敗")
    parser.add_argument("--api-token", default=os.getenv("MEDICAL_DEID_API_TOKEN"), help="API token")
    parser.add_argument("--username", default=os.getenv("MEDICAL_DEID_SMOKE_USERNAME"), help="password auth username")
    parser.add_argument("--password", default=os.getenv("MEDICAL_DEID_SMOKE_PASSWORD"), help="password auth password")
    parser.add_argument(
        "--frontend-proxy",
        action="store_true",
        help="目標 URL 是前端同源代理（例如 http://host:5173），跳過 CORS preflight",
    )
    parser.add_argument(
        "--frontend-origin",
        default=None,
        help="用於 CORS preflight 的前端 Origin，預設由 --url 推導為同 host 的 5173 port",
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    frontend_origin = args.frontend_origin or default_frontend_origin(base_url, args.frontend_proxy)
    global STRICT_WARNINGS, API_HEADERS
    STRICT_WARNINGS = args.ci
    if args.api_token:
        API_HEADERS = {"Authorization": f"Bearer {args.api_token}"}

    print(bold("\n╔══════════════════════════════════════════════════╗"))
    print(bold("║  PHI 去識別化工具 — 功能驗證                        ║"))
    print(bold("╚══════════════════════════════════════════════════╝"))
    print(f"  目標: {bold(base_url)}")
    if frontend_origin:
        print(f"  前端 Origin: {bold(frontend_origin)}")
    print(f"  時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    all_results: list[CheckResult] = []
    file_id: str | None = None
    task_id: str | None = None

    # Step 0: Server 可連線
    r0 = check_step0_server(base_url, args.verbose, frontend_origin)
    all_results.append(r0)
    if not r0.passed:
        print(f"\n{red('✗ 後端 server 無法連線，終止驗證。')}")
        sys.exit(1)

    # Optional login for password/RBAC production mode. Cookies are kept in API_SESSION.
    r_auth = authenticate(base_url, args.username, args.password)
    all_results.append(r_auth)
    if not r_auth.passed:
        print(f"\n{red('✗ 登入/session 建立失敗，終止驗證。')}")
        sys.exit(1)

    # Step 1: Health/LLM
    r1 = check_step1_health(base_url, args.verbose)
    all_results.append(r1)

    # Step 2: Upload
    r2, file_id = check_step2_upload(base_url, args.verbose)
    all_results.append(r2)

    # Step 3: Preview
    r3 = check_step3_preview(base_url, file_id, args.verbose)
    all_results.append(r3)

    # Step 4: Settings
    r4 = check_step4_settings(base_url, args.verbose)
    all_results.append(r4)

    # Step 5: Process (可跳過)
    if args.skip_process:
        print(f"\n{yellow('[步驟 5]')} 去識別化處理 — {yellow('已跳過 (--skip-process)')}")
    else:
        r5, task_id = check_step5_process(base_url, file_id, args.verbose, args.process_timeout)
        all_results.append(r5)

    # Step 6: Results
    r6 = check_step6_results(base_url, task_id, args.verbose)
    all_results.append(r6)

    # Step 7: Reports
    r7 = check_step7_reports(base_url, task_id, args.verbose)
    all_results.append(r7)

    # Step 8: Download
    if args.skip_process:
        print(f"\n{yellow('[步驟 8]')} 下載去識別化資料 — {yellow('已跳過 (--skip-process)')}")
    else:
        r8 = check_step8_download(base_url, task_id, args.verbose)
        all_results.append(r8)

    # 清理
    if not args.skip_cleanup:
        cleanup_test_data(base_url, file_id, args.verbose)

    # ─── 最終報告 ────────────────────────────────────────────────────────────
    print(bold("\n╔══════════════════════════════════════════════════╗"))
    print(bold("║  驗證結果摘要                                        ║"))
    print(bold("╚══════════════════════════════════════════════════╝"))

    total_passed = 0
    total_checks = 0
    for r in all_results:
        p, t = r.counts
        total_passed += p
        total_checks += t
        icon = green("✓") if r.passed else red("✗")
        bar = f"{p}/{t}"
        print(f"  {icon} {r.name:<20} {bar}")

    print(f"\n  整體: {total_passed}/{total_checks} 項檢查通過")
    print()

    all_passed = all(r.passed for r in all_results)
    if all_passed:
        print(green(bold("  🎉 全部通過！完整使用流程功能正常。")))
        sys.exit(0)
    else:
        print(yellow(bold("  ⚠  部分檢查未通過，請查看上方詳情。")))
        sys.exit(1)


if __name__ == "__main__":
    main()
