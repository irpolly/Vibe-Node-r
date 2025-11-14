
import os
import io
import zipfile
from flask import Flask, request, jsonify, abort, send_from_directory, send_file
from flask_cors import CORS
from session import Session
import uuid
import threading
import vertexai

# --- App Initialization ---
app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app) # Enable Cross-Origin Resource Sharing for local dev
app.config['ARTIFACT_FOLDER'] = os.path.join(os.getcwd(), 'artifacts')

# --- Vertex AI Initialization ---
# In a Cloud Run environment, project and location can often be inferred.
# We'll initialize it here once at startup for robustness.
try:
    # The project and location are usually available as environment variables in Cloud Run.
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    location = os.environ.get('GOOGLE_CLOUD_REGION') # e.g., 'europe-west4'
    
    if not project_id or not location:
        print("⚠️  GOOGLE_CLOUD_PROJECT or GOOGLE_CLOUD_REGION not set. vertexai.init() will try to infer them.")
        # For local testing, you might need to set these manually or use `gcloud auth application-default login`
        vertexai.init()
        print("✅ Vertex AI initialized with inferred settings.")
    else:
        vertexai.init(project=project_id, location=location)
        print(f"✅ Vertex AI initialized successfully for project: {project_id} in location: {location}")

except Exception as e:
    # This will print a clear error to the logs if initialization fails, which is critical for debugging "Service Unavailable" errors.
    print(f"❌ FATAL: Failed to initialize Vertex AI: {e}")
    # This is a non-recoverable error, so we log it prominently. The app will likely fail health checks.


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

@app.route('/api/instruct', methods=['POST'])
def instruct_session():
    """
    Sends a new instruction to an active session for iterative changes.
    """
    data = request.json
    session_id = data.get('workflowId')
    instruction = data.get('instruction')

    if not session_id or not instruction:
        abort(400, description="Missing 'workflowId' or 'instruction' in request.")

    session = get_session(session_id)
    
    if session.is_running():
        abort(409, description="Session is already running. Please wait for the current task to complete.")

    # Run the instruction in a separate thread
    thread = threading.Thread(target=session.run_instruction, args=(instruction,))
    thread.start()
    
    print(f"🗣️ Kicking off instruction for session: {session_id}")
    return jsonify({"success": True, "message": "Instruction received and is being processed."}), 202


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

@app.route('/api/artifacts/zip/<session_id>')
def zip_artifacts(session_id):
    """Creates a zip file of all artifacts for a session and sends it."""
    session = get_session(session_id)
    directory = session.artifact_path
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in session.get_artifacts():
            file_path = os.path.join(directory, filename)
            if os.path.exists(file_path):
                zf.write(file_path, arcname=filename)
    
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        download_name=f'vibe-artifacts-{session_id}.zip',
        as_attachment=True,
        mimetype='application/zip'
    )


# --- Frontend Serving ---
# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    full_path = os.path.join(app.static_folder, path)
    # Use isfile to prevent a 500 error if the path is a directory.
    # os.path.exists returns True for directories, but send_from_directory
    # raises an exception, which can crash the server or cause health check failures.
    if path != "" and os.path.isfile(full_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['ARTIFACT_FOLDER']):
        os.makedirs(app.config['ARTIFACT_FOLDER'])
    app.run(debug=True, port=5000)
