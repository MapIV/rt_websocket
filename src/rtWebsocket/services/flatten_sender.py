import json
import time
import bson
import numpy as np
from pypcd4 import PointCloud

class FlattenSender:
    def __init__(self, topic_name: str, file_path: str, chunk_size: int = 1024 * 100):
        """
        topic_name: WebSocketで使用するトピック名
        file_path: PCDファイルのパス
        chunk_size: 1回のデータ送信時のポイント数
        """
        self.__topic_name =  topic_name 
        self.__chunk_size = chunk_size  
        self.__data = self._read_pcd_file(file_path)
        self.__filename = file_path.split("/")[-1]
        self.__chunk_index = 0 

    def _read_pcd_file(self, file_path: str):
        """
        PCDファイルを読み取り、NaNを除去してNumpy配列に変換
        """
        try: 
            pc: PointCloud = PointCloud.from_path(file_path)
            array: np.ndarray = pc.numpy()

            # NaNを含むポイントを除去
            mask = ~np.isnan(array[:, :4]).any(axis=1)
            filtered_array = array[mask]

            print(f"PCD file: {file_path}")
            print(f"Original shape: {array.shape}, Filtered shape: {filtered_array.shape}")

            return filtered_array

        except Exception as e:
            print(f"Error reading PCD file: {str(e)}")
            return []


    def get_data(self):
        try:
            if len(self.__data) == 0:
                print("No data")
                return None

            chunk_data = self.__data[:self.__chunk_size]

            if len(chunk_data) == 0:
                print("All data has been sent.")
                return None
            print(f"before flatten and tobyte time: {time.time()}")
            points_bytes = chunk_data[:, :3].astype(np.float32).tobytes()
            print(f"after flatten  and tobyte: {time.time()}")
            
         
            # 送信済みデータを削除
            self.__data = self.__data[self.__chunk_size:]
            self.__chunk_index += 1
            return points_bytes
        
        except Exception as e:
            print(f"get_data error {e}")
            return None

    def cleanup(self):
        self.__data = []
        self.__chunk_index = 0