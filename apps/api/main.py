"""
apps/api/main.py – minimal FastAPI back-end for FlexPolicy
──────────────────────────────────────────────────────────
* /health  – liveness probe
* /        – friendly index
* /items   – insert a demo row into Supabase
* /draft   – stream GPT chat completions token-by-token (SSE)

Works with the public OpenAI endpoint (set OPENAI_API_KEY + OPENAI_MODEL
in apps/api/.env).  Supabase uses SERVICE_ROLE only in local dev.
"""

from __future__ import annotations

###############################################################################
# Imports                                                                     #
###############################################################################

import asyncio
import os
from typing import AsyncGenerator, Tuple

from dotenv import load_dotenv              # type: ignore
from fastapi import FastAPI, HTTPException  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from openai import OpenAI, OpenAIError      # type: ignore
from pydantic import BaseModel              # type: ignore
from sse_starlette.sse import EventSourceResponse   # type: ignore
from supabase import Client as SupabaseClient, create_client  # type: ignore

###############################################################################
# Environment / top-level config                                              #
###############################################################################

load_dotenv("apps/api/.env", override=False)

# ── OpenAI ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing – add it to apps/api/.env")

openai_client: OpenAI = OpenAI(api_key=OPENAI_API_KEY)

# ── Supabase ───────────────────────────────────────────────────────────────
SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE: str | None = os.getenv("SUPABASE_SERVICE_ROLE")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE):
    raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE missing in .env")

supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# ── FastAPI instance & CORS ────────────────────────────────────────────────
app = FastAPI(title="FlexPolicy API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

###############################################################################
# Helpers                                                                     #
###############################################################################


def unwrap_error(exc: OpenAIError) -> Tuple[int, str]:
    """
    Map any OpenAI SDK error → (status_code, short_code).

    * Azure errors expose `status_code` + `error`/`code`
    * Public endpoint errors expose `status_code` + `code`
    * RateLimitError sets `code=None`
    """
    status = getattr(exc, "status_code", 500)
    short = getattr(exc, "code", None) or exc.__class__.__name__
    return status, str(short)


###############################################################################
# Pydantic schemas                                                            #
###############################################################################


class DraftIn(BaseModel):
    prompt: str


class ItemIn(BaseModel):
    name: str


###############################################################################
# Routes                                                                      #
###############################################################################


@app.get("/", include_in_schema=False)
async def index() -> dict[str, str]:
    """Welcome banner (avoids 404 on `/`)."""
    return {"service": "FlexPolicy API", "status": "ok"}


@app.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/items", summary="Insert a demo row into Supabase")
async def add_item(item: ItemIn) -> dict[str, object]:
    """Insert *item.name* into public.demo_items and return Supabase response."""
    resp = supabase.table("demo_items").insert({"name": item.name}).execute()
    return {"inserted": resp.data}


@app.post("/draft", summary="Stream GPT response via SSE")
async def draft(req: DraftIn) -> EventSourceResponse:
    """
    Stream GPT chat completions token-by-token.

    Browser consumes this as an EventSource (Server-Sent Events).
    """

    async def talk_to_gpt() -> AsyncGenerator[dict[str, str], None]:
        buffer: list[str] = []  # collect ~10 tokens before flushing – smoother UI
        try:
            stream = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                temperature=0.2,
                stream=True,
                messages=[
                    {"role": "system", "content": "Ontario ESA policy assistant"},
                    {"role": "user", "content": req.prompt},
                ],
            )

            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    buffer.append(token)

                if len(buffer) >= 10:
                    yield {"data": "".join(buffer)}
                    buffer.clear()

                await asyncio.sleep(0)  # cooperative yield

            if buffer:
                yield {"data": "".join(buffer)}

        except OpenAIError as exc:  # covers RateLimitError, APIError, etc.
            status, short = unwrap_error(exc)
            yield {"event": "error", "data": f"{status}:{short}"}

    return EventSourceResponse(talk_to_gpt())


################################################################################
# End                                                                         ##
################################################################################