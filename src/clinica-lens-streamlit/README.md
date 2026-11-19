# Clinica-lens Streamlit UI

Demo UI: login, streaming chat, per-user conversation history.
The UI never touches the database. It only calls the FastAPI service with a Bearer token.

## Run

```bash
pip install -r requirements.txt
API_BASE=http://localhost:8000/api/v1 streamlit run app.py
```

Docker: `docker build -t clinica-lens-ui . && docker run -p 8501:8501 -e API_BASE=http://host:8000/api/v1 clinica-lens-ui`

## API contract the backend must provide

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/login` | body `{user_name, password}` -> `{access_token}`; 401 on bad credentials |
| POST | `/threads` | -> `threads_id` for the context |
| GET | `/threads/{thread_id}` | -> `{messages: [{role, content}]}`; 404 if not found **or not owned by the user** |
| POST | `/threads/{thread_id}/runs` | body `{question, thread_id}`; SSE `data:` events |

SSE events: `{"token": "..."}`, `{"status": "querying database"}`, `{"done": true, "request_id": "..."}`, `{"error": "..."}`.


## Encountered bugs and solutions
1. Auth: 422 Unprocessable Entity
The error comes from the validation of request format
- if we use OAuth2PasswordRequestForm in FastAPI to handle auth, the script must be:
```python
httpx.post(
            f"{API_BASE}/auth/login",
            data={"username": user_name, "password": password},
            timeout=_TIMEOUT,
        )
```
    with request body `data`, with `username` and `password`. Error made: `json` instead of `data`, `user_name` instead of `username` as key.

2. Send request: status_code": 404
- check if route in added into router

3. TypeError: AsyncBatchedBaseStore.asearch() got some positional-only arguments passed as keyword arguments: 'namespace_prefix'
In LangGraph’s store API, namespace_prefix is a positional-only parameter
```python
# incorrect
items = await store.asearch(namespace_prefix=namespace(user_id), limit=50)
# correct
items = await store.asearch(namespace(user_id), limit=50)
```
