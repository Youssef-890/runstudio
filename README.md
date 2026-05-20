# RunStudio — Cloud REPL

Application web Flask : exécuter du **Python**, **JavaScript** et **C++** dans le navigateur ou sur le serveur, avec comptes utilisateurs et sauvegarde des scripts.

---

## Pour le professeur (démarrage rapide — Windows)

1. Ouvrir le dossier **`interactive-repl`** (pas `step1_only`).
2. Double-cliquer **`install.bat`** (une seule fois) — installe Flask et les dépendances.
3. Double-cliquer **`run.bat`** — démarre le serveur.
4. Ouvrir dans le navigateur : **http://127.0.0.1:5000/**

**Test rapide :** laisser le langage *Python*, cliquer **Run** → la sortie doit afficher les résultats de `print` (ex. `Hello`).

**Compte utilisateur (optionnel) :** *Create account* → enregistrer un nom d’utilisateur → *Save to workspace* pour sauvegarder un script côté serveur.

**Vérification automatique (optionnel) :**

```powershell
cd interactive-repl
.\install.bat
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest tests/test_app.py
```

---

## What to submit (zip)

Include the **`interactive-repl`** folder **without**:

- `.venv/` or `step1_only/.venv/` (virtual environments — too large)
- `database/app.db` (created automatically on first run)
- `.pytest_cache/`

The teacher runs **`install.bat`** then **`run.bat`**.

---

## Run locally (manual)

```bash
cd interactive-repl
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
set FLASK_DEBUG=1
python app.py
```

Open **http://127.0.0.1:5000/**

| Feature | Notes |
|--------|--------|
| Python (server) | Restricted builtins — local/trusted use only |
| Python (browser) | Pyodide via CDN — needs internet |
| JavaScript (server) | Requires **Node.js** on PATH |
| C++ (server) | Requires **g++** or **clang++** (see below) |

---

## Project structure

```
interactive-repl/
  app.py              # Flask entry point
  routes/             # HTTP: auth, execute, scripts API
  services/           # Python sandbox, Node, C++ runners
  models/             # Users (SQLite)
  templates/          # HTML pages
  static/             # CSS, JavaScript
  database/schema.sql # SQLite schema
  tests/              # Smoke tests (pytest)
  install.bat / run.bat
```

The folder **`step1_only/`** is an old step-1 prototype — **do not use it** for grading; use the project root above.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/execute` | JSON `code`, `language` (`python` \| `javascript` \| `cpp`) |
| GET/POST | `/login`, `/register` | Session auth |
| GET | `/logout` | End session |
| GET/POST/PUT/DELETE | `/api/scripts` | CRUD (logged-in user only) |

---

## C++ on Windows (optional)

**Recommended:** [MSYS2](https://www.msys2.org/) → `pacman -S mingw-w64-ucrt-x86_64-gcc` → add `C:\msys64\ucrt64\bin` to PATH.

Without a compiler, Python and JavaScript (browser mode) still work.

---

## Security note

Python server mode uses a restricted builtin set, not full isolation. JS/C++ run as OS processes — for trusted / educational environments only.

Set **`SECRET_KEY`** in production (environment variable).
