import os
import threading
import time
from flask import Flask, request, render_template_string, send_file, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ملف نصي لتخزين النسبة الحالية للمعالجة
PROGRESS_FILE = os.path.join(UPLOAD_FOLDER, 'progress.txt')

def set_progress(val):
    with open(PROGRESS_FILE, 'w') as f:
        f.write(str(val))

def get_progress():
    if not os.path.exists(PROGRESS_FILE):
        return 0
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return int(f.read().strip())
    except:
        return 0

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
    </style>
</head>
<body>
<div class="container">
    <h2>محرر الفيديو السحابي الخارق ⚡</h2>
    <p>دقة 2K و 4K بمعدل 120 إطاراً مع عداد معالجة ذكي</p>
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
            <label>3. اختر الجودة الفائقة (120 FPS):</label>
            <select name="quality">
                <option value="2k_120">2K QHD — 120 FPS (ينصح به)</option>
                <option value="4k_120">4K Ultra HD — 120 FPS</option>
                <option value="1080_120">Full HD — 120 FPS</option>
            </select>
        </div>
        <button type="submit">بدء الرندرة السحابية (120fps)</button>
    </form>
</div>
</body>
</html>
"""

def simulate_and_run_ffmpeg(orig_path, clips_files, quality):
    import subprocess
    set_progress(5) # بدأت العملية، حفظ الملفات المرفوعة
    
    clips_dir = os.path.join(UPLOAD_FOLDER, 'clips')
    os.makedirs(clips_dir, exist_ok=True)
    for f in os.listdir(clips_dir): os.remove(os.path.join(clips_dir, f))
    
    for i, file in enumerate(clips_files):
        file.save(os.path.join(clips_dir, f"clip_{i}.mp4"))
    
    set_progress(15) # تم تنظيم وترتيب اللقطات
    
    output_path = os.path.join(UPLOAD_FOLDER, 'output_final.mp4')
    if os.path.exists(output_path): os.remove(output_path)
    
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
            filter_complex += f"[{i}:v]scale={q['w']}:{q['h']}:force_original_aspect_ratio=decrease,pad={q['w']}:{q['h']}:(ow-iw)/2:(oh-ih)/2,fps={q['fps']}[v{i}];"
        
        for i in range(len(clips)): filter_complex += f"[v{i}]"
        filter_complex += f"concat=n={len(clips)}:v=1:a=0[v]"
        
        input_args.extend(["-i", orig_path])
        
        set_progress(35) # تم إنشاء خريطة دمج الفريمات والأبعاد
        
        ffmpeg_cmd = [
            "ffmpeg", "-y"
        ] + input_args + [
            "-filter_complex", filter_complex, 
            "-map", "[v]", 
            "-map", f"{len(clips)}:a", 
            "-c:v", "libx264", 
            "-b:v", q['b'], 
            "-preset", "ultrafast", 
            "-c:a", "aac", 
            output_path
        ]
        
        # تشغيل ffmpeg ومحاكاة تقدم العداد تدريجياً لراحة العين أثناء الرندرة الثقيلة
        process = subprocess.Popen(ffmpeg_cmd)
        
        current_p = 35
        while process.poll() is None:
            time.sleep(1)
            if current_p < 95:
                current_p += 4  # يزيد العداد ببطء بينما المعالج شغال في الخلفية
                set_progress(current_p)
                
        if process.returncode == 0:
            set_progress(100) # انتهى بنجاح!
        else:
            set_progress(-1)  # حصل خطأ
            
    except Exception as e:
        print(f"Error: {e}")
        set_progress(-1)

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
    
    set_progress(0)
    threading.Thread(target=simulate_and_run_ffmpeg, args=(orig_path, clips_files, quality)).start()
    
    # صفحة الانتظار الذكية؛ تحتوي على جافاسكريبت يقوم بتحديث العداد تلقائياً كل ثانية
    return """
    <body style="background: #121212; color: white; font-family: Arial, sans-serif; text-align: center; padding-top: 50px;" dir="rtl">
        <div style="max-width: 450px; margin: 0 auto; background: #1e1e1e; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
            <h2>🚀 جاري العمل على فيديو الـ 120fps...</h2>
            <p>يرجى عدم إغلاق هذه الصفحة. السيرفر يقوم بالمعالجة الآن.</p>
            
            <!-- شكل العداد الدائري أو البار المئوي -->
            <div style="background: #333; border-radius: 20px; width: 100%; height: 25px; margin: 25px 0; overflow: hidden;">
                <div id="progress-bar" style="background: linear-gradient(90deg, #e1306c, #0095f6); width: 0%; height: 100%; transition: width 0.4s ease;"></div>
            </div>
            
            <h1 id="progress-text" style="color: #0095f6; font-size: 48px; margin: 10px 0;">0%</h1>
            <p id="status-msg" style="color: #aaa;">يتم الآن رفع الفيديوهات وتحضير السيرفر...</p>
            
            <div id="download-zone" style="display: none; margin-top: 20px;">
                <h3 style="color: #28a745;">✨ اكتملت الرندرة بنجاح عالي!</h3>
                <a href="/download" style="display: inline-block; background: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;">📥 تحميل الفيديو بدقة 120fps الآن</a>
            </div>
        </div>

        <script>
            function checkProgress() {
                fetch('/progress_status')
                    .then(response => response.json())
                    .then(data => {
                        let p = data.progress;
                        if (p === -1) {
                            document.getElementById('progress-text').innerText = "خطأ";
                            document.getElementById('status-msg').innerText = "عذراً، حدث ضغط زائد على السيرفر المجاني، يرجى المحاولة بلقطات أقصر.";
                            document.getElementById('progress-bar').style.backgroundColor = "#dc3545";
                            return;
                        }
                        
                        // تحديث شكل البار والنسبة المئوية
                        document.getElementById('progress-bar').style.width = p + "%";
                        document.getElementById('progress-text').innerText = p + "%";
                        
                        if (p > 5 && p <= 15) document.getElementById('status-msg').innerText = "جاري تجميع اللقطات وتنسيق التوقيت الفني...";
                        if (p > 15 && p <= 45) document.getElementById('status-msg').innerText = "جاري رفع معدل الإطارات إلى 120fps وصناعة النعومة الخارقة...";
                        if (p > 45 && p < 100) document.getElementById('status-msg').innerText = "جاري معالجة الصوت والألوان وضغط الأبعاد النهائية لتناسب إنستغرام...";
                        
                        if (p === 100) {
                            document.getElementById('status-msg').innerText = "تم حفظ الفيديو بنجاح!";
                            document.getElementById('download-zone').style.display = "block";
                        } else {
                            setTimeout(checkProgress, 1500); // إعادة الفحص كل ثانية ونصف
                        }
                    });
            }
            setTimeout(checkProgress, 1000); // ابدأ الفحص بعد ثانية من الدخول
        </script>
    </body>
    """

@app.route('/progress_status')
def progress_status():
    return jsonify({"progress": get_progress()})

@app.route('/download')
def download():
    output_path = os.path.join(UPLOAD_FOLDER, 'output_final.mp4')
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    else:
        return "الملف غير موجود، يرجى إعادة الرندرة."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
