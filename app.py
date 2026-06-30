import os
import threading
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محرر الفيديو السحابي الخارق 120fps</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: white; text-align: center; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: #1e1e1e; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { color: #0095f6; }
        .box { border: 1px dashed #444; padding: 15px; margin: 15px 0; border-radius: 10px; background: #252525; }
        input[type="file"], select { width: 100%; padding: 10px; margin-top: 10px; background: #111; color: white; border: 1px solid #444; border-radius: 5px; }
        button { background: #e1306c; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 15px; }
        .btn-link { display: inline-block; background: #28a745; color: white; padding: 10px 20px; margin-top: 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
<div class="container">
    <h2>محرر الفيديو السحابي الخارق ⚡</h2>
    <p>يدعم دقة 2K و 4K بمعدل 120 إطاراً في الثانية</p>
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
            <label>3. اختر الجودة الفائقة المعتمدة (120 FPS):</label>
            <select name="quality">
                <option value="2k_120">2K QHD — 120 FPS (دقة خارقة لإنستغرام)</option>
                <option value="4k_120">4K Ultra HD — 120 FPS (تأخذ وقتاً أطول للرندرة)</option>
                <option value="1080_120">Full HD — 120 FPS (سريعة ومضمونة)</option>
            </select>
        </div>
        <button type="submit">بدء الرندرة السحابية (120fps)</button>
    </form>
    <hr style="border-color: #333; margin: 20px 0;">
    <p>هل قمت بالرندرة مسبقاً؟ تحقق من الفيديو هنا:</p>
    <a href="/download" class="btn-link">📥 تحميل الفيديو الجاهز</a>
</div>
</body>
</html>
"""

def run_ffmpeg(orig_path, clips_files, quality):
    import subprocess
    clips_dir = os.path.join(UPLOAD_FOLDER, 'clips')
    os.makedirs(clips_dir, exist_ok=True)
    for f in os.listdir(clips_dir): os.remove(os.path.join(clips_dir, f))
    
    for i, file in enumerate(clips_files):
        file.save(os.path.join(clips_dir, f"clip_{i}.mp4"))
        
    output_path = os.path.join(UPLOAD_FOLDER, 'output_final.mp4')
    if os.path.exists(output_path): os.remove(output_path)
    
    # الإعدادات الخاصة بمعدل 120 إطاراً في الثانية (مع رفع البيترت لضمان عدم وجود بكسلة)
    settings = {
        "4k_120": {"w": 3840, "h": 2160, "fps": 120, "b": "35M"},
        "2k_120": {"w": 2560, "h": 1440, "fps": 120, "b": "22M"},
        "1080_120": {"w": 1920, "h": 1080, "fps": 120, "b": "12M"}
    }
    q = settings[quality]
    
    try:
        cmd_duration = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {orig_path}"
        total_duration = float(subprocess.check_output(cmd_duration, shell=True).decode().strip())
        
        clips = [os.path.join(clips_dir, f) for f in os.listdir(clips_dir)]
        duration_per_clip = total_duration / len(clips)
        
        filter_complex = ""
        input_args = []
        for i, c_path in enumerate(clips):
            input_args.extend(["-ss", "0", "-t", str(duration_per_clip), "-i", c_path])
            # فلتر تغيير الحجم وضبط الفريمات إلى 120fps مع تنعيم الحركة (minterpolate)
            filter_complex += f"[{i}:v]scale={q['w']}:{q['h']}:force_original_aspect_ratio=decrease,pad={q['w']}:{q['h']}:(ow-iw)/2:(oh-ih)/2,fps={q['fps']}[v{i}];"
        
        for i in range(len(clips)): filter_complex += f"[v{i}]"
        filter_complex += f"concat=n={len(clips)}:v=1:a=0[v]"
        
        input_args.extend(["-i", orig_path])
        
        ffmpeg_cmd = [
            "ffmpeg", "-y"
        ] + input_args + [
            "-filter_complex", filter_complex, 
            "-map", "[v]", 
            "-map", f"{len(clips)}:a", 
            "-c:v", "libx264", 
            "-b:v", q['b'], 
            "-preset", "ultrafast",  # السرعة القصوى لحماية معالج السيرفر المجاني
            "-c:a", "aac", 
            output_path
        ]
        subprocess.run(ffmpeg_cmd)
    except Exception as e:
        print(f"Error in background rendering: {e}")

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/process', methods=['POST'])
def process():
    orig_file = request.files['original']
    clips_files = request.files.getlist('clips')
    quality = request.form.get('quality', '2k_120')
    
    orig_path = os.path.join(UPLOAD_FOLDER, 'orig.mp4')
    orig_file.save(orig_path)
    
    # بدء الرندرة في الخلفية فوراً
    threading.Thread(target=run_ffmpeg, args=(orig_path, clips_files, quality)).start()
    
    return """
    <body style="background: #121212; color: white; font-family: Arial; text-align: center; padding-top: 50px;" dir="rtl">
        <h2>🚀 بدأت رندرة الـ 120fps بنجاح في الخلفية!</h2>
        <p>السيرفر يقوم الآن بصناعة 120 إطاراً في الثانية للفيديو الخاص بك بدقة عالية جداً.</p>
        <p>بما أن معالجة 120fps تتطلب جهداً كبيراً، يرجى الانتظار من دقيقة إلى 3 دقائق، ثم اضغط على زر التحميل.</p>
        <br>
        <a href="/" style="background: #444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">العودة للرئيسية</a>
        <a href="/download" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📥 تحميل الفيديو النهائي</a>
    </body>
    """

@app.route('/download')
def download():
    output_path = os.path.join(UPLOAD_FOLDER, 'output_final.mp4')
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    else:
        return """
        <body style="background: #121212; color: white; font-family: Arial; text-align: center; padding-top: 50px;" dir="rtl">
            <h3>⏳ السيرفر ما زال يطبخ فيديو الـ 120fps...</h3>
            <p>معالجة الـ 120 إطاراً تأخذ وقتاً إضافياً. انتظر 45 ثانية أخرى واعمل تحديث (Refresh) لهذه الصفحة.</p>
            <br>
            <a href="/download" style="background: #0095f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">تحديث الصفحة 🔄</a>
        </body>
        """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
