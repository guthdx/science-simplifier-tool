# Science Simplifier Tool

A web-based application that transforms complex scientific papers into accessible, easy-to-understand summaries using AI.

## Features

- **File Upload**: Support for PDF and TXT files (up to 50MB)
- **AI-Powered Simplification**: Uses OpenAI GPT-4 to analyze and simplify scientific content
- **Comprehensive Multi-Format Outputs**:
  - Community Summary (6th grade reading level)
  - Three draft blog posts
  - Three draft Facebook posts
  - YouTube video script (3-5 minutes)
  - Main Findings summary (8th grade reading level)
  - How This Information Can Be Used (for various stakeholders)
- **Multiple Download Formats**: Download results as HTML or PDF
- **SCP Deployment Commands**: Automatically generates commands for deploying to web servers
- **Clean Interface**: Modern, responsive web interface with structured, accessible output
- **Automated Processing**: Upload, process, and download in a streamlined workflow

## How It Works

1. **Upload** your scientific paper (PDF or TXT format)
2. **Choose** your preferred output format (HTML or PDF)
3. **Process** - the AI analyzes the paper and creates multiple simplified outputs for different platforms and audiences
4. **Download** your comprehensive results with all deliverables
5. **Deploy** (optional) - use the provided SCP commands to deploy the simplified HTML to your web server
   - Original papers are automatically deployed to `test.mbiri.net/original_papers/sst_uploads/`
   - Generated HTML includes a "View Original Paper" link that works immediately

## Technology Stack

- **Backend**: Python Flask
- **AI**: OpenAI GPT-4 API
- **PDF Processing**: PyPDF2, WeasyPrint
- **Web Server**: Gunicorn + Nginx
- **Deployment**: Ubuntu VM + Cloudflare Tunnel

## Project Structure

```
science-simplifier-tool/
├── app.py                  # Main Flask application
├── templates/
│   └── index.html         # Frontend HTML
├── static/
│   ├── css/
│   │   └── style.css      # Styles
│   └── js/
│       └── main.js        # Frontend JavaScript
├── uploads/               # Temporary upload directory
├── outputs/               # Generated output files
├── original_papers/
│   └── sst_uploads/       # Local backup of uploaded papers
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── sst.service           # Systemd service file
├── nginx-sst.conf        # Nginx configuration
├── DEPLOYMENT.md         # Deployment instructions
└── README.md             # This file
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Quick Start (Development)

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the application
python app.py
```

Visit http://localhost:5000 in your browser.

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `FLASK_ENV`: Environment (production/development)
- `FLASK_DEBUG`: Debug mode (True/False)

## API Endpoints

- `GET /` - Main application interface
- `POST /api/simplify` - Upload and process paper
  - Returns download URL, original paper URL, and SCP deployment commands
- `GET /api/download/<filename>` - Download processed file
- `GET /api/original/<filename>` - Serve original paper files (for local testing)
- `GET /health` - Health check endpoint

## Output Structure

Each processed paper generates a comprehensive HTML page with the following sections:

1. **Community Summary** - Accessible overview written for general audiences
2. **Blog Posts** - Three ready-to-publish blog post examples
3. **Social Media Content** - Three engaging Facebook posts
4. **Video Script** - 3-5 minute YouTube video script
5. **Main Findings** - Plain-language summary of research findings
6. **Practical Applications** - How different stakeholders can use the findings

All content is formatted with clear headings, proper styling, and includes a link to the original paper.

## License

This project is for personal use.

## Access

Live at: https://sst.mbiri.net
