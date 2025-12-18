# 🧠 NexGen Logistics – Intelligent Order Orchestration Engine

## 📌 Project Overview
This project is an **Intelligent Order Orchestration System** built for **NexGen Logistics Pvt. Ltd.**  
It recommends the **best warehouse and vehicle combination** for an order by optimizing **cost, delay risk, distance, inventory health, and CO₂ emissions**.

The system is implemented as an **interactive Streamlit dashboard** using real-world logistics datasets.

---

## 🚀 Key Features
- 📦 Inventory-aware warehouse selection  
- 🛣️ Route feasibility & delay risk analysis  
- 🚚 Fleet-based CO₂ emission estimation  
- 🌱 Sustainability-focused decision-making  
- 📊 Interactive visual analytics (Radar, Heatmap, Gauge, Scatter)  
- ⬇️ Downloadable fulfillment report  

---

## 🧠 Decision Logic
The system uses a **Multi-Criteria Decision Analysis (MCDA)** approach.

### Fulfillment Score Formula:
Fulfillment Score = 0.35 × Cost +0.25 × Delay Risk +0.20 × Distance +0.10 × CO₂ Emissions +0.10 × Inventory Strain


➡️ Lower score = better fulfillment option.

---

## 🧩 Tech Stack
- **Python**
- **Streamlit** (UI & Dashboard)
- **Pandas & NumPy** (Data processing)
- **Plotly** (Interactive visualizations)

---

## 📂 Datasets Used
- `orders.csv`
- `warehouse_inventory.csv`
- `routes_distance.csv`
- `vehicle_fleet.csv`
- `delivery_performance.csv`
- `cost_breakdown.csv`

(All files are placed inside the `data/` directory)

---

## ▶️ How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
