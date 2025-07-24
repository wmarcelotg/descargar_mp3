from flask import Flask, request, render_template, send_from_directory
import os
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = "static/downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/", methods=["GET", "POST"])
def index():
    video_title = None
    download_link = None

    if request.method == "POST":
        video_url = request.form["url"]
        format_type = request.form["format"]

        ydl_opts_info = {
            'quiet': True,
            'noplaylist': True  # 🔒 Forzamos a no procesar playlists
        }

        # Extraer solo información
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict.get('title', 'Desconocido')

        # Configuración de descarga
        ydl_opts_download = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'noplaylist': True,  # 🔒 otra vez, por seguridad
            'quiet': True
        }

        if format_type == "mp3":
            ydl_opts_download.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        elif format_type == "mp4":
            ydl_opts_download.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                'merge_output_format': 'mp4',
            })

        filename = None
        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
            result = ydl.extract_info(video_url, download=True)
            if 'entries' in result:
                result = result['entries'][0]  # por si acaso es playlist

            filename = ydl.prepare_filename(result)
            if format_type == "mp3":
                filename = filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")

        filename_only = os.path.basename(filename)
        download_link = f"/download/{filename_only}"

    return render_template("index.html", download_link=download_link, video_title=video_title)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    import os

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)
