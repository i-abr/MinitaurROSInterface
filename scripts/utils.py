import numpy as np

def mapFromTo(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def minitaurFKForURDF(t0,t1):
    l1 = 0.1
    l2 = 0.2
    meanAng = 0.5 * (t0 + t1)
    diffAng = 0.5 * (t0 - t1)
    if (meanAng < 0):
        meanAng = meanAng + np.pi
        diffAng = diffAng + np.pi
    l1c = l1 * np.cos(meanAng)
    l1s = l1 * np.sin(meanAng)
    r = np.sqrt(l2 * l2 - l1s * l1s) - l1c
    if r < 0:
        r = -r
    # r tested - looks right
    # stupid law of cosines
    phi = np.arccos((l2 * l2 + l1 * l1 - r * r)/ (2 * l1 * l2))
    return np.pi - phi, np.pi + phi, r

def convert_to_leg_model(motor_angles):
    """A helper function to convert motor angles to leg model.

    Args:
    motor_angles: raw motor angles:

    Returns:
    leg_angles: the leg pose model represented in swing and extension.
    """
    # TODO(sehoonha): clean up model conversion codes
    num_legs = 4
    # motor_angles = motor_angles / (np.pi / 4.)
    leg_angles = np.zeros(num_legs * 2)
    for i in range(num_legs):
        motor1, motor2 = motor_angles[2 * i:2 * i + 2]
        swing = (-1)**(i // 2) * 0.5 * (motor2 - motor1)
        extension = 0.5 * (motor1 + motor2)
        extension = minitaurFKForURDF(motor1, motor2)[2]
        leg_angles[i] = swing
        leg_angles[i + num_legs] = extension

    return leg_angles
