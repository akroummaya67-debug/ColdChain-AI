import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Page Configuration
st.set_page_config(
    page_title="ColdChain AI | Operations Dashboard",
    page_icon="🧊",
    layout="wide"
)

st.title("🧊 ColdChain AI: Thermal Logistics Copilot")
st.write("Autonomous surface temperature routing and cargo protection engine.")

st.markdown("---")

# Session State for results
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# Comprehensive US States & Cities Preset Database
US_DATABASE = {
    "Alabama (AL)": {"Birmingham": [33.5186, -86.8104], "Montgomery": [32.3792, -86.3077]},
    "Alaska (AK)": {"Anchorage": [61.2181, -149.9003], "Juneau": [58.3019, -134.4197]},
    "Arizona (AZ)": {"Phoenix": [33.4484, -112.0740], "Tucson": [32.2226, -110.9747]},
    "Arkansas (AR)": {"Little Rock": [34.7465, -92.2896]},
    "California (CA)": {"Los Angeles": [33.7405, -118.2728], "San Francisco": [37.7749, -122.4194], "San Diego": [32.7157, -117.1611], "Sacramento": [38.5816, -121.4944]},
    "Colorado (CO)": {"Denver": [39.7392, -104.9903]},
    "Florida (FL)": {"Miami": [25.7617, -80.1918], "Orlando": [28.5383, -81.3792], "Tampa": [27.9506, -82.4572]},
    "Georgia (GA)": {"Atlanta": [33.7490, -84.3880]},
    "Illinois (IL)": {"Chicago": [41.8781, -87.6298]},
    "Nevada (NV)": {"Las Vegas": [36.1699, -115.1398], "Reno": [39.5296, -119.8138]},
    "New York (NY)": {"New York City": [40.7128, -74.0060], "Buffalo": [42.8864, -78.8784]},
    "Texas (TX)": {"Houston": [29.7604, -95.3698], "Dallas": [32.7767, -96.7970], "Austin": [30.2672, -97.7431]}
}

# Sidebar Controls
st.sidebar.header("📦 Cargo Specifications")
cargo_type = st.sidebar.selectbox(
    "Cargo Type",
    ["Insulin Vaccines", "Fresh Produce", "Blood Samples", "Biomedical Products"]
)
max_safe_temp = st.sidebar.number_input("Max Safe Surface Temp (°C)", value=40.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.header("📍 Route Location Selector")

location_mode = st.sidebar.radio("Location Mode", ["US Database Presets", "Custom US Coords/City"])

if location_mode == "US Database Presets":
    selected_state = st.sidebar.selectbox("Select US State", list(US_DATABASE.keys()))
    available_cities = list(US_DATABASE[selected_state].keys())
    selected_city = st.sidebar.selectbox("Select City", available_cities)
    
    base_lat, base_lon = US_DATABASE[selected_state][selected_city]
    origin_coords = [base_lat, base_lon]
    destination_coords = [round(base_lat + 0.02, 4), round(base_lon + 0.02, 4)]
    alt_coords = [round(base_lat - 0.015, 4), round(base_lon + 0.03, 4)]
else:
    selected_state = "Custom State"
    selected_city = st.sidebar.text_input("Enter US City Name", "Miami, FL")
    origin_coords = [25.7617, -80.1918]
    destination_coords = [25.7800, -80.1700]
    alt_coords = [25.7500, -80.2000]

# Trigger Analysis
if st.sidebar.button("Run AI Thermal Analysis", type="primary", use_container_width=True):
    try:
        primary_route = [origin_coords, destination_coords]
        alternative_route = [origin_coords, alt_coords]

        with st.spinner("Fetching FortyGuard surface heat data & evaluating AI decision..."):
            from fortyguard import get_surface_temperature
            from agent import generate_thermal_decision

            primary_temp = get_surface_temperature(primary_route[1][0], primary_route[1][1])
            alt_temp = get_surface_temperature(alternative_route[1][0], alternative_route[1][1])

            primary_data = {"avg_temperature": primary_temp}
            alt_data = {"avg_temperature": alt_temp}

            # تحديد التوصية الافتراضية بناءً على مقارنة الحرارة
            recommendation = "TRIGGER_PROACTIVE_COOLING" if primary_temp > max_safe_temp else "PROCEED_PRIMARY"

            agent_input = {
                "cargo_type": cargo_type,
                "max_safe_temp": max_safe_temp,
                "primary_route": primary_data,
                "alternative_route": alt_data,
                "recommendation": recommendation
            }

            ai_decision = generate_thermal_decision(agent_input)

            response_json = {
                "cargo_type": cargo_type,
                "max_safe_temp": max_safe_temp,
                "primary_route": primary_data,
                "alternative_route": alt_data,
                "ai_agent_decision": ai_decision
            }

            st.session_state.analysis_result = {
                "data": response_json,
                "primary": primary_route,
                "alt": alternative_route,
                "city": selected_city,
                "state": selected_state
            }

    except Exception as e:
        st.error(f"Analysis Execution Error. Details: {e}")

# Main Display Logic
if st.session_state.analysis_result:
    res = st.session_state.analysis_result
    data = res["data"]
    primary = res["primary"]
    alt = res["alt"]
    
    st.success(f"Thermal Route Analysis Completed for **{res['city']} ({res['state']})**")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cargo Threshold", f"{data['max_safe_temp']} °C")
    m2.metric("Primary Route Avg Heat", f"{data['primary_route']['avg_temperature']} °C")
    m3.metric("Alternative Route Avg Heat", f"{data['alternative_route']['avg_temperature']} °C")
    m4.metric("Thermal Risk Status", "HIGH" if data['primary_route']['avg_temperature'] > data['max_safe_temp'] else "SAFE")

    st.markdown("---")

    col_map, col_agent = st.columns([2, 1])

    with col_map:
        st.subheader("🗺️ Realistic GIS Navigation Map")
        m = folium.Map(location=primary[0], zoom_start=12, tiles="OpenStreetMap")

        folium.Marker(primary[0], popup="Start: Origin", icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(primary[1], popup="End: Primary Destination", icon=folium.Icon(color="red", icon="flag")).add_to(m)
        folium.Marker(alt[1], popup="End: Safe Alternative Destination", icon=folium.Icon(color="blue", icon="shield")).add_to(m)

        folium.PolyLine(primary, color="red", weight=5, opacity=0.8, tooltip="Primary Route").add_to(m)
        folium.PolyLine(alt, color="blue", weight=5, opacity=0.8, dash_array='5, 10', tooltip="Alternative Safe Route").add_to(m)

        st_folium(m, width=700, height=420, key="clear_logistics_map")

    with col_agent:
        st.subheader("🤖 AI Agent Recommendation")
        ai_data = data.get("ai_agent_decision", {})
        action_code = ai_data.get("action", "N/A")

        if action_code == "TRIGGER_PROACTIVE_COOLING":
            st.error(f"**Action Triggered:** PROACTIVE COOLING")
            st.caption("Street surface heat exceeds safe limit. Increased truck refrigeration power.")
        elif action_code == "REROUTE_RECOMMENDED":
            st.warning(f"**Action Triggered:** DYNAMIC REROUTING")
            st.caption("Diverting cargo path to cooler alternative corridor.")
        else:
            st.success(f"**Status:** NORMAL OPERATIONS")
            st.caption("Road surface conditions are within safe thermal bounds.")

        st.markdown("**LLM Reasoning:**")
        st.info(ai_data.get('reasoning'))

        with st.expander("View Raw API Payload"):
            st.json(data)
