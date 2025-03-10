import ffmpeg
import struct
import cv2

class Videoh264Sender:
    def __init__(self, topic_name,video_path):
        self.__topic_name =  topic_name
        self.__cap = cv2.VideoCapture(video_path)

    def get_data(self):
        """
        動画のフレームを取得して、バイトデータに変換して返す(H264)
        """
        try:
            if not self.__cap.isOpened():
                print("VideoCapture not opened.")
                return None
            ret, frame = self.__cap.read()

            if not ret:
                print("Frame read failed.")
                self.__cap.release()
                return None  # 動画の終端なら None を返す

            print(f"Frame shape: {frame.shape}")
            print(f"Frame type: {frame.dtype}")
            process = (
                ffmpeg
                .input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f"{int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
                .output('pipe:', format='webm', vcodec='libvpx-vp9', pix_fmt='yuv420p')
                .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            )
            encoded_frame, err =  process.communicate(input=frame.tobytes())
            # self.__process.stdin.flush()  # データが送られたか確認

            if not encoded_frame:
                print("Failed to read encoded frame.")
                return None
            
            # H26をHEADERに追加
            header = struct.pack("3s", b"vp9")
            return header + encoded_frame
        
        except Exception as e:
            print(f"get_data error {e}")
            return None

    def cleanup(self):
        """
        リソースの解放
        """
        self.__cap.release()