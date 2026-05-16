#!/usr/bin/env python3
"""
APSS — Launch file LiDAR + robot_state_publisher
Avvia:
  - Driver RPLIDAR A1M8 su /dev/ttyUSB1
  - robot_state_publisher con URDF apss_robot
  - tf statico map → odom → base_footprint
"""
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from ament_index_python.packages import get_package_share_directory as get_pkg


def generate_launch_description():

    pkg_share = get_package_share_directory('udemy_ros2_pkg')
    urdf_file = os.path.join(pkg_share, 'urdf', 'apss_robot.urdf.xml')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([

        # RPLIDAR A1M8
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar',
            parameters=[{
                'serial_port': '/dev/ttyUSB1',
                'serial_baudrate': 115200,
                'frame_id': 'laser',
                'angle_compensate': True,
                'scan_mode': 'Standard',
            }],
            output='screen',
        ),

        # robot_state_publisher con URDF APSS
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen',
        ),

        # tf statico: map → odom
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom',
            arguments=['--x', '0', '--y', '0', '--z', '0',
                       '--roll', '0', '--pitch', '0', '--yaw', '0',
                       '--frame-id', 'map',
                       '--child-frame-id', 'odom'],
            output='screen',
        ),

        # SLAM Toolbox — modalita mapping online
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            parameters=[{
                'use_sim_time': False,
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_footprint',
                'scan_topic': '/scan',
                'mode': 'mapping',
                'max_laser_range': 8.0,
                'minimum_laser_range': 0.2,
                'resolution': 0.05,
                'minimum_travel_distance': 0.1,
                'minimum_travel_heading': 0.1,
                'map_update_interval': 5.0,
            }],
            output='screen',
        ),

        # RViz2 con configurazione APSS
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(pkg_share, 'rviz', 'apss.rviz')],
            output='screen',
        ),

    ])
