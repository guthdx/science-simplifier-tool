#!/bin/bash

# Science Simplifier Tool - Quick Setup Script
# This script helps automate the deployment process

set -e

echo "======================================"
echo "Science Simplifier Tool - Setup"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

# Step 1: Check Python version
echo "[1/8] Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Step 2: Create virtual environment
echo ""
echo "[2/8] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Step 3: Activate and install dependencies
echo ""
echo "[3/8] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Dependencies installed"

# Step 4: Set up environment file
echo ""
echo "[4/8] Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API key:"
    echo "   nano .env"
else
    echo ".env file already exists"
fi

# Step 5: Create necessary directories
echo ""
echo "[5/8] Creating directories..."
mkdir -p uploads outputs
chmod 755 uploads outputs
echo "Directories created"

# Step 6: Test application
echo ""
echo "[6/8] Testing Flask application..."
python app.py &
APP_PID=$!
sleep 3

if curl -s http://localhost:5000/health > /dev/null; then
    echo "✓ Flask app is running correctly"
    kill $APP_PID
else
    echo "✗ Flask app failed to start"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

# Step 7: Set up systemd service
echo ""
echo "[7/8] Setting up systemd service..."
echo "Run these commands to install the service:"
echo "  sudo cp sst.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable sst.service"
echo "  sudo systemctl start sst.service"

# Step 8: Set up Nginx
echo ""
echo "[8/8] Setting up Nginx configuration..."
echo "Run these commands to install nginx config:"
echo "  sudo cp nginx-sst.conf /etc/nginx/sites-available/sst.mbiri.net"
echo "  sudo ln -s /etc/nginx/sites-available/sst.mbiri.net /etc/nginx/sites-enabled/"
echo "  sudo nginx -t"
echo "  sudo systemctl reload nginx"

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Run the systemd and nginx commands shown above"
echo "3. Configure Cloudflare tunnel (see DEPLOYMENT.md)"
echo "4. Visit https://sst.mbiri.net"
echo ""
echo "Application Features:"
echo "- Generates 6 comprehensive outputs per paper"
echo "- Provides SCP commands for web deployment"
echo "- Supports HTML and PDF download formats"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"
