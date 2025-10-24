from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # "user" or "assistant"
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

# System message for the legal chatbot
SYSTEM_MESSAGE = """You are a knowledgeable legal assistant specializing in consumer protection law. 
You provide accurate, helpful information about consumer rights, warranties, refunds, fraud protection, 
contract disputes, product liability, and all aspects of consumer protection legislation.

Your role is to:
- Answer questions clearly and comprehensively about consumer protection laws
- Explain consumer rights in various situations
- Provide guidance on how consumers can protect themselves
- Explain legal concepts in simple, understandable terms
- Cover topics including but not limited to: refunds, warranties, fraud, unfair practices, contract terms, 
  product safety, data protection, online purchases, and dispute resolution

Always provide thorough, accurate information while being clear that you're providing general legal information, 
not personalized legal advice. Answer every question the user asks related to consumer protection."""

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Consumer Protection Legal Chatbot API"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Store user message
        user_msg = ChatMessage(
            session_id=request.session_id,
            role="user",
            message=request.message
        )
        user_doc = user_msg.model_dump()
        user_doc['timestamp'] = user_doc['timestamp'].isoformat()
        await db.chat_messages.insert_one(user_doc)
        
        # Initialize chat with Gemini
        chat = LlmChat(
            api_key=os.environ['GEMINI_API_KEY'],
            session_id=request.session_id,
            system_message=SYSTEM_MESSAGE
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Create user message
        user_message = UserMessage(text=request.message)
        
        # Get response from AI
        ai_response = await chat.send_message(user_message)
        
        # Store assistant response
        assistant_msg = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            message=ai_response
        )
        assistant_doc = assistant_msg.model_dump()
        assistant_doc['timestamp'] = assistant_doc['timestamp'].isoformat()
        await db.chat_messages.insert_one(assistant_doc)
        
        return ChatResponse(
            response=ai_response,
            session_id=request.session_id
        )
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(1000)
        
        # Convert ISO string timestamps back to datetime objects
        for msg in messages:
            if isinstance(msg['timestamp'], str):
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
        
        return messages
    except Exception as e:
        logging.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@api_router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    try:
        result = await db.chat_messages.delete_many({"session_id": session_id})
        return {"deleted_count": result.deleted_count, "session_id": session_id}
    except Exception as e:
        logging.error(f"Error clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()