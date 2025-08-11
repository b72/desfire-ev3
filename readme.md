# Project Setup Guide

## 1. Create a Python Virtual Environment (optional)

```bash
python -m venv YourEnv
```

## 2. Activate the Virtual Environment (optional)

- **Windows:**
    ```bash
    YourEnv\Scripts\activate.bat
    ```
- **macOS/Linux:**
    ```bash
    source YourEnv/bin/activate
    ```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create a `.env` file in the project root and update the values as needed.

## 5. Run the Project

```bash
python test.py
```