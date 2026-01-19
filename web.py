from pygame.math import Vector2
import pygame
import math
from forces import *
from physics_objects import *

# Manager class to handle all web updating
class Web():
    def __init__(self, web_joints = [], web_lines = [], gravity_acc=(0,9.8)):
        self.web_joints = web_joints
        self.web_lines = web_lines
        self.gravity = Gravity(gravity_acc, objects_list = web_joints)
        pairs = None # May need to calculate all pairs if we want to construct a web with premade joints
        self.bonds = SpringForce(stiffness=0, natural_length = 0)
        self.update_bonds()

    # Update all lines and joints
    def update(self,dt):
        for object in self.web_joints + self.web_lines :
            object.update(dt)
    
    def update_bonds(self):
        self.bonds.clear()
        for line in self.web_lines:
            self.bonds.add_unique_pair((line.joints[0], line.joints[1]), natural_length=line.length*0.9, stiffness=0.01)
    
    def clear_force(self):
        for object in self.web_joints + self.web_lines:
            object.clear_force()

    def add_joint(self, joint):
        self.web_joints.append(joint)
        for line in joint.connected_lines:
            if not line in self.web_lines:
                self.web_lines.append(line)
        if not joint.locked:
            self.gravity.objects_list.append(joint)
        self.update_bonds()

    # Remove a joint and all lines connected to it
    def remove_joint(self, joint, merge_lines=False):
        if merge_lines and len(joint.connected_lines) == 2 and len(joint.connected_joints) == 2:
            joint_a = joint.connected_joints[0]
            joint_b = joint.connected_joints[1]
            new_line = WebLine(joints=joint.connected_joints)
            # Adjust joint 0
            joint_a.connected_joints.remove(joint)
            joint_a.connected_joints.append(joint_b)
            line_a = joint_a.find_line_with_joint(joint)
            joint_a.connected_lines.remove(line_a)
            joint_a.connected_lines.append(new_line)
            # Adjust joint 1
            joint_b.connected_joints.remove(joint)
            joint_b.connected_joints.append(joint_a)
            line_b = joint.connected_joints[1].find_line_with_joint(joint)
            joint_b.connected_lines.remove(line_b)
            joint_b.connected_lines.append(new_line)
            self.web_joints.remove(joint)
            self.web_lines.remove(line_a)
            self.web_lines.remove(line_b)
            self.web_lines.append(new_line)

        elif not merge_lines:
            self.web_joints.remove(joint)
            for line in joint.connected_lines:
                self.web_lines.remove(line)
        else:
            print("Num connected lines: ", len(joint.connected_lines), ", joints: ", len(joint.connected_joints))
    

    # Remove a line and its points if no other lines connect to them
    def remove_line(self,line):
        self.web_lines.remove(line)
        removing_joints = []
        for joint in line.joints:
            if len(joint.connected_joints) == 1:
                removing_joints.append(joint)
        for joint in removing_joints:
            self.remove_joint(joint)


    # Splits a line into two and adds a new joint in the middle
    def add_joint_to_line(self, joint, line):
        joint_a = line.joints[0]
        joint_b = line.joints[1]
        if line in self.web_lines: self.web_lines.remove(line)

        line1 = WebLine([joint_a,joint])
        if joint_b in joint_a.connected_joints: joint_a.connected_joints.remove(joint_b)
        joint_a.connected_joints.append(joint)
        if line in joint_a.connected_lines: joint_a.connected_lines.remove(line)
        joint_a.connected_lines.append(line1)
        joint.connected_lines.append(line1)
        joint.connected_joints.append(joint_a)

        line2 = WebLine([joint, joint_b])
        if joint_a in joint_b.connected_joints: joint_b.connected_joints.remove(joint_a)
        joint_b.connected_joints.append(joint)
        if line in joint_b.connected_lines: joint_b.connected_lines.remove(line)
        joint_b.connected_lines.append(line2)
        joint.connected_lines.append(line2)
        self.web_joints.append(joint)
        joint.connected_joints.append(joint_b)

        self.web_lines += [line1,line2]
        joint.locked = False
        joint.mass = 1


    # Finds the closest line from a pos
    def get_closest_line(self, pos):
        pass

    # Draw all joints and lines
    def draw(self, window, offset = Vector2(0,0)):
        for thing in self.web_lines + self.web_joints:
            thing.draw(window, offset)
    

class WebJoint(Circle):
    def __init__(self, pos, radius=5, width=0, connected_joints = [], locked = False, **kwargs):
        self.connected_joints : WebJoint = connected_joints
        super().__init__(radius, (255,0,0), width, pos=pos, **kwargs)

        # Make the new web lines
        self.connected_lines = []
        for joint in connected_joints:
            web_line = WebLine(joints=[self, joint], pos = self.pos)
            self.connected_lines.append(web_line)
            joint.connected_lines.append(web_line)

        self.locked = locked
        if locked:
            self.mass = math.inf

    def update(self, dt):
        if self.locked:
            self.vel = Vector2(0,0)
            self.avel = 0
        else:
            super().update(dt)

    def get_pairs(self):
        pairs = []
        for joint in self.connected_joints:
            pairs.append((self, joint))
        return pairs

    def draw(self, window, offset=Vector2(0,0)):
        return
        if self.locked:
            pygame.draw.circle(window, (200,200,200), center=self.pos + offset, radius=self.radius)
        else:
            pygame.draw.circle(window, self.color, center=self.pos + offset, radius=self.radius)
    
    def generate_lines(self):
        self.connected_lines = []
        #self.connected_joints = []
        for joint in self.connected_joints:
            if self not in joint.connected_joints:
                joint.connected_joints.append(self)
            line = WebLine(joints=[self, joint])
            self.connected_lines.append(line)
            joint.connected_lines.append(line)

            
    def find_line_with_joint(self, joint):
        for line in self.connected_lines:
            if joint in line.joints:
                return line
        

class WebLine(Polygon):
    def __init__(self, joints = [], color=(255,255,255), width=0, length = None, **kwargs):
        local_points = [Vector2(0,0), joints[1].pos - joints[0].pos]
        super().__init__(local_points, color, width, **kwargs)
        self.joints = joints
        if length:
            self.length = length
        else:
            self.length = Vector2(joints[0].pos - joints[1].pos).magnitude()
        self.mass = math.inf

    def update(self, dt):
        self.local_points = [Vector2(0,0), self.joints[1].pos - self.joints[0].pos]
        self.pos = self.joints[0].pos
        super().update(dt)

    def draw(self, window, offset = Vector2(0,0)):
        #pygame.draw.circle(window, (0,0,255),radius = 5, center=self.pos + offset)
        if len(self.joints) > 1:
            pygame.draw.line(window, self.color, Vector2(self.points[0] + offset), Vector2(self.points[1] + offset), 10)
            #pygame.draw.circle(window, (0,0,255),radius = 5, center=self.pos + offset) #DEBUG



