import os
import threading
import time
from flask import Flask, request, render_template_string, send_file, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# استخدام ذاكرة السيرفر المباشرة لضمان عمل العداد بدقة وبدون مشاكل ملفات
PROGRESS_MEMORY = 0

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محرر الفيديو السحابي الخارق 120fps</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0f0c20 0%, #15102a 50%, #060409 100%);
            color: #f0f0f0; 
            text-align: center; 
            padding: 20px;
            margin: 0;
            min-height: 100vh;
        }
        .container { 
            max-width: 500px; 
            margin: 30px auto; 
            background: rgba(25, 20, 45, 0.65); 
            padding: 30px; 
            border-radius: 24px; 
            box-shadow: 0 8px 32px 0 rgba(142, 68, 173, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        h2 { 
            color: #00f2fe; 
            text-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
            font-size: 26px;
            margin-bottom: 5px;
        }
        .subtitle {
            color: #9b51e0;
            font-size: 14px;
            margin-bottom: 25px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .box { 
            border: 1px solid rgba(255, 255, 255, 0.08); 
            padding: 20px; 
            margin: 20px 0; 
            border-radius: 16px; 
            background: rgba(10, 5, 20, 0.5); 
            text-align: right;
            transition: all 0.3s ease;
        }
        .box:hover {
            border-color: #00f2fe;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.15);
        }
        label {
            font-size: 14px;
            color: #ccc;
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        input[type="file"], select { 
            width: 100%; 
            padding: 12px; 
            margin-top: 5px; 
            background: #0d091b; 
            color: #fff; 
            border: 1px solid #332554; 
            border-radius: 10px; 
            outline: none;
            font-size: 14px;
        }
        input[type="file"]::file-selector-button {
            background: #4a154b;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
        }
        button { 
            background: linear-gradient(90deg, #ff007f, #7928ca); 
            color: white; 
            border: none; 
            padding: 16px; 
            width: 100%; 
            border-radius: 12px; 
            font-size: 18px; 
            font-weight: bold;
            cursor: pointer; 
            margin-top: 20px; 
            box-shadow: 0 4px 15px rgba(255, 0, 127, 0.3);
            transition: all 0.3s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 0, 127, 0.5);
            filter: brightness(1.1);
        }
    </style>
</head>
<body>
<div class="container">
    <h2>الـمُـحـرّر الـسّـحـابـي الـخـارق ✨</h2>
    <div class="subtitle">Engine: 120 FPS Ultra Cinema</div>
    
    <form action="/process" method="post" enctype="multipart/form-data">
        <div class="box">
            <label>🎬 1. فيديو المصدر (الأساسي):</label>
            <input type="file" name="original" accept="video/*" required>
        </div>
        <div class="box">
            <label>⚡ 2. لقطاتك الجديدة القوية:</label>
            <input type="file" name="clips" accept="video/*" multiple required>
        </div>
        <div class="box">
            <label>💎 3. دقة العرض ومعدل الفريمات:</label>
            <select name="quality">
                <option value="2k_120">2K QHD — 120 FPS (نعومة سينمائية)</option>
                <option value="4k_120">4K Ultra HD — 120 FPS (رندرة ثقيلة)</option>
                <option value="1080_120">Full HD — 120 FPS (سريع جداً)</option>
            </select>
        </div>
        <button type="submit">بدء الرندرة السحابية 🚀</button>
    </form>
</div>
</body>
</html>
"""

def simulate_and_run_ffmpeg(orig_path, clips_files, quality):
    import subprocess
    global PROGRESS_MEMORY
    PROGRESS_MEMORY = 5
    
    clips_dir = os.path.join(UPLOAD_FOLDER, 'clips')
    os.makedirs(clips_dir, exist_ok=True)
    for f in os.listdir(clips_dir): os.remove(os.path.join(clips_dir, f))
    
    for i, file in enumerate(clips_files):
        file.save(os.path.join(clips_dir, f"clip_{i}.mp4"))
    
    PROGRESS_MEMORY = 15
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
        PROGRESS_MEMORY = 30
        
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
        
        process = subprocess.Popen(ffmpeg_cmd)
        
        current_p = 30
        while process.poll() is None:
            time.sleep(1)
            if current_p < 96:
                current_p += 4
                PROGRESS_MEMORY = current_p
                
        if process.returncode == 0:
            PROGRESS_MEMORY = 100
        else:
            PROGRESS_MEMORY = -1
            
    except Exception as e:
        print(f"Error: {e}")
        PROGRESS_MEMORY = -1

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/process', methods=['POST'])
def process():
    global PROGRESS_MEMORY
    PROGRESS_MEMORY = 0
    
    orig_file = request.files['original']
    clips_files = request.files.getlist('clips')
    quality = request.form.get('quality', '2k_120')
    
    orig_path = os.path.join(UPLOAD_FOLDER, 'orig.mp4')
    orig_file.save(orig_path)
    
    threading.Thread(target=simulate_and_run_ffmpeg, args=(orig_path, clips_files, quality)).start()
    
    # واجهة الانتظار الفخمة والسينمائية الجديدة مع العداد المضمون
    return """
    <body style="background: linear-gradient(135deg, #0f0c20 0%, #060409 100%); color: white; font-family: Arial, sans-serif; text-align: center; padding-top: 80px;" dir="rtl">
        <div style="max-width: 450px; margin: 0 auto; background: rgba(25, 20, 45, 0.7); padding: 40px; border-radius: 24px; box-shadow: 0 0 30px rgba(0, 242, 254, 0.2); border: 1px solid rgba(0, 242, 254, 0.2); backdrop-filter: blur(10px);">
            <h2 style="color: #00f2fe; text-shadow: 0 0 10px rgba(0,242,254,0.5); margin-bottom: 5px;">🚀 جاري ضخ الـ 120fps...</h2>
            <p style="color: #9b51e0; font-size: 13px; font-weight: bold; letter-spacing: 2px;">RENDER ENGINE RUNNING</p>
            
            <!-- بار التحميل المضيء والنيون -->
            <div style="background: #0d091b; border-radius: 20px; width: 100%; height: 20px; margin: 30px 0; overflow: hidden; border: 1px solid #332554; box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);">
                <div id="progress-bar" style="background: linear-gradient(90deg, #ff007f, #00f2fe); width: 0%; height: 100%; box-shadow: 0 0 15px #00f2fe; transition: width 0.4s ease;"></div>
            </div>
            
            <h1 id="progress-text" style="color: #ff007f; font-size: 54px; margin: 10px 0; font-weight: 900; text-shadow: 0 0 15px rgba(255,0,127,0.4);">0%</h1>
            <p id="status-msg" style="color: #a5a1b8; font-size: 14px;">يتم الآن حقن الفيديوهات إلى السيرفر...</p>
            
            <div id="download-zone" style="display: none; margin-top: 30px; animation: fadeIn 0.5s ease;">
                <h3 style="color: #00f2fe; text-shadow: 0 0 10px rgba(0,242,254,0.4);">✨ اكتملت الرندرة السينمائية!</h3>
                <a href="/download" style="display: inline-block; background: linear-gradient(90deg, #00f2fe, #4facfe); color: black; padding: 14px 30px; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 15px rgba(0,242,254,0.4); transition: transform 0.2s;">📥 تحميل فيديو الـ 120fps الحارق</a>
            </div>
        </div>

        <script>
            function checkProgress() {
                // استدعاء الرابط المباشر من السيرفر بدون كاش
                fetch('/progress_status?t=' + new Date().getTime())
                    .then(response => response.json())
                    .then(data => {
                        let p = data.progress;
                        if (p === -1) {
                            document.getElementById('progress-text').innerText = "خطأ";
                            document.getElementById('status-msg').innerText = "حدث ضغط زائد، قلل حجم اللقطات وجرب مرة أخرى.";
                            return;
                        }
                        
                        document.getElementById('progress-bar').style.width = p + "%";
                        document.getElementById('progress-text').innerText = p + "%";
                        
                        if (p > 5 && p <= 15) document.getElementById('status-msg').innerText = "🎬 جاري قص وتنسيق لقطاتك وتطابقها التلقائي...";
                        if (p > 15 && p <= 50) document.getElementById('status-msg').innerText = "⚡ جاري رفع الفريمات لـ 120fps وتنعيم الحركة الحركية...";
                        if (p > 50 && p < 100) document.getElementById('status-msg').innerText = "💎 نضع اللمسات السينمائية الأخيرة ومطابقة الصوت الأصلي...";
                        
                        if (p === 100) {
                            document.getElementById('status-msg').innerText = "تمت العملية بنجاح ساحق!";
                            document.getElementById('download-zone').style.display = "block";
                        } else {
                            setTimeout(checkProgress, 1000); // فحص كل ثانية واحدة بدقة
                        }
                    }).catch(err => {
                        // إعادة المحاولة في حال حدوث اهتزاز بالشبكة
                        setTimeout(checkProgress, 1000);
                    });
            }
            setTimeout(checkProgress, 800);
        </script>
    </body>
    """

@app.route('/progress_status')
def progress_status():
    global PROGRESS_MEMORY
    return jsonify({"progress": PROGRESS_MEMORY})

@app.route('/download')
def download():
    output_path = os.path.join(UPLOAD_FOLDER, 'output_final.mp4')
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    else:
        return "الملف جاهز ولكن هناك خطأ بالتحميل، يرجى إعادة المحاولة."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
