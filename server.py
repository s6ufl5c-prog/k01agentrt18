import os
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import load_config
from src.engine import GoogleAutoRedeemer
from src.mailnest import MailNestClient
from src.proxy_manager import ProxyManager
from src.account_manager import AccountManager

app = FastAPI(title="Google Auto-Redeemer & Management WebUI")

# Data Managers
proxy_mgr = ProxyManager()
account_mgr = AccountManager()
MAILNEST_CONFIG_FILE = "data_mailnest.json"


def get_saved_mailnest_config() -> dict:
    if os.path.exists(MAILNEST_CONFIG_FILE):
        try:
            with open(MAILNEST_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"api_key": "", "project_code": "aws001"}


def save_mailnest_config_file(cfg: dict):
    with open(MAILNEST_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# Static mount
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


# ---------------- Stats API ----------------
@app.get("/api/stats")
def get_stats():
    return account_mgr.get_stats()


@app.get("/api/accounts")
def get_accounts():
    return account_mgr.get_all()


# ---------------- MailNest API ----------------
class MailNestConfigRequest(BaseModel):
    api_key: str
    project_code: str


@app.get("/api/mailnest/config")
def get_mailnest_config():
    return get_saved_mailnest_config()


@app.post("/api/mailnest/config")
def save_mailnest_config_endpoint(req: MailNestConfigRequest):
    cfg = {"api_key": req.api_key.strip(), "project_code": req.project_code.strip()}
    save_mailnest_config_file(cfg)
    return {"success": True, "message": "配置保存成功"}


@app.post("/api/mailnest/test")
def test_mailnest_endpoint(req: MailNestConfigRequest):
    client = MailNestClient(api_key=req.api_key, project_code=req.project_code)
    return client.test_connection()


@app.post("/api/mailnest/create_mailbox")
def create_mailbox_endpoint():
    cfg = get_saved_mailnest_config()
    client = MailNestClient(api_key=cfg.get("api_key", ""), project_code=cfg.get("project_code", ""))
    return client.get_new_email()


@app.get("/api/mailnest/messages")
def get_messages_endpoint(mailbox_id: str):
    cfg = get_saved_mailnest_config()
    client = MailNestClient(api_key=cfg.get("api_key", ""), project_code=cfg.get("project_code", ""))
    return client.get_messages(mailbox_id)


# ---------------- Proxy Management API ----------------
class ProxyCreateRequest(BaseModel):
    address: str
    type: Optional[str] = "家宽"
    country_name: Optional[str] = "美国"
    country_code: Optional[str] = "US"
    protocol: Optional[str] = "http"


class ProxyUpdateRequest(BaseModel):
    status: Optional[bool] = None
    latency: Optional[int] = None
    address: Optional[str] = None
    type: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    ids: List[str]


@app.get("/api/proxies")
def get_proxies(query: str = "", status_filter: str = "all"):
    return proxy_mgr.get_all(query=query, status_filter=status_filter)


@app.post("/api/proxies")
def add_proxy_endpoint(req: ProxyCreateRequest):
    return proxy_mgr.add_proxy(
        address=req.address,
        proxy_type=req.type or "家宽",
        country_name=req.country_name or "美国",
        country_code=req.country_code or "US",
        protocol=req.protocol or "http"
    )


@app.put("/api/proxies/{proxy_id}")
def update_proxy_endpoint(proxy_id: str, req: ProxyUpdateRequest):
    updates = {k: v for k, v in req.dict().items() if v is not None}
    updated = proxy_mgr.update_proxy(proxy_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return updated


@app.delete("/api/proxies/{proxy_id}")
def delete_proxy_endpoint(proxy_id: str):
    success = proxy_mgr.delete_proxy(proxy_id)
    return {"success": success}


@app.post("/api/proxies/batch_delete")
def batch_delete_endpoint(req: BatchDeleteRequest):
    count = proxy_mgr.batch_delete(req.ids)
    return {"deleted_count": count}


@app.post("/api/proxies/{proxy_id}/test")
def test_single_proxy(proxy_id: str):
    return proxy_mgr.test_proxy(proxy_id)


@app.post("/api/proxies/batch_test")
def batch_test_proxies():
    return proxy_mgr.batch_test()


# ---------------- Task Execution API ----------------
class TaskRunRequest(BaseModel):
    url: str
    auto_confirm: Optional[bool] = True
    proxy: Optional[str] = None


@app.post("/api/tasks/run")
def run_redeem_task(req: TaskRunRequest):
    config = load_config()
    # Override proxy if provided or pick from active proxy list
    proxy_to_use = req.proxy or proxy_mgr.get_active_proxy_url() or ""
    if proxy_to_use:
        config["redeemer"]["proxy"] = proxy_to_use

    config["redeemer"]["auto_confirm"] = req.auto_confirm
    config["redeemer"]["headless"] = True  # webui runs headless

    redeemer = GoogleAutoRedeemer(config)
    result = redeemer.redeem(req.url)

    # Save account record
    account_mgr.add_record(
        email=result.account_email or "Auto Google Account",
        plan_name=result.plan_name or "Google One / Service Offer",
        status="success" if result.success else "failed",
        error_msg=result.message if not result.success else ""
    )

    return {
        "success": result.success,
        "status": result.status,
        "message": result.message,
        "plan_name": result.plan_name,
        "account_email": result.account_email
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
