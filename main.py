from fastapi import Depends
from auth import get_current_user
import dal_users as dau

"""
main.py — NeuralOrbit entry point
Run with:  python main.py
  or:      uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os

# ── Import routers ────────────────────────────────
from router_users import router as users_router
from router_models import router as models_router

# ── Also ensure models DB table is initialised ────
import dal_models as dam
DB_NAME_MODELS = "models.db"
dam.dm_create_table(DB_NAME_MODELS)

# ── App ───────────────────────────────────────────
app = FastAPI(
    title="NeuralOrbit API",
    description="ML Platform — polynomial regression as a service",
    version="1.0.0",
)

# ── CORS — allow the local HTML pages to call the API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────
app.include_router(users_router)
app.include_router(models_router)

# ── Serve the frontend HTML files ─────────────────
# Place index.html and dashboard.html in the same folder as main.py
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", include_in_schema=False)
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "index.html not found — place it next to main.py"}

@app.get("/dashboard.html", include_in_schema=False)
def serve_dashboard():
    dash_path = os.path.join(FRONTEND_DIR, "dashboard.html")
    if os.path.exists(dash_path):
        return FileResponse(dash_path)
    return {"message": "/dashboard.html not found — place it next to main.py"}

@app.get("/index.html", include_in_schema=False)
def serve_index_explicit():
    return serve_index()

# ── /users/me — convenience endpoint the dashboard needs ─
# (adds a proper /users/me so the token owner can fetch their own data)


DB_NAME_USERS = "users.db"

@app.get("/users/me", tags=["Users"])
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    user = dau.du_get_user_by_user_name(current_user["user_name"], DB_NAME_USERS)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    # Never expose the hashed password
    return {k: v for k, v in user.items() if k != "password"}


# ── Run ───────────────────────────────────────────
if __name__ == "__main__":
    print("\n🪐  ML Industry is launching...")
    print("   API docs  →  http://127.0.0.1:8000/docs")
    print("   Frontend  →  http://127.0.0.1:8000/\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
