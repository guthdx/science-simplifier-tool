# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Science Simplifier Tool is a Flask web application that uses OpenAI GPT-4 to transform complex scientific papers (PDF/TXT) into accessible summaries. Users upload documents, the AI processes them, and users download simplified versions in HTML or PDF format.

## Development Commands

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python app.py  # Runs on http://localhost:5000

# Install/update dependencies
pip install -r requirements.txt

# Test health endpoint
curl http://localhost:5000/health
```

### Production Deployment
```bash
# Run setup script (creates venv, installs deps, tests app)
./setup.sh

# Service management
sudo systemctl start sst.service
sudo systemctl stop sst.service
sudo systemctl restart sst.service
sudo systemctl status sst.service

# View application logs
sudo journalctl -u sst.service -f

# Nginx commands
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
sudo tail -f /var/log/nginx/sst-error.log
```

## Architecture

### Single-File Flask Application (`app.py`)

The entire backend logic resides in `app.py` with the following key functions:

- **File Processing Pipeline**: `extract_text_from_file()` → `simplify_paper_with_ai()` → `generate_html_output()` or `generate_pdf_output()`
- **OpenAI Integration**: Uses GPT-4o-mini model with specific prompting to simplify scientific content while maintaining accuracy
- **File Handling**: Generates unique IDs for each upload/output to prevent conflicts; cleans up uploaded files after processing

### Configuration

Environment variables in `.env`:
- `OPENAI_API_KEY` - Required for AI processing
- `FLASK_ENV` - Set to "production" in deployment
- `FLASK_DEBUG` - Set to "False" in production

File size limit: 50MB (configured in `app.py:21`)

### Directory Structure

```
uploads/                    - Temporary storage for user uploads (auto-cleaned after processing)
outputs/                    - Generated HTML/PDF files for download
templates/                  - Single index.html file (main UI)
static/                     - CSS, JS, and logo images
original_papers/sst_uploads/ - Local backup of uploaded papers (also deployed to test.mbiri.net)
```

### Original Papers Storage

When users upload papers through SST, the original files are automatically saved to:
- **SST server**: `/home/guthdx/science-simplifier-tool/original_papers/sst_uploads/`
- **Web server**: `/var/www/test.mbiri.net/html/original_papers/sst_uploads/` (auto-deployed)

This distinguishes SST uploads from manually curated papers in `/var/www/test.mbiri.net/html/original_papers/`.

### Production Stack

- **WSGI Server**: Gunicorn with 3 workers, bound to 127.0.0.1:5000
- **Reverse Proxy**: Nginx forwards external traffic to Gunicorn
- **Process Manager**: systemd service (`sst.service`) manages the application lifecycle
- **Domain Access**: Cloudflare Tunnel exposes https://sst.mbiri.net

## API Endpoints

- `GET /` - Serves main interface (index.html)
- `POST /api/simplify` - Accepts file upload + format parameter, returns download URL and SCP commands
  - Response includes `scp_commands` object with deployment commands for test.mbiri.net
  - Response includes `original_paper_url` with direct link to the deployed original paper
- `GET /api/download/<filename>` - Sends file with appropriate MIME type
- `GET /api/original/<filename>` - Serves original paper files from sst_uploads (for local testing)
- `GET /health` - Returns `{"status":"healthy"}`

## Key Implementation Details

### OpenAI API Call
Located in `simplify_paper_with_ai()` (app.py:60-97). Uses:
- Model: `gpt-4o-mini`
- Temperature: 0.7
- Max tokens: 8000 (increased for comprehensive outputs)
- Custom prompt that generates 6 distinct deliverables:
  1. Community Summary (6th grade reading level)
  2. Three draft blog posts
  3. Three draft Facebook posts
  4. YouTube video script (3-5 minutes)
  5. Main Findings (8th grade reading level)
  6. How This Information Can Be Used (examples for different stakeholders)

### HTML Generation with Markdown Conversion
The `generate_html_output()` function (app.py:103-233) includes:
- Basic markdown-to-HTML conversion (## headings, **bold**, paragraphs)
- Structured styling with sections for each deliverable
- Link to original paper at `https://test.mbiri.net/original_papers/sst_uploads/{uuid}_{filename}`
- Responsive design optimized for readability

### PDF Generation
Uses WeasyPrint to convert HTML to PDF (app.py:230-240). The HTML template is shared between HTML output and PDF generation.

### SCP Command Generation
Automatically generates SCP commands for deploying to test.mbiri.net:
- Simplified HTML file → `/var/www/test.mbiri.net/html/` (requires manual SCP)
- Original paper → Automatically saved to `/var/www/test.mbiri.net/html/original_papers/sst_uploads/` (no SCP needed)
- Commands displayed in UI after successful processing

### File Security
- `secure_filename()` sanitizes uploads
- `allowed_file()` validates extensions (only PDF/TXT)
- Unique UUID prefixes prevent filename collisions
- Files validated for minimum 100 characters of extractable text

### Error Handling
All route handlers wrap processing in try/except blocks and return JSON error responses with appropriate HTTP status codes.

## Maintenance

### Cleanup Old Output Files
```bash
# Remove files older than 7 days (consider adding to cron)
find /home/guthdx/science-simplifier-tool/outputs -name "*.html" -mtime +7 -delete
find /home/guthdx/science-simplifier-tool/outputs -name "*.pdf" -mtime +7 -delete

# Cleanup SST-uploaded original papers (on both locations)
find /var/www/test.mbiri.net/html/original_papers/sst_uploads -type f -mtime +30 -delete
find /home/guthdx/science-simplifier-tool/original_papers/sst_uploads -type f -mtime +30 -delete
```

### Update Application
```bash
cd /home/guthdx/science-simplifier-tool
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart sst.service
```

## Important Notes

- The `.env` file contains sensitive API keys - never commit to version control
- Application runs on 127.0.0.1:5000 (localhost only) - Nginx provides external access
- Uploaded files are deleted immediately after processing for security/storage management
- The production service uses Gunicorn's systemd notify integration for reliable process management
