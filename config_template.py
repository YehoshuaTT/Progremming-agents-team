# Configuration file for API keys
# Copy this to config.py and add your actual API keys

import os

# Load from environment variables or set directly
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your_gemini_api_key_here')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')

# Model configurations
GEMINI_MODEL = "gemini-pro"
OPENAI_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 4000
TEMPERATURE = 0.7
