# Fly ArduPlane in SITL
from __future__ import print_function
import math
import os
import shutil

#import util, pexpect, sys, time, math, shutil, os
from timeit import default_timer as timer
from common import *
from pymavlink import mavutil

from common import *
from pysim import util

class GeoLocation:
    '''
    Class representing a coordinate on a sphere, most likely Earth.
    
    This class is based from the code smaple in this paper:
        http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
        
    The owner of that website, Jan Philip Matuschek, is the full owner of 
    his intellectual property. This class is simply a Python port of his very
    useful Java code. All code written by Jan Philip Matuschek is owned by
    Jan Philip Matuschek. Ported from site: https://github.com/jfein/PyGeoTools
    '''
 
 
    MIN_LAT = math.radians(-90)
    MAX_LAT = math.radians(90)
    MIN_LON = math.radians(-180)
    MAX_LON = math.radians(180)
    
    EARTH_RADIUS = 6378.1  # kilometers
    
    
    @classmethod
    def from_degrees(cls, deg_lat, deg_lon):
        rad_lat = math.radians(deg_lat)
        rad_lon = math.radians(deg_lon)
        return GeoLocation(rad_lat, rad_lon, deg_lat, deg_lon)
        
    @classmethod
    def from_radians(cls, rad_lat, rad_lon):
        deg_lat = math.degrees(rad_lat)
        deg_lon = math.degrees(rad_lon)
        return GeoLocation(rad_lat, rad_lon, deg_lat, deg_lon)
    
    
    def __init__(
            self,
            rad_lat,
            rad_lon,
            deg_lat,
            deg_lon
    ):
        self.rad_lat = float(rad_lat)
        self.rad_lon = float(rad_lon)
        self.deg_lat = float(deg_lat)
        self.deg_lon = float(deg_lon)
        self._check_bounds()
        
    def __str__(self):
        degree_sign= u'\N{DEGREE SIGN}'
        return ("({0:.4f}deg, {1:.4f}deg) = ({2:.6f}rad, {3:.6f}rad)").format(
            self.deg_lat, self.deg_lon, self.rad_lat, self.rad_lon)
        
    def _check_bounds(self):
        if (self.rad_lat < GeoLocation.MIN_LAT 
                or self.rad_lat > GeoLocation.MAX_LAT 
                or self.rad_lon < GeoLocation.MIN_LON 
                or self.rad_lon > GeoLocation.MAX_LON):
            raise Exception("Illegal arguments")
            
    def distance_to(self, other, radius=EARTH_RADIUS):
        '''
        Computes the great circle distance between this GeoLocation instance
        and the other.
        '''
        return radius * math.acos(
                math.sin(self.rad_lat) * math.sin(other.rad_lat) +
                math.cos(self.rad_lat) * 
                math.cos(other.rad_lat) * 
                math.cos(self.rad_lon - other.rad_lon)
            )
            
    def bounding_locations(self, distance, radius=EARTH_RADIUS):
        '''
        Computes the bounding coordinates of all points on the surface
        of a sphere that has a great circle distance to the point represented
        by this GeoLocation instance that is less or equal to the distance argument.
        
        Param:
            distance - the distance from the point represented by this GeoLocation
                       instance. Must be measured in the same unit as the radius
                       argument (which is kilometers by default)
            
            radius   - the radius of the sphere. defaults to Earth's radius.
            
        Returns a list of two GeoLoations - the SW corner and the NE corner - that
        represents the bounding box.
        '''
        
        if radius < 0 or distance < 0:
            raise Exception("Illegal arguments")
            
        # angular distance in radians on a great circle
        rad_dist = distance / radius
        
        min_lat = self.rad_lat - rad_dist
        max_lat = self.rad_lat + rad_dist
        
        if min_lat > GeoLocation.MIN_LAT and max_lat < GeoLocation.MAX_LAT:
            delta_lon = math.asin(math.sin(rad_dist) / math.cos(self.rad_lat))
            
            min_lon = self.rad_lon - delta_lon
            if min_lon < GeoLocation.MIN_LON:
                min_lon += 2 * math.pi
                
            max_lon = self.rad_lon + delta_lon
            if max_lon > GeoLocation.MAX_LON:
                max_lon -= 2 * math.pi
        # a pole is within the distance
        else:
            min_lat = max(min_lat, GeoLocation.MIN_LAT)
            max_lat = min(max_lat, GeoLocation.MAX_LAT)
            min_lon = GeoLocation.MIN_LON
            max_lon = GeoLocation.MAX_LON
        
        return [ GeoLocation.from_radians(min_lat, min_lon) , 
            GeoLocation.from_radians(max_lat, max_lon) ]

# get location of scripts
testdir = os.path.dirname(os.path.realpath(__file__))


# HOME_LOCATION='-35.362938,149.165085,585,354' Original location
WIND="0,180,0.2" # speed,direction,variance
WP_MISSION_FILENAME = "auto_mission.txt"

homeloc = None

def wait_ready_to_arm(mavproxy):
    # wait for EKF and GPS checks to pass
    mavproxy.expect('IMU0 is using GPS')

def takeoff(mavproxy, mav):
    """Takeoff get to 30m altitude."""

    wait_ready_to_arm(mavproxy)

    mavproxy.send('arm throttle\n')
    mavproxy.expect('ARMED')

    mavproxy.send('switch 4\n')
    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')

    # some rudder to counteract the prop torque
    mavproxy.send('rc 4 1700\n')

    # some up elevator to keep the tail down
    mavproxy.send('rc 2 1200\n')

    # get it moving a bit first
    mavproxy.send('rc 3 1500\n')
    mav.recv_match(condition='VFR_HUD.groundspeed>6', blocking=True)

    # a bit faster again, straighten rudder
    mavproxy.send('rc 3 1700\n')
    mavproxy.send('rc 4 1500\n')
    mav.recv_match(condition='VFR_HUD.groundspeed>12', blocking=True)

    # hit the gas harder now, and give it some more elevator
    mavproxy.send('rc 2 1100\n') 
    mavproxy.send('rc 3 2000\n')

    # gain a bit of altitude
    if not wait_altitude(mav, homeloc.alt+150, homeloc.alt+200, timeout=60):
        return False

    # level off
    mavproxy.send('rc 2 1500\n')

    print("TAKEOFF COMPLETE")
    return True


def fly_left_circuit(mavproxy, mav):
    """Fly a left circuit, 200m on a side."""
    mavproxy.send('switch 4\n')
    wait_mode(mav, 'FBWA')
    mavproxy.send('rc 3 2000\n')
    if not wait_level_flight(mavproxy, mav):
        return False

    print("Flying left circuit")
    # do 4 turns
    for i in range(0, 4):
        # hard left
        print("Starting turn %u" % i)
        mavproxy.send('rc 1 1000\n')
        if not wait_heading(mav, 270 - (90*i), accuracy=10):
            return False
        mavproxy.send('rc 1 1500\n')
        print("Starting leg %u" % i)
        if not wait_distance(mav, 100, accuracy=20):
            return False
    print("Circuit complete")
    return True


def fly_RTL(mavproxy, mav):
    """Fly to home."""
    print("Flying home in RTL")
    mavproxy.send('switch 2\n')
    wait_mode(mav, 'RTL')
    if not wait_location(mav, homeloc, accuracy=20,
                         target_altitude=homeloc.alt, height_accuracy=20,
                         timeout=180):
        return False
    print("RTL Complete")
    return True


def fly_LOITER(mavproxy, mav, num_circles=4):
    """Loiter where we are."""
    print("Testing LOITER for %u turns" % num_circles)
    mavproxy.send('loiter\n')
    wait_mode(mav, 'LOITER')

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    initial_alt = m.alt
    print("Initial altitude %u\n" % initial_alt)

    while num_circles > 0:
        if not wait_heading(mav, 0, accuracy=10, timeout=60):
            return False
        if not wait_heading(mav, 180, accuracy=10, timeout=60):
            return False
        num_circles -= 1
        print("Loiter %u circles left" % num_circles)

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    final_alt = m.alt
    print("Final altitude %u initial %u\n" % (final_alt, initial_alt))

    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')

    if abs(final_alt - initial_alt) > 20:
        print("Failed to maintain altitude")
        return False

    print("Completed Loiter OK")
    return True


def fly_CIRCLE(mavproxy, mav, num_circles=1):
    """Circle where we are."""
    print("Testing CIRCLE for %u turns" % num_circles)
    mavproxy.send('mode CIRCLE\n')
    wait_mode(mav, 'CIRCLE')

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    initial_alt = m.alt
    print("Initial altitude %u\n" % initial_alt)

    while num_circles > 0:
        if not wait_heading(mav, 0, accuracy=10, timeout=60):
            return False
        if not wait_heading(mav, 180, accuracy=10, timeout=60):
            return False
        num_circles -= 1
        print("CIRCLE %u circles left" % num_circles)

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    final_alt = m.alt
    print("Final altitude %u initial %u\n" % (final_alt, initial_alt))

    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')

    if abs(final_alt - initial_alt) > 20:
        print("Failed to maintain altitude")
        return False

    print("Completed CIRCLE OK")
    return True


def wait_level_flight(mavproxy, mav, accuracy=5, timeout=30):
    """Wait for level flight."""
    tstart = get_sim_time(mav)
    print("Waiting for level flight")
    mavproxy.send('rc 1 1500\n')
    mavproxy.send('rc 2 1500\n')
    mavproxy.send('rc 4 1500\n')
    while get_sim_time(mav) < tstart + timeout:
        m = mav.recv_match(type='ATTITUDE', blocking=True)
        roll = math.degrees(m.roll)
        pitch = math.degrees(m.pitch)
        print("Roll=%.1f Pitch=%.1f" % (roll, pitch))
        if math.fabs(roll) <= accuracy and math.fabs(pitch) <= accuracy:
            print("Attained level flight")
            return True
    print("Failed to attain level flight")
    return False


def change_altitude(mavproxy, mav, altitude, accuracy=30):
    """Get to a given altitude."""
    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')
    alt_error = mav.messages['VFR_HUD'].alt - altitude
    if alt_error > 0:
        mavproxy.send('rc 2 2000\n')
    else:
        mavproxy.send('rc 2 1000\n')
    if not wait_altitude(mav, altitude-accuracy/2, altitude+accuracy/2):
        return False
    mavproxy.send('rc 2 1500\n')
    print("Reached target altitude at %u" % mav.messages['VFR_HUD'].alt)
    return wait_level_flight(mavproxy, mav)


def axial_left_roll(mavproxy, mav, count=1):
    """Fly a left axial roll."""
    # full throttle!
    mavproxy.send('rc 3 2000\n')
    if not change_altitude(mavproxy, mav, homeloc.alt+300):
        return False

    # fly the roll in manual
    mavproxy.send('switch 6\n')
    wait_mode(mav, 'MANUAL')

    while count > 0:
        print("Starting roll")
        mavproxy.send('rc 1 1000\n')
        if not wait_roll(mav, -150, accuracy=90):
            mavproxy.send('rc 1 1500\n')
            return False
        if not wait_roll(mav, 150, accuracy=90):
            mavproxy.send('rc 1 1500\n')
            return False
        if not wait_roll(mav, 0, accuracy=90):
            mavproxy.send('rc 1 1500\n')
            return False
        count -= 1

    # back to FBWA
    mavproxy.send('rc 1 1500\n')
    mavproxy.send('switch 4\n')
    wait_mode(mav, 'FBWA')
    mavproxy.send('rc 3 1700\n')
    return wait_level_flight(mavproxy, mav)


def inside_loop(mavproxy, mav, count=1):
    """Fly a inside loop."""
    # full throttle!
    mavproxy.send('rc 3 2000\n')
    if not change_altitude(mavproxy, mav, homeloc.alt+300):
        return False

    # fly the loop in manual
    mavproxy.send('switch 6\n')
    wait_mode(mav, 'MANUAL')

    while count > 0:
        print("Starting loop")
        mavproxy.send('rc 2 1000\n')
        if not wait_pitch(mav, -60, accuracy=20):
            return False
        if not wait_pitch(mav, 0, accuracy=20):
            return False
        count -= 1

    # back to FBWA
    mavproxy.send('rc 2 1500\n')
    mavproxy.send('switch 4\n')
    wait_mode(mav, 'FBWA')
    mavproxy.send('rc 3 1700\n')
    return wait_level_flight(mavproxy, mav)


def test_stabilize(mavproxy, mav, count=1):
    """Fly stabilize mode."""
    # full throttle!
    mavproxy.send('rc 3 2000\n')
    mavproxy.send('rc 2 1300\n')
    if not change_altitude(mavproxy, mav, homeloc.alt+300):
        return False
    mavproxy.send('rc 2 1500\n')

    mavproxy.send("mode STABILIZE\n")
    wait_mode(mav, 'STABILIZE')

    count = 1
    while count > 0:
        print("Starting roll")
        mavproxy.send('rc 1 2000\n')
        if not wait_roll(mav, -150, accuracy=90):
            return False
        if not wait_roll(mav, 150, accuracy=90):
            return False
        if not wait_roll(mav, 0, accuracy=90):
            return False
        count -= 1

    mavproxy.send('rc 1 1500\n')
    if not wait_roll(mav, 0, accuracy=5):
        return False

    # back to FBWA
    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')
    mavproxy.send('rc 3 1700\n')
    return wait_level_flight(mavproxy, mav)


def test_acro(mavproxy, mav, count=1):
    """Fly ACRO mode."""
    # full throttle!
    mavproxy.send('rc 3 2000\n')
    mavproxy.send('rc 2 1300\n')
    if not change_altitude(mavproxy, mav, homeloc.alt+300):
        return False
    mavproxy.send('rc 2 1500\n')

    mavproxy.send("mode ACRO\n")
    wait_mode(mav, 'ACRO')

    count = 1
    while count > 0:
        print("Starting roll")
        mavproxy.send('rc 1 1000\n')
        if not wait_roll(mav, -150, accuracy=90):
            return False
        if not wait_roll(mav, 150, accuracy=90):
            return False
        if not wait_roll(mav, 0, accuracy=90):
            return False
        count -= 1
    mavproxy.send('rc 1 1500\n')

    # back to FBWA
    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')

    wait_level_flight(mavproxy, mav)

    mavproxy.send("mode ACRO\n")
    wait_mode(mav, 'ACRO')

    count = 2
    while count > 0:
        print("Starting loop")
        mavproxy.send('rc 2 1000\n')
        if not wait_pitch(mav, -60, accuracy=20):
            return False
        if not wait_pitch(mav, 0, accuracy=20):
            return False
        count -= 1

    mavproxy.send('rc 2 1500\n')

    # back to FBWA
    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')
    mavproxy.send('rc 3 1700\n')
    return wait_level_flight(mavproxy, mav)

def test_CRUISE(mavproxy, mav, count=1, mode='CRUISE'):
    """Fly CRUISE mode."""
    mavproxy.send("mode %s\n" % mode)
    wait_mode(mav, mode)
    mavproxy.send('rc 3 1700\n')
    mavproxy.send('rc 2 1500\n')

    # lock in the altitude by asking for an altitude change then releasing
    mavproxy.send('rc 2 1000\n')
    wait_distance(mav, 50, accuracy=20)
    mavproxy.send('rc 2 1500\n')
    wait_distance(mav, 50, accuracy=20)

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    initial_alt = m.alt
    print("Initial altitude %u\n" % initial_alt)

    if not wait_distance(mav, 8000, accuracy=20, timeout=500):
        return False

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    final_alt = m.alt
    print("Final altitude %u initial %u\n" % (final_alt, initial_alt))

    # back to FBWA
    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')

    if abs(final_alt - initial_alt) > 20:
        print("Failed to maintain altitude")
        return False

    return wait_level_flight(mavproxy, mav)


def test_FBWB(mavproxy, mav, count=1, mode='FBWB'):
    """Fly FBWB or CRUISE mode."""
    mavproxy.send("mode %s\n" % mode)
    wait_mode(mav, mode)
    mavproxy.send('rc 3 1700\n')
    mavproxy.send('rc 2 1500\n')

    # lock in the altitude by asking for an altitude change then releasing
    mavproxy.send('rc 2 1000\n')
    wait_distance(mav, 50, accuracy=20)
    mavproxy.send('rc 2 1500\n')
    wait_distance(mav, 50, accuracy=20)

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    initial_alt = m.alt
    print("Initial altitude %u\n" % initial_alt)

    print("Flying right circuit")
    # do 4 turns
    for i in range(0, 4):
        # hard left
        print("Starting turn %u" % i)
        mavproxy.send('rc 1 1800\n')
        if not wait_heading(mav, 0 + (90*i), accuracy=20, timeout=60):
            mavproxy.send('rc 1 1500\n')
            return False
        mavproxy.send('rc 1 1500\n')
        print("Starting leg %u" % i)
        if not wait_distance(mav, 100, accuracy=20):
            return False
    print("Circuit complete")

    print("Flying rudder left circuit")
    # do 4 turns
    for i in range(0, 4):
        # hard left
        print("Starting turn %u" % i)
        mavproxy.send('rc 4 1900\n')
        if not wait_heading(mav, 360 - (90*i), accuracy=20, timeout=60):
            mavproxy.send('rc 4 1500\n')
            return False
        mavproxy.send('rc 4 1500\n')
        print("Starting leg %u" % i)
        if not wait_distance(mav, 100, accuracy=20):
            return False
    print("Circuit complete")

    m = mav.recv_match(type='VFR_HUD', blocking=True)
    final_alt = m.alt
    print("Final altitude %u initial %u\n" % (final_alt, initial_alt))

    # back to FBWA
    mavproxy.send('mode FBWA\n')
    wait_mode(mav, 'FBWA')

    if abs(final_alt - initial_alt) > 20:
        print("Failed to maintain altitude")
        return False

    return wait_level_flight(mavproxy, mav)


def setup_rc(mavproxy):
    """Setup RC override control."""
    for chan in [1, 2, 4, 5, 6, 7]:
        mavproxy.send('rc %u 1500\n' % chan)
    mavproxy.send('rc 3 1000\n')
    mavproxy.send('rc 8 1800\n')


def fly_mission(mavproxy, mav, filename, height_accuracy=-1, target_altitude=None):
    """Fly a mission from a file."""
    global homeloc
    print("Flying mission %s" % filename)
    
     # wait for EKF to settle
    wait_seconds(mav, 15)
    
    #mavproxy.send('arm throttle\n')
    #mavproxy.expect('ARMED')    
    
    mavproxy.send('wp load %s\n' % filename)
    mavproxy.expect('Flight plan received')
    mavproxy.send('wp list\n')
    mavproxy.expect('Requesting [0-9]+ waypoints')
    mavproxy.send('switch 1\n')  # auto mode
    wait_mode(mav, 'AUTO')
    
    # max_dist determines when it finishes the way point
    # timeout is the number of seconds that the command should finish entirely
    if not wait_waypoint(mav, 1, 1, max_dist=100):
        return False
    if not wait_groundspeed(mav, 0, 0.5, timeout=360):
        return False
    mavproxy.expect("Auto disarmed")
    print("Mission OK")
    return True

def generate_wpfile():
    ''' Generates the waypoint file
    '''
    LAND_LAT = -35.362881 # Location of landing runway
    LAND_LONG = 149.165222
    START_ALT = 585.40 #Meters relative to sea level, this is global altitude
    FILE_NAME = "auto_mission.txt"
    
    header = "QGC WPL 110\n"
    line0 = "0    0    0    16    0.000000    0.000000    0.000000    0.000000    {0:11.6f}    {1:11.6f}    {2:3.2f}    1\n"
    line1 = "1    1    3    16    0.000000    0.000000    0.000000    0.000000    {0:11.6f}    {1:11.6f}    {2:3.2f}    1\n"
    line2 = "2    0    3    189    0.000000    0.000000    0.000000    0.000000    {0:11.6f}    {1:11.6f}    {2:3.2f}    1\n" #189 - Start landing sequence
    line3 = "3    0    3    16    0.000000    0.000000    0.000000    0.000000    {0:11.6f}    {1:11.6f}    {2:3.2f}    1\n"
    line4 = "4    0    3    16    0.000000    0.000000    0.000000    0.000000    {0:11.6f}    {1:11.6f}    {2:3.2f}    1\n"
    
    #Climb or descend - If you want the plane to continue, put in the exact same altitude as line 4 and 
    # the first parameter should be 0
    # If you want to climb, then put in 1 as first param and put in a large altitude
    line5 = "5    0    3    30    {0:1.6f}    0.000000    0.000000    0.000000    0.000000    0.000000    {1:3.2f}    1\n" 
    line6 = "6    0    3    21    {0:11.6f}   0.000000    0.000000    0.000000    {1:11.6f}    {2:11.6f}    {3:3.2f}    1\n" #21 - Land cmd

    # Choose a random descent angle between 1-5 degrees
#     descentAngle = random.randrange(1,6) # In degrees
    descentAngle = 3 # Choosing 3 degrees for now
    
    # Given a descentAngle,  we choose a horizontal distance in km and height
    # in meters of the start of the descend
    # We are scaling this in comparison to the AIAA paper so that our simulation
    # doesn't take that much time
    horiDist = random.uniform(1.25, 5) # in Km
    
    # In meters
    descend_start_alt = math.tan(descentAngle * (math.pi / 180)) * horiDist * 1000

    # We fix the home location to be the take off point, which is the landing 
    # lat PLUS the horiDst and plus a little extra to allow for the distance
    # traveled during take off    
    land_loc = GeoLocation.from_degrees(LAND_LAT, LAND_LONG)
    takeoff_dist = 1
    SW_loc, NE_loc = land_loc.bounding_locations(horiDist)
    SW_halfway_loc, NE_halfway_loc = land_loc.bounding_locations(horiDist/2.)
    home_loc, notused = land_loc.bounding_locations(horiDist + takeoff_dist)
    
    diceroll = random.random()
    
    with open(WP_MISSION_FILENAME, "w") as f:        
        f.write(header)
        
        # Home location
        f.write(line0.format(home_loc.deg_lat, LAND_LONG, START_ALT))
        
        # The scenario is one where the plane goes up to a target altitude
        # and then starts the descend, the path of descend is a straight line
        
        # 1st waypoint is the one that the plane will catch after it has 
        # been called back from take off, altitude should be the same as the
        # descent alt
        rndlat = random.uniform(-2000, 2000)
        lat = home_loc.deg_lat + rndlat * 10**-6
        
        f.write(line1.format(lat, LAND_LONG, descend_start_alt))
        
        # 2nd waypoint
        # The start of the descend, we take the SW_loc and take only the lat
        # but keep the lon the same        
        f.write(line2.format(0.0, 0.0, 0.0))
        
        # 3rd waypoint
        # Start of landing sequence
        f.write(line3.format(SW_loc.deg_lat, LAND_LONG, descend_start_alt))
        
        # 4th waypoint
        # This is halfway between start of descend and landing
        f.write(line4.format(SW_halfway_loc.deg_lat, LAND_LONG, descend_start_alt/2.))
                
        # 5th waypoint
        # Now we decide whether we have a go around
        if (diceroll < 0.1): # 10% chance of go around
            f.write(line5.format(1.0, descend_start_alt)) # Pull up
            # Landing
            f.write(line6.format(descend_start_alt, LAND_LAT, LAND_LONG, 0.0))
        else:
            f.write(line5.format(0.0, descend_start_alt/2.)) #continue descent
            # We have to push the home location back it since it always land short
            f.write(line6.format(0.0, LAND_LAT + 0.002 , LAND_LONG, 0.0)) 
        
        # 6th waypoint
        # Landing
        f.write("\n")
        f.write("# Descent Angle:{0:1d}\n".format(descentAngle))
        f.write("# Descent Distance:{0:5.2f}\n".format(horiDist * 1000))
        f.write("# Descent Height:{0:4.2f}\n".format(descend_start_alt))
        f.write("# GoAround:{0:1d}\n".format(1 if (diceroll < 0.1) else 0))

    return '{0},{1},585,354'.format(home_loc.deg_lat, LAND_LONG)

def parseConfigFile(filepath):
    try:
        with open(filepath, 'r') as infile:
            config_file = json.load(infile)
            return config_file
    except IOError:
        return None
    
def fly_ArduPlane(binary, viewerip=None, use_map=False, valgrind=False, gdb=False, gdbserver=False, speedup=1,
                  wpfile='auto_mission.txt', elfname='ArduPlane.elf', instance=0, configfile='config.txt'):
    """Fly ArduPlane in SITL.

    you can pass viewerip as an IP address to optionally send fg and
    mavproxy packets too for local viewing of the flight in real time
    """
    global homeloc
    print('Config file: {}'.format(configfile))
    config_settings = parseConfigFile(configfile)
    print(config_settings)
    
#     print("Generating mission file")
#     HOME_LOCATION = generate_wpfile().strip(' ')
    HOME_LOCATION = "-35.362881,149.165222,582,354"
    #HOME_LOCATION = "-35.402830,149.165222,585.00,354"
    
    mav_sitl_port = 5501 + 10*instance
    mav_out_port = 19550 + 10*instance
    options = '--sitl=127.0.0.1:{0} --out=127.0.0.1:{1} --streamrate=10'.format(mav_sitl_port, mav_out_port)
    if viewerip:
        options += " --out=%s:14550" % viewerip
    if use_map:
        options += ' --map'

    sitl = util.start_SITL(binary, model='plane-elevrev', home=HOME_LOCATION, speedup=speedup,
                           valgrind=valgrind, gdb=gdb, gdbserver=gdbserver,
                           defaults_file=os.path.join(testdir, 'default_params/plane-jsbsim.parm'),
                           elfname=elfname, instance=instance)
    mavproxy = util.start_MAVProxy_SITL('ArduPlane', options=options, instance=instance)
    mavproxy.expect('Telemetry log: (\S+)')
    logfile = mavproxy.match.group(1)
    print("LOGFILE %s" % logfile)

    # buildlog = util.reltopdir("../buildlogs/ArduPlane-test.tlog")
    # print("buildlog=%s" % buildlog)
    # if os.path.exists(buildlog):
    #     os.unlink(buildlog)
    # try:
    #     os.link(logfile, buildlog)
    # except Exception:
    #     pass

    util.expect_setup_callback(mavproxy, expect_callback)

    mavproxy.expect('Received [0-9]+ parameters')

    expect_list_clear()
    expect_list_extend([sitl, mavproxy])

    print("Started simulator")

    # get a mavlink connection going
    try:
        mav = mavutil.mavlink_connection('127.0.0.1:{0}'.format(mav_out_port), robust_parsing=True)
    except Exception as msg:
        print("Failed to start mavlink connection on 127.0.0.1:{0}".format(mav_out_port) % msg)
        raise
    mav.message_hooks.append(message_hook)
    mav.idle_hooks.append(idle_hook)

    failed = False
    fail_list = []
    e = 'None'
    try:
        print("Waiting for a heartbeat with mavlink protocol %s" % mav.WIRE_PROTOCOL_VERSION)
        mav.wait_heartbeat()
        print("Setting up RC parameters")
        setup_rc(mavproxy)
        print("Waiting for GPS fix")
        mav.recv_match(condition='VFR_HUD.alt>10', blocking=True)
        mav.wait_gps_fix()
        while mav.location().alt < 10:
            mav.wait_gps_fix()
        homeloc = mav.location()
        print("Home location: %s" % homeloc)
        start = timer()
        if not takeoff(mavproxy, mav):
            print("Failed takeoff")
            failed = True
#         if not fly_left_circuit(mavproxy, mav):
#             print("Failed left circuit")
#             failed = True
#         if not axial_left_roll(mavproxy, mav, 1):
#             print("Failed left roll")
#             failed = True
#         if not inside_loop(mavproxy, mav):
#             print("Failed inside loop")
#             failed = True
#         if not test_stabilize(mavproxy, mav):
#             print("Failed stabilize test")
#             failed = True
#         if not test_acro(mavproxy, mav):
#             print("Failed ACRO test")
#             failed = True
#         if not test_FBWB(mavproxy, mav):
#             print("Failed FBWB test")
#             failed = True
#        if not test_FBWB(mavproxy, mav, mode='CRUISE'):
#            print("Failed CRUISE test")
#            failed = True
#         if not fly_RTL(mavproxy, mav):
#             print("Failed RTL")
#             failed = True
#         if not fly_LOITER(mavproxy, mav):
#             print("Failed LOITER")
#             failed = True
#         if not fly_CIRCLE(mavproxy, mav):
#             print("Failed CIRCLE")
#             failed = True
        if not test_CRUISE(mavproxy, mav):
            print("Failed CRUISE test")
            failed = True        
        # if not fly_mission(mavproxy, mav, os.path.join(testdir, wpfile), height_accuracy = 10,
        #                    target_altitude=homeloc.alt):
        #     print("Failed mission")
        #     failed = True
#         if not log_download(mavproxy, mav, util.reltopdir("../buildlogs/ArduPlane-log.bin")):
#             print("Failed log download")
#             failed = True
    except pexpect.TIMEOUT, e:
        print("Failed with timeout")
        failed = True
        fail_list.append("timeout")

    end = timer()
    print('========== TOTAL TIME : {} ============'.format(end - start))
    mav.close()
    util.pexpect_close(mavproxy)
    util.pexpect_close(sitl)

    valgrind_log = util.valgrind_log_filepath(binary=binary, model='plane-elevrev')
    if os.path.exists(valgrind_log):
        os.chmod(valgrind_log, 0o644)
        shutil.copy(valgrind_log, util.reltopdir("../buildlogs/ArduPlane-valgrind.log"))

    if failed:
        print("FAILED: %s" % e, fail_list)
        return False
    return True
