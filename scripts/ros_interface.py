'''
MIT License (modified)

Copyright (c) 2018 Ghost Robotics
Authors:
Avik De <avik@ghostrobotics.io>
Tom Jacobs <tom.jacobs@ghostrobotics.io>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this **file** (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

''' How to use:

See main.py

'''

''' ROS interface for ethernet example '''
bROS = False
try:
    import rospy
    import numpy as np
    import tf
    import std_msgs
    from sensor_msgs.msg import Imu, BatteryState, JointState, Joy
    from std_msgs.msg import UInt32
    from nav_msgs.msg import Odometry
    from geometry_msgs.msg import Twist, Pose
    from utils import mapFromTo, minitaurFKForURDF, convert_to_leg_model
    bROS = True
except:
    print('No ROS found; continuing.')


class RosInterface(object):

    def __init__(self):

        # ROS variables
        self.robotname = "robot0"
        self.publish_time = 0
        self.pubs = []
        self.subs = []

        # Commands received from ROS
        self.behaviorId = 0
        self.behaviorMode = 0

        # initialize the rot command and the ext command
        self.rot_cmd = [0.0, 0.0, 0.0, 0.0]
        self.ext_cmd = [0.14, 0.14, 0.14, 0.14]

        self.initROS()

    def initROS(self):

        # Get robot name param from ROS
        if bROS:
            try:
                if rospy.has_param('robotname'):
                    self.robotname = rospy.get_param('robotname')
            except:
                print("ROS master not running.")

            # Create publishers and subscribers
            self.pubs = [
                rospy.Publisher(self.robotname + '/state/imu', Imu, queue_size=10),
                rospy.Publisher(self.robotname + '/state/batteryState', BatteryState, queue_size=10),
                rospy.Publisher(self.robotname + '/state/behaviorId', UInt32, queue_size=10),
                rospy.Publisher(self.robotname + '/state/behaviorMode', UInt32, queue_size=10),
                rospy.Publisher(self.robotname + '/state/joint', JointState, queue_size=10),
                rospy.Publisher(self.robotname + '/state/jointURDF', JointState, queue_size=10),
                rospy.Publisher(self.robotname + '/state/joystick', Joy, queue_size=10),
                rospy.Publisher(self.robotname + '/state/pose', Pose, queue_size=10),
            ]
            # going to comment these out for now since we are not using this variation just yet
            self.subs = [
                # rospy.Subscriber(robotname + '/command/cmd_vel', Twist, self.cmd_vel_callback),
                # rospy.Subscriber(robotname + '/command/joy', Joy, self.joy_callback),
                rospy.Subscriber('/joy', Joy, self.joy_callback),
                # rospy.Subscriber(robotname + '/command/behaviorId', UInt32, self.behaviorId_callback),
                # rospy.Subscriber(robotname + '/command/behaviorMode', UInt32, self.behaviorMode_callback),
            ]

            # Init ROS node
            rospy.init_node('ethernet_robot_control')

    def getCommands(self):
        return self.rot_cmd, self.ext_cmd

    def joy_callback(self, data):
        lateral = mapFromTo(data.axes[3], -1.0, 1.0, -0.1, 0.1)
        linear_x = mapFromTo(data.axes[1], -1.0, 1.0, 0.12, 0.18)
        for i in range(len(self.ext_cmd)):
            self.ext_cmd[i] = linear_x
            self.rot_cmd[i] = lateral

    # TODO: implement the following
    def cmd_vel_callback(self, data):
        """not implemented"""
        linear_x = data.linear.x
        angular_z = data.angular.z

    def behaviorId_callback(self, data):
        """not implemented"""
        behaviorId = data.data

    def behaviorMode_callback(self, data):
        """not implemented"""
        behaviorMode = data.data

    def publishState(self, state, ros_pub_dec, numDoF):
        # Publish our robot state to ROS topics /robotname/state/* periodically
        self.publish_time += 1
        if bROS and self.publish_time > ros_pub_dec:
            publish_time = 0

            # Construct /robotname/state/imu ROS message
            msg = Imu()
            msg.linear_acceleration.x = state['imu/linear_acceleration'][0]
            msg.linear_acceleration.y = state['imu/linear_acceleration'][1]
            msg.linear_acceleration.z = state['imu/linear_acceleration'][2]
            msg.angular_velocity.x = state['imu/angular_velocity'][0]
            msg.angular_velocity.y = state['imu/angular_velocity'][1]
            msg.angular_velocity.z = state['imu/angular_velocity'][2]
            msg.orientation_covariance = state['imu/orientation_covariance']
            msg.linear_acceleration_covariance = np.empty(9)
            msg.linear_acceleration_covariance.fill(state['imu/linear_acceleration_covariance'])
            msg.angular_velocity_covariance = np.empty(9)
            msg.angular_velocity_covariance.fill(state['imu/angular_velocity_covariance'])
            roll, pitch, yaw = state['imu/euler'] # Convert from euler to quaternion using ROS tf
            quaternion = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
            msg.orientation.x = quaternion[0]
            msg.orientation.y = quaternion[1]
            msg.orientation.z = quaternion[2]
            msg.orientation.w = quaternion[3]
            self.pubs[0].publish(msg)

            # Construct /robotname/state/pose
            msg = Pose()
            msg.orientation.x = quaternion[0]
            msg.orientation.y = quaternion[1]
            msg.orientation.z = quaternion[2]
            msg.orientation.w = quaternion[3]
            # TODO: Get height from robot state, have robot calculate it
            msg.position.z = 0.0
            self.pubs[7].publish(msg)

            # Construct /robotname/state/batteryState
            msg = BatteryState()
            msg.current = state['battery/current']
            msg.voltage = state['battery/voltage']
            #num_cells = 8
            num_cells = 4
            if 'battery/cell_voltage' in state:
                if state['battery/cell_voltage'] > 0:
                    num_cells = len(state['battery/cell_voltage'])
            # FIXME: do i really need this?
            def percentage(total_voltage, num_cells):
                # Linearly interpolate charge from voltage
                # https://gitlab.com/ghostrobotics/SDK/uploads/6878144fa0e408c91e481c2278215579/image.png
                charges =  [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
                voltages = [3.2, 3.5, 3.6, 3.65, 3.8, 4.2]
                return np.interp(total_voltage / num_cells, voltages, charges)
            if msg.percentage <= 0:
                msg.percentage = percentage(msg.voltage, num_cells)
            self.pubs[1].publish(msg)

            # Construct /robotname/state/behaviorId
            msg = UInt32()
            msg.data = state['behaviorId']
            self.pubs[2].publish(msg)

            # Construct /robotname/state/behaviorMode
            msg = UInt32()
            msg.data = state['behaviorMode']
            self.pubs[3].publish(msg)

            # Construct /robotname/state/joint
            msg = JointState()
            msg.name = []
            msg.position = []
            msg.velocity = []
            msg.effort = []
            for j in range(len(state['joint/position'])):
                msg.name.append(str(j))
                msg.position.append(state['joint/position'][j])
                msg.velocity.append(state['joint/velocity'][j])
                msg.effort.append(state['joint/effort'][j])
            self.pubs[4].publish(msg)
            msg.position = convert_to_leg_model(msg.position)
            # Translate for URDF in NGR
            # vision60 = False
            # if(vision60):
            #     for i in range(8, 2):
            #         msg.position[i] += msg.position[i-1];
            #         msg.velocity[i] += msg.velocity[i-1];
            # else:
            #     # other URDF
            #     # for URDF of Minitaur FIXME use the class I put in ethernet.py for RobotType
            #     msg.position.extend([0, 0, 0, 0, 0, 0, 0, 0])
            #     msg.position[11], msg.position[10], r = minitaurFKForURDF(msg.position[0], msg.position[1])
            #     msg.position[14], msg.position[15], r = minitaurFKForURDF(msg.position[2], msg.position[3])
            #     msg.position[9], msg.position[8], r = minitaurFKForURDF(msg.position[4], msg.position[5])
            #     msg.position[13], msg.position[12], r = minitaurFKForURDF(msg.position[6], msg.position[7])
            #     # other URDF problems (order important)
            #     for j in range(4):
            #         msg.position[j] = -msg.position[j]

            self.pubs[5].publish(msg)

        # Construct /robotname/state/joystick
        msg = Joy()
        msg.axes = state['joy/axes']
        msg.buttons = state['joy/buttons']
        self.pubs[6].publish(msg)

        # Current robot twist received back from robot
        # TODO:
        #state['twist/linear']
        #state['twist/angular']
    def toContinue(self):
        if bROS:
            return not rospy.is_shutdown()
        else:
            return True
