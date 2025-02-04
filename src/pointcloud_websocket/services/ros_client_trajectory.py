import rospy
from sensor_msgs.msg import PointCloud2
from pypcd import PointCloud
from nav_msgs.msg import Path
import bson
import numpy as np
import logging as getLogger

class RosClientTrajectory:
    def __init__(self, topic_name):
        self.__data = np.array([])
        print("set_data")
        self.__input_topic =  topic_name
        self.__logger = getLogger("Log").getChild("RosClient")    
        rospy.init_node('listener', anonymous=True) 
        rospy.loginfo("Subscribed to: {}".format(self.__input_topic))
        self.__sub = rospy.Subscriber(self.__input_topic, Path, self._callback,queue_size=1)

    def connect_subscription(self):
        try : 
            self.__logger.info("spin start")
            rospy.spin()
            self.__logger.info("spin end")
        except Exception as e:
            print(f"connect_subscription error {e}")

    # dataを返し、クリアする
    def get_data(self):
        if len(self.__data) == 0:
            return None

        try:
            self.__logger.info("lock acquire")
            # データを直接bsonにシリアライズ
            bson_data = bson.BSON.encode({'header':self.__input_topic,'points': self.__data})
            # データをクリア
            self.__data =[]
            return bson_data
        finally:
            # self.__lock.release()
            self.__logger.info("lock release")
    

    # dataを別スレッドで処理する
    def _callback(self, path_msg):
            if self.__data != [] :
                return
            points = [] 
   
            for pose_stamped in path_msg.poses:
                point = pose_stamped.pose.position  
                points.append([point.x, point.y, point.z])
            # Get all points
            self.__logger.info("trajectory to list start")
            self.__data = points
            self.__logger.info("trajectory to list end")

    def cleanup(self):
        self.__logger.info("Shutting down")
        self.__sub.unregister()
        


