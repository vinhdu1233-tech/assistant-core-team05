# assistant-core-team05

CSC10014 · Smart Virtual Assistant · Team 05

## Run the Lab 07 app

From the repository root, activate a Python virtual environment and install the app:

```shell
python -m pip install -r requirements.txt
python -m pip install -e .
```

Start FastAPI in the first terminal:

```shell
python -m uvicorn assistant_api.main:create_app --factory
```

In a second terminal, activate the same environment and start Streamlit:

```shell
python -m streamlit run ui/app.py
```

Open <http://localhost:8501>. The API health endpoint is <http://localhost:8000/health>.
See the [Windows setup guide](docs/lab07/setup.md) for environment activation.
The [integrated browser results](docs/lab07/m5_e2e_test_checklist.md) cover the chat workflow, feedback, phone layout and service failures.

## Source materials
- Tutorial and starter monolith: https://github.com/CSC10014-at-fit-hcmus/public_materials/tree/main/lab03
- Local starter: `git clone https://github.com/CSC10014-at-fit-hcmus/public_materials.git`, then open `public_materials/lab03/monolith`.

## Team workflow
1. Read [team module contracts](docs/team_contracts.md) before coding.
2. Create your own `feature/mX-...` branch from `main` and work only on the assigned files.
3. Open a pull request to `main`, include tests or a test plan and request review.
4. Tech Lead integrates reviewed PRs, runs `python -m pytest -q` and `python -m ruff check .`.
5. Once integrated and tested, Tech Lead creates tag `v0.3-core`.

**Individual work still required by the tutorial:** own refactor PR, `docs/lab3/before_after.md`, H1 AI-extension review, and AI-use log; confirm assessment expectations with the instructor if using divided-module PRs.

Do not commit actual `.env`, credentials, `.venv` or `__pycache__`.

## Functional requirements
Greetings, deterministic tuition calculations, CSV office lookup, handbook JSON rule search with source attribution, provider fallback, CLI and structured secret-free logging.

## Members
- M1 `vinhdu1233-tech`: service, CLI, architecture, integration and tag.
- M2 `TuanTu2205`: config and logging.
- M3 `tree312-coder`: knowledge and responder.
- M4 `dmdung2520`: tools, router, tests, Ruff CI.
- M5 `fumeneko`: .env.example and .gitignore.
- M6 `lnmthi`: typed models, errors, pyproject.toml, pinned requirements.
