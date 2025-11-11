# main.py
import os
import json
import base64
import zipfile
from io import BytesIO
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory, abort
from google.cloud import storage
from agents import create_agents, BaseAgent

# ----------------------------------------------------------------------
# Flask + static build folder
# ----------------------------------------------------------------------
app = Flask(__name__, static_folder="build", static_url_path="/")
SESSIONS_ROOT = "sessions"
os.makedirs(SESSIONS_ROOT, exist_ok=True)

# ----------------------------------------------------------------------
# Helper: write artifact (text or base64 media)
# ----------------------------------------------------------------------
def write_artifact(session_dir: str, filename: str, content: str):
    path = os.path.join(session_dir, "artifacts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Detect base64 media (simple heuristic)
    if content.strip().startswith("data:"):
        # e.g. data:image/png;base64,....
        header, b64 = content.split(",", 1)
        raw = base64.b64decode(b64)
        ext = header.split(";")[0].split("/")[-1]   # png, mp3, etc.
        final_path = os.path.splitext(path)[0] + f".{ext}"
        with open(final_path, "wb") as f:
            f.write(raw)
        return final_path
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path


# ----------------------------------------------------------------------
# /finalize – receives canvas + vibe → creates ADK root_agent & runs
# ----------------------------------------------------------------------
@app.route("/finalize", methods=["POST"])
def finalize():
    data = request.json
    vibe = data.get("vibe", "")
    canvas_cfg = data.get("config", {})               # {nodes: [...], edges: [...]}
    root_id = data.get("root_node_id")                # user-selected root

    # ------------------------------------------------------------------
    # 1. Create session folder
    # ------------------------------------------------------------------
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"{ts}_{os.urandom(4).hex()}"
    session_dir = os.path.join(SESSIONS_ROOT, session_id)
    artifacts_dir = os.path.join(session_dir, "artifacts")
    staging_dir = os.path.join(session_dir, "staging")
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(staging_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 2. Build agents from canvas
    # ------------------------------------------------------------------
    agents = create_agents(canvas_cfg)

    if not root_id or root_id not in agents:
        # fallback – pick first node that contains "manager" in title (case-insensitive)
        for nid, ag in agents.items():
            if "manager" in ag.role.lower():
                root_id = nid
                break
        else:
            return jsonify({"error": "No root manager defined"}), 400

    root_agent: BaseAgent = agents[root_id]

    # ------------------------------------------------------------------
    # 3. Simple graph traversal (source → target)
    # ------------------------------------------------------------------
    edges = {e["source"]: e["target"] for e in canvas_cfg.get("edges", [])}
    log_lines: List[str] = []

    def run_node(node_id: str, incoming: str) -> str:
        ag = agents[node_id]
        out = ag.generate(incoming, vibe)
        # Save artifact
        safe_name = f"{node_id}_{ag.role.replace(' ', '_')}.txt"
        write_artifact(session_dir, safe_name, out)
        # Log
        log_lines.append(f"[{node_id} | {ag.role}] → {out[:120]}{'...' if len(out)>120 else ''}\n")
        return out

    # Kick-off with the root
    context = vibe
    current = root_id
    visited = set()

    while current and current not in visited:
        visited.add(current)
        context = run_node(current, context)
        current = edges.get(current)                     # follow single outgoing edge

    # ------------------------------------------------------------------
    # 4. Persist error / full log (never delete)
    # ------------------------------------------------------------------
    full_log = "\n".join(log_lines)
    with open(os.path.join(staging_dir, "run.log"), "w", encoding="utf-8") as f:
        f.write(full_log)

    # ------------------------------------------------------------------
    # 5. Return session info
    # ------------------------------------------------------------------
    return jsonify({
        "session_id": session_id,
        "preview_url": f"/output/{session_id}",
        "download_zip": f"/zip/{session_id}"
    })


# ----------------------------------------------------------------------
# Serve the built React app
# ----------------------------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if path.startswith("output/") or path.startswith("zip/"):
        return abort(404)          # handled by dedicated routes
    return app.send_static_file("index.html")


# ----------------------------------------------------------------------
# Preview route – loads generated index.html inside an iframe
# ----------------------------------------------------------------------
@app.route("/output/<session_id>")
def output(session_id):
    session_dir = os.path.join(SESSIONS_ROOT, session_id)
    index_path = os.path.join(session_dir, "artifacts", "index.html")
    if not os.path.exists(index_path):
        # fallback – try any html file
        for f in os.listdir(os.path.join(session_dir, "artifacts")):
            if f.endswith(".html"):
                index_path = os.path.join(session_dir, "artifacts", f)
                break
        else:
            return "No HTML generated yet.", 404

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
    # Simple wrapper so the iframe can be rotated, etc.
    wrapper = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Vibe Preview</title>
    <style>body,html,iframe{{margin:0;height:100%;width:100%;border:none}}</style>
    </head><body>
    <iframe srcdoc="{html.replace('"', '&quot;')}" frameborder="0"></iframe>
    </body></html>
    """
    return wrapper


# ----------------------------------------------------------------------
# Download a single file from staging/artifacts
# ----------------------------------------------------------------------
@app.route("/download/<session_id>/<path:filename>")
def download_file(session_id, filename):
    session_dir = os.path.join(SESSIONS_ROOT, session_id)
    return send_from_directory(session_dir, filename, as_attachment=True)


# ----------------------------------------------------------------------
# Full session zip (artifacts + staging logs)
# ----------------------------------------------------------------------
@app.route("/zip/<session_id>")
def zip_session(session_id):
    session_dir = os.path.join(SESSIONS_ROOT, session_id)
    if not os.path.isdir(session_dir):
        abort(404)

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(session_dir):
            for f in files:
                full = os.path.join(root, f)
                arcname = os.path.relpath(full, session_dir)
                z.write(full, arcname)
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"vibe_session_{session_id}.zip",
    )


# ----------------------------------------------------------------------
# Health check
# ----------------------------------------------------------------------
@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    # For local dev
    app.run(host="0.0.0.0", port=5000, debug=True)