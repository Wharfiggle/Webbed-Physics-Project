import pygame
from pygame.math import Vector2
from pygame.locals import *
from physics_objects import Circle, Wall, Polygon
import contact
from forces import Gravity
from web import *
import itertools
import math
import json
from player import Player

pygame.init()

# Timing Variables
fps = 60
dt = 1/fps
clock = pygame.time.Clock()
window = pygame.display.set_mode(flags=FULLSCREEN)
width, height = window.get_width(), window.get_height()
objects = []

web = Web()
locked = True
mouse_circle = Polygon([(0,0),(0,50),(50,50),(50,0)], (100,100,100),1)
mouse_circle = Circle(radius=100,color=(0,0,255),mass=100000)
gravity = Gravity((0,9.8 * 300), objects_list=[web])
gravity = Gravity((0,9.8), objects_list = [mouse_circle])
running = True
while running:
    # update the display
    pygame.display.update()
    # delay for correct timing
    clock.tick(fps)
    # clear the screen
    window.fill([0,255,0])
    # EVENTS
    while event := pygame.event.poll():
        if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False
        if event.type == MOUSEBUTTONDOWN:
            joint = WebJoint(pos=pygame.mouse.get_pos(), connected_joints=web.web_joints[len(web.web_joints) - 3:], locked=locked)
            web.add_joint(joint)
        if event.type == KEYDOWN and event.key == K_TAB:
            locked = not locked
        if event.type == KEYDOWN and event.key == K_SPACE:
            mouse_circle.pos = pygame.mouse.get_pos()
            mouse_circle.vel = Vector2(0,0)


    for a, b in itertools.product(web.web_joints, web.web_lines):
        c = contact.generate(a, b)
    for line in web.web_lines:
        c = contact.generate(mouse_circle,line,resolve=False)
        if c.overlap > 0:
            window.fill((255,255,0))
        c.resolve()

    # Clear Forces
    web.clear_force()
    mouse_circle.clear_force()
    # Forces
    web.gravity.apply()
    gravity.apply()
    web.bonds.apply()
    # Updates
    web.update(dt)
    mouse_circle.update(dt)
    # Draws
    web.draw(window)
    mouse_circle.draw(window)


    