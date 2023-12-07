#!/usr/bin/env python
import socket
import rospy 
from std_msgs.msg import String, Bool
from threading import Thread, Timer, Event
import time 
import signal


class udp2rosBridge:

    def __init__(self):

        ''' ROS INITIALIZATION '''
        rospy.init_node('udp2ros_qr_bridge', anonymous=True)
        print("UDP to ROS QR Bridge started")

        self.HoloGaze_results_publisher = rospy.Publisher('/HoloGaze_results', String, queue_size=10)
        self.idle_publisher = rospy.Publisher('/idle', Bool, queue_size=10)
        rospy.Subscriber('/HoloGaze_activation', Bool, self.activation_callback)
        print("ROS initialized")

        ''' SOCKET INITIALIZATION '''
        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Define the server address and port
        self.server_address = ('130.251.13.131', 3090)

        # Bind the socket to a specific address and port
        self.sock.bind(self.server_address)
        print("Socket created")

        ''' START SOCKET LISTENING LOOP ON A SEPARATE THREAD '''
        self.thread_stop_event = Event()
        self.socket_thread = Thread(target=self.socket_reading_loop)
        self.socket_thread.start()

        ''' SET THE TIMER THREAD AND CALLBACK '''
        self.idle_delay = 5.0
        self.timer = Timer(self.idle_delay, self.timer_callback)
        # self.timer.start()
        print("Timer created")

        ''' THIS PREVENTS THE IDLE CLASSIFICATION UNTIL ROS SIG IS RECEIVED '''
        self.idle_activation = False


    def timer_create_and_start(self):
        self.timer = Timer(self.idle_delay, self.timer_callback)
        # print('Timer created')
        self.timer.start()
        # print('Timer started')


    def timer_callback(self):
        print(">>>>> Timer Callback Started <<<<<")
        self.idle_publisher.publish(True)
        self.idle_activation = False
        '''Logic of the callback'''
        print(">>>>> Timer Callback Ended <<<<<")

    
    def reset_timer(self):
        self.timer.cancel()
        # print('Timer stopped')
        self.timer_create_and_start()
        

    def activation_callback(self, msg):
        print("Received message: ", msg.data)
        self.idle_activation = True
        print("idle_activation set to: ", msg.data)


    def thread_stop(self):
        print('thread_stop Called')
        self.thread_stop_event.set()
        self.idle_activation = False
        self.timer.cancel()


    def thread_stopped(self):
        # print(self.thread_stop_event.is_set())
        return self.thread_stop_event.is_set()


    def socket_reading_loop(self):
        print('===== Started socket_reading_loop =====')
        while not self.thread_stopped():
            # Receive data from clients
            data, address = self.sock.recvfrom(4096)
            msg = String()
            msg.data = data.decode()
            print('Received:', msg.data, 'from:', address)

            if 'manipulating' in msg.data.lower():
                if self.idle_activation:
                    self.reset_timer()
            elif 'idle' in msg.data.lower():
                continue
            else:
                self.HoloGaze_results_publisher.publish(msg.data)

        # Close the socket
        self.sock.close()
        print('===== socket_reading_loop Ended =====')



if __name__ == "__main__":
    bridge = udp2rosBridge()
    rospy.spin()
    bridge.thread_stop()
