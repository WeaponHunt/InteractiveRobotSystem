import cv2
import numpy as np
import time
from flask import Flask, Response

app = Flask(__name__)

def generate_frames():
    while True:
        # 1. 创建一个 640x480 的黑色背景测试画面
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 2. 在画面上画上当前时间
        curr_time = time.strftime("%H:%M:%S", time.localtime())
        cv2.putText(img, f"Server Time: {curr_time}", (100, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        
        # 3. 将图片编码为 JPG
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        # 4. 使用 multipart 格式发送（这是 MJPEG 的标准格式）
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.1)  # 限制在 10 FPS 左右，降低 CPU 占用

@app.route('/video_feed')
def video_feed():
    # 返回视频流
    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    # 极简 HTML 页面
    return """
    <html>
      <body style="background: #222; color: white; text-align: center;">
        <h1>极简局域网监控测试</h1>
        <img src="/video_feed" style="border: 2px solid #555;">
        <p>如果你能看到跳动的时间，说明网络和 Python 服务正常。</p>
      </body>
    </html>
    """

if __name__ == "__main__":
    # 监听 0.0.0.0 以便局域网访问
    app.run(host='0.0.0.0', port=5000, debug=False)