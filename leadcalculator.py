from __future__ import division
import math

class UnitConversionsMixin(object):
    '''
    Unit conversion calculations
    5280 feet = 1 mile
    '''
    
    @classmethod
    def fps_to_mph(cls, fps):
        '''
        converts fps to mph
        '''
        return (fps / 5280) * 3600

    @classmethod
    def mph_to_fps(cls, mph):
        '''
        converts mph to fps
        '''
        return (mph * 5280) / 3600

    @classmethod
    def angle_to_thumbs(cls, angle):
        '''
        converts degree angle to thumbs.  
        this method assumes the average human thumb width is approximately 2 degrees
        '''
        return angle / 2


class TrigonometryMixin(object):
    '''
    Trigonometric calculations
    '''

    @classmethod
    def angle_by_sides(cls, a, b, c):
        # applies law of cosines where we are trying to return the angle C (opposite corner of c)
        cos_C = (c**2 - b**2 - a**2) / (-2 * a * b)
        C = math.acos(cos_C)
        return math.degrees(C)

    @classmethod
    def side_by_angles_and_side(cls, a, angle_a, angle_b):
        # applies law of sines where we are trying to return the side b (opposit corner of angle B)
        b = (math.sin(math.radians(angle_b)) * a) / math.sin(math.radians(angle_a))
        return b


class Shooter(object):
    '''
    Represents a shooter
    '''
    velocity = 1200  # velocity of shotshell in feet per second
    position = (0,0)  # position of shooter in cartesian coordinates (x,y).  This should always be (0,0)
    direction = 0  # direction in which the station is pointing in degree angle 0 = 360 = 12 o'clock. 90 = 3 o'clock. 180 = 6 o'clock. 270 = 9 o'clock.

    def __init__(self, velocity=1200, direction=0):
        self.velocity = velocity



class Thrower(object):
    '''
    Represents a thrower
    '''
    position = (0,0)  # position of thrower in cartesian coordinates (x,y) where each unit of measurement is in feet
    velocity = 41  # velocity of clay targets in miles per hour
    direction = 0  # direction of clay target trajectory in degree angle 0 = 360 = 12 o'clock. 90 = 3 o'clock. 180 = 6 o'clock. 270 = 9 o'clock. 
    destination = (40,40) # position of destination of target in cartesian coordinates (x,y) where each unit of measuremnt is in feet

    def __init__(self, position, direction=None, destination=None, velocity=41):
        self.position = position
        self.direction = direction
        self.velocity = velocity
        self.destination = destination
        if not self.velocity and not self.destination:
            raise Exception('You must specify either a direction (angle) or destination (end position)')
        if direction is None:
            self.direction = self.destination_to_direction(destination)

    def direction_to_destination(self, direction, distance=100, offset=None):
        #import ipdb; ipdb.set_trace()
        hypotenuse = distance
        if offset is None:
            offset = self.position
        if direction > 270:
            # quadrant IV
            angle = 360 - direction
            rads = math.radians(angle)
            y_diff = math.cos(rads) * hypotenuse
            x_diff = math.sin(rads) * hypotenuse * -1
        elif direction > 180:
            # quadrant III
            angle = direction - 180
            rads = math.radians(angle)
            y_diff = math.cos(rads) * hypotenuse * -1
            x_diff = math.sin(rads) * hypotenuse * -1
        elif direction > 90:
            # quadrant II
            angle = 180 - direction
            rads = math.radians(angle)
            y_diff = math.cos(rads) * hypotenuse * -1
            x_diff = math.sin(rads) * hypotenuse
        else:
            # quadrant I
            angle = direction
            rads = math.radians(angle)
            y_diff = math.cos(rads) * hypotenuse
            x_diff = math.sin(rads) * hypotenuse
        return (round(x_diff + offset[0], 2), round(y_diff + offset[1], 2))

    def destination_to_direction(self, destination):
        x_diff = destination[0] - self.position[0]
        y_diff = destination[1] - self.position[1]
        hypotenuse = math.sqrt(x_diff**2 + y_diff**2)
        cos_angle = abs(y_diff) / hypotenuse
        angle = math.degrees(math.acos(cos_angle))
        if x_diff >= 0:
            if y_diff >= 0:
                # quadrant I
                direction = angle
            else:
                # quadrant II
                direction = 180 - angle
        else:
            if y_diff >= 0:
                # quadrant IV
                direction = 360 - angle
            else:
                # quadrant III
                direction = 180 + angle
        return direction


class LeadCalculator(UnitConversionsMixin, TrigonometryMixin):
    '''
    Lead Calculator class
    '''

    @classmethod
    def _get_angle_by_sides(cls, a, b, c):
        # applies law of cosines where e are trying to return the angle C (opposite of side c
        cos_C = (c**2 - b**2 - a**2) / (-2 * a * b)
        C = math.acos(cos_C)
        return math.degrees(C)

    @classmethod
    def lead_by_breakpoint_location(cls, shooter, thrower, breakpoint):
        # breakpoint location in cartesian coordinates tuple(x,y)

        # find breakpoint distance from shooter
        shot_x_diff = breakpoint[0] - shooter.position[0]
        shot_y_diff = breakpoint[1] - shooter.position[1]
        shot_distance = math.sqrt(shot_x_diff**2 + shot_y_diff**2)
        shot_time = shot_distance / shooter.velocity
        target_diff = cls.mph_to_fps(thrower.velocity) * shot_time

        # reverse direction
        reverse_direction = (thrower.direction + 180) % 360
        target_location = thrower.direction_to_destination(reverse_direction, target_diff, breakpoint)
        
        # find target distance from shooter at moment of trigger pull
        pull_x_diff = target_location[0] - shooter.position[0]
        pull_y_diff = target_location[1] - shooter.position[1]
        target_distance = math.sqrt(pull_x_diff**2 + pull_y_diff**2)

        # find lead in angle
        lead_angle = cls._get_angle_by_sides(shot_distance, target_distance, target_diff)

        # find lead in thumb widths
        lead_thumbs = cls.angle_to_thumbs(lead_angle)

        # find visual lead in ft
        visual_lead_ft = target_distance * math.sin(math.radians(lead_angle))

        return {
            'lead_ft': round(target_diff, 2),
            'lead_angle': round(lead_angle, 2),
            'lead_thumbs': round(lead_thumbs, 2),
            'visual_lead_ft': round(visual_lead_ft, 2),
            'breakpoint': breakpoint,
            'pullpoint': target_location,
            'shot_distance': round(shot_distance, 2),
            'target_distance': round(target_distance, 2),
            'trajectory': round(thrower.direction, 2)
        }

    @classmethod
    def lead_by_shooter_angle(cls, shooter, thrower, shot_angle):
        # shooter angle in degrees 0 = 360 = 12 o'clock. 90 = 3 o'clock. 180 = 6 o'clock. 270 = 9 o'clock

        # find distance from shooter to thrower
        delta_x = thrower.position[0] - shooter.position[0]
        delta_y = thrower.position[1] - shooter.position[1]
        thrower_shooter_distance = math.sqrt(delta_x**2 + delta_y**2)

        # find angle to thrower
        cos_angle = abs(delta_y) / thrower_shooter_distance
        angle_to_thrower = math.degrees(math.acos(cos_angle))
        if delta_x >= 0:
            if delta_y >= 0:
                #quadrant I
                pass
            else:
                #quadrant II
                angle_to_thrower = 180 - angle_to_thrower
        else:
            if delta_y >= 0:
                #quadrant IV
                angle_to_thrower = 360 - angle_to_thrower
            else:
                #quadrant III
                angle_to_thrower = 180 + angle_to_thrower

        # find broad shooter angle
        broad_shooter_angle = abs(angle_to_thrower - shot_angle)

        # find broad thrower angle
        thrower_to_shooter_angle = (angle_to_thrower + 180) % 360
        broad_thrower_angle = abs(thrower.direction - thrower_to_shooter_angle)

        # find broad breakpoint angle
        broad_breakpoint_angle = 180 - (broad_thrower_angle + broad_shooter_angle)

        # get breakpoint distance from shooter
        shot_distance = cls.side_by_angles_and_side(thrower_shooter_distance, broad_breakpoint_angle, broad_thrower_angle)

        # get breakpoint distance from thrower
        breakpoint_distance_from_thrower = cls.side_by_angles_and_side(thrower_shooter_distance, broad_breakpoint_angle, broad_shooter_angle)

        # get breakpoint location
        breakpoint = thrower.direction_to_destination(thrower.direction, breakpoint_distance_from_thrower)
        
        # get shot time
        shot_time = shot_distance / shooter.velocity

        # get actual lead
        target_diff = cls.mph_to_fps(thrower.velocity) * shot_time

        # reverse direction
        reverse_direction = (thrower.direction + 180) % 360
        target_location = thrower.direction_to_destination(reverse_direction, target_diff, breakpoint)

        # find target distance from shooter at moment of trigger pull
        pull_x_diff = target_location[0] - shooter.position[0]
        pull_y_diff = target_location[1] - shooter.position[1]
        target_distance = math.sqrt(pull_x_diff**2 + pull_y_diff**2)

        # find lead in angle
        lead_angle = cls._get_angle_by_sides(shot_distance, target_distance, target_diff)

        # find lead in thumb widths
        lead_thumbs = cls.angle_to_thumbs(lead_angle)

        # find visual lead in ft
        visual_lead_ft = target_distance * math.sin(math.radians(lead_angle))

        return {
            'lead_ft': round(target_diff, 2),
            'lead_angle': round(lead_angle, 2),
            'lead_thumbs': round(lead_thumbs, 2),
            'visual_lead_ft': round(visual_lead_ft, 2),
            'breakpoint': breakpoint,
            'pullpoint': target_location,
            'shot_distance': round(shot_distance, 2),
            'target_distance': round(target_distance, 2),
            'trajectory': round(thrower.direction, 2)
        }



shooter = Shooter(velocity=1300)
shooter2 = Shooter()
shooter3 = Shooter(velocity=1100)

#thrower = Thrower(position=(40,40), direction=30)
#thrower2 = Thrower(position=(40,40), destination=(90.0, 126.60254037844388))
thrower1 = Thrower(position=(40,60), direction=270)
thrower2 = Thrower(position=(40,90), direction=270)
thrower3 = Thrower(position=(40,120), direction=270)
thrower4 = Thrower(position=(40,150), direction=270)

#import ipdb; ipdb.set_trace()
#print LeadCalculator.lead_by_breakpoint_location(shooter, thrower, (90, 126.6))

#print LeadCalculator.lead_by_breakpoint_location(shooter, thrower4, (0, 150))
#print LeadCalculator.lead_by_breakpoint_location(shooter, thrower3, (0, 120))
#print LeadCalculator.lead_by_breakpoint_location(shooter, thrower2, (0, 90))
#print LeadCalculator.lead_by_breakpoint_location(shooter, thrower1, (0, 60))

print LeadCalculator.lead_by_breakpoint_location(shooter2, thrower4, (0, 150))
print LeadCalculator.lead_by_breakpoint_location(shooter2, thrower3, (0, 120))
print LeadCalculator.lead_by_breakpoint_location(shooter2, thrower2, (0, 90))
print LeadCalculator.lead_by_breakpoint_location(shooter2, thrower1, (0, 60))

#print LeadCalculator.lead_by_breakpoint_location(shooter3, thrower4, (0, 150))
#print LeadCalculator.lead_by_breakpoint_location(shooter3, thrower3, (0, 120))
#print LeadCalculator.lead_by_breakpoint_location(shooter3, thrower2, (0, 90))
#print LeadCalculator.lead_by_breakpoint_location(shooter3, thrower1, (0, 60))

print LeadCalculator.lead_by_shooter_angle(shooter2, thrower4, 0)
