# SEBI Vidyalaya

Interactive chat interface for SEBI certification exam preparation with speech-to-text and multi-language support.

## How to Run

### Prerequisites
- Python 3.8+
- Google Cloud credentials JSON file
- Azure OpenAI access

### Step 1: Clone and Navigate
```bash
git clone <repository-url>
cd sebi_vidyalaya
```

### Step 2: Install Dependencies
```bash
uv sync
```

### Step 3: Configure Environment
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your credentials:
   - `GOOGLE_CREDS_JSON`: Path to your Google Cloud service account JSON file
   - `GOOGLE_PROJECT_ID`: Your Google Cloud project ID
   - `AZURE_ENDPOINT`: Your Azure OpenAI endpoint URL
   - `AZURE_API_KEY`: Your Azure OpenAI API key
   - `DEPLOYMENT_NAME`: Your Azure OpenAI deployment name
   - `SERPER_API_KEY`: Your Serper API key (for web search)

### Step 4: Place Google Cloud Credentials
Place your Google Cloud service account JSON file in the path specified in your `.env` file.

### Step 5: Run the Application
```bash
python app.py
```

The application will start on `http://localhost:8080`

### Production Deployment
```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```

## Features
- Multi-exam support (Investor Awareness, MF Foundation, Investment Advisor)
- Real-time speech-to-text transcription
- Image upload support
- Multi-language support (6 Indian languages + English)
- Modern glassmorphism UI design