
import os
from flask import Flask, request, jsonify, abort, send_from_directory
from flask_cors import CORS
from session import Session
import uuid
import threading

# --- App Initialization ---
app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app) # Enable Cross-Origin Resource Sharing for local dev
app.config['ARTIFACT_FOLDER'] = os.path.join(os.getcwd(), 'artifacts')

# In-memory storage for active sessions. In a production environment,
# this would be replaced with a database like Redis or Firestore.
SESSIONS = {}

# --- Helper Functions ---
def get_session(session_id):
    """Retrieves a session or aborts if not found."""
    session = SESSIONS.get(session_id)
    if not session:
        abort(404, description=f"Session with ID '{session_id}' not found.")
    return session

# --- API Endpoints ---
@app.route('/api/deploy', methods=['POST'])
def deploy_workflow():
    """
    Creates a new virtual environment (Session) for a given workflow.
    """
    workflow_data = request.json
    if not workflow_data or 'nodes' not in workflow_data or 'edges' not in workflow_data:
        abort(400, description="Invalid workflow data provided.")

    session_id = str(uuid.uuid4())
    artifact_path = os.path.join(app.config['ARTIFACT_FOLDER'], session_id)
    
    try:
        new_session = Session(session_id, workflow_data, artifact_path)
        SESSIONS[session_id] = new_session
        print(f"✅ New session created: {session_id}. Total sessions: {len(SESSIONS)}")
        return jsonify({"success": True, "workflowId": session_id}), 201
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        abort(500, description=f"Failed to prepare the session environment: {e}")

@app.route('/api/run', methods=['POST'])
def run_session():
    """
    Starts the execution of a deployed workflow with a user-provided vibe.
    This runs the agent workflow in a background thread to not block the API.
    """
    data = request.json
    session_id = data.get('workflowId')
    vibe = data.get('vibe')
    instructions = data.get('instructions') # Can be None

    if not session_id or not vibe:
        abort(400, description="Missing 'workflowId' or 'vibe' in request.")

    session = get_session(session_id)
    
    if session.is_running():
        abort(409, description="Session is already running.")

    # Run the workflow in a separate thread to avoid blocking the request
    thread = threading.Thread(target=session.run_workflow, args=(vibe, instructions))
    thread.start()
    
    print(f"🚀 Kicking off workflow for session: {session_id}")
    return jsonify({"success": True, "message": "Workflow execution started."}), 202

@app.route('/api/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """
    Pollable endpoint for the frontend to get the latest status,
    messages, and artifacts from a running session.
    """
    session = get_session(session_id)
    
    return jsonify({
        "sessionId": session.session_id,
        "status": session.get_status(),
        "messages": [msg.to_dict() for msg in session.get_messages()],
        "artifacts": session.get_artifacts()
    })

@app.route('/api/artifacts/<session_id>/<path:filename>')
def serve_artifact(session_id, filename):
    """Serves a generated artifact file from a session's directory."""
    session = get_session(session_id)
    directory = session.artifact_path
    print(f"Serving artifact: {filename} from {directory}")
    return send_from_directory(directory, filename)

# --- Frontend Serving ---
# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['ARTIFACT_FOLDER']):
        os.makedirs(app.config['ARTIFACT_FOLDER'])
    app.run(debug=True, port=5000)
