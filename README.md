# Job Application Tracker API

A RESTful backend built with **Python, Flask, and SQLite** to track job and internship applications, plus a **Pandas automation script** that generates progress reports.

## Features
- Full CRUD REST API for applications (company, role, status, date, notes)
- Input validation with clear error responses (400/404) and request logging
- Filter by status (`GET /api/applications?status=interview`)
- SQL aggregation endpoint (`GET /api/stats`) using `GROUP BY`
- Parameterized SQL queries (protects against SQL injection)
- Automation script: exports data to CSV and computes status counts, weekly activity, and response rate with Pandas
- Unit tests for API and reporting logic (12 tests)

## Tech Stack
Python 3, Flask, SQLite (`sqlite3`), Pandas, unittest, Git/GitHub

## Setup
```bash
git clone https://github.com/rajendra-pal/job-tracker-api.git
cd job-tracker-api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # API runs at http://127.0.0.1:5000
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/applications` | Create an application |
| GET | `/api/applications` | List (optional `?status=`) |
| GET | `/api/applications/<id>` | Get one |
| PUT | `/api/applications/<id>` | Update fields |
| DELETE | `/api/applications/<id>` | Delete |
| GET | `/api/stats` | Counts by status |

### Example
```bash
curl -X POST http://127.0.0.1:5000/api/applications \
  -H "Content-Type: application/json" \
  -d '{"company": "Zenithbyte", "role": "Python Development Intern"}'
```

## Generate a Report (automation)
```bash
python scripts/generate_report.py --db tracker.db --out reports
```
Creates `applications.csv`, `summary_by_status.csv`, and `summary_by_week.csv`, and prints the response rate.

## Run Tests
```bash
python -m unittest discover -v
```

## Project Structure
```
app/         Flask app factory, routes, database helpers
scripts/     Pandas reporting script
tests/       API and report tests
run.py       Entry point
```

## Possible Improvements
Authentication, pagination, Docker, and a small web front end.
