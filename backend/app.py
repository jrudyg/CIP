"""
CIP Backend Application — P7.S2
Main Flask application with SSE streaming support.

Phase: P7.S2
Task: S2.T3
Author: CAI (Backend Architect)

Run with:
    python app.py
    
Or with gunicorn:
    gunicorn -w 1 -k gevent app:app
"""

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify

# Optional CORS support
try:
    from flask_cors import CORS
    HAS_CORS = True
except ImportError:
    HAS_CORS = False
    CORS = None

# Import blueprints
from api.v1.stream import stream_bp

# Import repositories for initialization
from session_state import get_session_repository
from event_log import get_event_log_repository
from shared.p7_streaming_contract import P7_CONTRACT_VERSION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("cip.app")


def create_app(config: dict = None) -> Flask:
    """
    Application factory.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config.update({
        "DEBUG": os.getenv("CIP_DEBUG", "false").lower() == "true",
        "SESSION_DB_PATH": os.getenv("CIP_SESSION_DB_PATH", "data/cip_sessions.db"),
        "EVENT_LOG_DB_PATH": os.getenv("CIP_EVENT_LOG_DB_PATH", "data/cip_events.db"),
        "SSE_KEEPALIVE_INTERVAL": int(os.getenv("SSE_KEEPALIVE_INTERVAL", "30")),
        "SSE_MAX_CONNECTIONS": int(os.getenv("SSE_MAX_CONNECTIONS_PER_SESSION", "5")),
        "SSE_EVENT_TTL_HOURS": float(os.getenv("SSE_EVENT_TTL_HOURS", "1.0")),
        "SSE_MAX_EVENTS": int(os.getenv("SSE_MAX_EVENTS_PER_SESSION", "1000")),
    })
    
    # Apply overrides
    if config:
        app.config.update(config)

    # Enable CORS if available
    if HAS_CORS and CORS:
        CORS(app, resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Client-Version", "Last-Event-ID"],
            }
        })

    # Initialize repositories
    with app.app_context():
        _init_repositories(app)

    # Register blueprints
    app.register_blueprint(stream_bp)
    logger.info(f"Registered blueprint: {stream_bp.name} at {stream_bp.url_prefix}")

    # Root endpoint
    @app.route("/")
    def root():
        return jsonify({
            "service": "CIP Backend",
            "version": "1.0.0",
            "contract_version": P7_CONTRACT_VERSION,
            "status": "running",
            "endpoints": {
                "stream": "/api/v1/stream/<session_id>",
                "replay": "/api/v1/stream/<session_id>/replay",
                "status": "/api/v1/stream/<session_id>/status",
                "health": "/api/v1/stream/health",
            },
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    logger.info(f"CIP Backend initialized (contract v{P7_CONTRACT_VERSION})")
    return app


def _init_repositories(app: Flask) -> None:
    """Initialize data repositories."""
    # Session state repository
    session_repo = get_session_repository(app.config["SESSION_DB_PATH"])
    logger.info(f"Session repository: {app.config['SESSION_DB_PATH']}")

    # Event log repository
    event_repo = get_event_log_repository(
        db_path=app.config["EVENT_LOG_DB_PATH"],
        ttl_hours=app.config["SSE_EVENT_TTL_HOURS"],
        max_events=app.config["SSE_MAX_EVENTS"],
    )
    logger.info(f"Event log repository: {app.config['EVENT_LOG_DB_PATH']}")


# Create default app instance
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("CIP_PORT", "5000"))
    debug = os.getenv("CIP_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting CIP Backend on port {port}")
    logger.info(f"SSE endpoint: http://localhost:{port}/api/v1/stream/<session_id>")
    
    # Note: For production, use gunicorn with gevent worker
    # gunicorn -w 1 -k gevent -b 0.0.0.0:5000 app:app
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True,
    )
