from agents.llm_client import call_nvidia_llm, extract_json_from_text

def run_component_agent(requirements: dict) -> dict:
    system_prompt = (
        "You are an electronics design engineer.\n\n"
        "Given system requirements, recommend components.\n"
        "Return JSON only in the following schema:\n"
        "{\n"
        '  "components": [\n'
        "    {\n"
        '      "name": "str (component model name)",\n'
        '      "reason": "str (reason for recommendation)",\n'
        '      "datasheet_keywords": ["str (keywords for datasheet search)"]\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = f"System Requirements:\n{requirements}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response_text = call_nvidia_llm(messages, temperature=0.2)
    return extract_json_from_text(response_text)
