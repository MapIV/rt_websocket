import rospy
from sensor_msgs.msg import PointCloud2
from pypcd import PointCloud
import bson
import numpy as np
import logging as getLogger

class RosClientXYZ:
    def __init__(self, topic_name):
        self.__data = np.array([])
        print("set_data")
        self.__input_topic =  topic_name
        self.__logger = getLogger("Log").getChild("RosClient")    
        rospy.init_node('listener', anonymous=True) 
        rospy.loginfo("Subscribed to: {}".format(self.__input_topic))
        self.__sub = rospy.Subscriber(self.__input_topic, PointCloud2, self._callback,queue_size=1)

    def connect_subscription(self):
        try : 
            self.__logger.info("xyz spin start")
            rospy.spin()
            self.__logger.info("spin end")
        except Exception as e:
            print(f"connect_subscription error {e}")

    # dataを返し、クリアする
    def get_data(self):
        if len(self.__data)== 0:
            return None

        try:
            self.__logger.info(" xyz lock acquire")
            # データを直接bsonにシリアライズ
            bson_data = bson.BSON.encode({'header':self.__input_topic,'points': list(self.__data)})
            # データをクリア
            self.__data = np.array([])
            return bson_data
        finally:
            # self.__lock.release()
            self.__logger.info(" xyzlock release")
    

    # dataを別スレッドで処理する
    def _callback(self, cloud_msg):
            if self.__data != np.array([]):
                return
            pc = PointCloud.from_msg(cloud_msg)
            points = pc.numpy(("x", "y", "z"))
            # Remove points where x, y, z are NaN
            mask = ~np.isnan(points[:, :3]).any(axis=1)
            self.__logger.info(f"xpoints shape: {points.shape}")
            # Get only every 10 dots.
            # filtered_points = points[mask].tolist()[::10]
            
            # Get all points
            self.__logger.info("xyz to list start")
            filtered_points = points[mask].tolist()
            self.__logger.info("xyz to list end")

            self.__data = filtered_points

    def cleanup(self):
        self.__logger.info("Shutting down")
        self.__sub.unregister()
        


