# Active Context

## 當前焦點

Web 服務發行前收斂：systemd 部署、同源 `/api` proxy、anonymous session 隔離、RBAC、真實進度回報、release smoke test、備份回滾與文件同步。
本輪補上 PHI 校對模式與 production hardening：安全預設仍隱藏原始值，但內測驗收可由上傳者按需揭露命中的 PHI 值以判斷 true/false positive；log/error path 已改為安全摘要，避免 PHI 進入第二份資料庫。

## 相關檔案

- `scripts/services/frontend-server.mjs` - production frontend static server + same-origin `/api` proxy
- `scripts/services/install-services.sh` - systemd install/update entrypoint
- `scripts/services/configure-lan-access.sh` - trusted LAN anonymous-session setup
- `scripts/services/configure-production-proxy.sh` - HTTPS/password/RBAC production setup
- `web/backend/main.py` - anonymous session middleware and startup cleanup/recovery
- `web/backend/security.py` - origin guard, service token, session auth helpers
- `web/backend/services/task_service.py` - persisted task state and interrupted task recovery
- `web/backend/services/file_service.py` - user-scoped uploads and raw upload purge
- `web/backend/services/result_sanitizer.py` - result/report PHI reveal policy and response sanitization
- `scripts/services/backup-runtime-state.sh` / `restore-runtime-state.sh` - runtime backup and rollback
- `scripts/check_workflow.py` - frontend-proxy smoke test, optional password login
- `web/frontend/src/infrastructure/api/base.ts` - frontend API base resolution, default `/api`
- `docs/DEPLOYMENT.md` - current deployment/runbook
- `docs/RELEASE_GUIDE.md` - release gate checklist

## 待解決問題

- [x] 完成 local release validation：backend unit、frontend lint/test/build、ruff F/E9、service script syntax
- [ ] 部署新版本後重跑 systemd frontend-proxy smoke
- [ ] 分段 Git commit：runtime/security、progress/UX、deployment/docs、CI/audit
- [ ] Push 到 `origin/master`
- [ ] 真正公開 production 前仍需正式 TLS 網域、醫院端身份政策、備份/稽核/監控策略

## 上下文

- 內測模式可使用 `MEDICAL_DEID_AUTH_MODE=anonymous_session`，不需要帳密，但仍以 HttpOnly cookie 建立每個瀏覽器/session 的資料隔離。
- 正式多人上線建議 `password` auth + admin/user RBAC + HTTPS reverse proxy。
- 瀏覽器不應直接呼叫 `:8000`；前端 bundle 預設 `/api`，由 frontend service 代理到 `127.0.0.1:8000`。
- Web UI 原始上傳檔不是「從不落地」，而是本機短暫暫存，處理完成後預設刪除，並由 startup cleanup/TTL 補償。
- `MEDICAL_DEID_STORE_RAW_PHI=1` + `MEDICAL_DEID_ALLOW_PHI_REVEAL=1` 只適合內測校對，會暫存在結果 artifact 保留命中的 PHI 值；production 建議關閉。
- 更新前先備份 `/etc/medical-deid`、systemd unit、`/var/lib/medical-deid`、`/var/log/medical-deid`，並保留 rollback tarball。
- systemd frontend 必須執行 `node scripts/services/frontend-server.mjs`，不可再使用舊的 `serve -s dist`。

## 更新時間

2026-05-11 16:35
