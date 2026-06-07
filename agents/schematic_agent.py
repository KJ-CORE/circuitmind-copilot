from agents.llm_client import call_nvidia_llm, extract_json_from_text

def run_schematic_agent(requirements: dict, components: list) -> dict:
    system_prompt = (
        "You are a senior hardware design engineer. Your task is to design a detailed wiring diagram "
        "and connection map between the microcontroller and recommended peripheral components.\n"
        "Return JSON only in the following schema:\n"
        "{\n"
        '  "connections": [\n'
        "    {\n"
        '      "from_component": "str (source device name)",\n'
        '      "from_pin": "str (source pin designation)",\n'
        '      "to_component": "str (destination device name)",\n'
        '      "to_pin": "str (destination pin designation)",\n'
        '      "connection_type": "str (type of wire connection e.g. Power, Ground, I2C, SPI, GPIO)"\n'
        "    }\n"
        "  ],\n"
        '  "explanation": "str (engineering explanation of the wiring decisions)"\n'
        "}"
    )

    user_prompt = f"Requirements:\n{requirements}\n\nComponents:\n{components}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response_text = call_nvidia_llm(messages, temperature=0.2)
    return extract_json_from_text(response_text)
