"""
Flask Application and REST API for Smart Compiler Error Detective.
Serves frontend UI and provides analysis, history, and sample code endpoints.
"""

import os
from datetime import datetime
from typing import List, Dict, Any
from flask import Flask, request, jsonify, send_from_directory
from backend.analyzers import get_analyzer, get_supported_languages
from backend.sample_programs import SAMPLES

# Configure Flask app to serve static frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

# In-memory session error history
SESSION_HISTORY: List[Dict[str, Any]] = []
MAX_HISTORY_ITEMS = 50


@app.route("/")
def index():
    """Serve main frontend single-page interface."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    """Serve frontend static assets (CSS, JS, icons)."""
    return send_from_directory(FRONTEND_DIR, path)


@app.route("/api/languages", methods=["GET"])
def api_languages():
    """List supported programming languages."""
    return jsonify({
        "success": True,
        "languages": get_supported_languages(),
    })


@app.route("/api/samples", methods=["GET"])
def api_samples():
    """Return curated sample code snippets for demonstration."""
    return jsonify({
        "success": True,
        "samples": SAMPLES,
    })


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    Main Compiler Error Detective analysis endpoint.
    Runs Lexical, Syntax, and Semantic analysis for the given language and source code.
    """
    data = request.get_json(silent=True) or {}
    language = data.get("language", "c").strip().lower()
    source_code = data.get("source_code", "")

    analyzer = get_analyzer(language)
    if not analyzer:
        return jsonify({
            "success": False,
            "error": f"Unsupported language '{language}'. Supported: {', '.join(get_supported_languages())}",
        }), 400

    # Run modular 3-phase compiler analysis
    result = analyzer.analyze(source_code)
    result_dict = result.to_dict()

    # Record in session history
    run_record = {
        "id": f"RUN_{len(SESSION_HISTORY) + 1}",
        "language": analyzer.language_name,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "total_errors": result.total_errors,
        "lexical_errors": result.lexical_errors_count,
        "syntax_errors": result.syntax_errors_count,
        "semantic_errors": result.semantic_errors_count,
        "warnings": result.warnings_count,
        "success": result.success,
        "summary": result.summary,
        "code_snippet": (source_code[:120] + "...") if len(source_code) > 120 else source_code,
    }
    SESSION_HISTORY.insert(0, run_record)
    if len(SESSION_HISTORY) > MAX_HISTORY_ITEMS:
        SESSION_HISTORY.pop()

    return jsonify(result_dict)


@app.route("/api/history", methods=["GET", "DELETE"])
def api_history():
    """Manage user session analysis history."""
    global SESSION_HISTORY
    if request.method == "DELETE":
        SESSION_HISTORY.clear()
        return jsonify({"success": True, "message": "Session history cleared."})

    return jsonify({
        "success": True,
        "history": SESSION_HISTORY,
    })


@app.route("/api/download-zip", methods=["GET"])
def api_download_zip():
    """Allow direct browser download of the packaged project zip archive."""
    zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "smart-compiler-error-detective.zip"))
    if os.path.exists(zip_path):
        return send_from_directory(os.path.dirname(zip_path), os.path.basename(zip_path), as_attachment=True)
    return jsonify({"error": "Zip file not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f" Smart Compiler Error Detective Server Starting")
    print(f" Access UI at: http://localhost:{port}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=True)
