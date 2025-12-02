# Science Simplifier Tool - Deployment Guide

This guide will walk you through deploying the Science Simplifier Tool on your Ubuntu VM with Nginx and Cloudflare Tunnel.

## Prerequisites

- Ubuntu VM with sudo access
- Nginx installed and running
- Python 3.8 or higher
- Cloudflare account with Zero Trust dashboard access
- OpenAI API key

## Step 1: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python3, pip, and system dependencies for WeasyPrint
sudo apt install -y python3 python3-pip python3-venv \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info
```

## Step 2: Set Up Python Virtual Environment

```bash
# Navigate to project directory
cd /home/guthdx/science-simplifier-tool

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your OpenAI API key
nano .env
```

Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
FLASK_ENV=production
FLASK_DEBUG=False
```

Save and exit (Ctrl+X, then Y, then Enter).

## Step 4: Test the Application

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Test run the Flask app
python app.py
```

Open another terminal and test:
```bash
curl http://localhost:5000/health
```

You should see: `{"status":"healthy"}`

Press Ctrl+C to stop the test server.

## Step 5: Set Up Systemd Service

```bash
# Copy the service file to systemd
sudo cp sst.service /etc/systemd/system/sst.service

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable sst.service

# Start the service
sudo systemctl start sst.service

# Check the service status
sudo systemctl status sst.service
```

## Step 6: Configure Nginx

```bash
# Copy the nginx config to sites-available
sudo cp nginx-sst.conf /etc/nginx/sites-available/sst.mbiri.net

# Create symbolic link to sites-enabled
sudo ln -s /etc/nginx/sites-available/sst.mbiri.net /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

## Step 7: Configure Cloudflare Tunnel

1. Go to the Cloudflare Zero Trust dashboard: https://one.dash.cloudflare.com/
2. Navigate to **Networks** → **Tunnels**
3. Find your existing tunnel (the one used for test.mbiri.net)
4. Click **Configure**
5. Go to the **Public Hostname** tab
6. Click **Add a public hostname**
7. Configure:
   - **Subdomain**: `sst`
   - **Domain**: `mbiri.net`
   - **Type**: HTTP
   - **URL**: `localhost:80` (or your VM's IP with port 80)
8. Click **Save hostname**

## Step 8: Test the Deployment

Visit https://sst.mbiri.net in your browser. You should see the Science Simplifier interface.

## Troubleshooting

### Check Flask App Logs
```bash
sudo journalctl -u sst.service -f
```

### Check Nginx Logs
```bash
sudo tail -f /var/log/nginx/sst-error.log
sudo tail -f /var/log/nginx/sst-access.log
```

### Restart Services
```bash
# Restart Flask app
sudo systemctl restart sst.service

# Restart Nginx
sudo systemctl restart nginx
```

### Check if Port 5000 is Listening
```bash
sudo netstat -tlnp | grep 5000
```

### Test Local Connection
```bash
curl http://localhost:5000/health
```

## File Permissions

Ensure the application directories are accessible:
```bash
chmod 755 /home/guthdx/science-simplifier-tool
chmod 755 /home/guthdx/science-simplifier-tool/uploads
chmod 755 /home/guthdx/science-simplifier-tool/outputs
chmod 755 /home/guthdx/science-simplifier-tool/original_papers/sst_uploads
chmod 755 /var/www/test.mbiri.net/html/original_papers/sst_uploads
```

## Updating the Application

To update the application after making changes:

```bash
cd /home/guthdx/science-simplifier-tool
source venv/bin/activate
git pull  # if using git
pip install -r requirements.txt  # if dependencies changed
sudo systemctl restart sst.service
```

### Recent Updates (2025-11-21)

**Original Paper Auto-Deployment:**
- Original papers are now automatically saved to `/var/www/test.mbiri.net/html/original_papers/sst_uploads/`
- "View Original Paper" links work immediately after processing (no manual SCP needed)
- SST uploads are stored in `sst_uploads/` subfolder to distinguish from manually curated papers
- New API endpoint `/api/original/<filename>` for local testing

**Previous Updates (2025-11-20):**
- **6 distinct deliverables** per paper (Community Summary, blog posts, Facebook posts, YouTube script, Main Findings, How to Use)
- **Increased AI token limit** to 8000 for comprehensive content generation
- **SCP deployment commands** automatically generated after processing
- **Enhanced HTML output** with markdown conversion and structured sections

After updating, verify the new features work:
```bash
# Test the health endpoint
curl http://localhost:5000/health

# Check the service logs
sudo journalctl -u sst.service -n 50
```

## Security Notes

- The `.env` file contains sensitive API keys - never commit it to version control
- The application runs locally on 127.0.0.1:5000 and is only accessible through Nginx
- Uploaded files are automatically deleted after processing
- Consider setting up log rotation for application logs
- Regularly update dependencies for security patches

## Maintenance

### Clean Up Old Output Files
```bash
# Remove output files older than 7 days
find /home/guthdx/science-simplifier-tool/outputs -name "*.html" -mtime +7 -delete
find /home/guthdx/science-simplifier-tool/outputs -name "*.pdf" -mtime +7 -delete

# Remove SST-uploaded original papers older than 30 days
find /var/www/test.mbiri.net/html/original_papers/sst_uploads -type f -mtime +30 -delete
find /home/guthdx/science-simplifier-tool/original_papers/sst_uploads -type f -mtime +30 -delete
```

You can add this to a cron job for automatic cleanup.

### Deploying Processed Papers to test.mbiri.net

After processing a paper:

1. **Original paper** → Automatically saved to `/var/www/test.mbiri.net/html/original_papers/sst_uploads/` (no action needed)
2. **Simplified HTML file** → Use the provided SCP command to deploy to `/var/www/test.mbiri.net/html/`

The generated HTML includes a "View Original Paper" link that works immediately after processing.

Make sure the target directories exist on your web server:
```bash
mkdir -p /var/www/test.mbiri.net/html/original_papers/sst_uploads
chmod 755 /var/www/test.mbiri.net/html/original_papers/sst_uploads
```

**Note:** The `sst_uploads/` subfolder is used for papers uploaded through SST, keeping them separate from manually curated papers in `/var/www/test.mbiri.net/html/original_papers/`.
