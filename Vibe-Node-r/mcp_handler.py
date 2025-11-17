# mcp_handler.py
import json
from flask import request, jsonify
from vertexai.generative_models import GenerativeModel  # Reuse your Vertex setup
import subprocess  # For sandboxed exec (or hook Vertex code tool)

def handle_mcp_request(session_id: str):
    data = request.get_json()
    if data.get('type') == 'context_fetch':
        # Example: Pull artifacts from session
        from session import Session  # Import your Session
        sess = Session(session_id)  # Or fetch from global SESSIONS
        artifacts = sess.get_artifacts()
        return jsonify({'context': {'artifacts': artifacts}, 'status': 'success'})
    elif data.get('type') == 'code_exec':
        # Sandboxed Python/JS exec (use subprocess for Python; node for JS)
        code = data.get('code', '')
        try:
            result = subprocess.run(['python', '-c', code], capture_output=True, text=True, timeout=10)
            return jsonify({'output': result.stdout, 'error': result.stderr, 'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'})
    return jsonify({'error': 'Invalid MCP type', 'status': 'error'})

# Export for main.py import