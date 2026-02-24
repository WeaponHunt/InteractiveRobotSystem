import asyncio
import cv2
from aiohttp import web
from aiortc import VideoStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

# 媒体中继，用于允许多个客户端同时连接
relay = MediaRelay()

class CameraStreamTrack(VideoStreamTrack):
    """
    该类负责从摄像头抓取画面并转换为 WebRTC 帧
    """
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # 将 OpenCV 的 BGR 格式转换为 WebRTC 帧
        new_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        new_frame.pts = pts
        new_frame.time_base = time_base
        return new_frame

async def index(request):
    content = open("index.html", "r", encoding="utf-8").read()
    return web.Response(content_type="text/html", text=content)

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState == "failed":
            await pc.close()

    # 将摄像头轨道添加到连接中
    pc.addTrack(relay.subscribe(CameraStreamTrack()))

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)