# SEBI Vidyalaya

Interactive chat interface for SEBI certification exam preparation with speech-to-text and multi-language support.

## How to Run

### Using Docker (Recommended)

#### Prerequisites
- Docker
- Google Cloud credentials JSON file
- Azure OpenAI access

#### Step 1: Clone and Navigate
```bash
git clone <repository-url>
cd sebi_vidyalaya
```

#### Step 2: Configure Environment
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

#### Step 3: Place Google Cloud Credentials
Place your Google Cloud service account JSON file in the project directory.

#### Step 4: Build and Run with Docker
```bash
# Build the Docker image
docker build -t sebi-vidyalaya .

# Run the container
docker run -p 8080:8080 sebi-vidyalaya
```

The application will be available at `http://localhost:8080`

### Local Development Setup

#### Prerequisites
- Python 3.11+
- Google Cloud credentials JSON file
- Azure OpenAI access

#### Step 1: Install Dependencies
```bash
uv sync
```

#### Step 2: Run the Application
```bash
python app.py
```

## Features
- Multi-exam support (Investor Awareness, MF Foundation, Investment Advisor)
- Real-time speech-to-text transcription
- Image upload support
- Multi-language support (6 Indian languages + English)
- Modern glassmorphism UI design