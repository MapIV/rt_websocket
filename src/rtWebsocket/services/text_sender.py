import json
import cv2
import struct

class TextSender:
    def __init__(self, topic_name):
        self.__topic_name =  topic_name
        self.__format = "txt"

    def get_data(self):
        """
        textを送る
        """
        try:
            test_text = json.dumps({
                "header" : "text",
                "data" : [
                    {
                        "status" : "ok",
                        "name" : "test",
                        "description" : "This is a test message."   
                    },
                    {
                        "status" : "error",
                        "name" : "test",
                        "description" : "This is a test message."   
                    },
                    {
                        "status" : "warning",
                        "name" : "test",
                        "description" : "This is a test message."   
                    }
                ]
            })
            return test_text
        
        except Exception as e:
            print(f"get_data error {e}")
            return None

    def cleanup(self):
        """
        リソースの解放
        """
        pass