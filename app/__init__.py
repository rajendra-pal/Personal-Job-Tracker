"""Application factory for the Job Application Tracker API."""
import logging
from flask import Flask, jsonify, render_template

from .db import init_db
from .routes import bp


def create_app(db_path="tracker.db"):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    init_db(db_path)
    app.register_blueprint(bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api")
    def api_info():
        return jsonify(
            name="Job Application Tracker API",
            endpoints={
                "health": "/api/health",
                "list/create applications": "/api/applications",
                "get/update/delete application": "/api/applications/<id>",
                "stats": "/api/stats",
            },
        )

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Resource not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled error: %s", e)
        return jsonify(error="Internal server error"), 500

    return app
