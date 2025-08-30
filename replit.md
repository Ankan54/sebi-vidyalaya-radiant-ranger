# Overview

SEBI Vidyalaya is an AI-powered educational platform designed to help users prepare for SEBI (Securities and Exchange Board of India) financial certifications. The application provides an interactive chat-based learning experience with multimodal support including text, voice, and image inputs. Users can choose from different certification paths like SEBI Investor Awareness, Mutual Fund Foundation, and Investment Advisor L1, then engage with an AI tutor that provides personalized guidance and explanations.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 for responsive design and components
- **JavaScript Architecture**: Vanilla JavaScript with modular design patterns
- **Real-time Communication**: Socket.IO for WebSocket connections enabling live chat functionality
- **Speech Integration**: Web Speech API for voice recognition with fallback support for multiple Indian languages
- **File Upload**: HTML5 file API with drag-and-drop support for images and PDFs

## Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM for database operations
- **Real-time Features**: Flask-SocketIO for bidirectional communication between client and server
- **Session Management**: Flask sessions with configurable secret keys
- **File Handling**: Werkzeug utilities for secure file uploads with size limitations (5MB max)
- **Database Architecture**: SQLAlchemy with declarative base, supporting both SQLite (default) and PostgreSQL via environment configuration
- **Middleware**: ProxyFix middleware for handling reverse proxy headers

## Data Storage Solutions
- **Primary Database**: SQLAlchemy ORM with support for SQLite (development) and PostgreSQL (production)
- **Session Storage**: Flask's built-in session management
- **File Storage**: Local filesystem storage in configurable upload directory
- **Database Schema**: Three main entities:
  - Users with authentication support via Flask-Login
  - ChatSessions linking users to specific exam types and languages
  - ChatMessages supporting multimodal content (text, image, audio) with metadata storage

## Authentication and Authorization
- **User Management**: Flask-Login integration with User model implementing UserMixin
- **Session Security**: Configurable session secret keys with environment variable support
- **Access Control**: Session-based access control for chat sessions with exam type validation

## External Dependencies

- **Google Cloud Speech-to-Text**: Service account authentication for audio transcription with multiple language support
- **Bootstrap 5 CDN**: Frontend styling and responsive components
- **Font Awesome CDN**: Icon library for UI elements
- **Google Fonts**: Inter and Open Sans fonts for typography
- **Socket.IO CDN**: Real-time communication library
- **Flask Extensions**: SQLAlchemy, SocketIO, and Login for core functionality
- **Python Libraries**: Werkzeug for WSGI utilities, logging for application monitoring

The application supports deployment flexibility with environment-based configuration for database connections, Google Cloud credentials, and session security settings.