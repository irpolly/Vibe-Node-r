# main.py (improved)
import os
import io
import zipfile
from flask import Flask, request, jsonify, abort, send_from_directory, send_file
from flask_cors import CORS
from session import Session
import uuid
import threading
import vertexai

app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app)
app.config['ARTIFACT_FOLDER'] = os.path.join(os.getcwd(), 'artifacts')

# --- Vertex AI Initialization (unchanged) ---
try:
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    location = os.environ.get('GOOGLE_CLOUD_REGION')
    if not project_id or not location:
        vertexai.init()
    else:
        vertexai.init(project=project_id, location=location)
    print(f"Vertex AI initialized")
except Exception as e:
    print(f"FATAL: Failed to initialize Vertex AI: {e}")

SESSIONS = {}  # Restore in-memory for quick access

def get_session(session_id):
    session = SESSIONS.get(session_id)
    if not session:
        abort(404, description=f"Session '{session_id}' not found.")
    return session

# Restore /api/deploy (from old) + integrate new FS
@app.route('/api/deploy', methods=['POST'])
def deploy_workflow():
    workflow_data = request.json
    if not workflow_data or 'nodes' not in workflow_data or 'edges' not in workflow_data:
        abort(400, description="Invalid workflow data.")

    session_id = str(uuid.uuid4())
    artifact_path = os.path.join(app.config['ARTIFACT_FOLDER'], session_id)
    os.makedirs(artifact_path, exist_ok=True)

    new_session = Session(session_id, workflow_data, artifact_path)  # Assuming Session has __init__
    SESSIONS[session_id] = new_session
    return jsonify({"success": True, "workflowId": session_id}), 201

# Restore /api/run (from old, threaded)
@app.route('/api/run', methods=['POST'])
def run_session():
    data = request.json
    session_id = data.get('workflowId')
    vibe = data.get('vibe')
    instructions = data.get('instructions')

    if not session_id or not vibe:
        abort(400, description="Missing 'workflowId' or 'vibe'.")

    session = get_session(session_id)
    if session.is_running():
        abort(409, description="Session already running.")

    thread = threading.Thread(target=session.run_workflow, args=(vibe, instructions))
    thread.start()
    return jsonify({"success": True, "message": "Workflow started."}), 202

# Restore /api/instruct (from old)
@app.route('/api/instruct', methods=['POST'])
def instruct_session():
    data = request.json
    session_id = data.get('workflowId')
    instruction = data.get('instruction')

    if not session_id or not instruction:
        abort(400, description="Missing 'workflowId' or 'instruction'.")

    session = get_session(session_id)
    if session.is_running():
        abort(409, description="Session busy.")

    thread = threading.Thread(target=session.run_instruction, args=(instruction,))
    thread.start()
    return jsonify({"success": True, "message": "Instruction processing."}), 202

# Restore /api/status (from old, for polling in OutputPage.tsx)
@app.route('/api/status/<session_id>', methods=['GET'])
def get_status(session_id):
    session = get_session(session_id)
    return jsonify({
        "sessionId": session.session_id,
        "status": session.get_status(),
        "messages": [msg.to_dict() for msg in session.get_messages()],
        "artifacts": session.get_artifacts()
    })

# Keep new /output, /zip, /health, catch_all

if __name__ == '__main__':
    if not os.path.exists(app.config['ARTIFACT_FOLDER']):
        os.makedirs(app.config['ARTIFACT_FOLDER'])
    app.run(debug=True, port=5000)