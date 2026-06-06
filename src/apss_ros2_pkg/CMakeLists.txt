cmake_minimum_required(VERSION 3.8)
project(apss_ros2_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/BatteryStats.msg"
  DEPENDENCIES
  sensor_msgs
  std_msgs
)

ament_python_install_package(scripts)

install(PROGRAMS
  scripts/oled_node.py
  scripts/battery_node.py
  scripts/obstacle_detector_node.py
  scripts/navigation_controller_node.py
  scripts/camera_publisher.py
  scripts/safety_node.py
  scripts/alarm_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}/
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

install(DIRECTORY
  urdf
  DESTINATION share/${PROJECT_NAME}/
)

install(DIRECTORY
  rviz
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
