# FastAPI Startup Troubleshooting

## Issue 1

### Error

ModuleNotFoundError: No module named 'app'

### Cause

The server was started from the wrong directory.

### Resolution

Navigate to:

services/runtime-api

Run:

uvicorn app.main:app --reload

---

## Issue 2

### Error

Attribute "app" not found in module "app.main"

### Cause

main.py did not contain the FastAPI application object.

### Resolution

Define:

app = FastAPI(...)

---

## Lessons Learned

- Always run Uvicorn from the project root.
- Verify the FastAPI application object exists.
- Test imports directly with Python before running Uvicorn.