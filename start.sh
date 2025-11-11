#!/bin/bash
# Project Firefly - Quick Start Script

echo "🔥 Project Firefly - Quick Start"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker and Docker Compose first"
    exit 1
fi

# Detect which Docker Compose command to use
DOCKER_COMPOSE=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo "✓ Using Docker Compose V2"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "✓ Using Docker Compose V1"
else
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose (V1 or V2)"
    exit 1
fi

# Create directories with proper permissions
echo "📁 Creating directories..."
mkdir -p data logs
chmod 777 data logs
echo "✓ Directories created"

# Build the container
echo "🔨 Building Docker image..."
$DOCKER_COMPOSE build
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi
echo "✓ Build complete"

# Start the container
echo "🚀 Starting Firefly..."
$DOCKER_COMPOSE up -d
if [ $? -ne 0 ]; then
    echo "❌ Failed to start container"
    exit 1
fi

echo ""
echo "================================"
echo "✅ Project Firefly is running!"
echo "================================"
echo ""
echo "🌐 Web Interface: http://localhost:8080"
echo "🔑 Default Login: admin / admin123"
echo ""
echo "⚠️  IMPORTANT: Change the default password after first login!"
echo ""
echo "📊 View logs: $DOCKER_COMPOSE logs -f"
echo "🛑 Stop: $DOCKER_COMPOSE down"
echo ""
