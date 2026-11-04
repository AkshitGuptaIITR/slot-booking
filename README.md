# 📅 High-Concurrency Slot Booking System

A robust, production-grade appointment and slot booking platform built with **FastAPI**, **PostgreSQL**, **SQLAlchemy (Async)**, and **React 19**. 

Designed with strict ACID guarantees, multi-layer concurrency control, and zero-frustration UX to eliminate race conditions, double-bookings, and stale state anomalies.

---

## 📑 Table of Contents
1. [Core Business Rules](#-core-business-rules)
2. [Tech Stack](#-tech-stack)
3. [Architecture & Project Structure](#-architecture--project-structure)
4. [Preliminary Requirements](#-preliminary-requirements)
5. [Installation & Setup](#-installation--setup)
6. [Running the Application](#-running-the-application)
7. [Running Automated Tests](#-running-automated-tests)
8. [Edge Cases Identified & Resolved](#-edge-cases-identified--resolved)
9. [Known Limitations](#-known-limitations)

---

## 📋 Core Business Rules

* **Slot Duration**: Exactly 30 minutes, aligned to the hour (`:00`) or half-hour (`:30`).
* **Working Hours**: Monday to Friday, **09:00 to 17:00 Asia/Kolkata (IST)** (16 slots/day; weekends strictly closed).
* **Booking Window**: Slots can be viewed and booked up to **14 days in advance**.
* **Per-User Quota**: Each user is restricted to a maximum of **2 active upcoming bookings** at any time.
* **Cancellation Policy**: Bookings can only be cancelled with at least **2 hours notice** prior to slot start time.
* **Idempotency**: All booking requests require an `Idempotency-Key` header with deterministic response caching and hash verification.

---

## 💻 Tech Stack

### Frontend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **[React](https://react.dev/)** | `19.x` | Modern reactive UI framework utilizing React 19 concurrent features |
| **[React Compiler](https://react.dev/learn/react-compiler)** | `1.0.0` | Automatic memoization of components and hooks without manual `useMemo` / `useCallback` overhead |
| **[Vite](https://vitejs.dev/)** | `8.x` | Next-generation frontend build tool, local dev server, and HMR engine with built-in API proxy |
| **[Tailwind CSS](https://tailwindcss.com/)** | `4.x` | Utility-first styling with `@tailwindcss/vite` for responsive, accessible UI components |
| **[Fetch API & Custom Services](frontend/src/services/api.js)** | Native | Decoupled client service layer handling slot fetching, holds, reservations, idempotency, and cancellation |

### Backend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **[Python](https://www.python.org/)** | `3.11+` | Core language runtime leveraging native async/await performance and typing improvements |
| **[FastAPI](https://fastapi.tiangolo.com/)** | `0.162+` | High-performance async web framework with automatic OpenAPI / Swagger generation |
| **[Uvicorn](https://www.uvicorn.org/)** | `0.54+` | Lightning-fast ASGI web server implementation |
| **[Pydantic v2](https://docs.pydantic.dev/)** | `2.14+` | High-speed data validation, request parsing, and response serialization |
| **[SQLAlchemy (Asyncio)](https://www.sqlalchemy.org/)** | `2.0+` | Modern asynchronous ORM enabling non-blocking database queries, savepoints, and row locking |
| **[asyncpg](https://github.com/MagicStack/asyncpg)** | `0.32+` | High-performance asynchronous PostgreSQL database driver for Python |
| **[Alembic](https://alembic.sqlalchemy.org/)** | `1.20+` | Schema migration management and version-controlled database schema evolution |
| **[Pytz](https://pythonhosted.org/pytz/) & [python-dateutil](https://dateutil.readthedocs.io/)** | Latest | Exact timezone translations (`Asia/Kolkata` IST & `UTC`) and working calendar boundaries |

### Database & Concurrency Control
| Component | Implementation | Purpose |
| :--- | :--- | :--- |
| **[PostgreSQL](https://www.postgresql.org/)** | `14+` | Primary ACID-compliant relational data store |
| **Transaction Advisory Locks** | `pg_advisory_xact_lock` | Serializes booking creation per `user_id` to guarantee the 2-booking quota without table-level locking |
| **Partial Unique Index** | `idx_unique_active_slot` | Enforces single-active-booking constraint at the database engine level on `(slot_start)` where `status = 'ACTIVE'` |
| **Row-Level Locking** | `SELECT ... FOR UPDATE` | Prevents race conditions during booking cancellations and validation checks |
| **In-Memory Hold Registry** | `InMemoryHoldService` | Thread-safe 2-minute ephemeral slot reservation with TTL countdown and automatic lazy pruning |

### Development, Testing & Code Quality
* **Pytest & Pytest-Asyncio**: Automated testing suite covering concurrent booking attempts, advisory lock serialization, and hold lifecycles.
* **HTTPX**: Async HTTP client for integration and end-to-end API testing.
* **Ruff**: Blazing fast Python code linter and formatter.
* **ESLint**: JavaScript and React syntax verification and hooks linting.

---

## 🏗 Architecture & Project Structure

```
slot-booking/
├── backend/
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── api/          # FastAPI route controllers & dependency injection
│   │   ├── core/         # Custom exceptions, security hashing, settings
│   │   ├── db/           # Async SQLAlchemy engine & base model
│   │   ├── models/       # Database entities (Booking, IdempotencyRecord)
│   │   ├── schemas/      # Pydantic v2 validation models
│   │   └── services/     # Business logic, hold service, DB advisory lock service
│   ├── tests/            # Pytest async test suite (holds, concurrency, idempotency)
│   ├── .env.example      # Sample backend environment configuration
│   └── pyproject.toml    # Backend dependencies and project metadata
├── frontend/
│   ├── src/
│   │   ├── components/   # Header, SlotBookingForm, SlotsGrid, BookingModal, MyBookings
│   │   ├── services/     # API client (fetch, hold, release, book, cancel)
│   │   └── utils/        # IST & UTC date-time calculations, validation helpers
│   ├── package.json      # Frontend dependencies and scripts
│   └── vite.config.js    # Vite configuration with proxy and React Compiler plugin
└── README.md
```

---

## 📋 Preliminary Requirements

Before installing and running the application locally, ensure your machine satisfies the following preliminary requirements:

### 1. System & Runtime Dependencies
* **Python**: `3.11` or higher
  * Verify with: `python --version` (or `python3 --version`)
  * Ensure `pip` and `venv` module are available.
* **Node.js**: `18.0.0` or higher (LTS 20.x or 22.x recommended)
  * Verify with: `node --version`
  * Includes `npm` (v9+): verify with `npm --version`
* **PostgreSQL**: `14.0` or higher
  * PostgreSQL server must be installed, active, and accepting connections.
  * Verify with: `psql --version` or check if the PostgreSQL service is running (`pg_isready -h localhost -p 5432`).
* **Git**: Installed for cloning and version control.

### 2. Network Ports
Ensure the following local network ports are free and not occupied by other services:
* **Port `5432`**: PostgreSQL database service
* **Port `8000`**: Backend FastAPI server (`uvicorn`)
* **Port `5173`**: Frontend Vite development server

### 3. Database Credentials & Access
* You must have administrative or user privileges in PostgreSQL to create a new database (e.g., `slotbook`).
* Note your PostgreSQL username, password, host, and port (default: `postgres`, `localhost`, `5432`).

---

## ⚙️ Installation & Setup

### 1. Create the Database
Connect to your local PostgreSQL instance using `psql` or your preferred GUI (pgAdmin, DBeaver, TablePlus):

```bash
# Connect via psql CLI
psql -U postgres
```

Inside the PostgreSQL prompt, create the database:
```sql
CREATE DATABASE slotbook;
\q
```

---

### 2. Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   * **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install backend dependencies:
   * **Using pip**:
     ```bash
     pip install -e ".[dev]"
     ```
   * *Alternatively, if using [uv](https://github.com/astral-sh/uv)*:
     ```bash
     uv sync
     ```

4. Configure environment variables:
   Copy the provided `.env.example` file to `.env`:
   * **Windows (PowerShell)**:
     ```powershell
     Copy-Item .env.example .env
     ```
   * **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```

   Edit `backend/.env` with your PostgreSQL credentials:
   ```env
   DATABASE_URL=postgresql+asyncpg://<username>:<password>@localhost:5432/slotbook
   ```
   > [!NOTE]
   > Ensure the connection string uses the `postgresql+asyncpg://` scheme for SQLAlchemy's asynchronous driver.

5. Apply database migrations:
   ```bash
   alembic upgrade head
   ```

---

### 3. Frontend Setup

1. Open a new terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

---

## 🚀 Running the Application

### 1. Start the Backend API Server
From the `backend/` directory with the virtual environment activated:
```bash
uvicorn app.main:app --reload --port 8000
```
* **API Base URL**: `http://localhost:8000`
* **Interactive Swagger Documentation**: `http://localhost:8000/docs`
* **Alternative Redoc Documentation**: `http://localhost:8000/redoc`

### 2. Start the Frontend Development Server
From the `frontend/` directory:
```bash
npm run dev
```
* **Web Application UI**: `http://localhost:5173`
* Vite automatically proxies all `/api/*` requests directly to `http://localhost:8000`, bypassing CORS hurdles during development.

---

## 🧪 Running Automated Tests

The backend includes automated integration and concurrency tests covering slot holds, advisory locks, and race condition prevention.

From the `backend/` directory:
```bash
pytest tests/ -v
```

Tests verify:
* **Hold lifecycle**: Acquisition, renewal, TTL expiration, lazy pruning, and unauthorized release prevention.
* **Pre-booking collision**: Bob is blocked when Alice holds or books a slot.
* **Concurrent quota enforcement**: Multiple parallel requests from the same user cannot breach the 2-booking quota.

---

## 🛡️ Edge Cases Identified & Resolved

### 1. Slot Collision Between Two Users (Same Slot at Same Millisecond)
* **The Problem**: Two users load the same available slot and click "Book" simultaneously. In standard `READ COMMITTED` isolation, both read `available: true` and attempt to insert.
* **The Resolution**:
  * **Database-Level Partial Unique Index**: `idx_unique_active_slot` on `slot_start` where `status = 'ACTIVE'`.
  * **Nested Transaction Savepoint**: `db.begin_nested()` catches `IntegrityError` and converts it into a clean `409 SLOT_TAKEN` exception without aborting the parent session.

### 2. Pre-Booking Form Collision (The "Typing Delay" Dilemma)
* **The Problem**: User A clicks a slot, opening an email modal. While User A takes 15 seconds to type, User B also clicks the slot, types their email, and submits first—causing User A's submission to unexpectedly fail.
* **The Resolution**:
  * **Temporary 2-Minute Slot Holds**: Clicking an available slot immediately calls `POST /slots/hold` via `InMemoryHoldService`.
  * **Exclusivity**: While held, other users see the slot styled as **"On Hold"** (disabled).
  * **Interactive Countdown**: The modal displays a live `MM:SS` countdown timer.
  * **Instant Release**: If the user cancels or closes the modal, `POST /slots/release-hold` frees the slot immediately without waiting for the TTL.

### 3. Per-User Quota Race (Bypassing the 2-Booking Limit)
* **The Problem**: A user with 1 active booking sends parallel API calls for Slot A and Slot B simultaneously. Both queries check `COUNT(*) < 2`, both evaluate to `1 < 2` (`True`), and both insert—resulting in 3 bookings.
* **The Resolution**:
  * **Database Advisory Locks**: Added [`DatabaseLockService`](backend/app/services/lock_service.py) calling `SELECT pg_advisory_xact_lock(hashtext('user:' || user_id))`.
  * This serializes booking creation strictly for the *same user* across concurrent workers without locking unrelated users or entire tables.

### 4. Idle Tab Stale Slots (Slot Starts While Viewing)
* **The Problem**: A user loads today's slots at 09:55 AM (10:00 AM is available). After a 10-minute distraction, they click 10:00 AM at 10:05 AM, causing a backend error: *"Cannot book a slot in the past"*.
* **The Resolution**:
  * **Client-Side Reactive Ticker**: `SlotsGrid.jsx` runs an interval comparing `slot.start <= currentTime`. When 10:00 AM arrives, the button dynamically transitions to **"Past Slot"** (disabled).
  * **Tab Focus & Visibility Listener**: Window `focus` and `visibilitychange` listeners silently re-fetch slots and bookings whenever the user navigates back to the tab.
  * **Periodic Polling**: Refreshes slots every 60 seconds in the background.

### 5. In-Flight Idempotency Re-submission
* **The Problem**: Flaky connections or rapid double-clicks submit duplicate requests with the same `Idempotency-Key` concurrently.
* **The Resolution**: `idempotency_records` table stores the payload hash (SHA-256), status code, and response body, returning deterministic cached responses for replays and rejecting payload mismatches with `422 IDEMPOTENCY_KEY_REUSED`.

### 6. Cancellation Window Clock Boundary
* **The Problem**: A user cancels a 12:00 PM booking at 09:59:59 AM. App server latency or clock drift could cause evaluation after 10:00:00 AM.
* **The Resolution**: `cancel_booking` uses `with_for_update()` row-level locks and strict UTC time comparison. Cancelled slots (`status = 'CANCELLED'`) are ignored by the partial unique index, allowing immediate re-booking.

### 7. Past Bookings vs. Active Quota
* **The Problem**: Does a user's booking history from yesterday block them from booking today?
* **The Resolution**: The quota query explicitly filters `Booking.slot_start >= now_utc`. Past bookings remain in history indefinitely without counting toward the 2-booking quota.

---

## ⚠️ Known Limitations

1. **In-Memory Hold Store (Single-Worker Limitation)**:
   * `InMemoryHoldService` uses a Python dictionary with `threading.Lock` for development and demo simplicity.
   * **Production Requirement**: In a multi-worker (`uvicorn --workers 4`) or multi-container Kubernetes cluster, holds must be moved to **Redis** (e.g., `SET slot:<id> <user_id> NX EX 120`) so hold state is globally shared across all server instances.

2. **Single Consultant Calendar**:
   * The current system models appointments for a single consultant.
   * Supporting multiple staff members or conference rooms would require adding a `resource_id` / `consultant_id` column to bookings and composite unique constraints on `(resource_id, slot_start)`.

3. **Fixed 30-Minute Slot Granularity**:
   * Only supports fixed 30-minute intervals.
   * Supporting variable meeting durations (e.g., 45, 60, or 90 minutes) would require PostgreSQL range types (`tstzrange`) and GiST exclusion constraints (`EXCLUDE USING gist`) to prevent overlapping time ranges.

4. **Timezone Representation in Frontend**:
   * Consultant working hours are strictly anchored to `Asia/Kolkata` (09:00–17:00 IST).
   * For international clients in distant timezones (e.g., US EST), calendar days in local time can cross day boundaries relative to IST working hours. Displaying an explicit "Times shown in IST (UTC+5:30)" banner helps avoid user confusion.
