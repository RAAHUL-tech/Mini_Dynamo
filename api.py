from flask import Flask, request, jsonify
from coordinator import Coordinator


def create_app(coordinator: Coordinator):
    app = Flask(__name__)

    # ---------- CLIENT-FACING API ----------

    @app.route("/kv/<key>", methods=["PUT"])
    def put_key(key):
        body = request.get_json(force=True)

        value = body["value"]
        n = body.get("N", 3)
        w = body.get("W", 2)

        success = coordinator.handle_put(key, value, n, w)
        status = 200 if success else 503

        return jsonify({"success": success}), status

    @app.route("/kv/<key>", methods=["GET"])
    def get_key(key):
        r = int(request.args.get("R", 2))

        versions = coordinator.handle_get(key, r)
        return jsonify({"versions": versions}), 200

    # ---------- INTERNAL NODE-TO-NODE API ----------

    @app.route("/internal/kv/<key>", methods=["PUT"])
    def internal_put(key):
        payload = request.get_json(force=True)
        coordinator.storage.put(key, payload)
        return jsonify({"status": "ok"}), 200

    @app.route("/internal/kv/<key>", methods=["GET"])
    def internal_get(key):
        versions = coordinator.storage.get(key)
        return jsonify({"versions": versions}), 200

    return app
