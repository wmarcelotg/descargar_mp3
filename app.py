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
    error_message = None

    if request.method == "POST":
        video_url = request.form.get("url")
        format_type = request.form.get("format")

        ydl_opts_info = {
            'quiet': True,
            'noplaylist': True,
            'cookies': 'cookies.txt'  # <- Añadir cookies
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                video_title = info_dict.get('title', 'Desconocido')

            ydl_opts_download = {
                'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
                'noplaylist': True,
                'quiet': True,
                'cookies': 'cookies.txt'  # <- Añadir cookies también aquí
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
                    result = result['entries'][0]
                filename = ydl.prepare_filename(result)

                if format_type == "mp3":
                    filename = filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")

            filename_only = os.path.basename(filename)
            download_link = f"/download/{filename_only}"

        except yt_dlp.utils.DownloadError as e:
            error_text = str(e)
            if "Sign in to confirm" in error_text or "This video is private" in error_text:
                error_message = "⚠️ Este video requiere inicio de sesión. Intenta con otro enlace o exporta cookies."
            else:
                error_message = f"❌ Error al descargar: {error_text}"
        except Exception as e:
            error_message = f"❌ Error inesperado: {str(e)}"

    return render_template("index.html",
                           video_title=video_title,
                           download_link=download_link,
                           error_message=error_message)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
