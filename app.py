import os
import subprocess
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)
# استخدام مجلد /tmp لأنه المجلد الوحيد المسموح بالكتابة فيه بمرونة في Render
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background: #050505; color: white; }</style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-md mx-auto bg-zinc-900 p-8 rounded-3xl border border-zinc-800 shadow-2xl">
        <h1 class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-blue-500 mb-6">المحرر الجبار</h1>
        <form action="/render" method="post" enctype="multipart/form-data" class="space-y-4">
            <input type="file" name="video" class="w-full p-3 bg-zinc-800 rounded-xl" required>
            <button type="submit" class="w-full p-4 bg-blue-600 rounded-xl font-bold hover:bg-blue-500 transition">بدء المعالجة الخارقة 🚀</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_UI

@app.route('/render', methods=['POST'])
def render():
    video = request.files['video']
    input_path = os.path.join(UPLOAD_FOLDER, 'in.mp4')
    output_path = os.path.join(UPLOAD_FOLDER, 'out.mp4')
    video.save(input_path)
    
    # أمر FFmpeg احترافي، خفيف، ومصمم ليُنهي العمل في أسرع وقت ممكن
    cmd = f"ffmpeg -i {input_path} -vf scale=1920:1080 -preset ultrafast -c:a copy {output_path}"
    subprocess.run(cmd, shell=True)
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
