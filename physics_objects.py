from pygame.math import Vector2
import pygame
import math

#TODO REMEBER TO UPDATE THIS VARIABLE BETWEEN PROJECTS vvv
pixels_per_meter = 300

# angle = theta
# angular velocity = w
# moment of inertia = I
# torque = S.mag x F.mag //MAY INCLUDE *SIN(ANGLE BETWEEN S AND F)//= T, S: vector from centor of mass, F: force vector
# update = T / I * dt
# position = theta = w * dt
# impulse = S x J / I

 
class PhysicsObject:
    def __init__(self, pos=Vector2(0,0), vel=Vector2(0,0), mass=1.0, angle=0, avel=0, momi=math.inf, static = False):
        self.pos = Vector2(pos) #pixels
        self.mass = mass #kg
        self.force = Vector2(0,0) # (kg * meters) / seconds^2
        self.vel = Vector2(vel) # meters / sec

        self.angle = angle # degrees
        self.avel = avel # rad / s
        self.momi = momi # kg * m^2

        #self.center_of_rotation = Vector2(0,0)

        self.static = static


    def clear_force(self):
        self.force = Vector2(0,0)

    def add_force(self, force):
        if not self.static:
            self.force += force
    
    def impulse(self, impulse, rc : Vector2 = None):
        if not self.static:
            self.vel += impulse/self.mass
        
        # rc is point of contact
        if rc is not None:
            # Sa is vector from center of rotation of a to contact point
            Sa = rc - self.pos#self.center_of_rotation
            self.avel += math.degrees((Sa.cross(impulse)) / self.momi)
            #print("Avel: " + str(self.avel) + "  tick: " + str(pygame.time.get_ticks())) # Get ticks() just to make sure that they are unique messages


    def set(self, pos = None, angle = None):
        if pos != None:
            self.pos = Vector2(pos)
        if angle != None:
            self.angle = angle


    def update(self, dt):
        if self.static:
            self.vel = Vector2(0,0)
        else:
            # update velocity using the current force
            self.vel += self.force / self.mass * dt
            # update position using the newly updated velocity
            self.pos += self.vel * dt * pixels_per_meter # m/s * s * p/m
            self.angle += self.avel * dt
            

class Circle(PhysicsObject):
    def __init__(self, radius=100, color=(255,255,255), width=0, **kwargs):
        # kwargs = keyword arguments
        super().__init__(**kwargs)
        self.radius = radius
        self.color = color
        self.width = width
        self.contact_type = "Circle"
    
    def draw(self, window, offset = Vector2(0,0)):
        pygame.draw.circle(window, self.color, self.pos + offset, self.radius, self.width)
        #pygame.draw.line(window, (255,255,255), self.pos + offset, self.pos + offset + self.radius*Vector2(0,1).rotate(self.angle))

    def resize(self, scaler):
        self.radius *= scaler
        return self
    
    def copy(self,pos=None, angle = None):
        if pos:
            return Circle(radius=self.radius,color=self.color,width=self.width,pos=pos,mass=self.mass,momi=self.momi)
        return Circle(radius=self.radius,color=self.color,width=self.width,pos=self.pos,mass=self.mass,momi=self.momi)

class Wall(PhysicsObject):
    def __init__(self, start : Vector2 = None, end : Vector2 = None, color = (255,255,255), width = 1, normals_length = 0):
        self.point1 = Vector2(start)
        self.point2 = Vector2(end)
        self.color = color
        self.width = width
        self.normal = (self.point2 - self.point1).normalize().rotate(90)
        super().__init__(pos = Vector2(self.point1 + self.point2) / 2, mass=math.inf)
        self.contact_type = "Wall"

    def draw(self, window, offset = Vector2(0,0)):
        pygame.draw.line(window, self.color, self.point1 + offset, self.point2 + offset, self.width)
        center_point = (self.point1 + self.point2)/2 + offset
        pygame.draw.line(window, (255,0,0),  center_point,center_point + self.normal)

class Polygon(PhysicsObject):
    def __init__(self, local_points=[], color=(255,255,255),width=0,normals_length=0, **kwargs):
        self.local_points=[Vector2(x) for x in local_points]
        self.local_normals = [(self.local_points[i] - self.local_points[i-1]).normalize().rotate(90)
                               for i in range(len(self.local_points))]
        
        for i in range(len(self.local_points)):
            d = [(point - self.local_points[i]).dot(self.local_normals[i]) for point in self.local_points]
            pos = sum(x>5e-13 for x in d)
            neg = sum(x<-5e-13 for x in d)
            if pos > 0:
                if neg == 0:
                    self.local_normals[i] *= -1
                else:
                    print("Nonconvex polygon defined")
                    print("i=" + str(i))
                    raise(ValueError, "Nonconvex polygon defined")
        
        self.color = color
        self.width = width
        self.normals_length = normals_length
        super().__init__(**kwargs)
        self.update_polygon()
        self.contact_type = "Polygon"


    def update_polygon(self):
        self.local_normals = [(self.local_points[i] - self.local_points[i-1]).normalize().rotate(90)
                               for i in range(len(self.local_points))]
        for i in range(len(self.local_points)):
            d = [(point - self.local_points[i]).dot(self.local_normals[i]) for point in self.local_points]
            pos = sum(x>5e-13 for x in d)
            neg = sum(x<-5e-13 for x in d)
            if pos > 0:
                if neg == 0:
                    self.local_normals[i] *= -1
                else:
                    print("Nonconvex polygon defined")
                    print("i=" + str(i))
                    raise(ValueError, "Nonconvex polygon defined")
        self.points = [local_point.rotate(self.angle) + self.pos for local_point in self.local_points]
        self.normals = [local_normal.rotate(self.angle) for local_normal in self.local_normals]

    def update(self,dt):
        super().update(dt)
        self.update_polygon()

    def draw(self,window,offset = Vector2(0,0)):
        pygame.draw.polygon(window, self.color, [point + offset for point in self.points], self.width)
        if self.normals_length > 0:
            for point, normal in zip(self.points, self.normals):
                pygame.draw.line(window, (255,0,0), start_pos=point + offset, end_pos=point + offset + self.normals_length*normal,width=5)


    def set(self, pos = None, angle = None):
        super().set(pos=pos,angle=angle)
        self.update_polygon()


    def flip(self, yaxis:bool=False):
        if len(self.points) < 3:
            return
        if not yaxis:
            temp_points = []
            temp_points.append(Vector2(self.local_points[0][0] * -1,self.local_points[0][1]))
            for i in range(len(self.local_points) - 1, 0, -1):
                # Negate the x component of the points indexed 1 through N
                temp_points.append(Vector2(self.local_points[i][0]*-1, self.local_points[i][1]))
            self.local_points = temp_points
            self.update_polygon()
        return self
    
    def copy(self, pos:Vector2=None, angle:float = None):
        new_polygon = Polygon(self.local_points, tuple(self.color), self.width, self.normals_length,
                       pos=Vector2(self.pos),mass=float(self.mass), vel=Vector2(self.vel),
                       angle=float(self.angle),avel=float(self.avel), momi=float(self.momi))
        if pos != None:
            new_polygon.pos = Vector2(pos)
        if angle != None:
            new_polygon.angle = float(angle)
        new_polygon.update_polygon()
        return new_polygon
    
    def resize(self, scaler):
        for i in range(len(self.local_points)):
            self.local_points[i] *= scaler
        self.update_polygon()
        return self
    

    
class UniformCircle(Circle):
    def __init__(self, density=1, radius = 1, **kwargs):
        # calculate mass and moment of inertia
        mass = density * math.pi * radius * 2
        momi = 0.5 * mass * radius * radius
        super().__init__(mass=mass, momi=momi, radius=radius, **kwargs)

class UniformPolygon(Polygon):
    def __init__(self, density=None, local_points=[], pos=Vector2(0,0), angle=0, shift=True, mass=None, **kwargs):
        if mass is not None and density is not None:
            raise("Cannot specify both mass and density.")
        if mass is None and density is None:
            mass = 1 # if nothing specified, default to mass = 1
        # Calculate mass, moment of inertia, and center of mass
        total_mass = 0 # kg
        total_momi = 0 # kg / m^2
        center_of_mass = Vector2(0,0) #pixels
        mass_numerator = Vector2(0,0) #kg

        # by looping over all "triangles" of the polygon
        for i in range(len(local_points)):
            Sa = Vector2(Vector2(local_points[i]))
            Sb = Vector2(Vector2(local_points[(i+1) % len(local_points)]))
            # triangle mass
            triangle_area = abs(Sb.cross(Sa) * 0.5)

            triangle_mass = triangle_area * density
            # triangle moment of inertia
            triangle_momi = triangle_mass / 6 * (Sa.magnitude_squared()
                                                  + Sb.magnitude_squared() 
                                                  + Sa.dot(Sb))
            # triangle center of mass

            # add to total mass
            total_mass += triangle_mass
            # add to total moment of inertia
            total_momi += triangle_momi
            # add to center of mass numerator
            mass_numerator += Vector2(Vector2(local_points[i]) + Vector2(local_points[(i+1) % len(local_points)]))/3 * triangle_mass
            #triangle_center_of_mass = Vector2(Vector2(local_points[i]) + Vector2(local_points[(i+1) % len(local_points)]))/3
            #center_of_mass += triangle_center_of_mass * triangle_mass

        # calculate total center of mass by dividing numerator by denominator (total mass)
        #center_of_mass = Vector2(center_of_mass) / total_mass
        center_of_mass = mass_numerator / total_mass
        # if mass is specified, then scale mass and momi
        if mass is not None:
            total_momi *= mass/total_mass
            total_mass = mass

        # Usually we shift local_points origin to center of mass
        if shift:
            # Shift local_points by center of mass offset
            shift_vec : Vector2 = Vector2(center_of_mass)
            for point in range(len(local_points)):
                local_points[point] = Vector2(local_points[point]) - shift_vec
            
            # shift pos of origin
            pos += shift_vec.rotate(angle)

            # Use parallel axis theorem to correct the moment of inertia
            total_momi -= total_mass * center_of_mass.magnitude_squared()

        if total_mass < 0:
            total_mass *= -1
            total_momi *= -1


        total_momi /= math.pow(pixels_per_meter,2)


        # Then call super().__init__() with those correct values
        super().__init__(mass=total_mass, momi=total_momi, local_points=local_points, pos=pos, angle=angle, **kwargs) 

    def draw(self,window):
        super().draw(window)
        #pygame.draw.circle(window,(0,255,0),self.pos + self.local_points[0].rotate(self.angle), 5) #point 0
        #pygame.draw.circle(window,(0,0,255), self.pos,5)

    # def copy(self,pos:Vector2=None, angle:float = None):
    #     super().copy(pos,angle)

# shape = UniformPolygon(density=0.01, local_points=[(0,0),(20,0),(20,10),(0,10)])
# print(shape.mass)
# print(shape.momi, shape.mass/12*(10**2+20**2))
# print(shape.local_points)