

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
    #print r
    if r < 0:
        r = -r
    # r tested - looks right
    # stupid law of cosines
    phi = np.arccos((l2 * l2 + l1 * l1 - r * r)/ (2 * l1 * l2))
    return np.pi - phi, np.pi + phi, r
