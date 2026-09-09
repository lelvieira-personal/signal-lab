# DEPLOY — stub

`render/streamlit_app.py` runs locally today:

```bash
uv run --extra app streamlit run render/streamlit_app.py -- --synthetic
```

Entrypoint conventions for the internal deployment platform are unknown, so
nothing here is configured for it. This file lists what has to be confirmed
before that can happen. It is a list of questions, not a design.

## To confirm with whoever owns the platform

1. **Entrypoint.** Does the platform expect `streamlit run <file>`, a WSGI/ASGI
   callable, a container with a `CMD`, or a named function in a module? The app
   is a `main()` in `render/streamlit_app.py` and can be reshaped to any of
   these; picking one before asking would be guessing.
2. **Python version and dependency install.** This repo pins Python 3.12 and
   locks with `uv`. Does the platform build from `pyproject.toml`, from a
   `requirements.txt`, or from a container image? Streamlit is an optional
   extra (`[project.optional-dependencies] app`) and is not in the core
   dependency set.
3. **Working directory and repo layout.** `streamlit_app.py` puts `src/` and
   the repo root on `sys.path` relative to its own location. If the platform
   copies only a subtree, that breaks. Which paths are guaranteed present?
4. **Where the results store lives.** The app reads `results/runs.db`, a local
   SQLite file. On a platform with an ephemeral filesystem that file has to
   come from somewhere: a mounted volume, an object store sync at startup, or
   a different database entirely. SQLite over a network filesystem is not
   safe for concurrent writes, though this app only reads.
5. **Artifacts.** Run detail reads parquet from `results/artifacts/<run_id>/`.
   Same question as the store: mounted, synced, or absent.
6. **Access control.** The report contains no client data, no positions and no
   PII by construction (SUBSTRATE section 1), but it does contain research
   direction. Who can reach the URL, and is authentication the platform's job
   or the app's?
7. **Secrets.** The app itself needs none. If the platform injects environment
   variables, confirm the mechanism, because `params/data_sources.yaml` names
   `FRED_API_KEY` and nothing key-shaped is ever committed.
8. **Refresh.** Is the app expected to poll the store, or to be redeployed
   after each nightly cycle? Polling changes nothing in this code but does
   change whether the store can be a snapshot copy.
9. **Resource ceiling.** The synthetic mock builds 28 runs of weekly series in
   about a second and the static HTML is roughly 5 MB, most of it inlined
   plotly.js. Confirm memory and response-time limits before the real store
   grows past a few hundred runs.

## Not blocking

The static report (`render/static_report.py`) needs none of the above. It
writes one self-contained HTML file that opens from an attachment or a shared
drive with no server and no network, which is the fallback if the platform
question stays open.
