import json
import os
import uuid
import shutil
from typing import Dict, Optional

SESSION_STORAGE_FILE = "sessions.json"

class SessionData:
    def __init__(self, session_id: str, user_data_dir: str, session_name: str = None):
        self.session_id = session_id
        self.user_data_dir = user_data_dir
        self.session_name = session_name if session_name else session_id
        self.proxy_host = ""
        self.proxy_port = ""
        self.proxy_user = ""
        self.proxy_password = ""

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_data_dir": self.user_data_dir,
            "session_name": self.session_name,
            "proxy_host": self.proxy_host,
            "proxy_port": self.proxy_port,
            "proxy_user": self.proxy_user,
            "proxy_password": self.proxy_password,
        }

    @staticmethod
    def from_dict(data: Dict):
        session_obj = SessionData(
            session_id=data["session_id"],
            user_data_dir=data["user_data_dir"],
            session_name=data.get("session_name"),
        )

        session_obj.proxy_host = data.get("proxy_host", "")
        session_obj.proxy_port = data.get("proxy_port", "")
        session_obj.proxy_user = data.get("proxy_user", "")
        session_obj.proxy_password = data.get("proxy_password", "")

        return session_obj


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.load_sessions()

    def load_sessions(self):
        if os.path.exists(SESSION_STORAGE_FILE):
            with open(SESSION_STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for session_id, session_info in data.items():
                    self.sessions[session_id] = SessionData.from_dict(session_info)
        else:
            self.sessions = {}

    def save_sessions(self):
        with open(SESSION_STORAGE_FILE, "w", encoding="utf-8") as f:
            data = {}
            for s_id, s_obj in self.sessions.items():
                data[s_id] = s_obj.to_dict()
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_session(self, base_dir="profiles") -> SessionData:
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)

        session_id = str(uuid.uuid4())[:8]
        user_data_dir = os.path.join(base_dir, f"profile_{session_id}")
        os.makedirs(user_data_dir, exist_ok=True)

        session_data = SessionData(session_id, user_data_dir)
        self.sessions[session_id] = session_data
        self.save_sessions()
        return session_data

    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            shutil.rmtree(self.sessions[session_id].user_data_dir, ignore_errors=True)
            del self.sessions[session_id]
            self.save_sessions()

    def rename_session(self, session_id: str, new_name: str):
        if session_id in self.sessions:
            self.sessions[session_id].session_name = new_name
            self.save_sessions()

    def get_session(self, session_id: str) -> Optional[SessionData]:
        return self.sessions.get(session_id)

    def list_sessions(self):
        return list(self.sessions.values())

    def set_proxy(self, session_id: str, host: str, port: str, user: str, password: str):
        if session_id in self.sessions:
            s = self.sessions[session_id]
            s.proxy_host = host
            s.proxy_port = port
            s.proxy_user = user
            s.proxy_password = password
            self.save_sessions()
