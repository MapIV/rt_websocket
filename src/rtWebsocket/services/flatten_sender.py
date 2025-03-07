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
        self.__field_data = []
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
            self.__field_data = list(pc.fields)[3:] 

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
            print(f"chunk_data: {chunk_data.shape}")

            if len(chunk_data) == 0:
                print("All data has been sent.")
                return None
            print(f"before flatten and tobyte time: {time.time()}")
            points_bytes = chunk_data[:, :3].flatten().tobytes()
            field_bytes = chunk_data[:, 3:].flatten().tobytes() if chunk_data.shape[1] > 3 else b''
            print(f"after flatten  and tobyte: {time.time()}")
            
            header = {
                'filename': self.__filename,
                'chunk_index': self.__chunk_index,
                'chunk_size': self.__chunk_size,
                'fields': self.__field_data,
                'points_length': len(points_bytes),
                'field_length': len(field_bytes)
            }

            # Encode the header as JSON and then to bytes
            header_bytes = json.dumps(header).encode('utf-8')
            
            # Create a 4-byte length prefix for the header
            header_len = len(header_bytes).to_bytes(4, byteorder='little')
            
            # Combine everything into a single byte string
            send_data = header_len + header_bytes + points_bytes + field_bytes
         
            # delete sent data
            self.__data = self.__data[self.__chunk_size:]
            self.__chunk_index += 1
            return send_data 
        
        except Exception as e:
            print(f"get_data error {e}")
            return None

    def cleanup(self):
        self.__data = []
        self.__chunk_index = 0
        self.__field_data = ['x', 'y', 'z',]
