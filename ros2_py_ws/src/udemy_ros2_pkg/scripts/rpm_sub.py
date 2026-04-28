#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class RpmSubscriber(Node):
    def __init__(self):
        super().__init__("rpm_sub_node")
        self.pub = self.create_subscription(Float32, "/rpm", self.subscriber_callback, 10)
        
    def subscriber_callback(self, msg):
        v =((2*3.14*0.04*msg.data)/60)*100
        print(f"Riceived:  {msg.data} RPM --> {v} cm/sec")
        
        
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
    print("RPM Subscriber Node Running...\nWaiting for data to be published...")

    try:
        rclpy.spin(my_sub)
    except KeyboardInterrupt:
        print("Terminating Node...")
        my_sub.destroy_node()


if __name__ == '__main__':
    main()