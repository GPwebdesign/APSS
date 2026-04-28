#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

WEEL_RADIUS = 12.5 / 100 #CENTIMETRI IN METRI

class RpmSubscriber(Node):
    def __init__(self):
        super().__init__("speed_sub_node")
        self.pub = self.create_subscription(Float32, "/rpm", self.calculate_speed, 10)
        self.pub = self.create_publisher(Float32, "speed", 10)
        
    def calculate_speed(self, msg):
        speed =((2*3.14*WEEL_RADIUS*msg.data)/60)
        print(f"Riceived:  {msg.data} RPM ")
        
        speed_msg = Float32()
        speed_msg.data = float(speed)
        print(f"Sending:  {speed} m/sec")
        self.pub.publish(speed_msg)
        
"""
RPM (rotazioni per minuto) è un'unità di misura della velocità di rotazione 
di un corpo puntiforme, che si muove lungo una circonferenza. 
La velocità lineare (espressa in m/sec) del corpo suddetto, 
è data dalla seguente formula:

V = 2 * π* R * W / 60
nella quale
V = velocità lineare
R = raggio espresso in metri
W = velocità angolare espressa in rpm       
"""


def main(args=None):
    rclpy.init()
    my_sub = RpmSubscriber()
    print("Speed Calculator Node Running...\nWaiting for data to be published...")

    try:
        rclpy.spin(my_sub)
    except KeyboardInterrupt:
        print("Terminating Node...")
        my_sub.destroy_node()


if __name__ == '__main__':
    main()