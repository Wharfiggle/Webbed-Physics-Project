import pygame
from pygame.math import Vector2
from pygame.locals import *
from physics_objects import Circle
import math

def lerpAngle(a:float, b:float, t:float):
    dtheta = b - a
    if(dtheta > math.pi):
        a += 2 * math.pi
    elif(dtheta < -math.pi):
        a -= 2 * math.pi
    return a + (b - a) * t

class Player(Circle):
    def __init__(self, speed = 10, **kwargs):
        super().__init__(**kwargs)
        self.speed = speed
        self.spider_img = pygame.image.load('Spider.png').convert_alpha()
        self.spider_img = pygame.transform.scale(self.spider_img, (self.radius * 2, self.radius * 2))
        self.move_vel = Vector2(0, 0)
        self.floorNormal = Vector2(0, 0)
        #self.floorNormalBuffer = []
        #self.floorNormalBufferSize = 5
        self.faceLeft = True
        self.spriteAngle = 0.0

    def draw(self, window, offset):
        newImg = self.spider_img
        if(not self.faceLeft):
            newImg = pygame.transform.flip(newImg, True, False)
        target_angle = -math.atan2(self.floorNormal.y, self.floorNormal.x) * 180.0 / math.pi + 90
        target_angle = math.degrees(-math.atan2(self.floorNormal.y, self.floorNormal.x)) + 90
        if(self.floorNormal == Vector2(0, 0)):
            target_angle = 0

        self.spriteAngle = lerpAngle(self.spriteAngle, target_angle, 0.3)
        newImg = pygame.transform.rotate(newImg, self.spriteAngle)
        #pygame.draw.circle(window, self.color, self.pos + offset, self.radius, self.width)
        window.blit(newImg, (self.pos.x + offset.x - newImg.get_width() / 2, self.pos.y + offset.y - newImg.get_height() / 2))
        #pygame.draw.line(window, (0,0,255), self.pos + offset, self.pos + self.direction * 50 + offset)

    def move(self, direction, dt):
        direction = Vector2(direction)
        if(direction.x > 0):
            self.faceLeft = False
        elif(direction.x < 0):
            self.faceLeft = True
        #rotate direction of movement based on floor's normal so the player can walk up and down slopes properly
        if(self.floorNormal != Vector2(0, 0)):
            up = math.atan2(self.floorNormal.y, self.floorNormal.x) * 180.0 / math.pi
            direction = direction.rotate(up - 90)
        self.direction = direction    
        a = self.move_vel
        b = direction * self.speed
        self.move_vel = a + (b - a) * dt * 5
        
    def update(self, dt):
        # if(self.floorNormalBuffer.num < 0):
        #     self.floorNormal = Vector2(0, 0)
        # else:
        #     self.floorNormal = self.floorNormalBuffer.pop(0)
        self.vel += self.move_vel
        super().update(dt)
        self.vel -= self.move_vel