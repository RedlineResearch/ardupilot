#!/usr/bin/env python

import random
import math
 
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


# Author: Moses Huang
# Purpose: Auto-generates a mission file saved to local folder 
# to generate random route to fly

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
    
def main(descentAngle):
    
    # Given a descentAngle,  we choose a horizontal distance in km and height
    # in meters of the start of the descend
    horiDist = random.uniform(5, 7) # in Km
    
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
    
    with open(FILE_NAME, "w") as f:        
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
        
if __name__ == '__main__':
    main(3)
