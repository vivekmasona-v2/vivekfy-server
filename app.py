from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os
import tempfile

app = Flask(__name__)

# Path to cookies.txt (upload this file to Railway)
COOKIES_PATH = os.path.join(os.getcwd(), 'cookies.txt')

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                'cookiefile': COOKIES_PATH,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',  # Best video + audio
                'merge_output_format': 'mp4',  # Merge with ffmpeg
                'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),  # Save to temp dir
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',  # Ensure MP4 output
                }],
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                # Send the merged file directly
                return send_file(
                    downloaded_file,
                    as_attachment=True,
                    download_name=f"{info['title']}.mp4"
                )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
