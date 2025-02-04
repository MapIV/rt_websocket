import pytest
from src.pointcloud_websocket.services.ros_client_xyz import RosClientXYZ
from src.pointcloud_websocket.services.ros_client_trajectory import RosClientTrajectory
from src.pointcloud_websocket.services.ros_client import RosClient

def test_ros_client_xyz():
    client = RosClientXYZ("/fake_topic")
    assert client.get_data() is None

def test_ros_client_trajectory():
    client = RosClientTrajectory("/fake_topic")
    assert client.get_data() is None

def test_ros_client():
    client = RosClient("/fake_topic")
    assert client.get_data() is None