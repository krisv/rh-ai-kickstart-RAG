# Idea Vault - Local Setup Instructions

## Prerequisites

- Python 3.7+
- pip (Python package installer)

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
    pip install -r requirements.txt
    ```

4.  **Run the Application**:
    *Ensure your virtual environment is active first (`source .venv/bin/activate`)*
    ```bash
    python3 app.py
    ```

5.  **Access the Application**:

    Open your web browser and go to `http://localhost:5000`.

---

## One-Step Setup and Run

If you want to set up and run the project in a single command in the background, you can use the following. This command will create the virtual environment (if it doesn't exist), install all dependencies, and start the application.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python3 app.py &
```

## Running Tests

To ensure everything is set up correctly, you can run the automated tests.

*Ensure your virtual environment is active first (`source .venv/bin/activate`)*
```bash
pytest
```

## Troubleshooting

- If you see a `ModuleNotFoundError`, it's likely your virtual environment is not active. Run `source .venv/bin/activate` and try again.
- Check the console output for any other error messages.