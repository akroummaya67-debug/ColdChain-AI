from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
from fortyguard import get_surface_temperature
from agent import generate_thermal_decision

app = FastAPI(
    title="ColdChain AI Engine",
    description="Autonomous thermal routing and cooling decision backend for cold-chain logistics."
)

class RouteRequest(BaseModel):
    cargo_type: str = "Insulin Vaccines"
    max_safe_temp: float = 40.0
    primary_route_coords: List[Tuple[float, float]]
    alternative_route_coords: List[Tuple[float, float]]

def calculate_route_average(coords_list: List[Tuple[float, float]]) -> dict:
    if not coords_list:
        return {"avg_temperature": 0.0, "points_analyzed": 0}
    
    total_temp = 0.0
    for lat, lon in coords_list:
        temp = get_surface_temperature(lat, lon)
        total_temp += temp
        
    avg_temp = round(total_temp / len(coords_list), 2)
    return {
        "avg_temperature": avg_temp,
        "points_analyzed": len(coords_list)
    }

@app.get("/")
def read_root():
    return {"status": "online", "system": "ColdChain AI Engine active"}

@app.post("/analyze-route")
def analyze_route(request: RouteRequest):
    try:
        primary_analysis = calculate_route_average(request.primary_route_coords)
        alt_analysis = calculate_route_average(request.alternative_route_coords)

        primary_avg = primary_analysis["avg_temperature"]
        alt_avg = alt_analysis["avg_temperature"]

        # Rule-based decision recommendation logic
        if primary_avg <= request.max_safe_temp:
            recommendation = "PROCEED_PRIMARY"
        elif alt_avg < primary_avg and alt_avg <= request.max_safe_temp:
            recommendation = "REROUTE_RECOMMENDED"
        else:
            recommendation = "TRIGGER_PROACTIVE_COOLING"

        analysis_payload = {
            "cargo_type": request.cargo_type,
            "max_safe_temp": request.max_safe_temp,
            "primary_route": primary_analysis,
            "alternative_route": alt_analysis,
            "recommendation": recommendation
        }

        # Generate intelligent decision reasoning via LLM Agent
        ai_decision = generate_thermal_decision(analysis_payload)

        return {
            "cargo_type": request.cargo_type,
            "max_safe_temp": request.max_safe_temp,
            "primary_route": primary_analysis,
            "alternative_route": alt_analysis,
            "system_recommendation": recommendation,
            "ai_agent_decision": ai_decision
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))