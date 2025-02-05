# import bson
# import numpy as np

# class BsonSender:
#     def __init__(self, topic_name):
#         self.__data = np.array([])
#         self.__topic_name =  topic_name
#         self.__is_set_data = False 

#     def set_data(self, data):
#         try:
#             __is_set_data = True
#             while(__is_set_data):
#                 data = np.random.rand(100,3)
                
#         except Exception as e:
#             print(f"set_data error {e}")

#     def get_data(self):
#         if len(self.__data) == 0:
#             return None

#         try:
#             # データを直接bsonにシリアライズ
#             bson_data = bson.BSON.encode({'header':self.__topic_name,'points': self.__data})
#             # データをクリア
#             self.__data =[]
#             return bson_data
#         finally:
#             pass

#     def cleanup(self):
#         self.__data = []