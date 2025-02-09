from flask import Flask, request, jsonify, redirect, send_file
from yt_dlp import YoutubeDL
import os
import tempfile
import threading

app = Flask(__name__)
COOKIES_PATH = os.path.join(os.getcwd(), 'cookies.txt')  # Path to cookies.txt

def cleanup_temp_dir(tmp_dir):
    """Delete temporary directory after a delay (ensure file is sent first)."""
    def delayed_cleanup():
        import time
        time.sleep(60)  # Wait 60 seconds before cleanup
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmp_dir)
    threading.Thread(target=delayed_cleanup).start()

@app.route('/stream_audio', methods=['GET'])
def stream_audio():
    """Stream audio by redirecting to the direct audio URL."""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        ydl_opts = {'cookiefile': COOKIES_PATH, 'format': 'bestaudio/best', 'quiet': True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return redirect(info.get("url"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download_audio', methods=['GET'])
def download_audio():
    """Download audio as MP3."""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        tmp_dir = tempfile.mkdtemp()
        output_path = os.path.join(tmp_dir, "audio.mp3")

        ydl_opts = {
            'cookiefile': COOKIES_PATH,
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        response = send_file(
            final_path,
            as_attachment=True,
            download_name=f"{info['title']}.mp3"
        )

        cleanup_temp_dir(tmp_dir)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream_video', methods=['GET'])
def stream_video():
    """Stream video by redirecting to the direct video URL."""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        ydl_opts = {'cookiefile': COOKIES_PATH, 'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best', 'quiet': True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return redirect(info.get("url"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download_video', methods=['GET'])
def download_video():
    """Download video as MP4."""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        tmp_dir = tempfile.mkdtemp()
        output_path = os.path.join(tmp_dir, "video.mp4")

        ydl_opts = {
            'cookiefile': COOKIES_PATH,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'merge_output_format': 'mp4',
            'outtmpl': output_path,
            'quiet': True,
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = ydl.prepare_filename(info)

        response = send_file(
            final_path,
            as_attachment=True,
            download_name=f"{info['title']}.mp4"
        )

        cleanup_temp_dir(tmp_dir)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Return video/audio metadata in JSON format."""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        ydl_opts = {'cookiefile': COOKIES_PATH, 'format': 'bestaudio/best', 'quiet': True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify({
            "title": info.get('title'),
            "duration": info.get('duration'),
            "thumbnail": info.get('thumbnail'),
            "uploader": info.get('uploader'),
            "url": info.get('webpage_url'),
            "formats": [{
                "format_id": f["format_id"],
                "ext": f["ext"],
                "resolution": f.get("resolution"),
                "filesize": f.get("filesize"),
                "url": f["url"]
            } for f in info.get('formats', [])]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

