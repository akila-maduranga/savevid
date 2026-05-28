#!/bin/bash

# One-command deployment script for Cloud Downloader
# This script deploys the entire stack with Caddy SSL on a VPS

set -e

echo "🚀 Cloud Downloader - One-Command Deployment"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and set your DOMAIN and CLOUDFLARE_API_TOKEN"
    echo "   Then run this script again."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if DOMAIN is set
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "yourdomain.com" ]; then
    echo "❌ DOMAIN is not set in .env file. Please set it and run again."
    exit 1
fi

echo "🌐 Deploying for domain: $DOMAIN"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p DOWNLOADS
mkdir -p youtube_api/downloads

# Stop existing containers if running
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Exit"; then
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo "✅ Deployment successful!"
echo ""
echo "🎉 Your Cloud Downloader is now running!"
echo "🌐 Access it at: https://$DOMAIN"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
echo "🔄 Restart services: docker-compose restart"
