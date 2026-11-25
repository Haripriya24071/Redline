# HEMS-Link (Redline)

**Multi-Hospital Emergency Patient Transfer & Coordination System**  
Operating Systems Case Study Prototype — III Semester, CSE (AI), Jain (Deemed-to-be) University.

> **Disclaimer:** Academic prototype using simulated hospital data for decision support only. It does not replace clinical judgement.

## Project Structure
- `os_engine/` — Complete OS Engine (`scheduler.py`, `matcher.py`, `reservation.py`, `banker.py`, `deadlock.py`, `workers.py`, `simulator.py`)
- `app.py` — Flask server & API routes
- `templates/` & `static/` — Liquid Glass UI with tactile keycap buttons, 9 screens + Style Guide, Light/Dark themes, and EN/HI/KN i18n
- `tests/` — Automated pytest suite covering T1–T12
- `contract.md` — Frozen API contract & data model spec
- `docs/a11y_report.md` — Accessibility walkthrough checklist

## Run Instructions
```bash
py -3 -m pip install -r requirements.txt
py -3 app.py
```
Open `http://127.0.0.1:5000` in your browser.

## Run Tests
```bash
py -3 -m pytest -v
```

