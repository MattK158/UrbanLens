# UrbanLens

> **Explore Austin like you live there — or like you're about to.**

UrbanLens is a full-stack urban data platform that transforms millions of raw City of Austin records into an interactive map dashboard. Visualize crime trends, 311 complaints, building permits, traffic incidents, and EMS response times — by neighborhood, over time, side by side.

Built for current residents who want to understand their city, and prospective residents who want to know where to live.

**[Live Demo →](https://urbanlens.io)** &nbsp;|&nbsp; **[Technical Design Document →](./DESIGN.md)**

---

![UrbanLens Dashboard](./docs/screenshot.png)

---

## Features

- **Interactive Map** — Heatmap and point-cluster views across 5 live datasets, rendered with Mapbox GL (WebGL) for smooth performance over millions of data points
- **Neighborhood Detail Panel** — Click any neighborhood to see stats, trends, and your UrbanLens Score breakdown
- **Neighborhood Comparison** — Pick two neighborhoods and compare them side by side — built for the "East Austin vs. South Congress" decision
- **UrbanLens Neighborhood Score** — A proprietary 0–100 composite score per neighborhood, weighted across safety, infrastructure, emergency response, and development activity. Full methodology in the [design doc](./DESIGN.md#9-urbanlens-neighborhood-score)
- **Time Range Filtering** — Filter all data to any window: last 30 days, 90 days, 12 months, or all time
- **Trend Charts** — Monthly volume charts with 3-month moving average for any dataset and neighborhood
- **Auto-Refreshing Data** — Ingestion pipeline pulls fresh data from the City of Austin API every 6 hours

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Mapbox GL JS (react-map-gl), Recharts |
| Backend | Python 3.11, FastAPI, SQLAlchemy, APScheduler |
| Database | PostgreSQL 15 + PostGIS |
| Deployment | AWS EC2, AWS RDS, AWS S3, CloudFront, Nginx |
| Data Source | City of Austin Open Data Portal (Socrata API) |

---

## Architecture Overview

```
React Frontend  →  FastAPI Backend  →  PostgreSQL + PostGIS
                        ↑
              APScheduler (every 6hrs)
                        ↑
          Austin Open Data Portal (Socrata API)
```

See the full system architecture, database schema, API design, and technical decision rationale in the **[Design Document](./DESIGN.md)**.

---

## Data Sources

All data is sourced from the [City of Austin Open Data Portal](https://data.austintexas.gov) via the Socrata SODA API. Datasets are refreshed every 6 hours via a scheduled ingestion pipeline.

| Dataset | Records | Refresh |
|---|---|---|
| 311 Unified Service Requests | 2M+ | Daily |
| Crime Reports | 500K+ | Weekly |
| Building Permits | 300K+ | Daily |
| Traffic Incidents | 1M+ | Daily |
| EMS Incident Responses | 400K+ | Monthly |

---

## Running Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 with PostGIS extension
- A free [Mapbox API token](https://mapbox.com)

### 1. Clone the repo

```bash
git clone https://github.com/Mattk158/urbanlens.git
cd urbanlens
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

```env
DATABASE_URL=postgresql://user:password@localhost:5432/urbanlens
AUSTIN_API_APP_TOKEN=your_socrata_app_token
```

Run database migrations and seed neighborhood boundaries:

```bash
python scripts/init_db.py
python scripts/seed_neighborhoods.py
```

Run the initial data ingestion (this will take a few minutes — pulling full historical data):

```bash
python scripts/ingest_all.py
```

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 3. Frontend setup

```bash
cd frontend
npm install
```

Copy the example environment file:

```bash
cp .env.example .env
```

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAPBOX_TOKEN=your_mapbox_token
```

Start the frontend:

```bash
npm start
```

App available at `http://localhost:3000`

---

## Project Structure

```
urbanlens/
├── README.md
├── DESIGN.md                   # Full technical design document
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── api/                # Route handlers
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── ingestion/          # Socrata API client + dataset ingestors
│   │   ├── scoring/            # UrbanLens Score computation engine
│   │   └── scheduler.py        # APScheduler job definitions
│   ├── scripts/
│   │   ├── init_db.py
│   │   ├── seed_neighborhoods.py
│   │   └── ingest_all.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView/
│   │   │   ├── NeighborhoodPanel/
│   │   │   ├── ComparisonView/
│   │   │   ├── TrendChartPanel/
│   │   │   └── Header/
│   │   ├── context/            # React Context + useReducer global state
│   │   ├── hooks/              # Custom React hooks
│   │   ├── api/                # API client functions
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
└── docs/
    └── screenshot.png
```

---

## UrbanLens Neighborhood Score

The score is a transparent, versioned composite index — not a black box. It combines four weighted components:

| Component | Weight | Signal |
|---|---|---|
| Safety | 40% | Crime density weighted by offense severity |
| Infrastructure | 25% | 311 complaint volume + resolution time |
| Emergency Response | 20% | Median EMS response time |
| Development | 15% | Building permit activity (growth signal) |

All scores are percentile-ranked relative to other Austin neighborhoods so they're always comparable. Full methodology, formulas, and versioning policy in the [design document](./DESIGN.md#9-urbanlens-neighborhood-score).

---

## Roadmap

- [x] Data ingestion pipeline (all 5 datasets)
- [x] UrbanLens Neighborhood Score v1.0
- [x] Interactive map with heatmap + point layers
- [x] Neighborhood detail panel
- [x] Neighborhood comparison view
- [x] Trend charts
- [x] AWS deployment
- [ ] Multi-city support (Dallas, Houston)
- [ ] User accounts + saved neighborhoods
- [ ] Anomaly detection / spike alerts
- [ ] Mobile app (React Native)
- [ ] Public score API

---

## Author

**Matthew Kelly** — Embedded Software Engineer  
[GitHub](https://github.com/Mattk158) · [LinkedIn](https://linkedin.com/in/matthewkelly) · [mattkelly872@gmail.com](mailto:mattkelly872@gmail.com)

---

*Data sourced from the [City of Austin Open Data Portal](https://data.austintexas.gov). UrbanLens is an independent project and is not affiliated with the City of Austin.*
