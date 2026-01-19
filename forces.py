import pygame
from pygame.math import Vector2
import itertools
import math
import physics_objects


class SingleForce:
    def __init__(self, objects_list=[]):
        self.objects_list = objects_list

    def apply(self, wind_vel = Vector2(0,0)):
        for obj in self.objects_list:
            force = self.force(obj)  # force function implemented in every subclass
            obj.add_force(force)

class PairForce:
    def __init__(self, objects_list=[]):
        self.objects_list = objects_list

    def apply(self):
        # Loop over all pairs of objects and apply the calculated force
        # to each object, respecting Newton's 3rd Law.  
        # Use either two nested for loops (taking care to do each pair once)
        # or use the itertools library (specifically, the function combinations).

        # for i in range(len(self.objects_list)):
        #     obj1 = self.objects_list[i]
        #     for j in range(i):
        #         obj2 = self.objects_list[j]
        #         force = self.force(obj1,obj2)
        #         obj1.add_force(force)
        #         obj2.add_force(-force)

        # combonations(iterable, length of tuple)
        for a,b in itertools.combinations(self.objects_list, 2):
            force = self.force(a,b)
            a.add_force(force)
            b.add_force(-force)


class BondForce:
    def __init__(self, pairs_list=[]):
        # pairs_list has the format 
        # [[obj1, obj2], [obj3, obj4], ... ] 
        # ^ each pair representing a bond
        self.pairs_list = pairs_list

    def apply(self):
        # Loop over all *pairs* from the pairs list.  
        # Calcuate the force between the pair
        for pair in self.pairs_list:
            a = pair[0]
            b = pair[1]
            force = self.force(a,b)
            #print("Force" + str(force))
            # Apply the force to each member of the pair respecting Newton's 3rd Law.
            ## Object a recieves the force
            a.add_force(force)
            ## Object b recieves negative the force
            b.add_force(-force)


# Add Gravity, SpringForce, SpringRepulsion, AirDrag
class Gravity(SingleForce):
    def __init__(self, acc=(0,0), **kwargs):
        self.acc = Vector2(acc)
        super().__init__(**kwargs)

    def force(self, obj):
        return obj.mass * self.acc
        # Note: this will throw an error if the object has infinite mass.
        # Think about how to handle those.
    

class SpringForce(BondForce):
    def __init__(self, stiffness=0.7, natural_length = 10, max_length = None, **kwargs): #pairs_list
        self.stiffness = stiffness
        self.natural_length = natural_length
        self.dictionary = {}
        self.max_length = max_length
        super().__init__(**kwargs)

    def force(self, obja, objb):
        # Offset Vector
        r = (Vector2(obja.pos) - Vector2(objb.pos))# / physics_objects.pixels_per_meter
        key = tuple((obja,objb))
        len_stiff = self.dictionary.get(key,None)
        if not len_stiff:
            key = tuple(objb,obja)
            len_stiff = self.dictionary.get(key,None)
        if not len_stiff:
            len_stiff = (None,None)
        # Natural Length
        if len_stiff[0] != None:
            l = len_stiff[0]
        else:
            l = self.natural_length
        # Dampening Constant
        b = 0.5
        # Velocity Offset Vector
        v = (Vector2(obja.vel) - Vector2(objb.vel))
        # Stiffness
        if len_stiff[1] != None:
            stiffness = len_stiff[1]
        else:
            stiffness = self.stiffness

        #F_spring=[-k(|r|-l)-bv⋅r ̂ ] r ̂
        return (-stiffness * (r.magnitude() - l) - (b * v).dot(r.normalize()) ) * r.normalize()
    
    def add_unique_pair(self, pair, natural_length = None, stiffness = None):
        if pair in self.pairs_list or (pair[1],pair[0]) in self.pairs_list:
            print("Pair already in pairs list")
            return
        self.pairs_list.append(pair)
        self.dictionary[pair] = (natural_length, stiffness)

    def clear(self):
        self.dictionary.clear()
        self.pairs_list.clear()


class Friction(SingleForce):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def force(self, obj):
        u = 0.3
        m = obj.mass #kg #0.2
        g = 9.8
        v = Vector2(0,0)
        if(obj.vel.magnitude() > 0):
            v = obj.vel.normalize()
        return -u * m * g * v

class AirDrag(SingleForce):
    def __init__(self, wind_vel = Vector2(0,0),**kwargs):
        super().__init__(**kwargs)
        self.wind_vel = wind_vel

    def set_wind(self, wind_force):
        self.wind_vel = wind_force

    def force(self, obj):
        self.objects_list
        mass_density = 1.204 #p: kilo / m^3 
        #flow_velocity = float # 0 - 1?
        drag_coefficient = 0.4 #C_d: Marble drag coefficeient 0.4-0.5, -ChatGPT
        reference_area = math.pi * pow(0.01,2) #A: reference area
        v = obj.vel - Vector2(self.wind_vel,0)
        return - 1/2 * mass_density * drag_coefficient * reference_area * v.magnitude() * v

class SpringRepulsion(PairForce):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def force(self, obja,objb):
        r = obja.pos - objb.pos
        if(obja.radius + objb.radius - r.magnitude() > 0):
            constant = 0.01
            return constant * (obja.radius + objb.radius - r.magnitude()) * r
        else:
            return Vector2(0,0)


    


