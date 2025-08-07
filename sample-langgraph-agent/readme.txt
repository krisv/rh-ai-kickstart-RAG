# Sample LangGraph Agent - Local Setup Instructions

## Prerequisites

- Python 3.7+
- pip (Python package installer)
- ollama

You can run a local llama stack using either ollama or openai (or both):
    ```bash
  export OLLAMA_URL=http://localhost:11434
  export OPENAI_API_KEY=put_your_key_here
  uv run --with llama-stack llama stack build --distro starter --image-type venv --run
    ```

## Configuration

The application is configured using environment variables. For convenience, you can manage these variables in two separate files:

- `config.env`: For non-sensitive configuration that can be safely checked into Git.
- `secret.env`: For secrets like your API key. This file is ignored by Git.

To get started, copy the provided `config.env.example` to `config.env` and `secret.env.example` to `secret.env` and fill in the required values.

## Manual Setup Instructions

1.  **Create a virtual environment** (only needs to be done once):
    ```bash
    python3 -m venv .venv
    ```

2.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```
    *Note: You must run this activation command every time you open a new terminal to work on this project.*

3.  **Install Dependencies** (only needs to be done once, or after pulling changes):
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  **Run the Application**:
    *Ensure your virtual environment is active first (`source .venv/bin/activate`)*

    When running locally, the application will automatically load the `config.env` and `secret.env` files.

    ```bash
    python3 app.py
    ```

5.  **Access the Application**:

    Open your web browser and go to `http://localhost:5000`.

---

## One-Step Setup

This command will create the virtual environment (if it doesn't exist) and install all dependencies.

```bash
python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt
```

## Background Execution

To run the application in the background and log all output to `output.log`, use the following command:

```bash
.venv/bin/python3 app.py > output.log 2>&1 &
```

## Running Tests

To ensure everything is set up correctly, you can run the automated tests.

*Ensure your virtual environment is active first (`source .venv/bin/activate`)*
```bash
pytest
```

## Podman Instructions

### Building the Image

1.  **Build the image**:

    ```bash
    podman build -t sample-langgraph-agent .
    ```

### Running the Container

1.  **Run the container**:

    ```bash
    podman run -d -p 8080:5000 --env-file config.env --env-file secret.env --name sample-langgraph-agent-test sample-langgraph-agent
    ```

2.  **Access the application**:

    Open your web browser and go to `http://localhost:8080`.

3.  **View logs**:

    ```bash
    podman logs sample-langgraph-agent-test
    ```

4.  **Stop and remove the container**:
    ```bash
    podman stop sample-langgraph-agent-test && podman rm sample-langgraph-agent-test
    ```

## Pushing the Image to Quay.io

After building your container image with Podman, you can share it by pushing it to a container registry like [Quay.io](https://quay.io).

1.  **Create a Quay.io Account**:
    If you don't have one already, go to [Quay.io](https://quay.io) and sign up for a free account.

2.  **Log in with Podman**:
    Use the `podman login` command to authenticate with your Quay.io credentials. You will be prompted for your username and password.
    ```bash
    podman login quay.io
    ```

3.  **Create a Public Repository**:
    In the Quay.io web interface, create a new **public** repository. It's best practice to name the repository the same as your image, for example, `sample-langgraph-agent`.

4.  **Tag the Image**:
    Before you can push the image, you need to tag it with your Quay.io username and the repository name. Replace `<your-username>` with your actual Quay.io username.
    ```bash
    podman tag sample-langgraph-agent:latest quay.io/<your-username>/sample-langgraph-agent:latest
    ```

5.  **Push the Image**:
    Now, push the tagged image to your Quay.io repository.
    ```bash
    podman push quay.io/<your-username>/sample-langgraph-agent:latest
    ```
    Your image is now available on Quay.io and can be pulled by others or deployed to a Kubernetes cluster.

## OpenShift Deployment

These instructions assume you have an OpenShift cluster and the `oc` command-line tool installed and configured.

### 1. Create a Project

If necessary, create a new project on your OpenShift cluster.
```bash
oc new-project sample-langgraph-agent
```
When using OpenShift Sandbox, you can skip this and just use the default <username>-dev

### 2. Create the API Key Secret

Create a secret from the `secret.env` file.

```bash
oc create secret generic openai-api-key --from-env-file=secret.env
```

### 3. Create the Configuration Map

Create a `ConfigMap` from the `config.env` file.

```bash
oc create configmap sample-langgraph-config --from-env-file=config.env
```

### 4. Apply the Deployment Files

Apply the YAML files in the `openshift` directory to deploy the application.

```bash
oc apply -f openshift/
```

### 5. Get the Application URL

```bash
oc get route sample-langgraph-agent --template='{{ .spec.host }}'
```

## Troubleshooting

- If you see a `ModuleNotFoundError`, it's likely your virtual environment is not active. Run `source .venv/bin/activate` and try again.
- Check the console output for any other error messages.