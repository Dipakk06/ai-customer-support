from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .agent import answer_customer
from .db import init_db, list_tickets, log_chat

app = FastAPI(title="AI Customer Support Agent", version="1.0.0")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    customer_name: str = Field(default="Demo Customer", max_length=100)

class ChatResponse(BaseModel):
    answer: str
    intent: str

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = answer_customer(request.message, request.customer_name)
        log_chat(request.message, result["answer"])
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail="The support agent encountered an error. Please try again.") from exc

@app.get("/tickets")
def tickets():
    return {"tickets": list_tickets()}
