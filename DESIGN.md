# UrbanLens — Technical Design Document

**Author:** Matthew Kelly  
**Version:** 1.0  
**Status:** In Progress  
**Last Updated:** 2026  
**Repository:** github.com/Mattk158/urbanlens

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Target Users](#3-target-users)
4. [Goals & Non-Goals](#4-goals--non-goals)
5. [Feature Specification](#5-feature-specification)
6. [System Architecture](#6-system-architecture)
7. [Data Sources & Ingestion Pipeline](#7-data-sources--ingestion-pipeline)
8. [Database Design](#8-database-design)
9. [UrbanLens Neighborhood Score](#9-urbanlens-neighborhood-score)
10. [API Design](#10-api-design)
11. [Frontend Architecture](#11-frontend-architecture)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Technical Decisions & Tradeoffs](#13-technical-decisions--tradeoffs)
14. [MVP Scope & Milestones](#14-mvp-scope--milestones)
15. [Future Enhancements](#15-future-enhancements)

---

## 1. Project Overview

**UrbanLens** is a full-stack urban data exploration platform that makes Austin, Texas city data accessible, visual, and actionable for everyday people. It ingests real datasets from the City of Austin's open data portal, processes them into a structured database, and surfaces them through an interactive map dashboard with trend charts, neighborhood breakdowns, and a proprietary composite safety and livability score.

The stack is Python (FastAPI) on the backend, React with Mapbox GL on the frontend, PostgreSQL with PostGIS for geospatial data storage, and AWS EC2 for deployment. Data is refreshed automatically on a scheduled interval so the platform always reflects current city conditions.

---

## 2. Problem Statement

Austin is one of the fastest-growing cities in the United States, adding tens of thousands of new residents each year. Despite this, the data that describes the city — crime reports, 311 service requests, construction permits, traffic incidents, emergency response records — is buried in raw spreadsheet downloads on a government portal that most people will never find, let alone be able to interpret.

For a current resident trying to understand their neighborhood, or a prospective resident trying to decide where to live, this data is genuinely valuable. But in its current form it is completely inaccessible. There is no way to visualize trends over time, compare neighborhoods against each other, or derive any meaningful signal from the raw numbers without downloading files and manipulating them manually.

UrbanLens solves this by acting as a translation layer between raw government data and human understanding — turning millions of rows of city records into a live, interactive map that anyone can use.

---

## 3. Target Users

### 3.1 Current Austin Residents

People who live in Austin and want a deeper understanding of what is happening in their neighborhood and across the city. This user wants to answer questions like: Are 311 complaint response times getting worse in my area? Has crime trended up or down in my zip code over the past year? Where is the most construction activity right now?

**Key needs:** Neighborhood-level granularity, time-series trends, ability to filter and explore freely.

### 3.2 Prospective Residents

People considering a move to Austin who want to evaluate different neighborhoods before committing. This user is comparing areas they don't know personally and wants objective data to inform their decision. They want to answer questions like: Which areas have the lowest crime rates? Where are neighborhoods improving vs. declining? What does the safety score look like in the areas I'm considering?

**Key needs:** Easy neighborhood comparison, clear scores and rankings, approachable UI that doesn't require data literacy.

---

## 4. Goals & Non-Goals

### Goals

- Ingest and store real Austin city datasets totaling millions of records
- Provide an interactive map visualization with multiple data layers
- Compute a UrbanLens Neighborhood Score — a proprietary composite livability metric per neighborhood
- Support neighborhood-level comparison between two areas side by side
- Auto-refresh data on a scheduled basis so the platform stays current
- Deploy to a live URL accessible to anyone
- Perform well under reasonable load with indexed queries and efficient API responses

### Non-Goals

- This is not a real-time streaming application — data refreshes on a schedule, not instantly
- This is not a predictive model — the score reflects current and historical data, not future forecasts
- This does not cover cities outside Austin in the MVP
- This is not a social platform — there are no user accounts, saved searches, or community features in V1
- This does not replace official city services or provide legally actionable information

---

## 5. Feature Specification

### 5.1 Interactive Map

The core of the application. A full-viewport map of Austin rendered with Mapbox GL JS, supporting the following interactions:

- **Layer selection:** User can toggle between datasets — 311 Service Requests, Crime Incidents, Building Permits, Traffic Incidents, EMS Response Times
- **Heatmap mode:** Dense point data rendered as a heatmap to surface concentration patterns
- **Point mode:** Individual incidents rendered as clustered markers with click-to-detail popover
- **Neighborhood overlay:** Austin neighborhood boundaries rendered as a polygon layer, highlighting on hover
- **Click to inspect:** Clicking a neighborhood opens the Neighborhood Detail Panel

### 5.2 Date Range Filter

A date range picker in the top toolbar allowing users to filter all displayed data to a specific time window. Default view is the trailing 90 days. Supports presets: Last 30 days, Last 90 days, Last 12 months, All time.

### 5.3 Neighborhood Detail Panel

A slide-in side panel triggered by clicking any neighborhood on the map. Contains:

- Neighborhood name and total area
- UrbanLens Neighborhood Score with breakdown by category
- Per-dataset stats for the selected time window: total incidents, trend direction (up/down vs. prior period), incidents per 1,000 residents
- A mini trend chart showing monthly volume over the past 12 months
- A rank relative to all Austin neighborhoods (e.g. "12th safest of 74 neighborhoods")

### 5.4 Neighborhood Comparison Mode

A dedicated view allowing the user to select two neighborhoods and compare them side by side. Displays both Neighborhood Detail Panels simultaneously with a visual diff highlighting which neighborhood scores higher in each category. Designed specifically for the prospective resident use case — "help me decide between East Austin and South Congress."

### 5.5 UrbanLens Neighborhood Score

A single composite score from 0–100 assigned to each neighborhood, updated on each data refresh. Detailed methodology described in Section 9.

### 5.6 Trend Charts

A bottom panel displaying time-series charts for the currently active dataset and selected neighborhood or city-wide view. Built with Recharts. Shows monthly aggregated volume with a 3-month moving average overlay to smooth noise.

### 5.7 Data Freshness Indicator

A small indicator in the UI showing when each dataset was last refreshed from the Austin open data portal. Keeps the platform honest about data recency.

---

## 6. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        CLIENT                           │
│              React + Mapbox GL + Recharts               │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / REST
┌──────────────────────▼──────────────────────────────────┐
│                    BACKEND (AWS EC2)                     │
│                  FastAPI (Python 3.11)                   │
│                                                         │
│   ┌─────────────┐    ┌──────────────┐    ┌──────────┐  │
│   │  API Routes  │    │  Score Engine │    │Scheduler │  │
│   │  /api/v1/*  │    │  (composite   │    │(APSched) │  │
│   └──────┬──────┘    │   metrics)    │    └────┬─────┘  │
│          │           └──────┬────────┘         │        │
└──────────┼─────────────────┼──────────────────┼────────┘
           │                 │                  │
┌──────────▼─────────────────▼──────────────────▼────────┐
│               PostgreSQL + PostGIS (EC2-hosted PostgreSQL)            │
│                                                         │
│   incidents │ permits │ ems │ traffic │ neighborhoods   │
│   scores    │ ingestion_log │ aggregates                │
└─────────────────────────────────┬───────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────┐
│              Austin Open Data Portal (Socrata API)       │
│   data.austintexas.gov — scheduled pull every 6 hours   │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**React Frontend** — All UI rendering, map interactions, chart display, and user input. Communicates exclusively with the FastAPI backend via REST. No direct database or external API access from the client.

**FastAPI Backend** — Serves all API endpoints, runs the scheduled ingestion jobs, executes the score computation engine, and manages all database interactions via SQLAlchemy ORM.

**Score Engine** — A standalone Python module within the backend responsible for computing and persisting neighborhood scores. Runs after each ingestion cycle completes.

**APScheduler** — Lightweight Python job scheduler embedded in the FastAPI application. Triggers data ingestion every 6 hours and score recomputation immediately after.

**PostgreSQL + PostGIS** — Primary data store. PostGIS extension enables native geospatial queries — point-in-polygon lookups to assign incidents to neighborhoods, radius queries, bounding box filters. Hosted on EC2-hosted PostgreSQL for managed backups and reliability.

**Austin Open Data Portal** — The Socrata-based open data API provided by the City of Austin. All datasets are accessed via the SODA (Socrata Open Data API) REST interface with incremental pulls using date filters to avoid re-ingesting historical data on every run.

---

## 7. Data Sources & Ingestion Pipeline

### 7.1 Datasets

| Dataset | Source ID | Update Frequency | Est. Record Count | Key Fields |
|---|---|---|---|---|
| 311 Unified Service Requests | `i26j-ai4z` | Daily | 2M+ | complaint type, lat/lng, opened date, closed date, status |
| Crime Reports | `fdj4-gpfu` | Weekly | 500K+ | offense type, category, lat/lng, occurred date |
| Building Permits | `3syk-w9eu` | Daily | 300K+ | permit type, address, lat/lng, issue date, value |
| Traffic Incidents | `r3af-2r8x` | Daily | 1M+ | incident type, lat/lng, published date |
| EMS Incident Responses | `7pas-4e5n` | Monthly | 400K+ | problem description, lat/lng, response time, unit |

### 7.2 Ingestion Strategy

Each dataset uses an **incremental ingestion** strategy. On first run, full historical data is pulled and stored. On subsequent runs, only records newer than the last successfully ingested timestamp are fetched. This keeps API calls small and fast.

```
Ingestion Run:
  1. Check ingestion_log for last_ingested_at per dataset
  2. Build SODA query with WHERE clause: updated_date > last_ingested_at
  3. Paginate through results (1000 records per page)
  4. Validate each record: required fields present, lat/lng in Austin bounding box
  5. Perform point-in-polygon lookup to assign neighborhood_id
  6. Upsert into target table (insert or update on unique constraint)
  7. Update ingestion_log with new timestamp and record count
  8. Trigger score recomputation
```

### 7.3 Data Validation

Before any record is persisted, it passes through a validation layer:

- Coordinates must fall within the Austin bounding box (lat 30.098°N–30.516°N, lng 97.928°W–97.562°W)
- Required fields must be non-null (incident type, date, coordinates)
- Dates must be parseable and not in the future
- Numeric fields (response times, permit values) must be positive
- Records failing validation are logged to a `rejected_records` table with the failure reason — they are not silently dropped

---

## 8. Database Design

### 8.1 Schema Overview

```sql
-- Neighborhood boundaries (loaded once from GeoJSON)
CREATE TABLE neighborhoods (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    slug            VARCHAR(100) NOT NULL UNIQUE,
    boundary        GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    area_sq_miles   DECIMAL(8,4),
    population      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 311 service requests
CREATE TABLE service_requests (
    id              SERIAL PRIMARY KEY,
    source_id       VARCHAR(50) UNIQUE NOT NULL,
    complaint_type  VARCHAR(200),
    category        VARCHAR(100),
    location        GEOMETRY(POINT, 4326),
    neighborhood_id INTEGER REFERENCES neighborhoods(id),
    opened_at       TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    status          VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Crime incidents
CREATE TABLE crime_incidents (
    id              SERIAL PRIMARY KEY,
    source_id       VARCHAR(50) UNIQUE NOT NULL,
    offense_type    VARCHAR(200),
    category        VARCHAR(100),
    severity        VARCHAR(50),
    location        GEOMETRY(POINT, 4326),
    neighborhood_id INTEGER REFERENCES neighborhoods(id),
    occurred_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Building permits
CREATE TABLE building_permits (
    id              SERIAL PRIMARY KEY,
    source_id       VARCHAR(50) UNIQUE NOT NULL,
    permit_type     VARCHAR(200),
    work_type       VARCHAR(100),
    location        GEOMETRY(POINT, 4326),
    neighborhood_id INTEGER REFERENCES neighborhoods(id),
    issued_at       TIMESTAMPTZ,
    permit_value    DECIMAL(14,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Traffic incidents
CREATE TABLE traffic_incidents (
    id              SERIAL PRIMARY KEY,
    source_id       VARCHAR(50) UNIQUE NOT NULL,
    incident_type   VARCHAR(200),
    location        GEOMETRY(POINT, 4326),
    neighborhood_id INTEGER REFERENCES neighborhoods(id),
    occurred_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- EMS responses
CREATE TABLE ems_incidents (
    id                  SERIAL PRIMARY KEY,
    source_id           VARCHAR(50) UNIQUE NOT NULL,
    problem_description VARCHAR(200),
    location            GEOMETRY(POINT, 4326),
    neighborhood_id     INTEGER REFERENCES neighborhoods(id),
    occurred_at         TIMESTAMPTZ,
    response_time_secs  INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Computed neighborhood scores (refreshed each ingestion cycle)
CREATE TABLE neighborhood_scores (
    id                      SERIAL PRIMARY KEY,
    neighborhood_id         INTEGER REFERENCES neighborhoods(id),
    computed_at             TIMESTAMPTZ DEFAULT NOW(),
    overall_score           DECIMAL(5,2),
    safety_score            DECIMAL(5,2),
    infrastructure_score    DECIMAL(5,2),
    emergency_response_score DECIMAL(5,2),
    development_score       DECIMAL(5,2),
    score_version           VARCHAR(20) DEFAULT '1.0'
);

-- Pre-aggregated monthly stats per neighborhood per dataset (for fast chart queries)
CREATE TABLE monthly_aggregates (
    id                  SERIAL PRIMARY KEY,
    neighborhood_id     INTEGER REFERENCES neighborhoods(id),
    dataset             VARCHAR(50) NOT NULL,
    year                INTEGER NOT NULL,
    month               INTEGER NOT NULL,
    record_count        INTEGER DEFAULT 0,
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(neighborhood_id, dataset, year, month)
);

-- Ingestion run log
CREATE TABLE ingestion_log (
    id                  SERIAL PRIMARY KEY,
    dataset             VARCHAR(50) NOT NULL,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    records_ingested    INTEGER,
    records_rejected    INTEGER,
    last_ingested_at    TIMESTAMPTZ,
    status              VARCHAR(20)
);
```

### 8.2 Indexing Strategy

Performance for map queries requires spatial indexes and composite indexes on the most common query patterns:

```sql
-- Spatial indexes for point-in-polygon and bounding box queries
CREATE INDEX idx_service_requests_location   ON service_requests   USING GIST(location);
CREATE INDEX idx_crime_incidents_location    ON crime_incidents     USING GIST(location);
CREATE INDEX idx_building_permits_location   ON building_permits    USING GIST(location);
CREATE INDEX idx_traffic_incidents_location  ON traffic_incidents   USING GIST(location);
CREATE INDEX idx_ems_incidents_location      ON ems_incidents       USING GIST(location);
CREATE INDEX idx_neighborhoods_boundary      ON neighborhoods       USING GIST(boundary);

-- Composite indexes for time-range + neighborhood queries (most common API pattern)
CREATE INDEX idx_crime_neighborhood_date     ON crime_incidents     (neighborhood_id, occurred_at DESC);
CREATE INDEX idx_service_neighborhood_date   ON service_requests    (neighborhood_id, opened_at DESC);
CREATE INDEX idx_permits_neighborhood_date   ON building_permits    (neighborhood_id, issued_at DESC);
CREATE INDEX idx_ems_neighborhood_date       ON ems_incidents       (neighborhood_id, occurred_at DESC);
CREATE INDEX idx_traffic_neighborhood_date   ON traffic_incidents   (neighborhood_id, occurred_at DESC);

-- For fast score lookups
CREATE INDEX idx_scores_neighborhood         ON neighborhood_scores (neighborhood_id, computed_at DESC);
CREATE INDEX idx_aggregates_lookup           ON monthly_aggregates  (neighborhood_id, dataset, year, month);
```

---

## 9. UrbanLens Neighborhood Score

The UrbanLens Neighborhood Score is a composite index from 0–100 assigned to every Austin neighborhood. It is designed to be transparent, explainable, and reproducible — not a black box. Every component is documented here.

### 9.1 Score Components

The overall score is a weighted average of four sub-scores:

| Component | Weight | Description |
|---|---|---|
| Safety Score | 40% | Based on crime incident density and severity |
| Infrastructure Score | 25% | Based on 311 complaint volume and resolution time |
| Emergency Response Score | 20% | Based on EMS average response time |
| Development Score | 15% | Based on building permit activity as a growth signal |

### 9.2 Computation Methodology

Each sub-score is computed on a rolling 12-month window and normalized against all other Austin neighborhoods so scores are always relative, not absolute. A neighborhood cannot score well by being in a low-data area — minimum record thresholds are required.

**Safety Score**

Computed from crime incidents per 1,000 residents over the trailing 12 months, weighted by offense severity (violent crime weighted 3x, property crime 1x, other 0.5x). Lower raw score = higher Safety Score.

```
raw_safety = (violent_crimes * 3 + property_crimes * 1 + other_crimes * 0.5) / (population / 1000)
safety_score = 100 - percentile_rank(raw_safety) * 100
```

**Infrastructure Score**

Computed from 311 complaint density (complaints per 1,000 residents) and average days to close open complaints. Neighborhoods with fewer complaints and faster resolution score higher.

```
raw_infra = (complaint_count / (population / 1000)) * 0.6 + avg_days_to_close * 0.4
infrastructure_score = 100 - percentile_rank(raw_infra) * 100
```

**Emergency Response Score**

Computed from median EMS response time in seconds over the trailing 12 months. Lower response time = higher score.

```
raw_ems = median(response_time_secs)
emergency_response_score = 100 - percentile_rank(raw_ems) * 100
```

**Development Score**

Building permit activity is treated as a positive signal — active construction indicates investment and neighborhood growth. This is the only component where a higher raw value produces a higher score.

```
raw_dev = permit_count / (population / 1000)
development_score = percentile_rank(raw_dev) * 100
```

**Overall Score**

```
overall_score = (safety_score * 0.40) +
                (infrastructure_score * 0.25) +
                (emergency_response_score * 0.20) +
                (development_score * 0.15)
```

### 9.3 Score Versioning

The score methodology is versioned. All computed scores are stored with a `score_version` field. When the methodology changes, historical scores are preserved and the version increments. This allows the UI to show "score last computed with methodology v1.0" and ensures reproducibility.

---

## 10. API Design

All endpoints are prefixed with `/api/v1/`. Responses are JSON. The API is stateless — no authentication required for MVP.

### Endpoints

**Neighborhoods**
```
GET /api/v1/neighborhoods
  Returns list of all neighborhoods with name, slug, boundary GeoJSON, and current overall score.
  Used to render the neighborhood polygon layer on the map.

GET /api/v1/neighborhoods/{slug}
  Returns full detail for one neighborhood: all sub-scores, stats per dataset, trend data.
  Used to populate the Neighborhood Detail Panel.

GET /api/v1/neighborhoods/{slug}/compare/{slug2}
  Returns side-by-side detail for two neighborhoods.
  Used to populate the Comparison View.
```

**Map Data**
```
GET /api/v1/map/{dataset}?start={date}&end={date}&bbox={west,south,east,north}
  Returns point data for the specified dataset within the given date range and bounding box.
  Bounding box limits data to the visible map viewport for performance.
  Dataset values: service_requests | crime | permits | traffic | ems

  Response: GeoJSON FeatureCollection
```

**Trends**
```
GET /api/v1/trends/{dataset}?neighborhood={slug}&months={n}
  Returns monthly aggregated counts for the specified dataset.
  If neighborhood is omitted, returns city-wide totals.
  Used to populate trend charts.
```

**Scores**
```
GET /api/v1/scores
  Returns current UrbanLens Neighborhood Score for all neighborhoods.
  Sorted by overall score descending.

GET /api/v1/scores/{slug}
  Returns full score breakdown for one neighborhood including score history.
```

**System**
```
GET /api/v1/health
  Returns API status, database connectivity, and last ingestion timestamps per dataset.
```

### Response Format Example

```json
GET /api/v1/neighborhoods/east-austin

{
  "slug": "east-austin",
  "name": "East Austin",
  "population": 18200,
  "area_sq_miles": 4.2,
  "scores": {
    "overall": 67.4,
    "safety": 58.1,
    "infrastructure": 71.2,
    "emergency_response": 74.8,
    "development": 82.3,
    "computed_at": "2026-02-20T06:00:00Z",
    "version": "1.0"
  },
  "stats": {
    "crime_incidents_90d": 312,
    "crime_trend": "down",
    "crime_trend_pct": -8.4,
    "service_requests_90d": 891,
    "service_requests_trend": "up",
    "service_requests_trend_pct": 3.1,
    "avg_ems_response_secs": 412,
    "permits_issued_90d": 47
  },
  "rank": {
    "overall": 28,
    "of": 74
  }
}
```

---

## 11. Frontend Architecture

### 11.1 Component Tree

```
App
├── Header (dataset selector, date range picker, comparison toggle)
├── MapView
│   ├── MapboxMap (base map, neighborhood polygon layer)
│   ├── DataLayer (heatmap or clustered points for active dataset)
│   └── NeighborhoodOverlay (boundary polygons with hover state)
├── NeighborhoodPanel (slide-in detail panel)
│   ├── ScoreCard (overall + sub-scores with visual breakdown)
│   ├── StatsGrid (per-dataset stats for selected window)
│   └── MiniTrendChart (12-month sparkline per dataset)
├── ComparisonView (side-by-side two-neighborhood layout)
│   ├── NeighborhoodPanel (left)
│   └── NeighborhoodPanel (right)
├── TrendChartPanel (bottom panel, monthly chart for active dataset)
│   └── RechartsLineChart (monthly volume + 3mo moving average)
└── DataFreshnessBar (footer showing last refresh per dataset)
```

### 11.2 State Management

React Context + useReducer for global state. No Redux — the application state is simple enough that a context-based approach keeps the codebase lean.

Global state contains: active dataset, selected date range, selected neighborhood slug, comparison neighborhood slug, map viewport bounds.

### 11.3 Map Implementation

Mapbox GL JS via the `react-map-gl` wrapper. Neighborhood boundaries loaded as a GeoJSON source on mount. Data layers added as Mapbox sources/layers and updated when the active dataset or date range changes. Heatmap vs. point clustering toggled via layer visibility.

Mapbox was chosen over Leaflet for its native support for large point datasets via WebGL rendering — Leaflet degrades noticeably above ~10,000 points. At 1M+ incidents in the database, WebGL rendering is a requirement not a nice-to-have.

---

## 12. Deployment Architecture

```
EC2 Instance (t3.small, Ubuntu 22.04)
  └── Nginx (reverse proxy, SSL termination)
       └── Uvicorn (ASGI server)
            └── FastAPI app
                 └── PostgreSQL + PostGIS (EC2-hosted)

```

**Domain**: urbanlensatx.com via Namecheap DNS → EC2 public IP
**SSL**: Let's Encrypt via Certbot (auto-renewing)
**Process management**: systemd (auto-restart on crash/reboot)
**Scheduled ingestion**: APScheduler embedded in FastAPI (every 6 hours)

---

## 13. Technical Decisions & Tradeoffs

### Why FastAPI over Django or Flask?

FastAPI provides automatic OpenAPI documentation, native async support, and Pydantic-based request/response validation out of the box. For a data API that needs to handle concurrent requests and return structured JSON, FastAPI's async capabilities and type safety make it a better fit than Flask. Django's ORM and admin interface are valuable in a full application context but add unnecessary complexity for an API-only backend.

### Why PostgreSQL + PostGIS over a dedicated geospatial database?

PostGIS turns PostgreSQL into a fully capable geospatial database. Using a single database for both relational and geospatial storage simplifies the infrastructure significantly. Alternatives like MongoDB with geospatial indexes were considered but PostgreSQL's ACID compliance, mature tooling, and the power of GIST indexes for polygon queries made it the clear choice.

### Why pre-aggregate monthly stats instead of computing on the fly?

Computing monthly aggregates at query time over millions of records would produce unacceptable latency for the trend chart API. The `monthly_aggregates` table is a materialized summary that is recomputed after each ingestion run. This trades storage for query speed — a standard pattern in data systems. The tradeoff is acceptable because ingestion runs on a schedule and the aggregates are always consistent with the underlying data.

### Why APScheduler instead of a separate worker process (Celery/Redis)?

For this scale, a separate task queue adds infrastructure complexity without meaningful benefit. APScheduler embedded in the FastAPI process is simpler to deploy, monitor, and reason about. If the application were to scale to multiple EC2 instances or real-time ingestion, migrating to Celery + Redis would be the natural next step.

### Why Mapbox GL over Leaflet?

Leaflet is a lighter library and well-suited for maps with a few hundred markers. UrbanLens needs to render tens of thousands of data points simultaneously as a heatmap. Mapbox GL uses WebGL for all rendering which handles this volume with smooth performance. The tradeoff is Mapbox requires an API token and has usage-based pricing — mitigated by Mapbox's generous free tier (50,000 map loads/month).

---

## 14. MVP Scope & Milestones

### Milestone 1 — Data Foundation
- [ ] PostgreSQL + PostGIS setup on RDS
- [ ] All five table schemas created with indexes
- [ ] Neighborhood boundary GeoJSON sourced and loaded
- [ ] Socrata API client written in Python
- [ ] Full historical ingestion for all five datasets
- [ ] Point-in-polygon assignment working for all records

### Milestone 2 — Backend API
- [ ] FastAPI project structure and all route definitions
- [ ] Map data endpoint returning GeoJSON by dataset + date range + bbox
- [ ] Neighborhood detail endpoint
- [ ] Trends endpoint returning monthly aggregates
- [ ] Score computation engine implemented and tested
- [ ] APScheduler job running ingestion + score recomputation
- [ ] Health endpoint

### Milestone 3 — Frontend Core
- [ ] React project scaffolded with routing
- [ ] Mapbox map rendering Austin with neighborhood polygons
- [ ] Dataset selector and date range picker wired to map data API
- [ ] Heatmap layer rendering for active dataset
- [ ] Neighborhood click opening detail panel

### Milestone 4 — Polish & Scoring
- [ ] Score card component with visual breakdown
- [ ] Trend chart panel with Recharts
- [ ] Neighborhood comparison view
- [ ] Data freshness indicator
- [ ] Responsive layout

### Milestone 5 — Deployment
- [ ] EC2 instance configured with Nginx + Uvicorn
- [ ] React build deployed to S3 + CloudFront
- [ ] Environment variables and secrets configured
- [ ] Domain name pointed to CloudFront
- [ ] Scheduled ingestion running and verified live

---

## 15. Future Enhancements

These features are explicitly out of scope for MVP but represent natural evolution of the platform:

**Multi-city support** — The ingestion pipeline is designed to be dataset-agnostic. Adding a second city (Dallas, Houston) would require sourcing equivalent datasets and adding a city selector to the UI. The schema accommodates this with a `city` field on all tables.

**User accounts and saved views** — Allow users to bookmark neighborhoods, save comparison views, and subscribe to weekly digest emails showing trend changes in their saved areas.

**Anomaly detection** — Add a statistical layer that flags neighborhoods experiencing unusual spikes in any dataset relative to their historical baseline. Surfaces emerging trends before they become obvious.

**Mobile application** — A React Native version of the map dashboard optimized for mobile use.

**Expanded datasets** — Austin publishes dozens more datasets (school ratings, flood zones, tree canopy coverage, noise complaints) that could enrich the neighborhood score with additional dimensions.

**Public score API** — Expose the UrbanLens Neighborhood Score as a public API endpoint so third parties (real estate sites, relocation tools) can integrate it.

---

*This document is maintained alongside the codebase. All significant architectural decisions should be reflected here as the project evolves.*
