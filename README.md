# 📊 Data Summarization System

> A fully integrated asset data management and analysis platform for **Pertamina Hulu Rokan (PHR)** — combining LLM (Gemini), Google Sheets, and the Model Context Protocol (MCP) in a single fullstack solution.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                  │
│   Vite · Tailwind CSS · Syncfusion Charts · Firebase│
└────────────────────┬────────────────────────────────┘
                     │ REST API + WebSocket (MCP)
┌────────────────────▼────────────────────────────────┐
│                  Backend (FastAPI)                  │
│         Clean Architecture (Domain-Driven)          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  REST Routes │  │  MCP Server  │  │ Scheduler │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
│       │                   │                         │
│  ┌────▼───────────────────▼────────────────────┐    │
│  │              Use Cases / Domain             │    │
│  └─────────────────────┬───────────────────────┘    │
│                        │                            │
│  ┌─────────────────────▼───────────────────────┐    │
│  │           Infrastructure Layer              │    │
│  │  PostgreSQL · Google Sheets API · Gemini AI │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature                   | Description                                                                  |
| ------------------------- | ---------------------------------------------------------------------------- |
| **AI Analysis**           | Automated executive summaries powered by Gemini with multi-model rotation    |
| **Asset Chat**            | Conversational interface for querying asset data in natural language         |
| **Interactive Dashboard** | Real-time visualization of asset condition, value, and inventory trends      |
| **Multi-Source Data**     | Dynamic support for Google Sheets Master & Cycle spreadsheets                |
| **Asset Cycle**           | Identifies assets recommended for renewal or replacement based on condition  |
| **Data Export**           | Download filtered data as CSV or XLSX                                        |
| **Account Management**    | Full user CRUD integrated with Firebase Authentication                       |
| **Daily Automation**      | Scheduled job for automatic analysis aligned with PHR's asset cycle calendar |
| **Role-Based Access**     | Feature restrictions based on user role (`admin` / `user`)                   |

---

## 🛠️ Tech Stack

### Backend

- **FastAPI** — REST API + WebSocket server
- **SQLAlchemy** + **PostgreSQL** — ORM and relational database
- **LangChain** + **Google Gemini** — LLM orchestration
- **Firebase Admin SDK** — Authentication & user management
- **Google Sheets API** — Primary asset data source
- **Model Context Protocol (MCP)** — Tool communication protocol between frontend and backend

### Frontend

- **React 18** + **Vite** — Modern UI framework
- **Tailwind CSS** — Utility-first styling
- **Syncfusion Charts** — Professional data visualization
- **React Router v6** — Client-side routing
- **Firebase SDK** — Token-based authentication
- **Axios** — HTTP client with automatic interceptors

---

## 📁 Project Structure

```
project-root/
├── backend/
│   ├── app/
│   │   ├── config.py                    # Environment configuration
│   │   ├── dependencies.py              # Dependency Injection Container
│   │   ├── domain/
│   │   │   ├── entities/                # User, History, File
│   │   │   ├── repositories/            # Interfaces (IHistoryRepository, etc.)
│   │   │   └── use_cases/
│   │   │       ├── analysis/            # trigger, save, get_dashboard, stats, etc.
│   │   │       ├── history/             # get_all, delete
│   │   │       ├── user/                # create, update, delete, get
│   │   │       └── mcp/                 # get_prompts, get_resources
│   │   ├── infrastructure/
│   │   │   ├── database/                # SQLAlchemy models & session
│   │   │   ├── repositories/            # Concrete SQLAlchemy implementations
│   │   │   └── services/
│   │   │       ├── document_analyzer.py      # LLM orchestration + key rotation
│   │   │       ├── chart_service.py           # Chart data builder
│   │   │       ├── google_sheets_*.py         # Google Sheets data source
│   │   │       ├── model_rotation_service.py  # Gemini API key rotation
│   │   │       ├── preview_state_service.py   # In-memory analysis state
│   │   │       ├── auth_service.py            # Firebase Auth service
│   │   │       └── download_service.py        # CSV/XLSX export
│   │   └── presentation/
│   │       ├── routes/web_api.py        # REST endpoints
│   │       ├── protocols/mcp_server.py  # MCP WebSocket handler
│   │       ├── auth.py                  # Token verification middleware
│   │       └── schemas.py               # Pydantic request/response schemas
│   ├── main.py                          # FastAPI entry point
│   ├── daily_job.py                     # Scheduled automation script
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── common/                  # Layout, Sidebar, Modal, Toast
    │   │   ├── dashboard/               # DashboardHeader, DashboardStats
    │   │   └── ui/                      # Button, Card, Input
    │   ├── contexts/
    │   │   ├── McpProvider.jsx          # WebSocket MCP context
    │   │   └── ToastContext.jsx         # Global toast notifications
    │   ├── hooks/
    │   │   ├── useAuth.jsx              # Auth context + Firebase listener
    │   │   ├── useAnalysis.js           # Dashboard analysis hook
    │   │   └── useAssetDataProcessor.js # Filter/sort/search hook
    │   ├── pages/
    │   │   ├── Home.jsx                 # Main dashboard
    │   │   ├── Stats.jsx                # Detailed statistics
    │   │   ├── Cycle.jsx                # Asset cycle view
    │   │   ├── MasterData.jsx           # Raw data table
    │   │   ├── CustomAnalysis.jsx       # AI chat
    │   │   ├── History.jsx              # Analysis history (admin)
    │   │   ├── AccountManagement.jsx    # Account management (admin)
    │   │   └── Login.jsx                # Login page
    │   ├── services/
    │   │   ├── api.js                   # Axios REST client
    │   │   ├── authService.js           # Firebase auth helper
    │   │   └── mcpService.js            # WebSocket MCP client
    │   └── utils/
    │       ├── assetUtils.js            # Currency, date formatting, sort
    │       └── firebase.js              # Firebase config & init
    ├── index.html
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.js
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, for local database)
- Google Cloud account (Sheets API + Firebase)
- One or more Gemini API Keys

---

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project-root
```

---

### 2. Backend Setup

#### Install dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Configure environment variables

Create a `.env` file in the backend root directory:

```env
# PostgreSQL Database
DB_USER=phr_user
DB_PASS=your_password
DB_NAME=phr_data_summarization
DB_HOST=localhost
DB_PORT=5433

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# Google Gemini (add up to 4 keys for rotation)
GEMINI_API_KEY=your_primary_key
GEMINI_API_KEY_2=your_second_key
GEMINI_API_KEY_3=
GEMINI_API_KEY_4=

# Google Sheets (Spreadsheet IDs)
GOOGLE_SHEET_ID_MASTER=your_master_sheet_id
GOOGLE_SHEET_ID_SIKLUS=your_cycle_sheet_id

# Firebase Service Account (JSON stringified)
FIREBASE_CONFIG_JSON={"type":"service_account",...}

# Google Sheets Service Account (JSON stringified, or place credentials.json in root)
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}
```

#### Start the database (via Docker)

```bash
docker-compose up -d
```

#### Run the backend server

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the frontend root directory:

```env
VITE_API_URL=http://localhost:8000
VITE_SYNCFUSION_LICENSE_KEY=your_syncfusion_key

VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_FIREBASE_MEASUREMENT_ID=
```

Start the development server:

```bash
npm run dev
# Available at http://localhost:3001
```

---

## 🐳 Docker Deployment

### Backend

```bash
cd backend
docker build -t phr-backend .
docker run -p 8000:8000 --env-file .env phr-backend
```

---

## ⚙️ Advanced Configuration

### Gemini Model Rotation

The system automatically rotates between models and API keys to avoid rate limits:

- Every **4 requests** → switches model (`gemini-2.5-flash` ↔ `gemini-2.5-flash-lite`)
- Every **8 requests** → rotates to the next API key (if multiple keys are configured)

Rotation state is persisted in `model_rotation_state.json` and survives server restarts.

### Google Sheets Format

The system expects sheets with header columns including at minimum:

```
NO ASSET | NAMA ASET | KONDISI | AREA | NILAI ASET | TANGGAL INVENTORY | ...
```

The header row is auto-detected by scanning for the `NO ASSET` and `KONDISI` columns.

### Daily Automation Job

Run `daily_job.py` as a scheduled task (e.g., via Azure Web Jobs or a cron job):

```bash
python daily_job.py
```

This script will:

1. Determine the active cycle sheet based on the current month (Cycle 1 / 2 / 3)
2. Run a full AI analysis pipeline
3. Automatically save the result to the history database

**PHR Cycle Calendar:**

| Month                | Cycle   |
| -------------------- | ------- |
| January – April      | Cycle 1 |
| May – August         | Cycle 2 |
| September – December | Cycle 3 |

---

## 🔐 Authentication & Authorization

The system uses **Firebase Authentication** as the identity provider:

- Users log in with email/password via Firebase
- Firebase JWT tokens are verified on every backend request
- Roles (`admin` / `user`) are stored as **custom claims** in Firebase and mirrored in the local database
- New users are automatically registered in the local database on first login

| Role    | Access                                                   |
| ------- | -------------------------------------------------------- |
| `user`  | Dashboard, Statistics, Asset Cycle, Master Data, AI Chat |
| `admin` | All of the above + Analysis History + Account Management |

---

## 🌐 API Reference

### REST Endpoints

| Method | Endpoint                 | Description                           |
| ------ | ------------------------ | ------------------------------------- |
| `GET`  | `/api/web/download`      | Download filtered data as CSV or XLSX |
| `POST` | `/api/web/llm-router`    | AI tool selection router              |
| `POST` | `/api/web/llm-summarize` | AI summarization of tool results      |

### WebSocket MCP

Connection: `ws://host/mcp`

Available MCP tools:

| Tool                 | Description                            |
| -------------------- | -------------------------------------- |
| `trigger_analysis`   | Trigger a full dashboard analysis      |
| `query_assets`       | Filter, count, or aggregate asset data |
| `get_dashboard_data` | Fetch dashboard summary data           |
| `get_stats_data`     | Detailed statistics + data table       |
| `get_sheet_names`    | List available sheets (master/cycle)   |
| `get_master_data`    | Raw data from a specific sheet         |
| `save_analysis`      | Persist current analysis to history    |
| `get_history`        | List all saved analysis records        |
| `delete_history`     | Delete a history entry by timestamp    |
| `get_all_users`      | List all users (admin only)            |
| `create_user`        | Create a new user (admin only)         |
| `update_user_email`  | Update a user's email (admin only)     |
| `delete_user`        | Delete a user (admin only)             |
| `query_resource`     | Query a saved analysis JSON file       |

---

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: brief description"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---

## 📄 License

This project was developed for internal use. All rights reserved.
