from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import os
import json
from dotenv import load_dotenv

from agent import ChatAgent
from image_analyzer import ImageAnalyzer

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Medical Assistant API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
chat_agent = ChatAgent()
image_analyzer = ImageAnalyzer()


# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    status: str


class ImageAnalysisResponse(BaseModel):
    analysis: str
    conditions: List[str]
    recommendations: str
    status: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Medical Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "image_analysis": "/api/analyze-image"
        }
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for disease information and preventive measures.
    Users can ask about disease trends, symptoms, and preventive measures.
    """
    try:
        print(f"[API] Received chat request: {request.message}")
        # Convert history to the format expected by the agent
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        # Get response from chat agent
        response = await chat_agent.get_response(request.message, history)
        print(f"[API] Sending response: {response}")
        
        return ChatResponse(
            response=response,
            status="success"
        )
    except Exception as e:
        print(f"[API ERROR] Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint for real-time response generation.
    Streams the response word by word for better UX.
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            print(f"[API STREAM] Received chat request: {request.message}")
            # Convert history to the format expected by the agent
            history = [{"role": msg.role, "content": msg.content} for msg in request.history]
            
            # Get response from chat agent
            response = await chat_agent.get_response(request.message, history)
            print(f"[API STREAM] Streaming response")
            
            # Stream the response word by word
            words = response.split()
            for i, word in enumerate(words):
                # Add space between words except for the first word
                chunk = word if i == 0 else f" {word}"
                
                # Send as SSE (Server-Sent Events) format
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
                
                # Small delay to simulate streaming (adjust as needed)
                import asyncio
                await asyncio.sleep(0.03)  # 30ms delay between words
            
            # Send final done message
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
            
        except Exception as e:
            print(f"[API STREAM ERROR] Stream error: {str(e)}")
            import traceback
            traceback.print_exc()
            error_data = json.dumps({
                'error': str(e),
                'done': True
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )



@app.post("/api/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Image analysis endpoint for medical report analysis.
    Accepts image uploads and returns detected conditions and recommendations.
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image file
        image_data = await file.read()
        
        # Analyze image
        analysis_result = await image_analyzer.analyze_report(image_data, file.content_type)
        
        return ImageAnalysisResponse(
            analysis=analysis_result["analysis"],
            conditions=analysis_result["conditions"],
            recommendations=analysis_result["recommendations"],
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Medical Assistant API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
