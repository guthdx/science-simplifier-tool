import os
import logging
import shutil
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from openai import OpenAI
from weasyprint import HTML
import uuid
from datetime import datetime
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ORIGINAL_PAPERS_FOLDER'] = '/var/www/test.mbiri.net/html/original_papers/sst_uploads'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise

def extract_text_from_file(file_path, filename):
    """Extract text from uploaded file based on extension"""
    ext = filename.rsplit('.', 1)[1].lower()

    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def simplify_paper_with_ai(paper_text):
    """Use OpenAI to simplify the scientific paper"""
    try:
        prompt = f"""You are designed to take in scientific papers and produce multiple simplified outputs for broader public understanding and engagement. You will provide the following as output:

1. Community Summary – a simplified summary written at about a 6th grade reading level, but without mentioning reading level in the output.

2. Three draft blog posts – examples of how the content could look in blog format.

3. Three draft Facebook posts – short, curiosity-piquing posts designed to boost engagement.

4. YouTube video script (3–5 minutes) – based on the paper.

5. Main Findings – a summary of the study's findings written in plain language at about an 8th grade level (do not label reading level).

6. How This Information Can Be Used – examples of how communities, health care providers, program directors, and legislators could use the findings, written in plain language at about an 8th grade level (do not label reading level).

All outputs must be crafted to make the science accessible and engaging for non-expert audiences. Technical terms must be simplified or explained with analogies and examples appropriate to the audience. Adapt tone and structure depending on the platform while maintaining accuracy and clarity.

Format your response with clear section headings for each deliverable (use ## for markdown headings).

Scientific Paper:
{paper_text}

Please provide all six outputs listed above."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at simplifying complex scientific papers for general audiences while maintaining accuracy. You create multiple formats of content for different platforms and audiences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8000
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise

def generate_html_output(simplified_text, original_filename, original_paper_link_filename=None):
    """Generate HTML file with simplified content"""
    # Use the link filename if provided, otherwise fall back to original_filename
    link_filename = original_paper_link_filename or original_filename

    # Convert markdown-style headings to HTML (basic conversion)
    import re
    content_html = simplified_text
    # Convert ## headings to <h2>
    content_html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content_html, flags=re.MULTILINE)
    # Convert ### headings to <h3>
    content_html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content_html, flags=re.MULTILINE)
    # Convert **bold** to <strong>
    content_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content_html)
    # Convert paragraphs (double newlines)
    content_html = re.sub(r'\n\n', '</p><p>', content_html)
    # Wrap in paragraphs
    content_html = f'<p>{content_html}</p>'
    # Clean up empty paragraphs
    content_html = re.sub(r'<p>\s*</p>', '', content_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simplified: {original_filename}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.8;
            color: #333;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
            font-size: 2.2em;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
            font-size: 1.6em;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        .metadata {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }}
        .original-paper-link {{
            margin-bottom: 30px;
            padding: 15px;
            background-color: #e8f4f8;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }}
        .original-paper-link a {{
            color: #2980b9;
            text-decoration: none;
            font-weight: bold;
        }}
        .original-paper-link a:hover {{
            text-decoration: underline;
        }}
        .content {{
            word-wrap: break-word;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .section {{
            margin-bottom: 35px;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        strong {{
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Science Simplifier Results</h1>
        <div class="metadata">
            <strong>Original Document:</strong> {original_filename}<br>
            <strong>Processed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        <div class="original-paper-link">
            <strong>📄 Original Paper:</strong>
            <a href="https://test.mbiri.net/original_papers/sst_uploads/{link_filename}" target="_blank">View Original Paper</a>
        </div>
        <div class="content">
{content_html}
        </div>
        <div class="footer">
            Generated by Science Simplifier Tool @ sst.mbiri.net
        </div>
    </div>
</body>
</html>"""
    return html_content

def generate_pdf_output(simplified_text, original_filename, original_paper_link_filename=None):
    """Generate PDF file with simplified content"""
    try:
        html_content = generate_html_output(simplified_text, original_filename, original_paper_link_filename)
        # Use WeasyPrint to convert HTML to PDF
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        return pdf_bytes
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/simplify', methods=['POST'])
def simplify():
    """Handle paper upload and simplification"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        output_format = request.form.get('format', 'html')

        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please upload PDF or TXT files.'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(upload_path)

        # Save a copy of the original paper for linking
        original_paper_filename = f"{unique_id}_{filename}"
        original_paper_path = os.path.join(app.config['ORIGINAL_PAPERS_FOLDER'], original_paper_filename)
        shutil.copy2(upload_path, original_paper_path)

        logger.info(f"File uploaded: {filename}")

        # Extract text from file
        logger.info("Extracting text from file...")
        paper_text = extract_text_from_file(upload_path, filename)

        if not paper_text or len(paper_text.strip()) < 100:
            os.remove(upload_path)
            return jsonify({'error': 'Could not extract sufficient text from the file. Please ensure the file contains readable text.'}), 400

        # Simplify with AI
        logger.info("Simplifying paper with AI...")
        simplified_text = simplify_paper_with_ai(paper_text)

        # Generate output based on format
        output_filename = f"simplified_{unique_id}_{filename.rsplit('.', 1)[0]}"

        if output_format == 'pdf':
            output_filename += '.pdf'
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            pdf_bytes = generate_pdf_output(simplified_text, filename, original_paper_filename)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        else:  # html
            output_filename += '.html'
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            html_content = generate_html_output(simplified_text, filename, original_paper_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        # Generate SCP command for deployment (original paper is already on test.mbiri.net)
        output_file_path = os.path.abspath(output_path)
        scp_command_html = f"scp {output_file_path} user@server:/var/www/test.mbiri.net/html/"

        logger.info(f"Simplification complete: {output_filename}")

        return jsonify({
            'success': True,
            'filename': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'original_paper_url': f'https://test.mbiri.net/original_papers/sst_uploads/{original_paper_filename}',
            'scp_commands': {
                'simplified': scp_command_html,
                'note': 'Replace "user@server" with your actual SSH credentials. Original paper is already deployed.'
            }
        })

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/download/<filename>')
def download(filename):
    """Download simplified file"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        # Determine mimetype
        if filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        else:
            mimetype = 'text/html'

        return send_file(file_path, as_attachment=True, download_name=filename, mimetype=mimetype)

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': 'Error downloading file'}), 500

@app.route('/api/original/<filename>')
def serve_original(filename):
    """Serve original paper files (for local testing)"""
    try:
        file_path = os.path.join(app.config['ORIGINAL_PAPERS_FOLDER'], filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        # Determine mimetype
        if filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        else:
            mimetype = 'text/plain'

        return send_file(file_path, mimetype=mimetype)

    except Exception as e:
        logger.error(f"Error serving original file: {e}")
        return jsonify({'error': 'Error serving file'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Ensure upload, output, and original papers directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ORIGINAL_PAPERS_FOLDER'], exist_ok=True)

    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=False)
