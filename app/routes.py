"""REST API endpoints for job applications (CRUD + filtering + stats)."""
from datetime import date

from flask import Blueprint, current_app, jsonify, request

from .db import VALID_STATUSES, get_connection

bp = Blueprint("applications", __name__, url_prefix="/api")


def _validate(data, partial=False):
    """Return a list of validation error messages for the request body."""
    errors = []
    if not partial:
        for field in ("company", "role"):
            if not str(data.get(field, "")).strip():
                errors.append(f"'{field}' is required")
    if "status" in data and data["status"] not in VALID_STATUSES:
        errors.append(f"'status' must be one of {list(VALID_STATUSES)}")
    if "applied_on" in data:
        try:
            date.fromisoformat(data["applied_on"])
        except (TypeError, ValueError):
            errors.append("'applied_on' must be a date in YYYY-MM-DD format")
    return errors


@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.post("/applications")
def create_application():
    data = request.get_json(silent=True) or {}
    errors = _validate(data)
    if errors:
        return jsonify(errors=errors), 400

    db_path = current_app.config["DB_PATH"]
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO applications (company, role, status, applied_on, notes, link) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                data["company"].strip(),
                data["role"].strip(),
                data.get("status", "applied"),
                data.get("applied_on", date.today().isoformat()),
                data.get("notes", ""),
                data.get("link", "").strip(),
            ),
        )
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (cur.lastrowid,)).fetchone()
        row_dict = dict(row)
    current_app.logger.info("Created application id=%s", row_dict["id"])
    return jsonify(row_dict), 201


@bp.get("/applications")
def list_applications():
    query, params = "SELECT * FROM applications", []
    status = request.args.get("status")
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY applied_on DESC, id DESC"

    db_path = current_app.config["DB_PATH"]
    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/applications/<int:app_id>")
def get_application(app_id):
    db_path = current_app.config["DB_PATH"]
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if row is None:
        return jsonify(error="Application not found"), 404
    return jsonify(dict(row))


@bp.put("/applications/<int:app_id>")
def update_application(app_id):
    data = request.get_json(silent=True) or {}
    errors = _validate(data, partial=True)
    if errors:
        return jsonify(errors=errors), 400

    allowed = ("company", "role", "status", "applied_on", "notes", "link")
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify(errors=["No valid fields to update"]), 400

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    db_path = current_app.config["DB_PATH"]
    with get_connection(db_path) as conn:
        cur = conn.execute(
            f"UPDATE applications SET {set_clause} WHERE id = ?", (*updates.values(), app_id)
        )
        if cur.rowcount == 0:
            return jsonify(error="Application not found"), 404
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        row_dict = dict(row)
    return jsonify(row_dict)


@bp.delete("/applications/<int:app_id>")
def delete_application(app_id):
    db_path = current_app.config["DB_PATH"]
    with get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    if cur.rowcount == 0:
        return jsonify(error="Application not found"), 404
    return "", 204


@bp.get("/stats")
def stats():
    db_path = current_app.config["DB_PATH"]
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS count FROM applications GROUP BY status"
        ).fetchall()
    counts = {s: 0 for s in VALID_STATUSES}
    counts.update({r["status"]: r["count"] for r in rows})
    return jsonify(total=sum(counts.values()), by_status=counts)
