import os
import uuid
from flask import render_template, request, jsonify, redirect, url_for, session, flash
from flask_socketio import emit, join_room, leave_room
from werkzeug.utils import secure_filename
from app import app, db, socketio
from models import ChatSession, ChatMessage
from speech_service import SpeechService
import logging

logger = logging.getLogger(__name__)

# Initialize speech service
speech_service = SpeechService()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
EXAM_TYPES = {
    'investor_awareness': 'SEBI Investor Awareness',
    'mutual_fund': 'Mutual Fund Foundation',
    'investment_advisor': 'Investment Advisor L1'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def landing():
    """Landing page with certification paths"""
    return render_template('landing.html', exam_types=EXAM_TYPES)

@app.route('/chat/<exam_type>')
def chat(exam_type):
    """Main chat interface"""
    if exam_type not in EXAM_TYPES:
        flash('Invalid exam type selected', 'error')
        return redirect(url_for('landing'))
    
    # Create or get chat session
    session_id = session.get('chat_session_id')
    chat_session = None
    
    if session_id:
        chat_session = ChatSession.query.get(session_id)
    
    if not chat_session or chat_session.exam_type != exam_type:
        chat_session = ChatSession()
        chat_session.exam_type = exam_type
        db.session.add(chat_session)
        db.session.commit()
        session['chat_session_id'] = chat_session.id
    
    # Get chat history
    messages = ChatMessage.query.filter_by(session_id=chat_session.id).order_by(ChatMessage.timestamp).all()
    
    return render_template('chat.html', 
                         exam_type=exam_type, 
                         exam_name=EXAM_TYPES[exam_type],
                         messages=messages,
                         session_id=chat_session.id)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """Handle image upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename) if file.filename else 'unnamed'
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file
            file.save(file_path)
            
            return jsonify({
                'success': True,
                'filename': unique_filename,
                'original_name': filename,
                'file_path': file_path
            })
        else:
            return jsonify({'error': 'Invalid file type. Please upload JPG, PNG, or PDF files.'}), 400
            
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': 'File upload failed. Please try again.'}), 500

@app.route('/set_language', methods=['POST'])
def set_language():
    """Set user's preferred language"""
    data = request.get_json()
    language = data.get('language', 'en')
    
    session['language'] = language
    
    # Update current chat session language if exists
    session_id = session.get('chat_session_id')
    if session_id:
        chat_session = ChatSession.query.get(session_id)
        if chat_session:
            chat_session.language = language
            db.session.commit()
    
    return jsonify({'success': True, 'language': language})

# WebSocket events
@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to SEBI Vidyalaya'})

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('join_session')
def on_join_session(data):
    """Join a chat session room"""
    session_id = data['session_id']
    join_room(f"session_{session_id}")
    logger.info(f'Client joined session {session_id}')

@socketio.on('leave_session')
def on_leave_session(data):
    """Leave a chat session room"""
    session_id = data['session_id']
    leave_room(f"session_{session_id}")
    logger.info(f'Client left session {session_id}')

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming chat messages"""
    try:
        session_id = data.get('session_id')
        message_content = data.get('message', '').strip()
        message_type = data.get('type', 'text')
        file_info = data.get('file_info')
        
        if not session_id or not message_content:
            emit('error', {'message': 'Invalid message data'})
            return
        
        # Get chat session
        chat_session = ChatSession.query.get(session_id)
        if not chat_session:
            emit('error', {'message': 'Chat session not found'})
            return
        
        # Save user message
        user_message = ChatMessage()
        user_message.session_id = session_id
        user_message.message_type = 'user'
        user_message.content = message_content
        user_message.content_type = message_type
        user_message.file_path = file_info.get('file_path') if file_info else None
        user_message.meta_data = file_info
        db.session.add(user_message)
        db.session.commit()
        
        # Emit user message to room
        emit('new_message', {
            'id': user_message.id,
            'type': 'user',
            'content': message_content,
            'content_type': message_type,
            'file_info': file_info,
            'timestamp': user_message.timestamp.isoformat()
        }, to=f"session_{session_id}")
        
        # Generate AI response (simulated streaming)
        ai_response = generate_ai_response(message_content, chat_session.exam_type, file_info)
        
        # Save AI message
        ai_message = ChatMessage()
        ai_message.session_id = session_id
        ai_message.message_type = 'ai'
        ai_message.content = ai_response
        ai_message.content_type = 'text'
        db.session.add(ai_message)
        db.session.commit()
        
        # Emit AI response with streaming effect
        emit('ai_response_start', {'message_id': ai_message.id}, to=f"session_{session_id}")
        
        # Simulate streaming by sending chunks
        words = ai_response.split()
        chunk_size = 3
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            emit('ai_response_chunk', {
                'message_id': ai_message.id,
                'chunk': chunk + ' '
            }, to=f"session_{session_id}")
            
        emit('ai_response_end', {
            'id': ai_message.id,
            'type': 'ai',
            'content': ai_response,
            'timestamp': ai_message.timestamp.isoformat()
        }, to=f"session_{session_id}")
        
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        emit('error', {'message': 'Failed to process message'})

@socketio.on('speech_recognition')
def handle_speech_recognition(data):
    """Handle real-time speech recognition"""
    try:
        audio_data = data.get('audio_data')
        language = data.get('language', 'en-US')
        
        if not audio_data:
            emit('speech_error', {'message': 'No audio data received'})
            return
        
        # Process speech with Google Cloud Speech-to-Text
        result = speech_service.transcribe_audio(audio_data, language)
        
        if result:
            emit('speech_result', {
                'transcript': result['transcript'],
                'confidence': result['confidence'],
                'is_final': result['is_final']
            })
        else:
            emit('speech_error', {'message': 'Speech recognition failed'})
            
    except Exception as e:
        logger.error(f"Speech recognition error: {str(e)}")
        emit('speech_error', {'message': 'Speech recognition service unavailable'})

def generate_ai_response(message, exam_type, file_info=None):
    """Generate AI response based on message and exam type"""
    # This is a simplified response generator
    # In production, this would integrate with an actual AI service
    
    exam_context = {
        'investor_awareness': 'SEBI Investor Awareness and Protection',
        'mutual_fund': 'Mutual Fund Regulations and Operations',
        'investment_advisor': 'Investment Advisory Services and Compliance'
    }
    
    context = exam_context.get(exam_type, 'SEBI Regulations')
    
    if file_info:
        response = f"I can see you've uploaded an image ({file_info.get('original_name', 'document')}). "
        response += f"Based on your question about '{message}' in the context of {context}, "
        response += "let me analyze the document and provide you with a comprehensive explanation. "
    else:
        response = f"Great question about '{message}' in the context of {context}. "
    
    response += f"This topic is essential for your {exam_type.replace('_', ' ').title()} certification. "
    response += "Let me break this down into key points: "
    response += "1) Regulatory framework and guidelines, "
    response += "2) Practical applications and case studies, "
    response += "3) Exam-specific focus areas. "
    response += "Would you like me to elaborate on any specific aspect?"
    
    return response
