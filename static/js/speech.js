// SEBI Vidyalaya Speech Recognition Module

class SpeechManager {
    constructor() {
        this.isSupported = this.checkSupport();
        this.isRecording = false;
        this.recognition = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.currentLanguage = 'en-US';
        this.confidenceThreshold = 0.5;
        
        // Supported languages for SEBI Vidyalaya
        this.supportedLanguages = {
            'en-US': 'English (US)',
            'hi-IN': 'Hindi (India)',
            'bn-IN': 'Bengali (India)',
            'te-IN': 'Telugu (India)',
            'ta-IN': 'Tamil (India)',
            'gu-IN': 'Gujarati (India)',
            'kn-IN': 'Kannada (India)',
            'ml-IN': 'Malayalam (India)',
            'mr-IN': 'Marathi (India)',
            'pa-IN': 'Punjabi (India)'
        };
        
        this.initializeRecognition();
    }
    
    checkSupport() {
        const hasWebSpeech = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        const hasMediaRecorder = 'MediaRecorder' in window;
        const hasGetUserMedia = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
        
        return {
            webSpeech: hasWebSpeech,
            mediaRecorder: hasMediaRecorder,
            getUserMedia: hasGetUserMedia,
            full: hasWebSpeech && hasMediaRecorder && hasGetUserMedia
        };
    }
    
    initializeRecognition() {
        if (!this.isSupported.webSpeech) {
            console.warn('Speech recognition not supported');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        this.recognition.lang = this.currentLanguage;
        
        // Event handlers
        this.recognition.onstart = () => this.onRecognitionStart();
        this.recognition.onresult = (event) => this.onRecognitionResult(event);
        this.recognition.onerror = (event) => this.onRecognitionError(event);
        this.recognition.onend = () => this.onRecognitionEnd();
    }
    
    async startRecording() {
        if (!this.isSupported.full) {
            throw new Error('Speech recording not fully supported in this browser');
        }
        
        if (this.isRecording) {
            console.warn('Already recording');
            return;
        }
        
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000,
                    channelCount: 1
                } 
            });
            
            this.setupMediaRecorder(stream);
            this.startWebSpeechRecognition();
            
            this.isRecording = true;
            this.onRecordingStart();
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.onRecordingError(error);
            throw error;
        }
    }
    
    setupMediaRecorder(stream) {
        this.audioChunks = [];
        
        // Configure MediaRecorder for better quality
        const options = {
            mimeType: 'audio/webm;codecs=opus'
        };
        
        try {
            this.mediaRecorder = new MediaRecorder(stream, options);
        } catch (error) {
            // Fallback to default format
            this.mediaRecorder = new MediaRecorder(stream);
        }
        
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };
        
        this.mediaRecorder.onstop = () => {
            this.processRecordedAudio();
            this.stopMediaStream(stream);
        };
        
        this.mediaRecorder.start(100); // Collect data every 100ms
    }
    
    startWebSpeechRecognition() {
        if (this.recognition) {
            this.recognition.lang = this.currentLanguage;
            this.recognition.start();
        }
    }
    
    stopRecording() {
        if (!this.isRecording) {
            return;
        }
        
        this.isRecording = false;
        
        // Stop speech recognition
        if (this.recognition) {
            this.recognition.stop();
        }
        
        // Stop media recording
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        this.onRecordingStop();
    }
    
    processRecordedAudio() {
        if (this.audioChunks.length === 0) {
            return;
        }
        
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Convert to base64 for transmission
        const reader = new FileReader();
        reader.onload = () => {
            const base64Audio = reader.result.split(',')[1];
            this.onAudioProcessed(base64Audio, audioBlob, audioUrl);
        };
        reader.readAsDataURL(audioBlob);
    }
    
    stopMediaStream(stream) {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    }
    
    setLanguage(languageCode) {
        if (this.supportedLanguages[languageCode]) {
            this.currentLanguage = languageCode;
            
            if (this.recognition) {
                this.recognition.lang = languageCode;
            }
            
            return true;
        }
        return false;
    }
    
    // Event handlers (to be overridden)
    onRecordingStart() {
        console.log('Recording started');
    }
    
    onRecordingStop() {
        console.log('Recording stopped');
    }
    
    onRecordingError(error) {
        console.error('Recording error:', error);
    }
    
    onRecognitionStart() {
        console.log('Speech recognition started');
    }
    
    onRecognitionResult(event) {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            const confidence = result[0].confidence;
            
            if (result.isFinal) {
                if (confidence >= this.confidenceThreshold) {
                    finalTranscript += transcript + ' ';
                }
            } else {
                interimTranscript += transcript;
            }
        }
        
        this.onTranscriptionUpdate({
            final: finalTranscript.trim(),
            interim: interimTranscript,
            confidence: event.results[event.results.length - 1][0].confidence || 0
        });
    }
    
    onRecognitionError(event) {
        console.error('Speech recognition error:', event.error);
        
        const errorMessages = {
            'no-speech': 'No speech was detected. Please try again.',
            'audio-capture': 'Audio capture failed. Please check your microphone.',
            'not-allowed': 'Microphone access denied. Please allow microphone access.',
            'network': 'Network error occurred. Please check your connection.',
            'aborted': 'Speech recognition was aborted.',
            'language-not-supported': 'The selected language is not supported.'
        };
        
        const userMessage = errorMessages[event.error] || 'Speech recognition failed. Please try again.';
        this.onRecognitionErrorOccurred(event.error, userMessage);
    }
    
    onRecognitionEnd() {
        console.log('Speech recognition ended');
        if (this.isRecording) {
            // Restart recognition if still recording
            setTimeout(() => {
                if (this.isRecording && this.recognition) {
                    this.recognition.start();
                }
            }, 100);
        }
    }
    
    onTranscriptionUpdate(data) {
        // Override this method to handle transcription updates
        console.log('Transcription update:', data);
    }
    
    onRecognitionErrorOccurred(errorCode, userMessage) {
        // Override this method to handle recognition errors
        console.log('Recognition error:', errorCode, userMessage);
    }
    
    onAudioProcessed(base64Audio, audioBlob, audioUrl) {
        // Override this method to handle processed audio
        console.log('Audio processed:', { base64Audio, audioBlob, audioUrl });
    }
    
    // Utility methods
    getSupportedLanguages() {
        return this.supportedLanguages;
    }
    
    getCurrentLanguage() {
        return this.currentLanguage;
    }
    
    getRecordingState() {
        return this.isRecording;
    }
    
    isFullySupported() {
        return this.isSupported.full;
    }
    
    getCapabilities() {
        return this.isSupported;
    }
    
    setConfidenceThreshold(threshold) {
        if (threshold >= 0 && threshold <= 1) {
            this.confidenceThreshold = threshold;
            return true;
        }
        return false;
    }
}

// Text-to-Speech functionality
class TextToSpeechManager {
    constructor() {
        this.isSupported = 'speechSynthesis' in window;
        this.voices = [];
        this.currentVoice = null;
        this.settings = {
            rate: 1.0,
            pitch: 1.0,
            volume: 1.0
        };
        
        if (this.isSupported) {
            this.loadVoices();
            speechSynthesis.onvoiceschanged = () => this.loadVoices();
        }
    }
    
    loadVoices() {
        this.voices = speechSynthesis.getVoices();
        this.selectBestVoice('en-US');
    }
    
    selectBestVoice(languageCode) {
        const preferredVoices = this.voices.filter(voice => 
            voice.lang.startsWith(languageCode.split('-')[0])
        );
        
        if (preferredVoices.length > 0) {
            // Prefer local voices over remote ones
            this.currentVoice = preferredVoices.find(voice => voice.localService) || preferredVoices[0];
        } else {
            this.currentVoice = this.voices[0] || null;
        }
    }
    
    speak(text, options = {}) {
        if (!this.isSupported || !text.trim()) {
            return Promise.reject(new Error('Text-to-speech not supported or empty text'));
        }
        
        return new Promise((resolve, reject) => {
            // Stop any ongoing speech
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Apply settings
            utterance.rate = options.rate || this.settings.rate;
            utterance.pitch = options.pitch || this.settings.pitch;
            utterance.volume = options.volume || this.settings.volume;
            utterance.voice = options.voice || this.currentVoice;
            
            // Event handlers
            utterance.onend = () => resolve();
            utterance.onerror = (event) => reject(new Error(`Speech synthesis error: ${event.error}`));
            utterance.onstart = () => this.onSpeechStart(text);
            utterance.onboundary = (event) => this.onSpeechBoundary(event);
            
            speechSynthesis.speak(utterance);
        });
    }
    
    stop() {
        if (this.isSupported) {
            speechSynthesis.cancel();
        }
    }
    
    pause() {
        if (this.isSupported) {
            speechSynthesis.pause();
        }
    }
    
    resume() {
        if (this.isSupported) {
            speechSynthesis.resume();
        }
    }
    
    setVoice(languageCode) {
        this.selectBestVoice(languageCode);
    }
    
    setSettings(settings) {
        this.settings = { ...this.settings, ...settings };
    }
    
    getVoices() {
        return this.voices;
    }
    
    isSpeaking() {
        return this.isSupported && speechSynthesis.speaking;
    }
    
    // Event handlers (to be overridden)
    onSpeechStart(text) {
        console.log('Speech started:', text);
    }
    
    onSpeechBoundary(event) {
        console.log('Speech boundary:', event);
    }
}

// Export for global use
window.SpeechManager = SpeechManager;
window.TextToSpeechManager = TextToSpeechManager;

// Create global instances
window.speechManager = new SpeechManager();
window.ttsManager = new TextToSpeechManager();
