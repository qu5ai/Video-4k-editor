import os
from flask import Flask, request, render_template_string, send_file
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# واجهة الموقع التي ستظهر على شاشة هاتفك
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محرر الفيديو السحابي 4K</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: white; text-align: center; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: #1e1e1e; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { color: #e1306c; }
        .box { border: 1px dashed #444; padding: 15px; margin: 15px 0; border-radius: 10px; background: #252525; }
        input[type="file"], select { width: 100%; padding: 10px; margin-top: 10px; background: #111; color: white; border: 1px solid #444; border-radius: 5px; }
        button { background: #0095f6; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 15px; }
    </style>
</head>
<body>
<div class="container">
    <h2>محرر الفيديو السحابي 4K 🎬</h2>
    <p>سيرفرك الخاص لمعالجة الفيديو بأعلى جودة</p>
    <form action="/process" method="post" enctype="multipart/form-data">
        <div class="box">
            <label>1. فيديو إنستغرام الأصلي (المصدر):</label>
            <input type="file" name="original" accept="video/*" required>
        </div>
        <div class="box">
            <label>2. لقطاتك الجديدة (اختر ملفات متعددة):</label>
            <input type="file" name="clips" accept="video/*" multiple required>
        </div>
        <div class="box">
            <label>3. اختر الجودة المطلوبة للرندرة:</label>
            <select name="quality">
                <option value="4k_120">4K Ultra HD — 120 FPS</option>
                <option value="4k_60">4K Ultra HD — 60 FPS</option>
                <option value="2k_60">2K QHD — 60 FPS</option>
            </select>
        </div>
        <button type="submit">بدء المونتاج والرندرة السحابية الحقيقية</button>
    </form>
</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/process', methods=['POST'])
def process():
    orig_file = request.files['original']
    clips_files = request.files.getlist('clips')
    quality = request.form.get('quality', '4k_120')
    
    # حفظ الملفات مؤقتاً على السيرفر
    orig_path = os.path.join(UPLOAD_FOLDER, 'orig.mp4')
    orig_file.save(orig_path)
    
    clips_dir = os.path.join(UPLOAD_FOLDER, 'clips')
    os.makedirs(clips_dir, exist_ok=True)
    
    # تنظيف المجلد القديم
    for f in os.listdir(clips_dir): os.remove(os.path.join(clips_dir, f))
    
    for i, file in enumerate(clips_files):
        file.save(os.path.join(clips_dir, f"clip_{i}.mp4"))
        
    output_path = os.path.join(UPLOAD_FOLDER, 'output_4k.mp4')
    
    # تشغيل محرك FFmpeg الخارق داخل السيرفر
    settings = {"4k_120": {"w": 3840, "h": 2160, "fps": 120, "b": "40M"}, "4k_60": {"w": 3840, "h": 2160, "fps": 60, "b": "30M"}, "2k_60": {"w": 2560, "h": 1440, "fps": 60, "b": "20M"}}
    q = settings[quality]
    
    # معرفة مدة الفيديو الأصلي
    cmd_duration = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {orig_path}"
    total_duration = float(subprocess.check_output(cmd_duration, shell=True).decode().strip())
    
    clips = [os.path.join(clips_dir, f) for f in os.listdir(clips_dir)]
    duration_per_clip = total_duration / len(clips)
    
    filter_complex = ""
    input_args = []
    for i, c_path in enumerate(clips):
        input_args.extend(["-ss", "0", "-t", str(duration_per_clip), "-i", c_path])
        filter_complex += f"[{i}:v]scale={q['w']}:{q['h']}:force_original_aspect_ratio=decrease,pad={q['w']}:{q['h']}:(ow-iw)/2:(oh-ih)/2,fps={q['fps']}[v{i}];"
    
    for i in range(len(clips)): filter_complex += f"[v{i}]"
    filter_complex += f"concat=n={len(clips)}:v=1:a=0[v]"
    
    input_args.extend(["-i", orig_path])
    
    ffmpeg_cmd = ["ffmpeg", "-y"] + input_args + ["-filter_complex", filter_complex, "-map", "[v]", "-map", f"{len(clips)}:a", "-c:v", "libx264", "-b:v", q['b'], "-preset", "veryfast", "-c:a", "aac", output_path]
    
    subprocess.run(ffmpeg_cmd)
    
    # إرسال الفيديو النهائي عالي الدقة لهاتفك مباشرة للتحميل
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
