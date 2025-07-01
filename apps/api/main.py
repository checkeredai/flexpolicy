from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware   # type: ignore # ← MUST be present
from pydantic import BaseModel # type: ignore
from supabase import create_client # type: ignore
import os

app = FastAPI()

# --- CORS so the browser accepts responses from :8000 -----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # front-end dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}

# --- Supabase admin client -----------------------------------------
SUPA_URL  = os.environ.get("SUPABASE_URL")
SUPA_KEY  = os.environ.get("SUPABASE_SERVICE_ROLE")  # use service role in dev
supabase  = create_client(SUPA_URL, SUPA_KEY)
# -------------------------------------------------------------------

class ItemIn(BaseModel):
    name: str

@app.post("/items")
def add_item(item: ItemIn):
    data = supabase.table("demo_items").insert({"name": item.name}).execute()
    return {"inserted": data.data}
