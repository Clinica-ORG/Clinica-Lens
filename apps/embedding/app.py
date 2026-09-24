from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn

from config import get_settings

settings = get_settings()
app = FastAPI()

# bge v1.5 512 tokens
model = SentenceTransformer(settings.model_name, device=settings.device)


class TextRequest(BaseModel):
    text: str
    is_query: bool = False


@app.post("/vectorize")
async def vectorize(request: TextRequest):
    text = request.text
    if request.is_query:
        text = "Represent this sentence for searching relevant passages: " + text
    vector = model.encode(text, normalize_embeddings=True).tolist()
    return {"vector": vector}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
