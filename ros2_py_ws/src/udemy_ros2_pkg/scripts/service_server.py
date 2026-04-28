#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from udemy_ros2_pkg.srv import OddEvenCheck


class OddEvenCheckServer(Node):
    def __init__(self):
        super().__init__("odd_even_service_node")
        self.srv = self.create_service(OddEvenCheck, 'odd_even_check', self.determine_odd_even)

    def determine_odd_even(self, request, response):
        print(f"Request Received ..processing {request.number}")

        #ricorda il servizio ha una richiesta con nome number di tipo int64 e 
        #una risposta con nome decision di tipo string
        
        # OddEvenCheck.srv
        # int64 number 
        # ---
        # string decision

        if request.number % 2 == 0:
            response.decision ="Even"
        elif request.number % 2 == 1:
            response.decision ="Odd"
        else:
            response.decision ="ERROR!!"
        
        print(request)
        print(response)

        return (response)
    
    


def main(args=None):
    rclpy.init()
    server_node = OddEvenCheckServer()
    print("Odd Even Check Service Server Node Running...")
    


    try:
        rclpy.spin(server_node)
    except KeyboardInterrupt:
        print("Terminating Node...")
        server_node.destroy_node()


if __name__ == '__main__':
    main()