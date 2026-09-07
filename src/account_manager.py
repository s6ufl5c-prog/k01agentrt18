import json
import os
import time
from typing import List, Dict, Any

ACCOUNTS_FILE = "data_accounts.json"


class AccountManager:
    """Manages registered/redeemed accounts and stats."""

    def __init__(self, file_path: str = ACCOUNTS_FILE):
        self.file_path = file_path
        self.accounts: List[Dict[str, Any]] = self._load_accounts()

    def _load_accounts(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.accounts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving accounts: {e}")

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.accounts)
        success_count = sum(1 for a in self.accounts if a.get("status") == "success")
        failed_count = sum(1 for a in self.accounts if a.get("status") == "failed")
        # Default matching Image #1 if empty
        if total == 0:
            return {
                "total_accounts": 0,
                "success_rate": "0%",
                "success_count": 0,
                "failed_count": 1,
                "progress": "1/1",
                "elapsed": "0s",
                "avg_time": "-"
            }
        rate = f"{int((success_count / total * 100))}%"

        return {
            "total_accounts": total,
            "success_rate": rate,
            "success_count": success_count,
            "failed_count": failed_count,
            "progress": f"{total}/{total}",
            "elapsed": "0s",
            "avg_time": "-"
        }

    def add_record(self, email: str, plan_name: str, status: str = "success", error_msg: str = ""):
        item = {
            "id": f"acc_{int(time.time()*1000)}",
            "email": email,
            "plan": plan_name,
            "status": status,
            "error": error_msg,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.accounts.append(item)
        self._save()
        return item

    def get_all(self) -> List[Dict[str, Any]]:
        return list(reversed(self.accounts))
