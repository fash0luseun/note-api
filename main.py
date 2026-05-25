"""
Notes API — Full CRUD with FastAPI
===================================
A REST API for managing notes, featuring:
- Full CRUD operations (Create, Read, Update, Delete)
- In-memory storage (no database needed)
- Strict HTTP status codes
- Input validation via Pydantic
- Pagination, filtering, and sorting (bonus)
- Custom request logging middleware (bonus)
- Auto-generated OpenAPI/Swagger docs (bonus — visit /docs)
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# ──────────────────────────────────────────────
# 1. LOGGING SETUP (Bonus: Observability)
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("notes_api")

# ──────────────────────────────────────────────
# 2. APP INITIALIZATION
# ──────────────────────────────────────────────
app = FastAPI(
    title="Notes API",
    description="A simple Notes API with full CRUD operations, validation, and pagination.",
    version="1.0.0",
)

# ──────────────────────────────────────────────
# 3. STATE MANAGEMENT (In-Memory Storage)
# ──────────────────────────────────────────────
# We use a dictionary for O(1) lookups by ID.
# In production, you'd replace this with a real database.
notes_db: dict[str, dict] = {}


# ──────────────────────────────────────────────
# 4. PYDANTIC MODELS (Input Validation)
# ──────────────────────────────────────────────
class NoteCreate(BaseModel):
    """Schema for creating a new note."""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the note")
    body: str = Field(..., min_length=1, max_length=10000, description="Body content of the note")
    tag: Optional[str] = Field(None, max_length=50, description="Optional tag for categorization")

    @field_validator("title", "body")
    @classmethod
    def must_not_be_blank(cls, v: str, info) -> str:
        if not v.strip():
            raise ValueError(f"{info.field_name} must not be blank or whitespace-only")
        return v.strip()


class NoteUpdate(BaseModel):
    """Schema for updating a note (partial updates allowed)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    body: Optional[str] = Field(None, min_length=1, max_length=10000)
    tag: Optional[str] = Field(None, max_length=50)

    @field_validator("title", "body")
    @classmethod
    def must_not_be_blank(cls, v, info):
        if v is not None and not v.strip():
            raise ValueError(f"{info.field_name} must not be blank or whitespace-only")
        return v.strip() if v else v


class NoteResponse(BaseModel):
    """Schema for the note returned in API responses."""
    id: str
    title: str
    body: str
    tag: Optional[str] = None
    created_at: str
    updated_at: str


# ──────────────────────────────────────────────
# 5. MIDDLEWARE (Bonus: Request Logging)
# ──────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Custom middleware that logs every incoming request."""
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


# ──────────────────────────────────────────────
# 6. CUSTOM VALIDATION ERROR HANDLER
# ──────────────────────────────────────────────
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 422 with structured, human-readable error messages."""
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": errors},
    )


# ──────────────────────────────────────────────
# 7. CRUD ENDPOINTS
# ──────────────────────────────────────────────

# ── CREATE ────────────────────────────────────
@app.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(note: NoteCreate):
    """
    Create a new note.

    - **title**: required, 1–200 characters
    - **body**: required, 1–10000 characters
    - **tag**: optional, for categorization

    Returns **201 Created** with the new note.
    """
    now = datetime.now(timezone.utc).isoformat()
    note_id = str(uuid.uuid4())

    new_note = {
        "id": note_id,
        "title": note.title,
        "body": note.body,
        "tag": note.tag,
        "created_at": now,
        "updated_at": now,
    }
    notes_db[note_id] = new_note
    return new_note


# ── READ (List all) ──────────────────────────
@app.get("/notes")
def list_notes(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Notes per page"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in title or body"),
    sort_by: str = Query("created_at", description="Sort field: created_at, updated_at, title"),
    order: str = Query("desc", description="Sort order: asc or desc"),
):
    """
    List all notes with pagination, filtering, and sorting.

    **Query parameters (all optional):**
    - `page` — page number (default: 1)
    - `limit` — results per page (default: 10, max: 100)
    - `tag` — filter by exact tag match
    - `search` — search in title and body (case-insensitive)
    - `sort_by` — field to sort by: created_at, updated_at, title
    - `order` — asc or desc (default: desc)

    Returns **200 OK** with paginated results.
    """
    # Start with all notes
    results = list(notes_db.values())

    # Filter by tag
    if tag:
        results = [n for n in results if n.get("tag") == tag]

    # Search in title/body
    if search:
        search_lower = search.lower()
        results = [
            n for n in results
            if search_lower in n["title"].lower() or search_lower in n["body"].lower()
        ]

    # Sort
    if sort_by not in ("created_at", "updated_at", "title"):
        sort_by = "created_at"
    reverse = order.lower() != "asc"
    results.sort(key=lambda n: n.get(sort_by, ""), reverse=reverse)

    # Pagination
    total = len(results)
    start = (page - 1) * limit
    end = start + limit
    paginated = results[start:end]

    return {
        "data": paginated,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": max(1, -(-total // limit)),  # ceiling division
        },
    }


# ── READ (Single) ────────────────────────────
@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: str):
    """
    Get a single note by its ID.

    Returns **200 OK** if found, **404 Not Found** if not.
    """
    note = notes_db.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id '{note_id}' not found")
    return note


# ── UPDATE (PATCH — partial update) ──────────
@app.patch("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: str, updates: NoteUpdate):
    """
    Update an existing note (partial update — only send the fields you want to change).

    Returns **200 OK** if updated, **404 Not Found** if not.
    Returns **422** if no valid fields are provided.
    """
    note = notes_db.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id '{note_id}' not found")

    # Apply only the fields that were actually sent
    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=422, detail="No fields provided to update")

    for key, value in update_data.items():
        note[key] = value

    note["updated_at"] = datetime.now(timezone.utc).isoformat()
    return note


# ── UPDATE (PUT — full replacement) ──────────
@app.put("/notes/{note_id}", response_model=NoteResponse)
def replace_note(note_id: str, note: NoteCreate):
    """
    Fully replace an existing note (all fields required).

    Returns **200 OK** if replaced, **404 Not Found** if not.
    """
    existing = notes_db.get(note_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Note with id '{note_id}' not found")

    existing["title"] = note.title
    existing["body"] = note.body
    existing["tag"] = note.tag
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    return existing


# ── DELETE ────────────────────────────────────
@app.delete("/notes/{note_id}", status_code=200)
def delete_note(note_id: str):
    """
    Delete a note by its ID.

    Returns **200 OK** with confirmation, **404 Not Found** if not.
    """
    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail=f"Note with id '{note_id}' not found")

    deleted_note = notes_db.pop(note_id)
    return {"detail": "Note deleted successfully", "deleted": deleted_note}


# ──────────────────────────────────────────────
# 8. HEALTH CHECK
# ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {"message": "Notes API is running", "docs": "/docs"}


# ──────────────────────────────────────────────
# 9. RUN THE SERVER
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
