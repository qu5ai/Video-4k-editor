import os
import threading
import subprocess
import time
from flask import Flask, request, render_template_string, jsonify, send_file

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp'
progress = 0

HTML = """
<!DOCTYPE html>
<html dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-white p-5">
    <div class="max-w-md mx-auto bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
        <h1 class="text-2xl font-bold mb-4 text-blue-400">محول 2K - 120FPS الخارق</h1>
        <form id="uploadForm" class="space-y-4">
            <input type="file" name="video" class="w-full bg-zinc-800 p-2 rounded" required>
            <button type="submit" class="w-full bg-blue-600 p-3 rounded font-bold">ابدأ المعالجة 🚀</button>
        </form>
        <div id="progressContainer" class="hidden mt-6">
            <div class="w-full bg-zinc-700 h-4 rounded-full overflow-hidden">
                <div id="bar" class="bg-blue-500 h-full w-0 transition-all duration-500"></div>
            </div>
            <p id="perc" class="text-center mt-2 font-mono">0%</p>
        </div>
        <a id="down" href="/download" class="hidden mt-4 block text-center bg-green-600 p-3 rounded font-bold">📥 تحميل الفيديو</a>
    </div>
    <script>
        document.getElementById('uploadForm').onsubmit = async (e) => {
            e.preventDefault();
            document.getElementById('progressContainer').classList.remove('hidden');
            let fd = new FormData(e.target);
            fetch('/process', {method: 'POST', body: fd});
            let interval = setInterval(async () => {
                let res = await fetch('/status');
                let data = await res.json();
                document.getElementById('bar').style.width = data.p + '%';
                document.getElementById('perc').innerText = data.p + '%';
                if(data.p >= 100) { clearInterval(interval); document.getElementById('down').classList.remove('hidden'); }
            }, 1000);
        }
    </script>
</body></html>
"""

@app.route('/')
def index(): return HTML

@app.route('/process', methods=['POST'])
def process():
    global progress
    progress = 0
    file = request.files['video']
    in_path = f"{UPLOAD_FOLDER}/in.mp4"
    out_path = f"{UPLOAD_FOLDER}/out.mp4"
    file.save(in_path)
    
    # المعالجة في الخلفية
    threading.Thread(target=lambda: render_video(in_path, out_path)).start()
    return "started"

def render_video(in_path, out_path):
    global progress
    # أمر 2K (2560x1440) + 120fps + حدة عالية
    cmd = f"ffmpeg -y -i {in_path} -vf \"scale=2560:1440,minterpolate='fps=120',unsharp=luma_amount=1.5\" -preset ultrafast -c:v libx264 -crf 22 -b:v 15M {out_path}"
    
    process = subprocess.Popen(cmd, shell=True)
    while process.poll() is None:
        if progress < 95: progress += 5
        time.sleep(2)
    progress = 100

@app.route('/status')
def status(): return jsonify({'p': progress})

@app.route('/download')
def download(): return send_file(f"{UPLOAD_FOLDER}/out.mp4", as_attachment=True)

if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)
