import pygame
from pygame.math import Vector2
from pygame.locals import *
from physics_objects import Circle, Wall, Polygon
import contact
import math

class Enemy(Circle):
    def __init__(self, speed = 1, spritePath = "", **kwargs):
        super().__init__(**kwargs)
        self.speed = speed
        if(spritePath != ""):
            self.sprite = pygame.image.load(spritePath).convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (self.radius * 4, self.radius * 4))
        else:
            self.color = (255, 0, 0)
        self.spriteAngle = 0.0
        self.playerPos = Vector2(0, 0)
        self.moveVel = Vector2(0, 0)
        self.faceLeft = True

    def draw(self, window, offset):
        if(self.color != (255, 0, 0)):
            newImg = self.sprite
            self.spriteAngle = -self.angle
            if(not self.faceLeft):
                newImg = pygame.transform.flip(newImg, True, False)
            newImg = pygame.transform.rotate(newImg, self.spriteAngle * 180 / math.pi)
            window.blit(newImg, (self.pos.x + offset.x - newImg.get_width() / 2, self.pos.y + offset.y - newImg.get_height() / 2))
        else:
            pygame.draw.circle(window, self.color, self.pos + offset, self.radius, self.width)
        
    def update(self, dt, playerPos):
        self.playerPos = playerPos
        moveDir = Vector2(0, 0)
        if(playerPos.x < self.pos.x - self.radius / 2):
            moveDir = Vector2(-1, 0)
            self.faceLeft = True
        elif(playerPos.x > self.pos.x + self.radius / 2):
            moveDir = Vector2(1, 0)
            self.faceLeft = False
        self.moveVel = self.moveVel + (moveDir * self.speed - self.moveVel) * dt * 2
        self.vel += self.moveVel
        super().update(dt)
        self.vel -= self.moveVel