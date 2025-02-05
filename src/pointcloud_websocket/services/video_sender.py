import bson
import numpy as np
import cv2

class ByteSender:
    def __init__(self, topic_name,video_path):
        self.__topic_name =  topic_name
        self.__video_path = video_path
        self.__cap = cv2.VideoCapture(self.__video_path)
        self.__height = self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.__width = self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    def get_data(self):
        """
        動画のフレームを取得して、バイトデータに変換して返す
        """
        try:
            ret, frame = self.__cap.read()
            if not ret:
                return None  # 動画の終端なら None を返す

            # フレームを NumPy の ndarray → bytes に変換
            frame_bytes = frame.flatten().tobytes()

            data = {
                "header": self.__topic_name,
                "width": self.__width,
                "height": self.__height,
                "pixel_size": 24,  # RGB (3チャンネル)なら24bit
                "data": frame_bytes
            }
            return data 
        finally:
            pass

    def cleanup(self):
        """
        リソースの解放
        """
        self.__cap.release()