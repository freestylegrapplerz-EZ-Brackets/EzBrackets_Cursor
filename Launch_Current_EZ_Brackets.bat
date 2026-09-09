@echo off
cd /d "%~dp0"
if exist "%~dp0..\.venv-codex\Scripts\python.exe" (
    "%~dp0..\.venv-codex\Scripts\python.exe" -m streamlit run app.py
) else if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m streamlit run app.py
) else (
    echo First follow the Python setup steps in README.md.
    pause
)
