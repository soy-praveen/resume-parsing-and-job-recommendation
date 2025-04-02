import os
import logging
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
import werkzeug.utils
from werkzeug.utils import secure_filename
from resume_parser import extract_text_from_resume, parse_resume
from job_recommender import get_job_recommendations
from chatgpt_service import generate_chatgpt_response, is_api_key_valid

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-dev-secret-key")

# Configure upload folder
UPLOAD_FOLDER = '/tmp/resume_uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload and processing"""
    # Check if a file was submitted
    if 'resume' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['resume']
    
    # Check if user didn't select a file
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.url)
    
    # Check if file is allowed
    if file and allowed_file(file.filename):
        # Generate a unique filename to prevent overwrites
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        try:
            # Extract text from the resume file
            extracted_text = extract_text_from_resume(filepath, file_extension)
            
            if not extracted_text:
                flash('Could not extract text from the uploaded file', 'danger')
                return redirect(url_for('index'))
            
            # Parse the resume using NLP
            parsed_data = parse_resume(extracted_text)
            
            # Get job recommendations based on the parsed resume
            job_recommendations = get_job_recommendations(parsed_data)
            
            # Store the results in the session
            session['parsed_data'] = parsed_data
            session['job_recommendations'] = job_recommendations
            
            # Redirect to results page
            return redirect(url_for('show_results'))
            
        except Exception as e:
            logging.error(f"Error processing resume: {str(e)}")
            flash(f'Error processing resume: {str(e)}', 'danger')
            return redirect(url_for('index'))
    else:
        flash(f'Unsupported file format. Please upload a PDF or DOCX file.', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def show_results():
    """Display the parsed resume data and job recommendations"""
    # Check if we have parsed data in the session
    if 'parsed_data' not in session or 'job_recommendations' not in session:
        flash('No resume data found. Please upload a resume first.', 'warning')
        return redirect(url_for('index'))
    
    parsed_data = session['parsed_data']
    job_recommendations = session['job_recommendations']
    
    return render_template('results.html', 
                          parsed_data=parsed_data,
                          job_recommendations=job_recommendations)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(413)
def file_too_large(e):
    flash('The file is too large. Maximum file size is 16MB.', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_server_error(e):
    flash('An internal server error occurred. Please try again later.', 'danger')
    return redirect(url_for('index'))

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """API endpoint for the career assistant chatbot"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp
    try:
        data = request.json
        
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        # We don't need to check API validity anymore since we have fallback responses
        # if not is_api_key_valid():
        #     return jsonify({
        #         'response': "I'm sorry, but the ChatGPT service is not available at the moment. "
        #                     "Please try again later or contact support for assistance."
        #     })
        
        # Get the query from the request
        query = data['query']
        
        # Get context from session if available
        context = {}
        if 'parsed_data' in session and 'job_recommendations' in session:
            parsed_data = session['parsed_data']
            job_recommendations = session['job_recommendations']
            
            # Add skills from resume
            if 'skills' in parsed_data:
                context['skills'] = parsed_data['skills']
                
            # Add target job information if available from request
            if 'jobIndex' in data and data['jobIndex'] is not None:
                try:
                    job_index = int(data['jobIndex'])
                    if 0 <= job_index < len(job_recommendations['jobs']):
                        selected_job = job_recommendations['jobs'][job_index]
                        context['job_title'] = selected_job['title']
                        context['missing_skills'] = selected_job['missing_skills']
                except (ValueError, IndexError) as e:
                    logging.error(f"Error processing job index: {str(e)}")
        
        # Generate response using ChatGPT
        response = generate_chatgpt_response(query, context)
        
        # Create response with CORS headers
        resp = make_response(jsonify({'response': response}))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    
    except Exception as e:
        logging.error(f"Error in chat API: {str(e)}")
        resp = make_response(jsonify({
            'error': 'An error occurred while processing your request.',
            'details': str(e)
        }), 500)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
