#!/bin/bash
# Quick start script for Universal Data Connector with bonus features

echo "🚀 Universal Data Connector - Bonus Features"
echo "================================================"
echo ""

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "✓ Docker found"
    
    # Check if Docker Compose is available  
    if command -v docker-compose &> /dev/null; then
        echo "✓ Docker Compose found"
        echo ""
        echo "Starting services with Docker Compose..."
        echo "  - API server (port 8000)"
        echo "  - Redis cache (port 6379)"
        echo ""
        docker-compose up --build
    else
        echo "✗ Docker Compose not found"
        echo "Please install Docker Compose or run locally with:"
        echo "  pip install -r requirements.txt"
        echo "  python -m uvicorn app.main:app --reload"
    fi
else
    echo "✗ Docker not found"
    echo ""
    echo "Running locally..."
    
    # Check if Python is available
    if command -v python &> /dev/null; then
        echo "✓ Python found"
        
        # Check if pip can install
        echo ""
        echo "Installing dependencies..."
        pip install -r requirements.txt
        
        echo ""
        echo "Starting Redis (Docker)..."
        docker run -d -p 6379:6379 redis:latest > /dev/null 2>&1 || echo "⚠️  Failed to start Redis"
        
        echo ""
        echo "Starting API server..."
        python -m uvicorn app.main:app --reload
    else
        echo "✗ Python not found"
        echo "Please install Python 3.11 or higher"
    fi
fi

echo ""
echo "Once running, visit:"
echo "  🌐 Web UI:     http://localhost:8000/ui/index.html"
echo "  📚 API Docs:   http://localhost:8000/docs"
echo "  📖 ReDoc:      http://localhost:8000/redoc"
echo ""
