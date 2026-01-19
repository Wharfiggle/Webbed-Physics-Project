import pygame
from pygame.math import Vector2
from pygame.locals import *
from physics_objects import Circle
import math
import random

def lerpAngle(a:float, b:float, t:float):
    dtheta = b - a
    if(dtheta > math.pi):
        a += 2 * math.pi
    elif(dtheta < -math.pi):
        a -= 2 * math.pi
    return a + (b - a) * t

class Fly(Circle):
    def __init__(self, speed = 1, **kwargs):
        angle = random.randrange(0,360)
        super().__init__(angle=angle,**kwargs)
        self.speed = speed
        self.sprite = pygame.image.load('Fly.png').convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (self.radius * 2, self.radius * 2))
        self.spriteAngle = 0.0
        self.origin = Vector2(self.pos + Vector2(random.randrange(-50,50),random.randrange(-50,50)))
        self.angleDelta = 0
        self.isIn = True
        self.time = 0

    def draw(self, window, offset):
        newImg = self.sprite
        #self.spriteAngle = lerpAngle(self.spriteAngle, -self.angle, 0.3)
        self.spriteAngle = -self.angle
        newImg = pygame.transform.rotate(newImg, self.spriteAngle * 180 / math.pi - 90)
        #pygame.draw.circle(window, self.color, self.pos + offset, self.radius, self.width)
        window.blit(newImg, (self.pos.x + offset.x - newImg.get_width() / 2, self.pos.y + offset.y - newImg.get_height() / 2))
        
    def update(self, dt):
        self.time += dt
        if(not self.isIn):
            posdiff = self.origin - self.pos
            newAngle = lerpAngle(self.angle, math.atan2(posdiff.y, posdiff.x), (8 + 2 * math.sin(self.time * 5)) * dt)
            self.angleDelta = newAngle - self.angle
            self.angle = newAngle
            if(posdiff.magnitude() < 20):
                self.isIn = True
        else:
            if((self.origin - self.pos).magnitude() > 40):
                self.isIn = False
        self.vel = Vector2(math.cos(self.angle), math.sin(self.angle)) * (self.speed + math.sin(self.time) / 5)
        super().update(dt)