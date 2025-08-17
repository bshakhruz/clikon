import subprocess, json, os, sys, threading

# Check if running inside PyInstaller bundle
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(__file__)

FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe")
FFPROBE_PATH = os.path.join(BASE_DIR, "ffmpeg", "ffprobe.exe")

AUDIO_EXTENSIONS = ('mp3', 'wav', 'aac', 'flac', 'ogg', 'opus', 'wma', 'm4a', 'caf', 'amr', 'aiff')
VIDEO_EXTENSIONS = ('mp4', 'avi', 'mkv', 'mov', 'flv', 'wmv', 'webm', 'mpeg', 'mpg', '3gp', 'm4v', 'ts', 'vob', 'gif')
IMAGE_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'heif', 'heic', 'raw', 'ico')

AUDIO_CODEC_MAP = {
    'mp3': 'libmp3lame',
    'aac': 'aac',
    'wav': 'pcm_s16le',
    'flac': 'flac',
    'ogg': 'libvorbis',
    'opus': 'libopus',
    'wma': 'wmav2',
    'm4a': 'aac',
    'caf': 'pcm_s16le',
    'amr': 'libopencore_amrnb',
    'aiff': 'pcm_s16le',
}

VIDEO_CODEC_MAP = {
    'mp4': 'libx264',
    'mkv': 'libx264',
    'avi': 'mpeg4',
    'mov': 'libx264',
    'flv': 'flv',
    'wmv': 'wmv2',
    'webm': 'libvpx',
}

def detect_media_type(file):
    if not os.path.exists(file):
        return "unknown"
    ext = os.path.splitext(file)[1].lstrip(".").lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    cmd = [
        FFPROBE_PATH, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_type", "-of", "json", file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return "unknown"
    return "video" if data.get("streams") else "audio"

# ----------------------------
# Background Conversion
# ----------------------------
def convert_media(input_file, target_ext=None, output_file=None, progress_callback=None):
    """
    Convert media file in a separate thread.
    progress_callback: optional function(progress_text) called with FFmpeg output lines
    """

    media_type = detect_media_type(input_file)
    base, _ = os.path.splitext(input_file)

    if target_ext:
        target_ext = target_ext.lstrip(".").lower()
        if media_type == "audio" and target_ext not in AUDIO_EXTENSIONS:
            raise ValueError(f"{target_ext} is not a valid audio format")
        if media_type == "video" and target_ext not in VIDEO_EXTENSIONS:
            raise ValueError(f"{target_ext} is not a valid video format")
        if media_type == "image" and target_ext not in IMAGE_EXTENSIONS:
            raise ValueError(f"{target_ext} is not a valid image format")
        output_file = output_file or f"{base}_converted.{target_ext}"
    else:
        _, ext = os.path.splitext(input_file)
        target_ext = ext.lstrip(".").lower()
        output_file = output_file or f"{base}_converted{ext}"

    cmd = [FFMPEG_PATH, "-y", "-i", input_file]

    if media_type == "audio":
        codec = AUDIO_CODEC_MAP.get(target_ext, "copy")
        cmd += ["-c:a", codec]
    elif media_type == "video":
        codec = VIDEO_CODEC_MAP.get(target_ext, "copy")
        cmd += ["-c:v", codec, "-c:a", "copy", "-preset", "veryfast"]

    cmd.append(output_file)

    # Run FFmpeg in background thread
    def run():

        si = None
        creationflags = 0
        if os.name == "nt":  # Windows only
            creationflags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=creationflags)
        for line in process.stdout:
            if progress_callback:
                progress_callback(line.strip())
        process.wait()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return output_file, thread  # return thread to allow GUI to join/wait if needed

# ----------------------------
# Optional CLI for testing
# ----------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert media files between formats.")
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--target_ext", help="Target extension")
    parser.add_argument("--output_file", help="Optional output file")
    args = parser.parse_args()

    def progress(text):
        print(text)

    output_file, thread = convert_media(args.input_file, args.target_ext, args.output_file, progress_callback=progress)
    thread.join()
    print(f"Converted file saved as: {output_file}")