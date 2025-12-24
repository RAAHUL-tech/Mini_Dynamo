from flask import Flask, request, jsonify
from coordinator import Coordinator
from config import DEFAULT_N, DEFAULT_R, DEFAULT_W
from utils import validate_quorum_params
from metrics import get_metrics


def create_app(coordinator: Coordinator):
    app = Flask(__name__)

    # ---------- CLIENT-FACING API ----------

    @app.route("/kv/<key>", methods=["PUT"])
    def put_key(key):
        body = request.get_json(force=True)

        value = body["value"]
        n = body.get("N", DEFAULT_N)
        w = body.get("W", DEFAULT_W)

        # Validate quorum parameters (using actual parameters, not defaults)
        if not validate_quorum_params(n, DEFAULT_R, w):
            return jsonify({"error": "Invalid quorum parameters"}), 400

        success = coordinator.handle_put(key, value, n, w)
        status = 200 if success else 503

        return jsonify({"success": success}), status

    @app.route("/kv/<key>", methods=["GET"])
    def get_key(key):
        r = int(request.args.get("R", DEFAULT_R))
        n = int(request.args.get("N", DEFAULT_N))

        # Validate quorum parameters (using actual parameters)
        if not validate_quorum_params(n, r, DEFAULT_W):
            return jsonify({"error": "Invalid quorum parameters"}), 400

        versions = coordinator.handle_get(key, r, n)
        return jsonify({"versions": versions}), 200

    @app.route("/kv/<key>", methods=["DELETE"])
    def delete_key(key):
        body = request.get_json(force=True) if request.is_json else {}
        n = body.get("N", DEFAULT_N)
        w = body.get("W", DEFAULT_W)

        # Validate quorum parameters
        if not validate_quorum_params(n, DEFAULT_R, w):
            return jsonify({"error": "Invalid quorum parameters"}), 400

        success = coordinator.handle_delete(key, n, w)
        status = 200 if success else 503

        return jsonify({"success": success}), status

    # ---------- INTERNAL NODE-TO-NODE API ----------

    @app.route("/internal/kv/<key>", methods=["PUT"])
    def internal_put(key):
        payload = request.get_json(force=True)
        coordinator.storage.put(key, payload)
        return jsonify({"status": "ok"}), 200

    @app.route("/internal/kv/<key>", methods=["GET"])
    def internal_get(key):
        # Internal GET should return ALL versions including tombstones
        versions = coordinator.storage.get_all(key)
        return jsonify({"versions": versions}), 200

    # ---------- METRICS API ----------

    @app.route("/metrics", methods=["GET"])
    def get_metrics_endpoint():
        """Get performance and availability metrics"""
        metrics = get_metrics()
        return jsonify(metrics.get_summary()), 200

    return app
