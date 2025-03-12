import time
import ffmpeg
import struct
import cv2

class VideoV9Sender:
    def __init__(self, topic_name,video_path):
        self.__topic_name =  topic_name
        self.__video_path = video_path  
        self.__cap = cv2.VideoCapture(video_path)
        self.__first_frame = True
        self.__sequence_number = 0

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
                return struct.pack("3s", b"end")  # 動画の終端なら None を返す

            print(f"Frame shape: {frame.shape}")
            print(f"Frame type: {frame.dtype}")
            # process = (
            #     ffmpeg
            #     .input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f"{int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            #     .output('pipe:', format='webm', vcodec='libvpx-vp9', pix_fmt='yuv420p',)
            #     .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            # )
            # print("before encoding time: ", time.time())
            # process = (
            #     ffmpeg
            #     .input(self.__video_path )
            #     .output('pipe:', format='webm', vcodec='libvpx-vp9', pix_fmt='yuv420p',speed=4)
            #     .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            # )
            # encoded_frame, err =  process.communicate(input=frame.tobytes())
            # # self.__process.stdin.flush()  # データが送られたか確認
            # print("after encoding time: ", time.time())
            # if not encoded_frame:
            #     print("Failed to read encoded frame.")
            #     return struct.pack("3s", b"end")
            _, buffer = cv2.imencode('.jpg', frame)
            print(f"buffer: {buffer}")  
             # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' +
                    buffer.tobytes() + b'\r\n')

            # # H26をHEADERに追加
            # header = struct.pack("3s", b"vp9")
            # return header + encoded_frame
            while self.__cap.isOpened():
                success, frame = self.__cap.read()
                if not success:
                    break
                
                success, buffer = cv2.imencode('.jpg', frame)
                if not success:
                    continue  # 画像のエンコードに失敗した場合はスキップ
                
                frame_bytes = buffer.tobytes()  # 明示的に bytes に変換

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       frame_bytes + b'\r\n')

            self.__cap.release()
        
        except Exception as e:
            print(f"get_data error {e}")
            return None

    def cleanup(self):
        """
        リソースの解放
        """
        self.__cap.release()