import cv2
import struct

class VideoSender:
    def __init__(self, topic_name,video_path,format="png"):
        self.__topic_name =  topic_name
        self.__cap = cv2.VideoCapture(video_path)
        self.__format = format # "jpg" or "png"

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

            # 圧縮してpngまたはjpegにエンコード
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, 90] if self.__format == "jpg" else [cv2.IMWRITE_PNG_COMPRESSION, 3]
            success, encoded_frame = cv2.imencode(f".{self.__format}", frame, encode_param)

            if not success:
                print("Frame encoding failed.")
                return None
            
            # フレームを uint8 → bytes に変換
            frame_bytes = encoded_frame.tobytes()
            
            header = struct.pack("3s", self.__format.encode("utf-8"))
            return header + frame_bytes
        
        except Exception as e:
            print(f"get_data error {e}")
            return None

    def cleanup(self):
        """
        リソースの解放
        """
        self.__cap.release()