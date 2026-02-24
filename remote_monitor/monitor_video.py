import asyncio
import cv2
import time
from aiohttp import web
from aiortc import VideoStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

relay = MediaRelay()

class VideoFileTrack(VideoStreamTrack):
    """
    该类负责从视频文件读取帧
    """
    def __init__(self, path):
        super().__init__()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            print(f"错误: 无法打开视频文件 {path}")

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        ret, frame = self.cap.read()
        
        # 如果视频播放结束，重头开始循环（模拟直播）
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        # 在画面上实时打印当前时间戳，方便你肉眼比对延迟
        curr_time = time.strftime("%H:%M:%S", time.localtime())
        cv2.putText(frame, f"Server Time: {curr_time}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 转换格式
        new_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        new_frame.pts = pts
        new_frame.time_base = time_base
        return new_frame

# --- 以下逻辑与之前基本一致，仅修改了 Track 的实例化 ---

async def index(request):
    with open("index.html", "r", encoding="utf-8") as f:
        return web.Response(content_type="text/html", text=f.read())

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    
    # 使用视频文件作为源
    video_track = VideoFileTrack("test.mp4") 
    pc.addTrack(relay.subscribe(video_track))

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})

app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)