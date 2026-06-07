from agents.llm_client import call_nvidia_llm, extract_json_from_text

def run_validation_agent(requirements: dict, components: list, connections: list, RAG_context: str = "") -> dict:
    system_prompt = (
        "Review this electronics design.\n\n"
        "Check:\n"
        "1. Power compatibility\n"
        "2. Voltage mismatch\n"
        "3. GPIO conflicts\n"
        "4. Communication conflicts\n"
        "5. Missing pull-up resistors\n\n"
        "Return JSON only in the following schema:\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "issues": "str (description of check/conflict found)",\n'
        '      "severity": "str (High, Medium, or Low)",\n'
        '      "fixes": "str (proposed correction action)"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"Requirements:\n{requirements}\n\n"
        f"Components:\n{components}\n\n"
        f"Connections:\n{connections}\n\n"
        f"Datasheet RAG Reference Context:\n{RAG_context}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response_text = call_nvidia_llm(messages, temperature=0.0)
    return extract_json_from_text(response_text)
