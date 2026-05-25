<<<<<<< HEAD
# Notes API

A REST API for managing notes, built with FastAPI (Python).

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The server starts at `http://localhost:8000`.  
Interactive docs (Swagger UI) at `http://localhost:8000/docs`.

## API Endpoints

| Method | Endpoint        | Description         | Status Code |
|--------|-----------------|---------------------|-------------|
| POST   | `/notes`        | Create a note       | 201         |
| GET    | `/notes`        | List all notes       | 200         |
| GET    | `/notes/{id}`   | Get a single note    | 200         |
| PATCH  | `/notes/{id}`   | Partially update     | 200         |
| PUT    | `/notes/{id}`   | Fully replace        | 200         |
| DELETE | `/notes/{id}`   | Delete a note        | 200         |

## Example Requests (curl)

### Create a note
```bash
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Note", "body": "Hello world!", "tag": "general"}'
```

### List notes with pagination
```bash
curl "http://localhost:8000/notes?page=1&limit=5&sort_by=created_at&order=desc"
```

### Get a single note
```bash
curl http://localhost:8000/notes/{note_id}
```

### Update a note (partial)
```bash
curl -X PATCH http://localhost:8000/notes/{note_id} \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

### Delete a note
```bash
curl -X DELETE http://localhost:8000/notes/{note_id}
```

## Query Parameters for GET /notes

| Param     | Default      | Description                          |
|-----------|-------------|--------------------------------------|
| `page`    | 1           | Page number                          |
| `limit`   | 10          | Results per page (max 100)           |
| `tag`     | —           | Filter by exact tag                  |
| `search`  | —           | Search in title and body             |
| `sort_by` | created_at  | Sort by: created_at, updated_at, title |
| `order`   | desc        | Sort order: asc or desc              |
=======
# note-api
>>>>>>> 66c9cc5385229b9465605541c90a5122e20ca8f2
