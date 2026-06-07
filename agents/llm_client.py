import json
import re
import sys
from openai import OpenAI
from app.config import settings

def safe_print(text: str, end: str = "\n", flush: bool = True):
    try:
        enc = sys.stdout.encoding or "utf-8"
        sys.stdout.buffer.write((text + end).encode(enc, errors="replace"))
        if flush:
            sys.stdout.flush()
    except Exception:
        try:
            print(text, end=end, flush=flush)
        except Exception:
            pass

def get_nvidia_client() -> OpenAI:
    return OpenAI(
        base_url=settings.nvidia_base_url,
        api_key=settings.openai_api_key
    )

def call_nvidia_llm(messages: list, temperature: float = 0.2, stream: bool = True) -> str:
    client = get_nvidia_client()

    payload = {
        "model": settings.nvidia_model,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": 16384,
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 2048
        },
        "stream": stream
    }

    full_content = []

    if stream:
        safe_print("\n=== Model Thinking Process ===")
        completion = client.chat.completions.create(**payload)
        for chunk in completion:
            if not chunk.choices:
                continue

            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
            if reasoning:
                safe_print(reasoning, end="", flush=True)

            content = chunk.choices[0].delta.content
            if content is not None:
                safe_print(content, end="", flush=True)
                full_content.append(content)
        safe_print("\n=== Thinking Finished ===\n")
        return "".join(full_content)
    else:
        payload["stream"] = False
        completion = client.chat.completions.create(**payload)
        return completion.choices[0].message.content

def extract_json_from_text(text: str) -> dict:
    try:
        return json.loads(text.strip(), strict=False)
    except Exception:
        pass

    matches = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text))
    if matches:
        for match in reversed(matches):
            try:
                return json.loads(match.group(1).strip(), strict=False)
            except Exception:
                pass

    for i in range(len(text) - 1, -1, -1):
        if text[i] == '}':
            brace_count = 0
            for j in range(i, -1, -1):
                if text[j] == '}':
                    brace_count += 1
                elif text[j] == '{':
                    brace_count -= 1
                    if brace_count == 0:
                        candidate = text[j:i+1].strip()
                        try:
                            return json.loads(candidate, strict=False)
                        except Exception:
                            break

    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1:
        try:
            return json.loads(text[start_idx:end_idx + 1].strip(), strict=False)
        except Exception:
            pass

    try:
        return json.loads(text.strip(), strict=False)
    except json.JSONDecodeError as e:
        safe_print(f"[JSON Parser] Error parsing JSON string: {e}\nRaw String: {text}")
        raise e
