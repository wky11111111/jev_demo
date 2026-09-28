"""Minimal Jev demo using OpenRouter's Decisions API (Python standard library only)."""

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
DEFAULT_TICKET = "同一个订单扣了两次款，请帮我退回多扣的一笔。"


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
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        API_URL,
        data=body,
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
    except URLError as exc:
        raise RuntimeError(f"请求 OpenRouter 失败: {exc.reason}") from None
    except TimeoutError:
        raise RuntimeError("请求超时，请检查网络后再试。") from None


def main() -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("没有找到 OPENROUTER_API_KEY。请先按 README 设置环境变量。", file=sys.stderr)
        return 2

    ticket = input(f"输入一条工单，直接回车使用示例：\n[{DEFAULT_TICKET}]\n> ").strip()
    if not ticket:
        ticket = DEFAULT_TICKET

    try:
        result = call_jev(api_key, build_payload(ticket))
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"调用失败：{exc}", file=sys.stderr)
        return 1

    answers = result.get("answers", {})
    team = answers.get("team", {})
    refund = answers.get("refund_intent", {})
    severity = answers.get("severity", {})

    print("\n--- Jev 判断结果 ---")
    print(f"模型快照: {result.get('model', MODEL)}")
    print(f"处理团队: {team.get('choice', '未返回')}")
    print(f"候选概率: {json.dumps(team.get('probabilities', {}), ensure_ascii=False)}")
    if "confidence" in team:
        print(f"Choice confidence: {team['confidence']}")
    print(f"退款意图为是的概率: {refund.get('noul', '未返回')}")
    print(f"问题严重程度: {severity.get('score', '未返回')}")
    print(f"严重程度分布: {json.dumps(severity.get('probabilities', {}), ensure_ascii=False)}")
    if "confidence" in severity:
        print(f"Score confidence: {severity['confidence']}")
    print(f"用量信息: {json.dumps(result.get('usage', {}), ensure_ascii=False)}")
    print("\n说明：以上是模型判断示例，不会执行退款或修改任何业务数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
