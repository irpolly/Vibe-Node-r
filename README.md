
# Vibe Coder - Live ADK Backend

This directory contains the live Python backend for the Vibe Coder application. It uses Flask to create a simple API that orchestrates a multi-agent workflow powered by the **live Gemini API**. This is not a simulation.

## Features

- **Live Gemini Integration**: Agents make real-time calls to the Gemini API to generate dynamic, unique responses for every run.
- **Session Management**: Creates a unique, sandboxed "session" for each deployed workflow.
- **Dynamic Agent Orchestration**: Instantiates and runs different agent classes (`Manager`, `Coder`, `Designer`, etc.) based on the workflow designed in the frontend.
- **Stateful Execution**: Each session tracks its own state, including a log of live agent messages and generated file artifacts.
- **API Interface**: Provides endpoints for the frontend to deploy, run, and check the status of a workflow.

## How to Run

1.  **Prerequisites**:
    *   Python 3.8+
    *   `pip` for package installation

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**:
    Install the required packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set API Key Environment Variable**:
    You must set your Gemini API key as an environment variable for the backend to function.
    
    On **Mac/Linux**:
    ```bash
    export API_KEY="YOUR_API_KEY_HERE"
    ```
    On **Windows (Command Prompt)**:
    ```bash
    set API_KEY="YOUR_API_KEY_HERE"
    ```
    On **Windows (PowerShell)**:
    ```powershell
    $env:API_KEY="YOUR_API_KEY_HERE"
    ```

5.  **Run the Server**:
    Start the Flask development server.
    ```bash
    flask --app main run
    ```
    The server will start and listen for requests on `http://127.0.0.1:5000`. The frontend application can now connect to this backend.

## API Endpoints

- `POST /deploy`
  - **Body**: JSON object representing the workflow from the React Flow canvas.
  - **Response**: Creates a new session and returns a unique `workflowId`.

- `POST /run`
  - **Body**: `{ "workflowId": "...", "vibe": "..." }`
  - **Response**: Starts the live agent execution for the given session in a background thread.

- `GET /status/<session_id>`
  - **Response**: Returns the current status (`PENDING`, `RUNNING`, `COMPLETED`), a list of agent messages, and a list of generated artifacts for the session.

- `GET /artifacts/<session_id>/<filename>`
  - **Response**: Serves the content of a generated file (e.g., `index.html`).
