"""Local web UI and small proxy for the OpenRouter Jev Decisions API."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


HOST = "127.0.0.1"
PORT = 8765
API_URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
ROOT = Path(__file__).resolve().parent


def build_payload(ticket: str) -> dict:
    return {
        "model": MODEL,
        "state": {"customer_message": ticket},
        "questions": {
            "team": {
                "type": "choice",
                "instructions": "根据客户当前主要诉求，选择最适合处理的团队。",
                "criteria": {
                    "billing": "扣款、退款、账单或支付结果问题",
                    "technical": "产品功能故障、报错或接口集成问题",
                    "account": "登录、密码、账号资料或权限问题",
                    "other": "以上类别均不适用，或信息不足以归类",
                },
            },
            "refund_intent": {
                "type": "noul",
                "instructions": "客户是否明确要求退还已经支付的款项？",
            },
            "severity": {
                "type": "score",
                "instructions": "按对客户主要业务流程的影响评估问题严重程度。",
                "criteria": [
                    "仅有轻微问题，不影响主要功能使用",
                    "部分功能受影响，但存在可行替代办法",
                    "核心流程不可用，且没有可行替代办法",
                ],
            },
        },
    }


def call_jev(api_key: str, payload: dict) -> dict:
    request = Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter 返回 HTTP {exc.code}: {detail}") from None
    except (URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", "请求超时")
        raise RuntimeError(f"请求 OpenRouter 失败：{reason}") from None


class DemoHandler(BaseHTTPRequestHandler):
    def _json(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        body = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/decision":
            self.send_error(404)
            return
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            self._json(503, {"error": "未找到 OPENROUTER_API_KEY。请在启动服务的终端中先设置环境变量。"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 16_000:
                self._json(413, {"error": "输入内容太长，请控制在 16000 字节以内。"})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            ticket = str(data.get("ticket", "")).strip()
            if not ticket:
                self._json(400, {"error": "请先输入一条工单内容。"})
                return
            result = call_jev(api_key, build_payload(ticket))
            self._json(200, result)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": f"请求格式不正确：{exc}"})
        except RuntimeError as exc:
            self._json(502, {"error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        # Avoid writing user ticket text or headers to the terminal.
        print(f"[{self.log_date_time_string()}] {self.command} {self.path}")


if __name__ == "__main__":
    print(f"Jev Demo 已启动：http://{HOST}:{PORT}")
    print("API Key 只从当前终端的 OPENROUTER_API_KEY 环境变量读取。按 Ctrl+C 停止。")
    ThreadingHTTPServer((HOST, PORT), DemoHandler).serve_forever()
