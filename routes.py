from typing import Optional
from fastapi import HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from app import app, templates
from speech_service import SpeechService
from orchestrator import orchestrator_agent, question_generator, explain_question_stream
import logging, json
from configs import config
from agents import fact_checker_crew

logger = logging.getLogger(__name__)

# Initialize speech service
speech_service = SpeechService()

EXAM_TYPES = {
    'investor_awareness': 'SEBI Investor Awareness Certification',
    'mf_foundation': 'NISM-Series-V-B: Mutual Fund Foundation Certification',
    'invest_advisor': 'NISM-Series-X-A: Investment Adviser (Level 1) Certification'
}

LANGUAGE_MAPPING = {
    'en-US': 'English',
    'hi-IN': 'Hindi',
    'bn-IN': 'Bengali',
    'mr-IN': 'Marathi',
    'kn-IN': 'Kannada',
    'gu-IN': 'Gujarati'
}


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    """Landing page with certification paths"""
    return templates.TemplateResponse("landing.html", {
        "request": request, 
        "exam_types": EXAM_TYPES,
        "page_type": "landing"
    })

@app.get("/chat/{exam_type}", response_class=HTMLResponse)
async def chat(request: Request, exam_type: str):
    """Main chat interface"""
    if exam_type not in EXAM_TYPES:
        raise HTTPException(status_code=404, detail="Invalid exam type selected")
    # exam_type = exam_type
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "exam_type": exam_type,
        "exam_title": EXAM_TYPES[exam_type],
        "messages": [],  # Empty list for prototype
        "page_type": "chat"
    })


@app.post("/transcribe")
async def transcribe_audio(
    audio_data: UploadFile = File(...),
    language: str = Form(default='en-US'),
    streaming: str = Form(default='false')
):
    """Transcribe audio data using Google Cloud Speech API"""
    try:
        # Read audio data
        audio_content = await audio_data.read()
        
        # Debug logging
        logger.info(f"Received audio: size={len(audio_content)}, content_type={audio_data.content_type}, language={language}, streaming={streaming}")
        
        # Determine if this is streaming (real-time) or final transcription
        is_streaming = streaming.lower() == 'true'
        
        # Check if audio content is not empty
        if len(audio_content) == 0:
            logger.warning("Received empty audio content")
            return JSONResponse({
                'success': False,
                'error': 'Empty audio data received'
            })
        
        result = speech_service.transcribe_audio_blob(audio_content, language, is_streaming)
        logger.info(f"Transcription result: {result}")
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post("/send_message")
async def send_message(request: Request):
    """Handle incoming chat messages with streaming response from orchestrator"""
    try:
        # Get JSON data from request body
        data = await request.json()
        
        chat_history = data.get('chat_history', [])
        language_code = data.get('language', 'en-US')
        config.exam_name = data.get('exam_type', 'investor_awareness')
        config.user_language = LANGUAGE_MAPPING.get(language_code, 'English')

        if not chat_history or not isinstance(chat_history, list):
            raise HTTPException(status_code=400, detail="Chat history required")
        
        # Stream response from orchestrator agent
        return StreamingResponse(
            orchestrator_agent(chat_history),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mock_exam")
async def mock_exam(request: Request):
    """Handle mock exam requests and return next question"""
    try:
        # Get JSON data from request body
        data = await request.json()
        
        messages = data.get('messages', [])
        is_initial = data.get('is_initial', False)
        exam_type = data.get('exam_type', '')
        
        if not isinstance(messages, list):
            raise HTTPException(status_code=400, detail="Messages must be a list")
        
        if not isinstance(is_initial, bool):
            raise HTTPException(status_code=400, detail="is_initial must be a boolean")
            
        if not exam_type or exam_type not in EXAM_TYPES:
            raise HTTPException(status_code=400, detail="Valid exam_type is required")
        
        question = question_generator(messages, exam_type, is_initial)

        return JSONResponse(json.loads(question))
        
    except Exception as e:
        logger.error(f"Mock exam error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_explanation")
async def generate_explanation(request: Request):
    """Generate explanation for exam answers with streaming response"""
    try:
        # Get JSON data from request body
        data = await request.json()
        
        question = data.get('question', '')
        language_code = data.get('language', 'en-US')
        exam_type = data.get('exam_type', '')
        
        if not question or not isinstance(question, str):
            raise HTTPException(status_code=400, detail="Question is required and must be a string")
            
        if exam_type not in EXAM_TYPES:
            raise HTTPException(status_code=400, detail="Valid exam_type is required")
        
        # Set configuration for the explanation generation
        config.exam_name = exam_type
        config.user_language = LANGUAGE_MAPPING.get(language_code, 'English')
        
        # Stream response using the new explanation streaming function
        return StreamingResponse(
            explain_question_stream(question),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Explanation generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fact_check")
async def fact_check(request: Request):
    """fact check a given answer against its source content and user question"""
    try:
        # Get JSON data from request body
        data = await request.json()
        
        question = data.get('user_query', '')
        language_code = data.get('language', 'en-US')
        answer = data.get('answer', '')

        if len(answer) <= 0:
            raise HTTPException(status_code=400, detail="Answer is required")
        
        source_info =  ""
        print(f"config.kb_results: {config.kb_results}")
        for res in config.kb_results:
            source_info += res.get("page_content") + "\n"
        
        # Set configuration for the explanation generation
        config.user_language = LANGUAGE_MAPPING.get(language_code, 'English')

        result = fact_checker_crew.kickoff(inputs={"user_question": question, 
                                                "source_content": source_info,
                                                "text_content": answer,
                                                "user_language": config.user_language})
        
        # Stream response using the new explanation streaming function
        return json.loads(str(result))
        
    except Exception as e:
        logger.error(f"Fact Checking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))