import cv2
import struct

class VideoSender:
    def __init__(self, topic_name,video_path):
        self.__topic_name =  topic_name
        self.__cap = cv2.VideoCapture(video_path)
        self.__height = int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.__width = int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    def get_data(self):
        """
        動画のフレームを取得して、バイトデータに変換して返す
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

            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)
            # フレームを NumPy の ndarray → bytes に変換
            frame_bytes = frame.flatten().tobytes()
            print(f"frame_bytes: {type(frame_bytes)}")  

            # headerのbyteの構築 (width, height, pixel_size, image_data)
            header = struct.pack("iii", self.__width, self.__height, 32)  # 24-bit RGB, 32-bit RGBA
            print(f"header: {type(header)}")

            return header + frame_bytes
        
        except Exception as e:
            print(f"get_data error {e}")
            return None

    def cleanup(self):
        """
        リソースの解放
        """
        self.__cap.release()