import math
import random
from scipy.spatial import distance
import numpy                                             
from numpy import sqrt, dot, cross                       
from numpy.linalg import norm 

random.seed(1234)

error_amount = 0.01

beacon_dist = 0.6096

beacon_1 = numpy.array([(math.sqrt(3.0) / 3.0) * beacon_dist, 0.0, 0.0])
beacon_2 = numpy.array([(math.sqrt(3.0) / -6.0) * beacon_dist, beacon_dist / 2.0, 0.0])
beacon_3 = numpy.array([(math.sqrt(3.0) / -6.0) * beacon_dist, beacon_dist / -2.0, 0.0])
beacon_4 = numpy.array([0.0, 0.0, (math.sqrt(6.0) / 3.0) * beacon_dist])


def trilaterate(p1, p2, p3, r1, r2, r3):
    temp1 = p2 - p1
    e_x = temp1/norm(temp1)
    temp2 = p3-p1
    i = dot(e_x, temp2)
    temp3 = temp2 - i*e_x
    e_y = temp3/norm(temp3)
    e_z = cross(e_x, e_y)
    d = norm(p2-p1)
    j = dot(e_y, temp2)
    x = (r1*r1 - r2*r2 + d*d) / (2*d)
    y = (r1*r1 - r3*r3 - 2*i*x + i*i + j*j) / (2*j)
    temp4 = r1*r1 - x*x - y*y                            
    if temp4 < 0:
        return numpy.array([numpy.nan, numpy.nan, numpy.nan]), numpy.array([numpy.nan, numpy.nan, numpy.nan])
    z = sqrt(temp4)
    p_12_a = p1 + x*e_x + y*e_y + z*e_z
    p_12_b = p1 + x*e_x + y*e_y - z*e_z
    return p_12_a, p_12_b


def avg_set(t1, t2, t3, t4):
    paverage = numpy.array([0.0, 0.0, 0.0])
    paverage_count = 0.0
    for p in [t1, t2, t3, t4]:
        if not math.isnan(p[0]):
            paverage += p
            paverage_count += 1.0

    if paverage_count != 0.0:
        paverage /= paverage_count
        return paverage
    else:
        return numpy.array([numpy.nan, numpy.nan, numpy.nan])


def trilaterate_j(p1, p2, p3, p4, r1, r2, r3, r4):
    bump = 0.0
    r1 += bump
    r2 += bump
    r3 += bump
    r4 += bump

    pa, pb = trilaterate(p1, p2, p3, r1, r2, r3)
    pc, pd = trilaterate(p2, p3, p4, r2, r3, r4)
    pe, pf = trilaterate(p3, p4, p1, r3, r4, r1)
    pg, ph = trilaterate(p4, p1, p2, r4, r1, r2)

    set_avg = []

    for t1 in [pa, pb]:
        for t2 in [pc, pd]:
            for t3 in [pe, pf]:
                for t4 in [pg, ph]:
                    set_avg += [avg_set(t1, t2, t3, t4)]

    paverage = numpy.array([0.0, 0.0, 0.0])
    lowest = 1.0
    for avg in set_avg:
        if not math.isnan(avg[0]):
            err_p1 = math.fabs((distance.euclidean(avg, p1) - r1) / r1)
            err_p2 = math.fabs((distance.euclidean(avg, p2) - r2) / r2)
            err_p3 = math.fabs((distance.euclidean(avg, p3) - r3) / r3)
            err_p4 = math.fabs((distance.euclidean(avg, p4) - r4) / r4)

            err = (err_p1 + err_p2 + err_p3 + err_p4) / 4.0

            if err < lowest:
                lowest = err
                paverage = avg

    return paverage, lowest


def get_error(measured, actual):
    perror_x = math.fabs(measured[0] - actual[0]) / math.fabs(actual[0]) if actual[0] != 0.0 else 0.0
    perror_y = math.fabs(measured[1] - actual[1]) / math.fabs(actual[1]) if actual[1] != 0.0 else 0.0
    perror_z = math.fabs(measured[2] - actual[2]) / math.fabs(actual[2]) if actual[2] != 0.0 else 0.0
    return (perror_x + perror_y + perror_z) / 3.0


def test_trilaterate(rx_point, num_tests, verbose=False):
    rx_beacon_1_dist = distance.euclidean(rx_point, beacon_1)
    rx_beacon_2_dist = distance.euclidean(rx_point, beacon_2)
    rx_beacon_3_dist = distance.euclidean(rx_point, beacon_3)
    rx_beacon_4_dist = distance.euclidean(rx_point, beacon_4)

    paverage = numpy.array([0.0, 0.0, 0.0])
    valid = 0

    for i in range(num_tests):
        # add errors
        rx_beacon_1_dist_error = rx_beacon_1_dist + random.uniform(-error_amount, error_amount)
        rx_beacon_2_dist_error = rx_beacon_2_dist + random.uniform(-error_amount, error_amount)
        rx_beacon_3_dist_error = rx_beacon_3_dist + random.uniform(-error_amount, error_amount)
        rx_beacon_4_dist_error = rx_beacon_4_dist + random.uniform(-error_amount, error_amount)

        ptemp, err = trilaterate_j(beacon_1, beacon_2, beacon_3, beacon_4,
                                   rx_beacon_1_dist_error, rx_beacon_2_dist_error,
                                   rx_beacon_3_dist_error, rx_beacon_4_dist_error)

        valid += 1 if err < 1.0 else 0
        paverage += ptemp

    paverage /= float(num_tests)

    deviate_x = math.fabs(paverage[0] - rx_point[0])
    deviate_y = math.fabs(paverage[1] - rx_point[1])
    deviate_z = math.fabs(paverage[2] - rx_point[2])
    deviate = distance.euclidean(rx_point, paverage)

    if verbose:
        print "ACT: X: %0.2f Y: %0.2f Z: %0.2f" % (rx_point[0], rx_point[1], rx_point[2])
        print "AVG: X: %0.2f Y: %0.2f Z: %0.2f" % (paverage[0], paverage[1], paverage[2])
        print "DEV: X: %0.2f Y: %0.2f Z: %0.2f" % (deviate_x, deviate_y, deviate_z)
        print ""
        print "DEVIATE: %0.2f" % deviate

    return deviate, (valid / float(num_tests))


def create_errormap():
    ply_points = ""

    num_points = 0

    ax_res = 20
    ax_dist = 100
    ax_step = float(ax_dist / ax_res)

    ay_res = 20
    ay_dist = 100
    ay_step = float(ay_dist / ay_res)

    az_res = 2
    az_dist = 3
    az_step = float(az_dist / az_res)

    best = 100.0
    worst = 0.0
    avg = 0.0

    valid = 0.0

    probes = []

    for x in range(-(ax_res/2), (ax_res/2)):
        for y in range(-(ay_res/2), (ay_res/2)):
            for z in range(-(az_res/2), (az_res/2)):
                dev, val = test_trilaterate(numpy.array([x*ax_step, y*ay_step, z*az_step]), 20)
                probes += [((x*ax_step, y*ay_step, z*az_step), dev)]
                num_points += 1
                valid += val
                worst = dev if dev > worst else worst
                best = dev if dev < best else best
                avg += dev

            print "%0.1f%%" % ((num_points / float(ax_res*ay_res*az_res))*100.0)

    for p in probes:
        ply_points += "%0.3f %0.3f %0.3f %d %d %d\n" % (p[0][0], p[0][1], p[0][2], int((p[1]/worst)*255.0), 0.0, 0.0)

    print "HI DEV: %0.5f" % worst
    print "LO DEV: %0.5f" % best
    print "AVG DEVIATE: %0.5f" % (avg / float(len(probes)))
    print "VALID: %0.5f%%" % ((valid / float(len(probes))) * 100.0)
    # ply_points += "%0.3f %0.3f %0.3f %d %d %d\n" % ((ax_res/2.0)*ax_step, 0, 0, 255, 0, 0)
    # ply_points += "%0.3f %0.3f %0.3f %d %d %d\n" % (0, (ax_res/2.0)*ax_step, 0, 0, 255, 0)
    # ply_points += "%0.3f %0.3f %0.3f %d %d %d\n" % (0, 0, (ax_res/2.0)*ax_step, 0, 0, 255)

    ply_file = "ply\n"
    ply_file += "format ascii 1.0\n"
    ply_file += "element vertex %d\n" % num_points
    ply_file += "property float x\n"
    ply_file += "property float y\n"
    ply_file += "property float z\n"
    ply_file += "property uchar red\n"
    ply_file += "property uchar green\n"
    ply_file += "property uchar blue\n"
    ply_file += "end_header\n"

    ply_file += ply_points

    f = open("errormap.ply", "w")
    f.write(ply_file)
    f.close()

# test_point = numpy.array([-20.0, -10.0, -20.0])
# test_trilaterate(test_point, 1000, True)

create_errormap()
