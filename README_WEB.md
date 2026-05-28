# KeepThisClip - Web Version

A powerful web-based downloader that downloads files from URLs (up to 2GB) including Instagram, TikTok, Twitter/X, YouTube, and 700+ more platforms. Built with Flask, yt-dlp, and Playwright for media extraction.

## Features

- 🌐 **Modern Web Interface** - Clean, responsive UI for downloading files
- 📥 **Multi-Platform Support** - YouTube, Instagram, TikTok, Twitter/X, Reddit, Facebook, Vimeo + 700+ more
- 🎬 **Quality Selection** - Choose video quality before downloading
- 🎵 **Audio Extraction** - Extract audio from videos
- ✏️ **Custom Filename** - Rename files before download
- 🔒 **SSL/HTTPS** - Automatic SSL with Caddy and Let's Encrypt
- 🚀 **One-Command Deployment** - Deploy to VPS with a single command
- 📊 **Live Progress** - Real-time download progress tracking
- 🐳 **Docker** - Fully containerized deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Caddy (SSL/Proxy)                      │
│                   Port 80/443 (HTTPS)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌──────────────┐  ┌────────────────┐
│ Flask App     │  │  YouTube API │  │  MongoDB       │
│ (Web UI)      │  │  (yt-dlp)    │  │  (Database)    │
│ Port 8080     │  │  Port 8001   │  │  Port 27017    │
└───────────────┘  └──────────────┘  └────────────────┘
```

## Quick Start (VPS Deployment)

### Prerequisites

- A VPS with Ubuntu/Debian (recommended: 2GB RAM, 20GB disk)
- A domain name (e.g., keepthisclip.com) pointed to your VPS
- DNS provider (Namecheap, GoDaddy, etc.) - Caddy uses HTTP challenge, works with any DNS

### One-Command Deployment

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/cloud-downloader.git
cd cloud-downloader
```

2. **Configure environment:**
```bash
cp .env.example .env
nano .env
```

Edit the following variables:
```env
DOMAIN=keepthisclip.com
```

3. **Point your domain to your VPS:**
- Go to your DNS provider (Namecheap, GoDaddy, etc.)
- Add an A record pointing to your VPS IP address
- Wait for DNS to propagate (usually 5-30 minutes)

4. **Deploy:**
```bash
chmod +x deploy.sh
./deploy.sh
```

That's it! Your KeepThisClip will be available at `https://keepthisclip.com`

## Manual Deployment

If you prefer manual deployment:

1. **Install Docker and Docker Compose:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Create directories:**
```bash
mkdir -p DOWNLOADS youtube_api/downloads
```

4. **Build and start:**
```bash
docker-compose build
docker-compose up -d
```

## Configuration

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DOMAIN` | Yes | Your domain name (e.g., keepthisclip.com) |
| `DATABASE_URL` | No | MongoDB connection string (default: mongodb://mongodb:27017/keepthisclip) |
| `FFMPEG_PATH` | No | Path to FFmpeg (default: /usr/bin/ffmpeg) |
| `YOUTUBE_API_URL` | No | YouTube API URL (default: http://youtube-api:8001) |
| `PORT` | No | Flask app port (default: 8080) |

**Note:** Caddy uses HTTP challenge for SSL, which works with any DNS provider (Namecheap, GoDaddy, etc.). No API token needed.

## Usage

1. Open your browser and go to `https://keepthisclip.com`
2. Paste a URL (YouTube, Instagram, TikTok, etc.)
3. Click "Check URL" to see available qualities
4. Select quality and download mode
5. Optionally enter a custom filename
6. Click "Start Download"
7. Wait for download to complete
8. Click "Download File" to save to your device

## API Endpoints

The web app also provides API endpoints for integration:

### Get Video Formats
```bash
POST /api/formats
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=xxxx"
}
```

### Start Download
```bash
POST /api/web-download
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=xxxx",
  "format_id": "best",
  "mode": "direct",
  "filename": "video.mp4"
}
```

Returns:
```json
{
  "download_id": "uuid-string"
}
```

### Check Progress
```bash
GET /api/progress/{download_id}
```

Returns:
```json
{
  "status": "downloading",
  "percentage": 45.5,
  "action": "Downloading...",
  "speed": "5.2 MB/s"
}
```

### Download File
```bash
GET /api/download-file/{download_id}
```

### Link Extraction API
```bash
GET /grab?url={url}
POST /grab
Content-Type: application/json
{"url": "https://example.com/video"}
```

## Management Commands

### View logs:
```bash
docker-compose logs -f
```

### Stop services:
```bash
docker-compose down
```

### Restart services:
```bash
docker-compose restart
```

### Update and rebuild:
```bash
git pull
docker-compose build
docker-compose up -d
```

### Clean up old downloads:
```bash
docker-compose exec app rm -rf /app/DOWNLOADS/*
```

## Troubleshooting

### SSL not working?
- Check that your domain DNS points to your VPS
- Verify Cloudflare API token has correct permissions
- Check Caddy logs: `docker-compose logs caddy`

### Downloads failing?
- Check app logs: `docker-compose logs app`
- Verify YouTube API is running: `docker-compose logs youtube-api`
- Check disk space: `df -h`

### Port 80/443 already in use?
- Stop other web servers (nginx, apache)
- Or modify Caddyfile to use different ports

## Security

- All downloads are isolated in Docker containers
- Automatic SSL with Let's Encrypt
- URL validation to prevent SSRF attacks
- Old downloads are automatically cleaned up (1 hour)

## Supported Platforms

yt-dlp supports 1700+ sites including:
- YouTube
- Instagram
- TikTok
- Twitter/X
- Facebook
- Reddit
- Vimeo
- Dailymotion
- Twitch
- SoundCloud
- Bilibili
- And many more...

## License

This project is based on the Telegram URL Uploader Bot, transformed into a web application.

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloader
- [Playwright](https://playwright.dev/) - Browser automation
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Caddy](https://caddyserver.com/) - Web server with automatic SSL
- [Docker](https://www.docker.com/) - Containerization
