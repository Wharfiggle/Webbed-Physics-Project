from pygame.math import Vector2
from physics_objects import *

# Returns a new contact object of the correct subtype
# This function has been done for you.
def generate(a, b, **kwargs):
    # Check if a's type comes later than b's alphabetically.
    # We will label our collision types in alphabetical order, 
    # so the lower one needs to go first.
    if b.contact_type < a.contact_type:
        a, b = b, a
    # This calls the class of the appropriate name based on the two contact types.
    return globals()[f"{a.contact_type}_{b.contact_type}"](a, b, **kwargs)
    

# Generic contact class, to be overridden by specific scenarios
class Contact():
    def __init__(self, a, b, resolve=False, **kwargs):
        self.a = a
        self.b = b
        self.kwargs = kwargs
        self.overlap = 0
        self.normal = Vector2(0,0)
        self.update() # the update() function is created in the derived classes
        if resolve:
            self.resolve(update=False)

    def update(self):
        pass

    def resolve(self, update=True, rebound=0, **kwargs):
        if update:
            self.update()
        
        # This pattern first checks keywords to resolve, then keywords given to contact.
        # Keywords given here to resolve override the previous ones given to contact.
        restitution = kwargs.get("restitution", self.kwargs.get("restitution", 0)) # 0 is default
        friction = kwargs.get("friction", self.kwargs.get("friction",0)) # o is default

        # RESOLVE OVERLAP
        if self.overlap > 0: # Only if they are overlapping
            m = 1/((1/self.a.mass) + (1/self.b.mass))
                    
            self.a.set(self.a.pos + m/self.a.mass * self.overlap * self.normal)
            self.b.set(self.b.pos - m/self.b.mass * self.overlap * self.normal)

            if self.point() is None:
                print("Error: No point")
            RPoint = self.point()

            # Sa and Sb
            AToPoint = RPoint - self.a.pos
            BToPoint = RPoint - self.b.pos
            
            VelRota = self.a.vel + math.radians(self.a.avel) * AToPoint.rotate(90)
            VelRotb = self.b.vel + math.radians(self.b.avel) * BToPoint.rotate(90)

            v = VelRota - VelRotb

            # RESOLVE VELOCITY
            vdotn = v.dot(self.normal)
            if vdotn < 0: # Only if they are moving towards each other
                # m is already calculated
                # normal impulse
                Jn = - (1 + restitution) * vdotn 
                m = 1 / ((1/self.a.mass) + 
                         (1/self.b.mass) +
                         (pow(AToPoint.cross(self.normal),2) / self.a.momi) + 
                         (pow(BToPoint.cross(self.normal),2) / self.b.momi))
                Jn *= m                
                Jn += m * rebound # Jump impulse

                # New
                tangent = self.normal.rotate(90)
                vdott = v.dot(tangent)
                Jt = - m * vdott #Tangential impulse
                if abs(Jt) < friction * Jn:
                    # Sticking friction                                        
                    shift_vec = vdott/vdotn * self.overlap * tangent
                    self.a.pos += shift_vec * m / self.a.mass
                    self.b.pos -= shift_vec * m / self.b.mass
                else:
                    Jt = friction * Jn * math.copysign(1, -vdott)

                impulse = Jn * self.normal + Jt * tangent


                
                self.a.impulse(impulse, self.point())
                self.b.impulse(-impulse, self.point())



# J = (-1 + Er) v * n)

# a = 1/ma
# b = 1/mb
# c = ((Sa x n)/Ia)
# d = ((Sb x n)/Ib)

# J /= (a + b + c + d)

# J = ((-1 + Er) v * n) / (1/ma + 1/mb + ((Sa x n)/Ia) + ((Sb x n)/Ib))


# KEY:
# J: impulse
# ma mb: modified mass
# Sa Sab: AToPoint BToPoint, 
# w: avel
# ra rb: center of rotation/center of mass?
# Ia Ib: momi / moment of inerita
# Er: restitution
# 

# Polygon: A, Circle : B
# S vectors are the radius to the contact point
# W vectors are angular velocity

# V` = Va + Varot
# V` = Vb + Vbrot
# V  = Va` - Vb`

# V = RW    or
# Vrot = Wa * Sarot90
## Va` = Va + WbSarot90
## Vb` = Vb + WbSbrot90

# Sa = Rpoint - Ra
# Sb = Rpoint - Rb

# RPoint = self.point()
# ReletiveVelocity = Radius * Momi
# ReletiveRotation = a.Momi * b.normal.rotate(90)
# VelRota = a.vel + a.avel
# VelRotb = b.vek + b.avel
# ReletiveVelRot = VelRota - VelRotb
# AToPoint = RPoint - a.pos
# BToPoint = RPoint - b.pos

        
# Contact class for two circles
class Circle_Circle(Contact):
    def update(self):  # compute the appropriate values
        self.a : Circle
        self.b : Circle

        r = self.a.pos - self.b.pos
        self.overlap = self.a.radius + self.b.radius - r.magnitude()
        if r.magnitude() > 0:
            self.normal = r.normalize()

    def point(self):
        return self.a.pos + (self.a.pos - self.b.pos) / 2
        

class Circle_Polygon(Contact):
    def update(self):  # compute the appropriate values
        self.a : Circle
        self.b : Polygon
        # self.overlap needs to be the minimum overlap
        # First set it to infinity and then keep searching for lower values
        self.overlap = math.inf
        for i, (point, normal) in enumerate(zip(self.b.points, self.b.normals)):
           r = self.a.pos - point
           overlap = self.a.radius - r.dot(normal)
           if overlap < self.overlap:
               self.overlap = overlap
               self.normal = normal
               self.index = i

        # Find the two points for the wall that is overlapped / Overlap with nearest vertex
        if 0 < self.overlap and self.overlap < self.a.radius:
            point1 = self.b.points[self.index]
            point2 = self.b.points[self.index - 1]


            end_point = None
            # Beyond point 1
            if (point1 - point2).dot(self.a.pos - point1) > 0:
                # Find the overlap between the circle and the endpoint (point1)
                end_point = point1
            # Beyond point 2
            elif (point2 - point1).dot(self.a.pos - point2) > 0:
                # Find the overlap between the circle and the endpoint (point2)
                end_point = point2
            if end_point:
                r = self.a.pos - end_point
                self.overlap = self.a.radius + 0 - r.magnitude()
                self.normal = (self.a.pos - end_point).normalize()
                if r.magnitude() > 0:
                    self.normal = r.normalize()

    def point(self):
        return self.a.pos + self.a.radius * (-self.normal)


# Contact class for Circle and a Wall
# Circle is before Wall because it comes before it in the alphabet
class Circle_Wall(Contact):
    def update(self):  # compute the appropriate values
        self.a : Circle
        self.b : Wall

        r = self.a.pos - self.b.pos
        self.overlap = self.a.radius - r.dot(self.b.normal) + self.b.width / 2
        self.normal = self.b.normal

    def point(self):
        return self.a.pos + self.a.radius * (-self.normal)


class Polygon_Polygon(Contact):
    def update(self):
        self.a : Polygon
        self.b : Polygon
        self.point_index = -1
        self.point_polygon = None
        self.overlap = math.inf

        # Loop through walls
        for pos, normal in zip(self.b.points, self.b.normals):

            most_overlapped_point = None
            most_point_overlap = -math.inf

            # Loops through points
            for i in range(len(self.a.points)):
                r = self.a.points[i] - pos
                overlap = -r.dot(normal)
                if overlap > most_point_overlap:
                    most_point_overlap = overlap
                    #self.normal = normal
                    #self.point_polygon = self.a
                    most_overlapped_point = i
            
            if most_point_overlap < self.overlap:
                self.overlap = most_point_overlap
                self.point_polygon = self.a
                self.point_index = most_overlapped_point
                self.normal = normal
            if most_point_overlap < 0:
                break

        # Loop through walls
        for pos, normal in zip(self.a.points, self.a.normals):
            most_overlapped_point = None
            most_point_overlap = -math.inf

            # Loops through points
            for i in range(len(self.b.points)):
                r = self.b.points[i] - pos
                overlap = -r.dot(normal)
                if overlap > most_point_overlap:
                    most_point_overlap = overlap
                    #self.normal = normal
                    #self.point_polygon = self.a
                    most_overlapped_point = i
            
            if most_point_overlap < self.overlap:
                self.overlap = most_point_overlap
                self.point_polygon = self.b
                self.point_index = most_overlapped_point
                self.normal = -normal
            if most_point_overlap < 0:
                break

        # for pos, normal in zip(self.a.points, self.a.normals):
        #     for i in range(len(self.b.points)):
        #         r = self.b.points[i] - pos
        #         overlap = -r.dot(normal)
        #         if overlap < self.overlap:
        #             self.overlap = overlap
        #             self.normal = -normal 
        #             self.point_polygon = self.b
        #             self.point_index = i

        #         if overlap < 0:
        #             break

    def point(self):
        if self.point_polygon == self.a:
            return self.point_polygon.points[self.point_index] - self.normal
        else:
            return self.point_polygon.points[self.point_index] + self.normal


class Polygon_Wall(Contact):
    def update(self):
        self.a : Polygon
        self.b : Wall
        # Loop over all points on the polygon and find the most overlapped point.
        self.point_index = 0
        self.overlap = 0
        for i in range(len(self.a.points)):
            r = self.a.points[i] - self.b.pos
            overlap = -r.dot(self.b.normal) + self.b.width / 2
            if overlap > self.overlap:
                self.point_index = i
                self.overlap = overlap
        self.normal = self.b.normal

    def point(self):
        return self.a.points[self.point_index] + self.normal


# Empty class for Wall - Wall collisions
# The intersection of two infinite walls is not interesting, so skip them
class Wall_Wall(Contact):
    def update(self):
        pass

    def point(self):
        pass
