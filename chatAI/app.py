import os
import tempfile
import logging
import socket
from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
import hashlib
from datetime import datetime, timedelta
import sys
import markdown
import re
import json
import time
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Constants
CACHE_DURATION = timedelta(minutes=5)
MIN_PORT = 15000
MAX_PORT = 16000
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'pdf'}

def find_free_port():
    """Find a free port in the specified range."""
    for port in range(MIN_PORT, MAX_PORT + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free ports found in range {MIN_PORT}-{MAX_PORT}")

def setup_gemini():
    """Configure Gemini API with error handling and model fallback."""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # List available models
        models = genai.list_models()
        logger.info("Available models:")
        for model in models:
            logger.info(f"- {model.name}")
        
        # Try models in order of preference
        model_names = [
            'gemini-1.5-pro-latest',      # Latest version
            'gemini-1.5-pro-001',         # Stable version
            'gemini-1.5-pro-002',         # Alternative version
            'gemini-1.0-pro-vision-latest', # Fallback option
            'gemini-pro-vision'           # Last resort
        ]
        
        for model_name in model_names:
            try:
                logger.info(f"Attempting to use model: {model_name}")
                model = genai.GenerativeModel(model_name)
                # Test the model with a simple prompt
                response = model.generate_content("Test connection")
                if response and response.text:
                    logger.info(f"Successfully initialized {model_name} model")
                    return model
            except Exception as e:
                logger.warning(f"Failed to use {model_name}: {str(e)}")
                continue
        
        # If all models fail, raise an exception
        raise Exception("Failed to initialize any of the available models")
        
    except Exception as e:
        logger.error(f"Error setting up Gemini: {str(e)}")
        raise

# Initialize Gemini model
try:
    model = setup_gemini()
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {str(e)}")
    sys.exit(1)

# Response cache
response_cache = {}

def get_cache_key(text, custom_prompt):
    """Generate a cache key from the input text and prompt."""
    content = f"{text or ''}{custom_prompt or ''}"
    return hashlib.md5(content.encode()).hexdigest()

def is_cache_valid(cache_key):
    """Check if the cached response is still valid."""
    if cache_key not in response_cache:
        return False
    cache_time = response_cache[cache_key]['timestamp']
    return datetime.now() - cache_time < CACHE_DURATION

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file):
    """Extract text from PDF file with error handling."""
    try:
        # Check file size
        file_size = os.fstat(file.fileno()).st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB")
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            reader = PdfReader(temp_file.name)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            os.unlink(temp_file.name)
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def create_study_plan_prompt(topic, pdf_content=None):
    """Create a structured prompt for the study plan generation."""
    base_prompt = """You are an expert study coach. Create a detailed learning plan based on the following content.
    The plan should be well-structured and include:
    1. 📚 Key Topics and Concepts
       - Main subjects to cover
       - Core concepts within each subject
       - Prerequisites and dependencies
    
    2. 🎯 Learning Objectives
       - Clear, measurable goals
       - Expected outcomes
       - Skills to be developed
    
    3. ⏰ Study Schedule
       - Daily/weekly plan
       - Time allocation for each topic
       - Break periods and review sessions
    
    4. ✍️ Practice Exercises
       - Recommended exercises
       - Practice problems
       - Self-assessment questions
    
    5. 📖 Additional Resources
       - Recommended readings
       - Online courses
       - Supplementary materials
       - Video tutorials
    
    6. 📊 Progress Tracking
       - Milestones
       - Assessment criteria
       - Success indicators
    
    Format the response in markdown with clear sections and bullet points.
    Make it engaging and motivational.
    Include specific time estimates for each section.
    Add practical tips and study techniques.
    """
    
    content = topic
    if pdf_content:
        content = f"{topic}\n\nAdditional content from PDF:\n{pdf_content}"
    
    return f"{base_prompt}\n\nContent to create study plan from:\n{content}"

def format_markdown(text):
    """Format the response text with proper markdown styling."""
    # Convert markdown to HTML with custom styling
    html = markdown.markdown(text)
    
    # Add custom styling classes
    html = html.replace('<h1>', '<h1 class="text-2xl font-bold text-accent mb-4 border-b border-accent pb-2">')
    html = html.replace('<h2>', '<h2 class="text-xl font-semibold text-light mb-3 flex items-center gap-2">')
    html = html.replace('<p>', '<p class="mb-4 text-gray-200">')
    html = html.replace('<ul>', '<ul class="list-disc pl-6 mb-4 space-y-2">')
    html = html.replace('<ol>', '<ol class="list-decimal pl-6 mb-4 space-y-2">')
    html = html.replace('<li>', '<li class="mb-2 text-gray-200">')
    
    # Add emoji icons to sections
    html = html.replace('>Key Topics and Concepts<', '><i class="fas fa-book text-accent"></i> Key Topics and Concepts<')
    html = html.replace('>Learning Objectives<', '><i class="fas fa-bullseye text-accent"></i> Learning Objectives<')
    html = html.replace('>Study Schedule<', '><i class="fas fa-calendar text-accent"></i> Study Schedule<')
    html = html.replace('>Practice Exercises<', '><i class="fas fa-pencil-alt text-accent"></i> Practice Exercises<')
    html = html.replace('>Additional Resources<', '><i class="fas fa-link text-accent"></i> Additional Resources<')
    html = html.replace('>Progress Tracking<', '><i class="fas fa-chart-line text-accent"></i> Progress Tracking<')
    
    return html

def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Retry a function with exponential backoff."""
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            error_message = str(e).lower()
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            
            if "429" in error_message and "quota" in error_message:
                # For quota errors, use longer delays and jitter
                delay = min(delay * 2 + random.uniform(0, 1), 60)  # Cap at 60 seconds
                logger.info(f"API quota exceeded. Waiting {delay:.1f} seconds before retry...")
            elif "rate limit" in error_message:
                # For rate limit errors, use medium delays
                delay = min(delay * 1.5 + random.uniform(0, 0.5), 30)  # Cap at 30 seconds
                logger.info(f"Rate limit reached. Waiting {delay:.1f} seconds before retry...")
            else:
                # For other errors, use shorter delays
                delay = min(delay * 1.2 + random.uniform(0, 0.2), 10)  # Cap at 10 seconds
                logger.info(f"Error occurred. Waiting {delay:.1f} seconds before retry...")
            
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    # If all retries failed, raise the last exception with a more descriptive message
    if "429" in str(last_exception).lower() and "quota" in str(last_exception).lower():
        raise Exception("API quota exceeded. Please try again later or contact support.")
    else:
        raise last_exception

def generate_study_plan(topic, pdf_content=None):
    """Generate a study plan using Gemini API"""
    try:
        # Check if we have a cached response
        cache_key = get_cache_key(topic, pdf_content)
        if cache_key in response_cache and is_cache_valid(cache_key):
            logger.info("Returning cached study plan")
            return jsonify({"study_plan": response_cache[cache_key]['response']})

        # Prepare the prompt
        prompt = create_study_plan_prompt(topic, pdf_content)
        
        try:
            # Generate content using Gemini
            def generate_content():
                response = model.generate_content(prompt)
                if not response or not response.text:
                    raise Exception("Empty response from Gemini API")
                return response
                
            response = retry_with_backoff(generate_content)
            study_plan = format_markdown(response.text)
            
            # Cache the response
            response_cache[cache_key] = {
                'response': study_plan,
                'timestamp': datetime.now()
            }
            
            return jsonify({"study_plan": study_plan})
            
        except Exception as e:
            error_message = str(e)
            if "429" in error_message and "quota" in error_message.lower():
                logger.error("Gemini API quota exceeded")
                return jsonify({
                    "error": "API quota exceeded. Please try again later or contact support.",
                    "details": "The AI service is currently experiencing high demand. Please try again in a few minutes.",
                    "retry_after": 60  # Suggest retrying after 1 minute
                }), 429
            else:
                logger.error(f"Error generating study plan: {error_message}")
                return jsonify({
                    "error": "Failed to generate study plan",
                    "details": "An error occurred while generating your study plan. Please try again.",
                    "retry_after": 30
                }), 500

    except Exception as e:
        logger.error(f"Unexpected error in generate_study_plan: {str(e)}")
        return jsonify({
            "error": "An unexpected error occurred",
            "details": "Please try again later or contact support if the problem persists.",
            "retry_after": 30
        }), 500

def create_test_prompt(content):
    """Create a prompt for test generation based on content."""
    base_prompt = """You are an expert educational assessment creator. Based on the provided content, create a comprehensive multiple-choice test that follows these guidelines:

    Test Structure:
    1. Create 8 questions of varying difficulty:
       - 3 basic understanding questions
       - 3 intermediate application questions
       - 2 advanced analysis questions
    
    Question Requirements:
    1. Each question should:
       - Be clear and unambiguous
       - Test a specific concept or skill
       - Include a mix of theoretical and practical aspects
       - Have 4 carefully crafted options (A, B, C, D)
    
    2. Answer options should:
       - Be plausible and relevant
       - Include common misconceptions as distractors
       - Avoid obvious wrong answers
       - Be similar in length and structure
    
    3. Question types to include:
       - Concept understanding
       - Application of knowledge
       - Problem-solving scenarios
       - Analysis of relationships
       - Cause and effect
    
    Return the response in the following JSON format:
    {
        "questions": [
            {
                "text": "Question text here",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": 0,  // Index of correct answer (0-3)
                "explanation": "Brief explanation of why this answer is correct",
                "difficulty": "basic/intermediate/advanced"
            }
        ]
    }
    
    Make sure the questions progress from basic to more challenging concepts."""
    
    return f"{base_prompt}\n\nContent to create test from:\n{content}"

def generate_test(content):
    """Generate a test based on content using Gemini API."""
    try:
        prompt = create_test_prompt(content)
        logger.info("Sending test generation request to Gemini API")
        
        def generate_content():
            response = model.generate_content(prompt)
            if not response or not response.text:
                raise Exception("Empty response from API")
            return response
        
        response = retry_with_backoff(generate_content)
        response_text = response.text
        
        # Find JSON content between curly braces
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            test_data = json.loads(json_match.group())
            
            # Convert test data to HTML
            html = '<div class="test-questions space-y-6">'
            for i, question in enumerate(test_data['questions']):
                html += f'''
                    <div class="question p-4 bg-white bg-opacity-5 rounded-lg">
                        <p class="text-lg font-medium mb-3">{i + 1}. {question['text']}</p>
                        <div class="options space-y-2">
                '''
                for j, option in enumerate(question['options']):
                    html += f'''
                        <label class="option block p-3 bg-white bg-opacity-5 rounded cursor-pointer hover:bg-opacity-10">
                            <input type="radio" name="q{i}" value="{j}" class="mr-2">
                            {option}
                        </label>
                    '''
                html += '''
                        </div>
                    </div>
                '''
            html += '</div>'
            
            return jsonify({
                "test": html,
                "success": True
            })
        else:
            raise ValueError("Could not extract test data from response")
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error generating test: {error_message}")
        
        if "429" in error_message and "quota" in error_message.lower():
            return jsonify({
                "error": "API quota exceeded",
                "details": "The AI service is currently experiencing high demand. Please try again in a few minutes.",
                "retry_after": 60,
                "html": '''
                    <div class="p-4 bg-yellow-100 text-yellow-800 rounded-lg">
                        <h3 class="text-lg font-semibold mb-2">API Quota Exceeded</h3>
                        <p class="mb-4">The AI service is currently experiencing high demand. Please try again in a few minutes.</p>
                        <button onclick="retryTestGeneration()" class="btn bg-yellow-500 hover:bg-yellow-600 text-white">
                            <i class="fas fa-redo mr-2"></i>Retry
                        </button>
                    </div>
                '''
            }), 429
        else:
            return jsonify({
                "error": "Failed to generate test",
                "details": "An error occurred while generating your test. Please try again.",
                "retry_after": 30,
                "html": '''
                    <div class="p-4 bg-red-100 text-red-800 rounded-lg">
                        <h3 class="text-lg font-semibold mb-2">Error Generating Test</h3>
                        <p class="mb-4">An error occurred while generating your test. Please try again.</p>
                        <button onclick="retryTestGeneration()" class="btn bg-red-500 hover:bg-red-600 text-white">
                            <i class="fas fa-redo mr-2"></i>Retry
                        </button>
                    </div>
                '''
            }), 500

@app.route('/')
def home():
    """Render the main page."""
    return render_template('index.html')

@app.route('/generate_study_plan', methods=['POST'])
def handle_study_plan():
    """Handle study plan generation request"""
    try:
        text = request.form.get('text', '').strip()
        pdf_file = request.files.get('pdf')
        pdf_content = None
        
        if pdf_file and pdf_file.filename:
            if not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({
                    "error": "Invalid file format",
                    "details": "Please upload a PDF file."
                }), 400
                
            try:
                pdf_content = extract_text_from_pdf(pdf_file)
            except Exception as e:
                logger.error(f"Error extracting PDF text: {str(e)}")
                return jsonify({
                    "error": "Failed to process PDF",
                    "details": "Could not extract text from the PDF file. Please try again or enter text manually."
                }), 400
        
        if not text and not pdf_content:
            return jsonify({
                "error": "Missing input",
                "details": "Please provide a study topic or upload a PDF file."
            }), 400
            
        # Generate study plan
        return generate_study_plan(text, pdf_content)
        
    except Exception as e:
        logger.error(f"Error in handle_study_plan: {str(e)}")
        return jsonify({
            "error": "An unexpected error occurred",
            "details": "Please try again later or contact support if the problem persists."
        }), 500

@app.route('/submit-test', methods=['POST'])
def submit_test():
    """Handle test submission and grading."""
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        
        # Here you would typically validate answers against correct ones
        # For now, we'll just return a simple response
        return jsonify({
            'result': '''
                <div class="p-4 bg-green-100 text-green-700 rounded">
                    <h2 class="text-xl font-bold mb-2">Test submitted successfully!</h2>
                    <p>Thank you for completing the test.</p>
                </div>
            '''
        })
    except Exception as e:
        logger.error(f"Error in submit_test route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/handle_test', methods=['POST'])
def handle_test():
    """Handle test generation request."""
    try:
        text = request.form.get('text', '').strip()
        pdf_file = request.files.get('pdf')
        pdf_content = None
        
        if pdf_file and pdf_file.filename:
            if not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({
                    "error": "Invalid file format",
                    "details": "Please upload a PDF file."
                }), 400
                
            try:
                pdf_content = extract_text_from_pdf(pdf_file)
            except Exception as e:
                logger.error(f"Error extracting PDF text: {str(e)}")
                return jsonify({
                    "error": "PDF processing failed",
                    "details": "Could not extract text from the PDF file. Please try again or enter text manually."
                }), 400
        
        if not text and not pdf_content:
            return jsonify({
                "error": "Missing input",
                "details": "Please provide text or upload a PDF file."
            }), 400
            
        content = text if text else pdf_content
        return generate_test(content)
        
    except Exception as e:
        logger.error(f"Error in handle_test: {str(e)}")
        return jsonify({
            "error": "Test generation failed",
            "details": "An unexpected error occurred. Please try again.",
            "retry_after": 30
        }), 500

if __name__ == '__main__':
    try:
        # Try to use port 3000 first
        port = 3000
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
        except OSError:
            # If port 3000 is not available, find a free port
            port = find_free_port()
            logger.info(f"Port 3000 is in use, using alternative port: {port}")
        
        logger.info(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1) 