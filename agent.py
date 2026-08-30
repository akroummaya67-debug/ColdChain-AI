import os
import json
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_thermal_decision(analysis_data: dict) -> dict:
    """
    Evaluates thermal analysis data using Groq LLM to issue autonomous logistical guidance.
    """
    cargo = analysis_data.get("cargo_type", "Sensitive Cargo")
    max_safe = analysis_data.get("max_safe_temp", 40.0)
    primary_avg = analysis_data.get("primary_route", {}).get("avg_temperature", 0.0)
    alt_avg = analysis_data.get("alternative_route", {}).get("avg_temperature", 0.0)
    recommendation = analysis_data.get("recommendation", "PROCEED_PRIMARY")

    system_prompt = (
        "You are ColdChain AI's autonomous thermal logistics copilot. "
        "Analyze street temperature heat risk data for pharmaceutical/perishable deliveries. "
        "Provide a concise, professional explanation and clear operational guidance."
    )

    user_prompt = f"""
    Delivery Route Analysis:
    - Cargo Type: {cargo}
    - Max Safe Threshold: {max_safe}°C
    - Primary Route Avg Asphalt Temp: {primary_avg}°C
    - Alternative Route Avg Asphalt Temp: {alt_avg}°C
    - System Recommended Action: {recommendation}

    Respond ONLY in valid JSON format with two fields:
    1. "action": The action code (PROCEED_PRIMARY, REROUTE_RECOMMENDED, or TRIGGER_PROACTIVE_COOLING)
    2. "reasoning": A 2-sentence executive explanation of the thermal risk and why this decision protects the cargo.
    """

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        decision_json = json.loads(response.choices[0].message.content)
        return decision_json

    except Exception as e:
        return {
            "action": recommendation,
            "reasoning": f"Automated fallback triggered: Primary route surface temp ({primary_avg}°C) exceeds cargo threshold ({max_safe}°C)."
        }

if __name__ == "__main__":
    sample_data = {
        "cargo_type": "Insulin Vaccines",
        "max_safe_temp": 40.0,
        "primary_route": {"avg_temperature": 42.0},
        "alternative_route": {"avg_temperature": 42.0},
        "recommendation": "TRIGGER_PROACTIVE_COOLING"
    }
    
    result = generate_thermal_decision(sample_data)
    print("\n--- AI Agent Decision Output ---")
    print(json.dumps(result, indent=2))