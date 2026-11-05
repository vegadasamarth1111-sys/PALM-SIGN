"""Palm/Sign web desk.

Run with:
    python app.py
"""

from __future__ import annotations

import argparse
import atexit
import io
import threading
import time
import webbrowser
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, Response, jsonify, render_template, request, send_file

from src.classifier import TrainingError
from src.config import MODEL_PATH, ROOT
from src.engine import VisionEngine

_TRAIN_LOCK = threading.Lock()


def create_app(start_engine: bool = True) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["JSON_SORT_KEYS"] = False

    engine = VisionEngine()
    app.extensions["vision_engine"] = engine
    if start_engine:
        engine.start()
        atexit.register(engine.stop)

    @app.before_request
    def ensure_engine_started() -> None:
        # Also makes `flask --app app run` behave correctly.
        engine.start()

    # --------------------------------------------------------------- pages
    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/video_feed")
    def video_feed() -> Response:
        def generate():
            last_seq = 0
            try:
                while True:
                    seq, jpeg = engine.wait_for_frame(last_seq, timeout=4.0)
                    if jpeg is None or seq == last_seq:
                        continue
                    last_seq = seq
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: "
                        + str(len(jpeg)).encode("ascii")
                        + b"\r\n\r\n"
                        + jpeg
                        + b"\r\n"
                    )
            except GeneratorExit:
                return
            except BrokenPipeError:
                return

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # ---------------------------------------------------------------- state
    @app.get("/api/state")
    def api_state():
        return jsonify(engine.snapshot())

    @app.get("/api/health")
    def api_health():
        state = engine.snapshot()
        return jsonify(
            {
                "ok": True,
                "camera": state["camera_ok"],
                "model": state["model"]["loaded"],
                "fps": state["fps"],
            }
        )

    # --------------------------------------------------------------- actions
    @app.post("/api/action")
    def api_action():
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("action", "")).strip()
        try:
            result = engine.action(name, payload.get("value"))
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, **result})

    @app.post("/api/collect")
    def api_collect():
        payload = request.get_json(silent=True) or {}
        action = str(payload.get("action", "start")).lower()
        try:
            if action == "cancel":
                state = engine.cancel_collection()
            elif action == "start":
                label = str(payload.get("label", "")).strip()
                target = int(payload.get("target", 80))
                state = engine.start_collection(label, target)
            else:
                return jsonify({"ok": False, "error": "Unknown capture action"}), 400
        except (ValueError, TypeError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, "collect": state})

    @app.post("/api/train")
    def api_train():
        if not _TRAIN_LOCK.acquire(blocking=False):
            return jsonify({"ok": False, "error": "A training run is already in progress."}), 409
        try:
            report = engine.train()
        except TrainingError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except (OSError, ValueError, RuntimeError) as exc:
            return jsonify({"ok": False, "error": f"Training failed: {exc}"}), 500
        finally:
            _TRAIN_LOCK.release()
        return jsonify({"ok": True, "report": report})

    @app.post("/api/reset")
    def api_reset():
        payload = request.get_json(silent=True) or {}
        if str(payload.get("confirm", "")) != "RESET":
            return jsonify({"ok": False, "error": "Reset needs explicit confirmation."}), 400
        try:
            engine.reset_lab()
        except (OSError, ValueError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True})

    @app.post("/api/settings/skin")
    def api_skin():
        payload = request.get_json(silent=True) or {}
        try:
            if "preset" in payload:
                settings = engine.set_skin_preset(str(payload["preset"]))
            elif "lower" in payload and "upper" in payload:
                settings = engine.set_skin_bounds(payload["lower"], payload["upper"])
            else:
                return jsonify({"ok": False, "error": "Send a preset or lower/upper bounds."}), 400
        except (ValueError, TypeError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, "settings": settings})

    # --------------------------------------------------------------- assets
    @app.get("/api/stage/<stage>.jpg")
    def api_stage(stage: str):
        if stage not in {"source", "light", "mask", "shape"}:
            return jsonify({"ok": False, "error": "Unknown stage"}), 404
        jpeg = engine.stage_jpeg(stage)
        if not jpeg:
            return _waiting_image(), 200, _image_headers()
        return Response(jpeg, mimetype="image/jpeg", headers=_image_headers())

    @app.get("/api/snapshot.jpg")
    def api_snapshot():
        jpeg = engine.latest_jpeg()
        if not jpeg:
            return jsonify({"ok": False, "error": "No frame is ready yet."}), 503
        name = f"palm-sign-{time.strftime('%Y%m%d-%H%M%S')}.jpg"
        return send_file(
            io.BytesIO(jpeg),
            mimetype="image/jpeg",
            as_attachment=True,
            download_name=name,
            max_age=0,
        )

    @app.get("/api/report")
    def api_report():
        state = engine.snapshot()
        return jsonify(
            {
                "model": state["model"],
                "dataset": state["dataset"],
                "feature_version": state["feature_version"],
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return app


def _image_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store, max-age=0",
        "Pragma": "no-cache",
    }


def _waiting_image() -> Response:
    canvas = np.full((240, 320, 3), (17, 18, 17), dtype=np.uint8)
    for x in range(0, 320, 24):
        cv2.line(canvas, (x, 0), (x, 240), (27, 28, 27), 1)
    cv2.putText(
        canvas,
        "WAITING",
        (104, 126),
        cv2.FONT_HERSHEY_DUPLEX,
        0.55,
        (130, 132, 126),
        1,
        cv2.LINE_AA,
    )
    ok, encoded = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    data = encoded.tobytes() if ok else b""
    return Response(data, mimetype="image/jpeg", headers=_image_headers())


app = create_app(start_engine=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Palm/Sign live workbench")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index (default: 0)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser")
    args = parser.parse_args()

    # A camera engine is per-process. Keeping the reloader off avoids two
    # processes fighting over the webcam.
    if app.extensions.get("vision_engine") is None:
        raise RuntimeError("Vision engine was not initialised")
    engine = app.extensions["vision_engine"]
    engine.camera_index = args.camera
    engine.start()
    atexit.register(engine.stop)

    url = f"http://{args.host}:{args.port}"
    if not args.no_browser:
        threading.Timer(1.1, lambda: webbrowser.open(url)).start()
    print("")
    print("  PALM / SIGN")
    print(f"  workbench  {url}")
    print(f"  camera     {args.camera}     model  {'loaded' if MODEL_PATH.exists() else 'not trained'}")
    print("  stop with Ctrl+C")
    print("")
    app.run(host=args.host, port=args.port, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
