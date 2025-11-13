# Vibe Node(r) 🚀

**Vibe Node(r)** is a dynamic, AI-driven workflow builder that transforms your vague ideas—or "vibes"—into functional, interactive web applications. Using a powerful multi-agent system powered by Google's Gemini API, you can visually design, constrain, and execute complex agentic workflows on a customizable canvas, bringing your concepts to life in minutes.

![Vibe Node(r) in action](https://storage.googleapis.com/vibe-node-r-assets/vibe-node-r-demo.gif)

## ✨ Core Features

-   **Visual Agentic Workflow Builder**: Design complex agent collaborations with a sleek, intuitive drag-and-drop interface powered by React Flow. Add, connect, and configure agents to create your ideal team.
-   **Live Gemini-Powered Agents**: Each agent is an autonomous entity making real-time calls to the Gemini API (`gemini-2.5-flash`) for dynamic reasoning, planning, and content generation.
-   **Vibe-to-Code Generation**: Start with a simple, high-level "vibe" (e.g., "a cat that uses portals to steal fish") and watch as the agents collaborate to generate a complete, playable web game.
-   **Real-Time Collaboration Log**: Monitor the agents' progress and decision-making process through a live-updating chat log that shows their "conversation."
-   **Interactive Live Preview**: The generated web application is instantly available for testing in a built-in smartphone emulator, which can be rotated for landscape or portrait mode.
-   **Iterative Development & Live Edits**: Once the initial version is created, send new instructions to the agents (e.g., "make the player faster" or "change the background to blue") and watch them modify the code in real-time.
-   **Full Artifact Management**: Download individual generated files (HTML, JS, CSS) or get a complete `.zip` archive of the entire project with a single click.
-   **Customizable Agents**: Double-click any agent on the canvas to configure its role, core goal, and the tools it has access to, allowing for fine-grained control over the workflow.
-   **Persistent Workflows**: Your workflow designs are automatically saved to your browser's local storage, so you can pick up right where you left off.

## 🛠️ Tech Stack

-   **Frontend**: React, TypeScript, Vite, React Flow, Tailwind CSS
-   **Backend**: Python, Flask, Gunicorn
-   **AI**: Google Gemini API via the Vertex AI SDK
-   **Deployment**: Containerized with Docker, ready for Google Cloud Run

## ⚙️ How It Works

1.  **Design**: On the **Builder Page**, you arrange and connect agent nodes (e.g., `Manager`, `Coder`, `Designer`, `Tester`) on the canvas to define the workflow structure.
2.  **Deploy**: When you click "Finalize & Run," the workflow configuration is sent to the Flask backend, which spins up a new, isolated `Session`.
3.  **Execute**: On the **Output Page**, you provide a "vibe" and optional instructions. This kicks off the root agent (typically the `Manager Agent`) in the session.
4.  **Collaborate**: The agents begin their work, communicating with each other and using the Gemini API to perform their specialized tasks—from writing a story to designing assets and generating code.
5.  **Generate**: The `Coder Agent` writes a complete project structure—typically `index.html`, `style.css`, and `game.js`—and saves them as artifacts within the session.
6.  **Preview & Iterate**: The generated `index.html` is loaded into the live preview emulator. You can then send new text-based instructions to the agents to refine or change the application.

## 🚀 Getting Started Locally

Follow these steps to run Vibe Node(r) on your local machine.

### 1. Prerequisites

-   Python 3.9+
-   Node.js 20+ & npm
-   `pip` for Python package installation
-   Google Cloud SDK (`gcloud` CLI)

### 2. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 3. Set Up the Backend (Python)

First, create and activate a Python virtual environment.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

Next, install the required Python packages.

```bash
pip install -r requirements.txt
```

### 4. Set Up the Frontend (Node.js)

Install the necessary Node.js dependencies.

```bash
npm install
```

### 5. Authenticate to Google Cloud

The application uses **Application Default Credentials (ADC)** to authenticate to the Vertex AI API. It does **not** use an `API_KEY` environment variable.

For local development, authenticate the `gcloud` CLI. This will open a browser window to log in with your Google account. The account must have the **"Vertex AI User"** role in your target GCP project.

```bash
gcloud auth application-default login
```

You also need to set your project ID for the SDK to find it.

```bash
gcloud config set project YOUR_PROJECT_ID_HERE
```

### 6. Run the Application

The backend is a Flask server that also serves the built frontend files. You must build the frontend first.

**Terminal 1: Build the Frontend**

This command compiles the React/TypeScript app into static HTML, CSS, and JS files in a `build` directory.

```bash
npm run build
```

**Terminal 2: Start the Backend**

Make sure your Python virtual environment is still activated. This command runs the Flask server, which will automatically serve the files from the `build` directory.

```bash
flask --app main run
```

The backend will start on `http://127.0.0.1:5000`. **Open this URL in your browser** to use the application.

(Note: `npm run dev` is only for advanced frontend development and will not connect to the Python backend without further configuration.)

## ☁️ Deployment

This application is pre-configured for easy deployment to serverless platforms like **Google Cloud Run**.

The included `Dockerfile` creates a production-ready container that builds the frontend, installs the backend dependencies, and runs the application with a Gunicorn server. When deploying to Cloud Run, ensure the service's runtime service account has the **"Vertex AI User"** IAM role.
