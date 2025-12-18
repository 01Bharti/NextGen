import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="NexGen Order Orchestration", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    # Assuming files exist in the 'data/' directory as per your snippet
    orders = pd.read_csv("data/orders.csv")
    warehouse = pd.read_csv("data/warehouse_inventory.csv")
    routes = pd.read_csv("data/routes_distance.csv")
    fleet = pd.read_csv("data/vehicle_fleet.csv")
    delivery = pd.read_csv("data/delivery_performance.csv")
    costs = pd.read_csv("data/cost_breakdown.csv")
    return orders, warehouse, routes, fleet, delivery, costs

try:
    orders, warehouse, routes, fleet, delivery, costs = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --------------------------------
# STANDARDIZE COLUMN NAMES
# --------------------------------
def clean_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df

orders = clean_columns(orders)
warehouse = clean_columns(warehouse)
routes = clean_columns(routes)
fleet = clean_columns(fleet)
delivery = clean_columns(delivery)
costs = clean_columns(costs)

# --------------------------------
# PRE-PROCESSING
# --------------------------------
cost_columns = [col for col in costs.columns if col.endswith("_inr") and col != "order_id"]
costs["total_cost"] = costs[cost_columns].sum(axis=1)

weather_mapping = {"low": 1, "medium": 2, "high": 3, "severe": 4}
if "weather_impact" in routes.columns:
    routes["weather_impact"] = (
        routes["weather_impact"]
        .astype(str)
        .str.lower()
        .map(weather_mapping)
        .fillna(0)
    )

routes["traffic_delay_minutes"] = pd.to_numeric(routes["traffic_delay_minutes"], errors="coerce").fillna(0)

# Merge Datasets
routes = routes.merge(
    delivery[["order_id", "delivery_status", "promised_delivery_days", "actual_delivery_days", "delivery_cost_inr"]],
    on="order_id", how="left"
)
routes = routes.merge(costs[["order_id", "total_cost"]], on="order_id", how="left")
routes["total_cost"] = routes["total_cost"].fillna(routes["total_cost"].median())
routes.fillna(0, inplace=True)

def normalize(col):
    return (col - col.min()) / (col.max() - col.min() + 1e-6)

# -----------------------------
# SIDEBAR – ORDER SIMULATOR
# -----------------------------
st.sidebar.title("📦 Order Simulator")

product = st.sidebar.selectbox("Product Category", orders["product_category"].unique())
priority = st.sidebar.selectbox("Delivery Priority", ["Express", "Standard", "Economy"])
destination = st.sidebar.selectbox("Destination City", orders["destination"].unique())
submit = st.sidebar.button("🔍 Find Best Fulfillment Option")

# -----------------------------
# MAIN DASHBOARD
# -----------------------------
st.title("🧠 Intelligent Order Orchestration Engine")
st.markdown("This system dynamically selects the **best warehouse + vehicle combination** by balancing cost, delay risk, distance, inventory, and CO₂.")

if submit:
    # 1. Filter Warehouses
    available_wh = warehouse[
        (warehouse["product_category"] == product) & 
        (warehouse["current_stock_units"] > warehouse["reorder_level"])
    ]

    if available_wh.empty:
        st.error("❌ No warehouse has sufficient stock for this product.")
        st.stop()

    # 2. Filter Routes
    route_data = routes[routes["route"].str.contains(destination, case=False, na=False)]
    if route_data.empty:
        st.warning("⚠️ No matching route found for selected destination.")
        st.stop()

    # 3. Build Options
    avg_distance = route_data["distance_km"].mean()
    avg_traffic = route_data["traffic_delay_minutes"].mean()
    avg_weather = route_data["weather_impact"].mean()
    avg_cost = route_data["total_cost"].mean()

    options = []
    for _, wh in available_wh.iterrows():
        for _, v in fleet.iterrows():
            options.append({
                "warehouse": wh["location"],
                "vehicle": v["vehicle_type"],
                "distance_km": avg_distance,
                "traffic_delay_minutes": avg_traffic,
                "weather_impact": avg_weather,
                "fuel_efficiency": v["fuel_efficiency_km_per_l"],
                "co2": v["co2_emissions_kg_per_km"] * avg_distance,
                "cost": avg_cost,
                "inventory_health": wh["current_stock_units"] - wh["reorder_level"]
            })

    options_df = pd.DataFrame(options)

    # 4. Scoring Engine
    options_df["cost_n"] = normalize(options_df["cost"])
    options_df["delay_risk"] = normalize(options_df["traffic_delay_minutes"] + options_df["weather_impact"])
    options_df["distance_n"] = normalize(options_df["distance_km"])
    options_df["co2_n"] = normalize(options_df["co2"])
    options_df["inventory_n"] = 1 - normalize(options_df["inventory_health"])

    options_df["fulfillment_score"] = (
        0.35 * options_df["cost_n"] + 0.25 * options_df["delay_risk"] +
        0.20 * options_df["distance_n"] + 0.10 * options_df["co2_n"] + 0.10 * options_df["inventory_n"]
    )

    best_option = options_df.sort_values("fulfillment_score").iloc[0]

    # --- KPI DISPLAY ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Recommended Warehouse", best_option["warehouse"])
    col2.metric("Vehicle Type", best_option["vehicle"])
    col3.metric("Estimated CO₂ (kg)", round(best_option["co2"], 2))

    st.divider()

    # --- NEW VISUALIZATIONS ---
    
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("🕸️ Strategy Analysis")
        # 
        radar_data = pd.DataFrame(dict(
            r=[best_option["cost_n"], best_option["delay_risk"], 
               best_option["distance_n"], best_option["co2_n"], best_option["inventory_n"]],
            theta=['Cost', 'Delay Risk', 'Distance', 'CO2', 'Inventory Strain']
        ))
        fig_radar = px.line_polar(radar_data, r='r', theta='theta', line_close=True)
        fig_radar.update_traces(fill='toself')
        st.plotly_chart(fig_radar, use_container_width=True)

    with row1_col2:
        st.subheader("🔋 Inventory Status")
        rec_wh_data = available_wh[available_wh["location"] == best_option["warehouse"]].iloc[0]
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rec_wh_data["current_stock_units"],
            title={'text': f"Units in {best_option['warehouse']}"},
            gauge={'axis': {'range': [0, rec_wh_data["current_stock_units"] * 1.5]},
                   'steps': [{'range': [0, rec_wh_data["reorder_level"]], 'color': "red"}],
                   'threshold': {'line': {'color': "black", 'width': 4}, 'value': rec_wh_data["reorder_level"]}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("🌱 Sustainability & Efficiency")
        fig_env = px.scatter(
            options_df, x="fuel_efficiency", y="co2", size="distance_km", color="vehicle",
            hover_name="warehouse", title="Fuel Efficiency vs. Carbon Footprint"
        )
        st.plotly_chart(fig_env, use_container_width=True)

    with row2_col2:
        st.subheader("⛈️ Route Reliability Heatmap")
        heatmap_data = options_df.pivot_table(index='warehouse', columns='vehicle', values='delay_risk')
        fig_heat = px.imshow(heatmap_data, color_continuous_scale='Reds', title="Risk Exposure (Red = High)")
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- EXISTING TABLES ---
    st.subheader("📋 Full Fulfillment Options Comparison")
    st.dataframe(options_df.sort_values("fulfillment_score"), use_container_width=True)

    st.download_button(
        "⬇️ Download Fulfillment Analysis",
        options_df.to_csv(index=False),
        "fulfillment_options.csv"
    )