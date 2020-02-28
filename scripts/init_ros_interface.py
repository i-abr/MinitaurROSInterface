#!/usr/bin/env python


import rospy
import roslaunch

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('num_agents', type=int, help='agent number', default=1)
args, unknown = parser.parse_known_args()


if __name__ == '__main__':
    package = 'minitaur_ros_interface'
    executable = 'main.py'

    nodes       = []
    processes   = []
    launch = roslaunch.scriptapi.ROSLaunch()
    launch.start()

    minitaur_ros_node = roslaunch.core.Node(package=package, node_type='main.py', name='minitaur_ros_interface',
                                                            args='enx00e04c011fc8', output="screen")
    nodes.append(minitaur_ros_nodein)
    processes.append(launch.launch(minitaur_ros_node))

    joy_node = roslaunch.core.Node(package)


    rospy.init_node('launch_node', anonymous=True)
    rospy.spin()
