import cv2
import time
import threading
from flask import Flask, Response

app = Flask(__name__)

# 全局变量存放当前帧
output_frame = None
lock = threading.Lock()

def video_reader():
    global output_frame
    cap = cv2.VideoCapture("remote_monitor/test.mp4")  # 替换为你的远程视频路径
    
    # --- 关键修改：获取视频原有的帧率 ---
    fps = cap.get(cv2.CAP_PROP_FPS) 
    if fps <= 0: fps = 24  # 防止读取失败
    
    # 计算每一帧应该间隔的时间（秒）
    frame_duration = 1.0 / fps 
    
    while True:
        start_time = time.time() # 记录处理开始时间
        
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        # 处理图片（加时间戳等）
        # ... (之前的处理逻辑)
        frame = cv2.resize(frame, (640, 480))
        # 编码图片
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            with lock:
                output_frame = buffer.tobytes()
        
        # --- 关键修改：精准控制时间 ---
        # 实际休眠时间 = 理论帧间隔 - 本次处理耗时
        processing_time = time.time() - start_time
        sleep_time = max(0, frame_duration - processing_time)
        time.sleep(sleep_time)

def generate():
    """给每个客户端发送全局缓存中的帧"""
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                continue
            frame = output_frame
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.04)

@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '<body style="background:#000; display:flex; justify-content:center;"><img src="/video_feed" style="height:90vh;"></body>'

if __name__ == "__main__":
    # 启动读取线程
    t = threading.Thread(target=video_reader)
    t.daemon = True
    t.start()
    # 启动 Web 服务
    app.run(host='0.0.0.0', port=5000, threaded=True)