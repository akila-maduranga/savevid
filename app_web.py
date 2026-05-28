import os
import asyncio
import urllib.parse
import uuid
import threading
from flask import Flask, request, jsonify, send_from_directory, send_file
from plugins.config import Config
import time

# Serve the new web frontend
app = Flask(__name__, static_folder="web_new")

# Runtime flags
app.is_ready = False
app.is_shutting_down = False

# Global cache for HTML
_INDEX_HTML_CACHE = None

# Import download progress tracking from upload.py
from plugins.helper.upload import WEB_DOWNLOAD_PROGRESS as DOWNLOAD_PROGRESS

async def prune_progress_task():
    """Background task to keep memory low by pruning old progress data."""
    while True:
        try:
            now = time.time()
            to_del = [did for did, info in DOWNLOAD_PROGRESS.items() 
                      if now - info.get("_last_update", now) > 3600]
            for did in to_del:
                # Clean up downloaded file before deleting entry
                filepath = DOWNLOAD_PROGRESS.get(did, {}).get("filepath")
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
                del DOWNLOAD_PROGRESS[did]
        except Exception:
            pass
        await asyncio.sleep(600)

@app.route("/")
def index():
    global _INDEX_HTML_CACHE
    if app.is_shutting_down:
        return "🔄 Server is shutting down…", 503
    if not app.is_ready:
        return "⏳ Server is starting…", 503

    if _INDEX_HTML_CACHE:
        return _INDEX_HTML_CACHE

    try:
        html_path = os.path.join("web_new", "index.html")
        if not os.path.exists(html_path):
            return "404 - Web assets missing", 404
            
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            _INDEX_HTML_CACHE = content
            return content
    except Exception as e:
        Config.LOGGER.error(f"Error serving index: {e}")
        return "Internal Server Error", 500

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("web_new", path)

def _is_valid_url(url: str) -> bool:
    """Basic URL validation to prevent SSRF attacks."""
    try:
        parsed = urllib.parse.urlparse(url)
        return bool(parsed.scheme in ('http', 'https') and parsed.netloc)
    except Exception:
        return False

@app.route('/api/formats', methods=["POST"])
def api_formats():
    """Endpoint to extract video qualities."""
    if not app.is_ready:
        return {"error": "Server is not ready"}, 503

    data = request.json
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}, 400

    if not _is_valid_url(url):
        return {"error": "Invalid URL"}, 400

    from plugins.helper.upload import fetch_ytdlp_formats
    
    try:
        # Run async function in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(fetch_ytdlp_formats(url))
        loop.close()
        return jsonify(res), 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/web-download', methods=["POST"])
def api_web_download():
    """Start a download task for web interface."""
    if not app.is_ready:
        return {"error": "Server is not ready"}, 503

    data = request.json
    url = data.get("url")
    if not url:
        return {"error": "URL missing"}, 400

    if not _is_valid_url(url):
        return {"error": "Invalid URL"}, 400

    format_id = data.get("format_id")
    mode = data.get("mode", "direct")
    filename = data.get("filename")

    # Generate unique download ID
    download_id = str(uuid.uuid4())
    
    # Queue the download task
    try:
        from plugins.helper.upload import download_to_file
        # Run in background thread
        def run_download():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(download_to_file(download_id, url, format_id, mode, filename))
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_download, daemon=True)
        thread.start()
        return jsonify({"download_id": download_id}), 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/progress/<download_id>', methods=["GET"])
def api_progress(download_id):
    """Get download progress."""
    if not app.is_ready:
        return {"error": "Server is not ready"}, 503

    progress = DOWNLOAD_PROGRESS.get(download_id)
    if progress:
        # Update last access time
        progress["_last_update"] = time.time()
        return jsonify({
            "status": progress.get("status", "downloading"),
            "percentage": progress.get("percentage", 0),
            "action": progress.get("action", "Downloading..."),
            "speed": progress.get("speed", "-- MB/s")
        }), 200
    else:
        return jsonify({"status": "not_found"}), 404

@app.route('/api/download-file/<download_id>', methods=["GET"])
def download_file(download_id):
    """Download the completed file."""
    if not app.is_ready:
        return "Server not ready", 503

    progress = DOWNLOAD_PROGRESS.get(download_id)
    if not progress or progress.get("status") != "complete":
        return "File not ready", 404

    filepath = progress.get("filepath")
    if not filepath or not os.path.exists(filepath):
        return "File not found", 404

    original_filename = progress.get("filename", "downloaded_file")
    return send_file(filepath, as_attachment=True, download_name=original_filename)

@app.route("/health")
def health():
    if app.is_shutting_down:
        return {"status": "shutting_down"}, 503
    if not app.is_ready:
        return {"status": "starting"}, 503
    return {"status": "ok"}, 200

# ── Link API Endpoints (for external integration) ─────────────────────────────

@app.route("/grab", methods=["GET"])
def grab_get():
    """Extract direct media links from any video URL (GET)."""
    if not app.is_ready:
        return {"error": "Server is not ready"}, 503

    url = request.args.get("url")
    if not url:
        return {"error": "No URL provided"}, 400

    if not _is_valid_url(url):
        return {"error": "Invalid URL"}, 400

    use_browser = request.args.get("use_browser", "true").lower() == "true"
    timeout = int(request.args.get("timeout", "25"))

    try:
        from plugins.helper.extractor import extract_links
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(extract_links(url, use_browser=use_browser, timeout=timeout))
        loop.close()
        if not result.get("links"):
            return {"error": f"No media links found for: {url}"}, 400
        return result, 200
    except Exception as e:
        return {"error": f"Extraction error: {str(e)}"}, 400


@app.route("/grab", methods=["POST"])
def grab_post():
    """Extract direct media links from any video URL (POST)."""
    if not app.is_ready:
        return {"error": "Server is not ready"}, 503

    data = request.json or {}
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}, 400

    if not _is_valid_url(url):
        return {"error": "Invalid URL"}, 400

    use_browser = data.get("use_browser", True)
    timeout = data.get("timeout", 25)

    try:
        from plugins.helper.extractor import extract_links
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(extract_links(url, use_browser=use_browser, timeout=timeout))
        loop.close()
        if not result.get("links"):
            return {"error": f"No media links found for: {url}"}, 400
        return result, 200
    except Exception as e:
        return {"error": f"Extraction error: {str(e)}"}, 400


@app.route("/extract", methods=["POST"])
def extract_post():
    """Raw yt-dlp extraction for drop-in compatibility."""
    if not app.is_ready:
        return {"error": "Server is not ready"}, 503

    data = request.json or {}
    url = data.get("url")
    if not url:
        return {"error": "Missing 'url' in JSON body"}, 400

    if not _is_valid_url(url):
        return {"error": "Invalid URL"}, 400

    try:
        from plugins.helper.extractor import extract_raw_ytdlp
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(extract_raw_ytdlp(url))
        loop.close()
        return result, 200
    except Exception as e:
        return {"error": str(e), "formats": [], "title": "Extraction Failed"}, 200


if __name__ == "__main__":
    # Start background pruning task
    def run_prune_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(prune_progress_task())
        finally:
            loop.close()
    
    prune_thread = threading.Thread(target=run_prune_task, daemon=True)
    prune_thread.start()
    
    # Mark app as ready
    app.is_ready = True
    
    # Run Flask app
    app.run(host="0.0.0.0", port=8080)
