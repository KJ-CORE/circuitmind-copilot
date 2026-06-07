from agents.llm_client import call_nvidia_llm, extract_json_from_text

def run_firmware_agent(requirements: dict, components: list, connections: list) -> str:
    system_prompt = (
        "You are an embedded systems engineer.\n\n"
        "Generate complete ESP32 firmware.\n"
        "Requirements: WiFi, Firebase, RFID integration where relevant.\n"
        "Return JSON only in the following schema:\n"
        "{\n"
        '  "code": "str (the complete, compilable Arduino/ESP32 C++ code)"\n'
        "}"
    )

    user_prompt = (
        f"Requirements:\n{requirements}\n\n"
        f"Components:\n{components}\n\n"
        f"Connections:\n{connections}\n\n"
        "Ensure all library hooks and pin definitions are filled completely in standard C++."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response_text = call_nvidia_llm(messages, temperature=0.1)
    result_dict = extract_json_from_text(response_text)
    return result_dict.get("code", "")
