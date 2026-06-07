from agents.llm_client import call_nvidia_llm, extract_json_from_text

def run_requirement_agent(prompt: str) -> dict:
    system_prompt = (
        "Extract electronics requirements. Return JSON only.\n"
        "Do not include any chat wrapper or conversational text.\n"
        "Return a JSON object with the following fields:\n"
        "{\n"
        '  "microcontroller": "str (microcontroller/board recommended/required)",\n'
        '  "sensors": ["str (list of required sensors)"],\n'
        '  "actuators": ["str (list of required actuators)"],\n'
        '  "communication": ["str (list of communication protocols)"],\n'
        '  "power": "str (power requirements)",\n'
        '  "cloud_services": ["str (list of cloud services)"],\n'
        '  "features": ["str (list of high-level features)"]\n'
        "}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response_text = call_nvidia_llm(messages, temperature=0.1)
    return extract_json_from_text(response_text)
