
# Vibe Node(r) - AI Agentic Workflow Builder

This project is an AI-driven workflow builder that turns vague ideas ("vibes") into functional outputs using multi-agent systems. You can design, constrain, and execute agentic workflows on a customizable canvas, then interact with the generated output in real-time.

## Features

- **Live Gemini Integration**: Agents make real-time calls to the Gemini API to generate dynamic, unique responses for every run.
- **Visual Workflow Canvas**: Use a drag-and-drop interface powered by React Flow to design and modify agent workflows.
- **Session Management**: Creates a unique, sandboxed "session" for each deployed workflow.
- **Dynamic Agent Orchestration**: Instantiates and runs different agent classes (`Manager`, `Coder`, `Designer`, etc.) based on the workflow designed in the frontend.
- **Stateful Execution**: Each session tracks its own state, including a log of live agent messages and generated file artifacts.
- **Multi-File Artifact Generation**: The Coder agent can generate entire projects with multiple files (HTML, CSS, JS).
- **Live Preview & Download**: View the generated `index.html` in a live iframe and download all created artifacts.

## How to Run Locally

1.  **Prerequisites**:
    *   Python 3.8+
    *   Node.js 20+ & npm
    *   `pip` for Python package installation

2.  **Create a Python Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**:
    Install both the Python and Node.js dependencies.
    ```bash
    # Install Python packages
    pip install -r requirements.txt

    # Install Node.js packages
    npm install
    ```

4.  **Set Gemini API Key**:
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

5.  **Run the Development Servers**:
    You will need to run the frontend (Vite) and backend (Flask) servers in separate terminals.

    **Terminal 1: Start the Backend (Flask)**
    ```bash
    flask --app main run
    ```
    The backend will be available at `http://127.0.0.1:5000`.

    **Terminal 2: Start the Frontend (Vite)**
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://127.0.0.1:5173` (or another port if 5173 is busy). Open this URL in your browser.

---

## How to Integrate Google AdSense

To monetize the application while users wait for the agents to generate code, you can integrate Google AdSense. You will need your own AdSense account.

### Step 1: Find Your Publisher ID

1.  Sign in to your AdSense account.
2.  Click **Account**.
3.  Click **Settings**, then **Account information**.
4.  Your Publisher ID is displayed here (e.g., `pub-1234567890123456`).

### Step 2: Update `index.html`

Open the `index.html` file and find the AdSense script tag in the `<head>` section. Replace the placeholder `ca-pub-XXXXXXXXXXXXXXXX` with your actual Publisher ID.

```html
<!-- In index.html -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=YOUR_PUBLISHER_ID"
     crossorigin="anonymous"></script>
```

### Step 3: Create an Ad Unit & Get the Ad Slot ID

1.  In your AdSense account, go to **Ads > By ad unit**.
2.  Create a new **Display ad**.
3.  Give it a name (e.g., "Vibe-Node-r Wait Time Ad").
4.  Choose your desired ad size (Responsive is recommended).
5.  Click **Create**.
6.  AdSense will show you a code snippet. You only need the **Ad Slot ID** from this snippet. It will be a number like `1234567890`.

### Step 4: Update `OutputPage.tsx`

Open the `pages/OutputPage.tsx` file. Find the `<AdSenseAd />` component and replace the placeholder `YYYYYYYYYY` in the `slot` prop with your actual Ad Slot ID.

```tsx
// In pages/OutputPage.tsx

// ... inside the OutputPage component's return statement
<AdSenseAd slot="YOUR_AD_SLOT_ID" /> 
```

After completing these steps, AdSense will be configured to display ads on the output page. It may take some time for ads to start appearing after you first set up an ad unit.
