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
from fly import Fly
from enemy import Enemy

# JSON file for loading the level from. May need to replace with absolute path (use /'s not \'s). 
level_file_name = "level.txt"

# initialize pygame and open window
pygame.init()
font = pygame.font.SysFont('sourcecodepro', 22, True, False)
window = pygame.display.set_mode(flags=FULLSCREEN)
width, height = window.get_width(), window.get_height()

# Camera
camera_offset = Vector2(width / 2, height * 3/5) # The desired offset of the camera related to the player
camera_target = camera_offset # Where the camera is lerping to
current_camera = camera_offset # Where the camera is currently

# Level Editing
editing_level = False
min_shapes = 0
max_shapes = 100
brown = (127,81,18)
green = (34, 139, 34)
paint_color = brown
polygon_widths = 0
mouse_polygon = None
premade_polygons = [
    Polygon([(0,0),(0,50),(50,50),(50,0)], (100,100,100),1),
    Polygon([(0,0),(0,50),(100,50),(100,0)], (100,100,100),1),
    Polygon([(0,0),(0,50),(500,50),(500,0)], (100,100,100),1),    
    Polygon([(0,0),(-28.868,50),(28.868,50)], (100,100,100),1),
    Polygon([(0,0),(0,25),(50,25)], (100,100,100),1),
    Polygon([(0,0),(0,50),(50,50)], (100,100,100),1),
    Polygon([(0,0),(0,50),(25,50)], (100,100,100),1)
]
for poly in premade_polygons:
    poly.mass = math.inf
    poly.color = (34, 139, 34)
    poly.width = 3
cur_poly_index = 0

coeff_of_friction = 0.8

# Timing Set up
fps = 60
dt = 1/fps
clock = pygame.time.Clock()

# Player Variables
player = Player(pos = (100, 300), radius = 20, mass = 1, speed = 2.5)
player_overlapping = False
fliesCollected = 0

objects = [] 
gravity_objects = [player]

flies_coords = [(200,300),(-122, 479),(-261, -92),(717, -484),(-194, -732),(729,-991),(-149,-1388),(362,-1799),(-614,-2270),(-2815,486),
(-914,461),(-2163,-52),(-3042,-528),(-3055,-73),(-2980,-1170),(-1244,-1127),(-1406,-1934),(-1768,-2989),(-2055,-2844),(-2346,-2723),(-2336,-3055),(-3020,-2850),(729,-2094),]
flies = []
for fly_coord in flies_coords:
    flies.append(Fly(pos = fly_coord, radius = 20, mass = 0.1, speed = 1, color = (0, 255, 0)))
total_flies = len(flies)


enemies_coords = [(-200,17),(731,-1230),(-1041,539),(-2713,537)]
enemies = []
for enemy_coord in enemies_coords:
    enemies.append(Enemy(pos = enemy_coord, radius = 30, mass = 1, speed = 0.5, spritePath = "Beetle.png"))
#enemies.append(Enemy(pos = (400, 300), radius = 30, mass = 1, speed = 0.5, spritePath = "Beetle.png"))
for i in enemies:
    gravity_objects.append(i)

# Build Level
floor = Wall((800,500), (0, 500), color=(0,255,0), normals_length = 10)
goal = Circle(radius=110, color=(50, 205, 50), pos=(3590,955))
check_points = []
cur_checkpoint = 0
check_points.append(Circle(radius=30,color=(255,255,0), pos=Vector2(230,537)))
check_points.append(Circle(radius=40,color=(255,255,0), pos=Vector2(-727,-2183)))

death = []
death.append(Circle(radius=40, color=(255,45,0), pos=(2953.17,876.63)))
death.append(Circle(radius=40, color=(255,45,0), pos=(3394.17,900.63)))
death.append(Circle(radius=20, color=(255,45,0), pos=(3739.5,1313.5)))
death.append(Circle(radius=40, color=(255,45,0), pos=(1710,62)))
for o in [goal] + check_points + death:
    o.width = polygon_widths

background = pygame.image.load('Background.png').convert_alpha()
background = pygame.transform.scale(background, (width * 1.5, height * 1.5))

# FILE LOAD SYSTEM
#open(level_file_name, "a")
#file = open(level_file_name, "r") #"w" write over, "a" append, "r" read, "x" create (will error if already exists)
with open(level_file_name, 'r', errors='ignore') as json_file:
    data = json.load(json_file)
#data = json.load(open(level_file_name))
# try:
#     with open(level_file_name) as json_file:
#         file_contents = json_file.read()
#         print(file_contents)
# except FileNotFoundError:
#     print(f"File not found: {level_file_name}")
# except Exception as e:
#    print(f"An error occurred: {e}")
polygons = []
for item in data:
    local_points = [pygame.Vector2(point["x"], point["y"]) for point in item["local_points"]]
    color = (item["color"]["r"], item["color"]["g"], item["color"]["b"])
    pos = pygame.Vector2(item["pos"]["x"],item["pos"]["y"])
    polygons.append(Polygon(
        local_points=local_points, 
        color=color,
        pos=pos,
        angle=item['angle'],
        mass = math.inf
        ))
for poly in polygons:
    poly.width = polygon_widths

jump_charge = 0
start_jump = False

fallThrough = False

# forces
gravity = Gravity(acc=[0,9.8], objects_list=gravity_objects)


web = Web(gravity_acc=[0,0])
grappleweb_proj_spider = None
grappleweb_proj_line = None # The line connecting the spider to the proj hook
grappleweb_proj_hook = None # The temporary projectile that flies out when grapplewebbing

grappleweb_spider = None # The web joint connected to the spider
grappleweb_line : WebLine = None # The line connecting the spider to the current hook
grappleweb_hook = None
grappleweb_hooked_line = None
grappleweb_length = None
grappleweb_lerp_point = 0

# game loop
running = True
while running:
    # update the display
    pygame.display.update()
    # delay for correct timing
    clock.tick(fps)
    # clear the screen
    window.fill([34, 139, 34])
    window.blit(background, current_camera / 10 - (width / 3, height / 3))


    # EVENTS
    while event := pygame.event.poll():
        # Quit
        if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False
        # Shoot grapple web
        if (event.type == MOUSEBUTTONDOWN or (event.type == KEYDOWN and event.key == K_e)) and not grappleweb_proj_hook:
            mouse_pos = pygame.mouse.get_pos() - current_camera
            old_grappleweb_spider = grappleweb_spider
            grappleweb_spider = WebJoint(pos=Vector2(player.pos + Vector2(0.1,0.1)), locked = False)
            if grappleweb_line: 
                # Update the current grappleweb variables
                grappleweb_hook.connected_joints.remove(old_grappleweb_spider)
                grappleweb_hook.connected_joints.append(grappleweb_spider)
                grappleweb_line.joints = [grappleweb_spider, grappleweb_hook]
                grappleweb_spider.connected_joints = [grappleweb_hook]
                grappleweb_spider.connected_lines = [grappleweb_line]
            grappleweb_proj_hook = WebJoint(pos=player.pos, locked = False, connected_joints=[grappleweb_spider])
            grappleweb_proj_hook.vel = ((mouse_pos - grappleweb_proj_hook.pos).normalize() * 1500 / pixels_per_meter)
            grappleweb_proj_line = WebLine([grappleweb_proj_hook, grappleweb_spider])
        
        if event.type == KEYDOWN and event.key == K_EQUALS:
            web.add_joint(WebJoint(pos=pygame.mouse.get_pos() - current_camera, connected_joints=web.web_joints, locked=True))
        if event.type == KEYDOWN and event.key == K_MINUS:
            web.add_joint(WebJoint(pos=pygame.mouse.get_pos() - current_camera, connected_joints=web.web_joints, locked=False))

        if(event.type == KEYDOWN and (event.key == K_s or event.key == K_DOWN)):
            fallThrough = True
        elif(event.type == KEYUP and (event.key == K_s or event.key == K_DOWN)):
            fallThrough = False

        if grappleweb_hook:
            # Lock grappleweb to ground
            if event.type == KEYDOWN and (event.key == K_s or event.key == K_DOWN):
                # If the grappleweb is connected to two things, add it to the web
                if grappleweb_hook.vel == Vector2(0,0) and player_overlapping and grappleweb_spider.pos.distance_to(grappleweb_hook.pos) > 50:
                    grappleweb_hook.connected_joints = grappleweb_hook.connected_lines = []
                    grappleweb_hook.generate_lines() #<???
                    #TODO what is the intention here? Just refreshing the connections? <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    web.add_joint(grappleweb_hook)
                    grappleweb_spider.connected_lines, grappleweb_spider.connected_joints = [grappleweb_line], [grappleweb_hook]
                    standing_on_line = None
                    web_check = Circle(pos=player.pos+Vector2(0,1), radius=player.radius)
                    for line in web.web_lines:
                        c = contact.generate(web_check, line, resolve=False)
                        if c.overlap >= 0:
                            standing_on_line = line
                            grappleweb_spider.pos=c.point()
                            break
                    
                    if standing_on_line:
                        # Connect the web to pre-existing web
                        grappleweb_spider.locked=False
                        web.add_joint_to_line(grappleweb_spider, standing_on_line)
                        web.web_lines.append(grappleweb_line)
                    else:
                        # Connect the web to the ground
                        web.add_joint(grappleweb_spider)
                        grappleweb_spider.locked = True
                        grappleweb_spider.pos += Vector2(0, player.radius)
                    grappleweb_line.length = grappleweb_spider.pos.distance_to(grappleweb_hook.pos) * 0.9
                    web.update_bonds()
                elif len(grappleweb_hook.connected_lines) > 1:
                    grappleweb_hook.connected_joints.remove(grappleweb_spider)
                    grappleweb_hook.connected_lines.remove(grappleweb_line)
                    web.remove_joint(grappleweb_hook, merge_lines=True)
                grappleweb_hook = None
                grappleweb_line = None
                grappleweb_spider = WebJoint(pos=Vector2(player.pos + Vector2(0.1,0.1)), locked = False)
                grappleweb_hooked_line = grappleweb_proj_hook = grappleweb_proj_line = None
                
        if event.type == KEYDOWN and event.key == K_DELETE:
            web.web_joints = []
            web.web_lines = []
        if event.type == KEYDOWN and event.key == K_RETURN:
            point = pygame.mouse.get_pos() - current_camera
            print("(" + str(point[0]) + "," + str(point[1]) + "),")
        
        # Toggle Editing
        if event.type == KEYDOWN and event.key == K_TAB:
            if editing_level:
                mouse_polygon = None
            else:
                mouse_polygon = premade_polygons[cur_poly_index].copy()
            editing_level = not editing_level
        # Checkpoint teleport
        if event.type == KEYDOWN:
            c_i = 0
            if event.key == K_1:
                c_i = 1
            if event.key == K_2:
                c_i = 2
            if c_i != 0:
                player.pos = Vector2(check_points[c_i - 1].pos)
                player.vel = Vector2(0,0)
                grappleweb_hook = None
                grappleweb_line = None
                grappleweb_proj_hook = None
                grappleweb_proj_line = None
                grappleweb_hooked_line = None 
        # Level editor events
        if event.type == KEYDOWN and editing_level:
            if event.key == K_b:
                paint_color = brown
            if event.key == K_g:
                paint_color = green

            # Cycle shape left
            if event.key == K_a:
                cur_poly_index -= 1
                if cur_poly_index < 0:
                    cur_poly_index += len(premade_polygons)
                mouse_polygon = premade_polygons[cur_poly_index].copy()
            # Cycle shape right
            if event.key == K_d:
                cur_poly_index += 1
                if cur_poly_index >= len(premade_polygons):
                    cur_poly_index -= len(premade_polygons)
                mouse_polygon = premade_polygons[cur_poly_index].copy()
            # Place shape
            if event.key == K_r and mouse_polygon and len(polygons) < max_shapes:
                new_polygon = mouse_polygon.copy()
                new_polygon.width = polygon_widths
                new_polygon.color = paint_color
                polygons.append(new_polygon)
            # Undo shape
            if event.key == K_BACKSPACE and len(polygons) > min_shapes:
                polygons.pop(len(polygons)-1)
            # Save level
            if event.key == K_t:
                # Compile polygon data
                polygons_data = []
                for polygon in polygons:
                    polygon_data = { 
                        #item['local_points'], item['color'], item['width'],item['pos'],item['angle']
                        "local_points": [{"x": point.x, "y": point.y} for point in polygon.local_points],
                        "color": {"r": polygon.color[0], "g": polygon.color[1], "b": polygon.color[2]},
                        "pos": {"x": polygon.pos.x, "y": polygon.pos.y},
                        "angle" : polygon.angle
                    }
                    polygons_data.append(polygon_data)
                # Write data to json file
                with open(level_file_name, 'w') as json_file:
                    json.dump(polygons_data, json_file, indent=4)

    # CONTROLS
    key = pygame.key.get_pressed()
    # Level Editing
    if mouse_polygon:
        if key[K_q]:
            mouse_polygon.angle -= dt * 45
        if key[K_e]:
            mouse_polygon.angle += dt * 45
        if key[K_w]:
            mouse_polygon.resize((1 + 2 * dt))
        if key[K_s]:
            mouse_polygon.resize(1/(1 + 2 * dt))
    # Jumping
    if key[K_SPACE] and jump_charge < 0.25:
        jump_charge = min(jump_charge + dt, 0.25)
    elif jump_charge > 0 and player_overlapping:   
        start_jump = True
    elif not key[K_SPACE] and jump_charge > 0:
        jump_charge = 0
    jc = jump_charge / 0.25
    player.color = (255, jc * 255,0)
    # Movement
    moveDir = Vector2(0, 0)
    if key[K_LEFT] or key[K_a]:
        moveDir += Vector2(-1, 0)
    if key[K_RIGHT] or key[K_d]:
        moveDir += Vector2(1, 0)
    player.move(moveDir, dt)
    # Grappleweb
    if grappleweb_hook and (grappleweb_hook.vel == Vector2(0,0) or not grappleweb_hook.locked):
        # Climb up grappleweb
        if key[K_w] or key[K_UP]:
            if player.pos.distance_to(grappleweb_hook.pos) > 10:
                player.vel += Vector2((grappleweb_hook.pos - player.pos).normalize() * 15 * dt)
                grappleweb_length = min(player.pos.distance_to(grappleweb_hook.pos), grappleweb_length)

            if player.pos.distance_to(grappleweb_hook.pos) > grappleweb_length:
                line_vec = (player.pos - grappleweb_hook.pos).normalize()
                player.pos = grappleweb_hook.pos + line_vec * grappleweb_length

        # Prevent sliding down
        elif player.pos.distance_to(grappleweb_hook.pos) >= grappleweb_length:
            line_vec = (player.pos - grappleweb_hook.pos).normalize()
            player.pos = grappleweb_hook.pos + line_vec * grappleweb_length
            line_vec.rotate_ip(90)
            player.vel = line_vec.dot(player.vel) * line_vec
        # Update grappleweb to smallest length
        else:
            grappleweb_length = min(player.pos.distance_to(grappleweb_hook.pos), grappleweb_length)
    if grappleweb_hooked_line:
        v1 = grappleweb_hooked_line.joints[0].pos
        v2 = grappleweb_hooked_line.joints[1].pos
        #grappleweb_hook.pos = v1.lerp(v2, grappleweb_lerp_point) # Shouldn't be included, but was stabilizing it actually


    # PHYSICS
    # Clear Forces
    for o in objects + [player] + enemies:
        o.clear_force()
    web.clear_force()
    # Gravity
    gravity.apply()
    web.gravity.apply()
    web.bonds.apply()
    for poly in polygons:
        poly.avel = 0

    # UPDATES
    for o in objects + [player]:
        o.update(dt)
    for i in enemies:
        i.update(dt, player.pos)
    if grappleweb_spider:
        grappleweb_spider.pos = player.pos
    if grappleweb_hook: 
        grappleweb_hook.update(dt)
        grappleweb_line.update(dt)
    if grappleweb_proj_hook:
        grappleweb_proj_hook.update(dt)
        grappleweb_proj_line.update(dt)
        if grappleweb_proj_hook.pos.distance_to(player.pos) > 1000:
            if grappleweb_proj_line in grappleweb_spider.connected_lines: grappleweb_spider.connected_lines.remove(grappleweb_proj_line)
            grappleweb_proj_hook = None
            grappleweb_proj_line = None
    web.update(dt)

    # COLLISIONS
    if start_jump:
        jump_rebound = 2 * jump_charge / 0.25 + 2.25
    else:
        jump_rebound = 0
    player_overlapping = False
    # Player and Level Collisions
    floorNormals = []
    for o in (objects + polygons):
        c = contact.generate(player,o,resolve=False, restitution=0.2, friction=coeff_of_friction)
        c.update()
        if c.overlap > 0:
            #if o in polygons and not hasattr(c, "index"):
                #print(c.overlap, c.normal)
            if(o in polygons):# and hasattr(0, "index")):
                point1 = c.b.points[c.index]
                point2 = c.b.points[c.index - 1]
                polyNormal = (point2 - point1).normalize().rotate(90)
                floorNormals.append(polyNormal)
                player_overlapping = True
                if start_jump:
                    jump_charge = 0                
        c.resolve(update=False, rebound=jump_rebound)
    for fly in flies:
        if Vector2(player.pos - fly.pos).magnitude() < player.radius * 1.5:
            flies.remove(fly)
            fliesCollected += 1
        fly.update(dt)

    for wl in web.web_lines:
        c = contact.generate(wl, player, resolve=False, restitution=0.0, friction=3.0)
        # Get the normal of the web line
        polyNormal = (wl.points[0] - wl.points[1]).normalize().rotate(90)
        # Check to make sure that we are using the upright normal
        if polyNormal.dot(Vector2(0,-1)) > 0:
            polyNormal *= -1
        slope = (wl.points[1].y - wl.points[0].y) / (wl.points[1].x - wl.points[0].x)
        yintercept = wl.points[0].x * -slope + wl.points[0].y
        if(player.pos.y <= slope * player.pos.x + yintercept and not fallThrough):
            # Add any overlapping weblines to possible floor normals
            if(c.overlap > 0):
                player_overlapping = True
                if start_jump:
                    jump_charge = 0
                floorNormals.append(polyNormal)
            c.update()
            c.resolve(update=False, rebound=jump_rebound)

    # Preference for walking on the most level floor
    currentFloorNormal = Vector2(0, 0)
    for i in floorNormals:
        if( abs( (i - Vector2(0, 1)).magnitude() ) < abs( (currentFloorNormal - Vector2(0, 1)).magnitude() ) ):
            currentFloorNormal = i
    player.floorNormal = currentFloorNormal
    #if(player.floorNormal != Vector2(0, 0)):
    #    player.vel += Vector2(0, -9.7) / player.mass * dt
    
    # Grapplehook Web Collisions
    if grappleweb_proj_hook and grappleweb_spider.pos.distance_to(grappleweb_proj_hook.pos) > 50:
        for o in polygons + web.web_lines:
            c = contact.generate(grappleweb_proj_hook, o, resolve=False)
            if c.overlap > 0:
                if grappleweb_hook and len(grappleweb_hook.connected_lines) > 1: #TODO <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    #TODO the bug is when you try to connect to a line that was split by the first hook
                    grappleweb_hook.connected_joints.remove(grappleweb_spider)
                    grappleweb_hook.connected_lines.remove(grappleweb_line)
                    web.remove_joint(grappleweb_hook, merge_lines=True)
                # Connect to the web line if it is a web
                if isinstance(o, WebLine):
                    grappleweb_hooked_line = o
                    j1 = grappleweb_hooked_line.joints[0].pos
                    j2 = grappleweb_hooked_line.joints[1].pos
                    v1 = j2 - j1
                    v2 = grappleweb_proj_hook.pos - j1
                    grappleweb_lerp_point = v2.dot(v1.normalize()) / v1.magnitude()
                else:
                    grappleweb_hooked_line = None

                # Lock the hook
                grappleweb_proj_hook.vel= Vector2(0,0)
                grappleweb_proj_hook.locked = True 

                


                # Promote proj grapple web into the connected variables
                grappleweb_hook = grappleweb_proj_hook
                grappleweb_line = grappleweb_proj_line
                grappleweb_line.color = (255,255,255)
                grappleweb_length = player.pos.distance_to(grappleweb_hook.pos)  
                grappleweb_hook.connected_lines = [grappleweb_line]
                grappleweb_line.joints = [grappleweb_spider, grappleweb_hook]
                # Clear the proj variables
                grappleweb_proj_hook = None
                grappleweb_proj_line = None

                if grappleweb_hooked_line:
                    web.add_joint_to_line(grappleweb_hook, grappleweb_hooked_line)
                break

    # Objects and Polygons Collisions
    for o in objects + enemies:
        for p in polygons:
            c = contact.generate(o, p, resolve=False, restitution=0.2, friction=coeff_of_friction)
            c.update()
            c.resolve(update=False)

    if not player_overlapping and start_jump:
        start_jump = False
    
    camera_target = -player.pos + camera_offset
    r = camera_target - current_camera
    current_camera = current_camera + r * 0.1

    # GRAPHICS    
    # Background

    # Grapplehook web
    if grappleweb_hook:
        #grappleweb_hook.draw(window, current_camera)
        grappleweb_line.draw(window, current_camera)
    if grappleweb_proj_hook:
        #grappleweb_proj_hook.draw(window, current_camera)
        grappleweb_proj_line.draw(window, current_camera)

    # Web
    web.draw(window, current_camera)
    for joint in web.web_joints:
        text = str(len(joint.connected_joints))
        label = font.render(text, False, (255,25,255), None)
        pos = Vector2(joint.pos + current_camera)
        window.blit(label, pos) #DEBUG

    # Unique level objects
    for o in [goal] + check_points + death:
        o.draw(window,current_camera) 

    # Level and player
    for o in objects + polygons + enemies + flies + [player]:
        o.draw(window, current_camera)

    # Mouse polygon
    if mouse_polygon:
        mouse_polygon.pos = Vector2(pygame.mouse.get_pos()) - current_camera
        mouse_polygon.update(dt)
        mouse_polygon.draw(window, current_camera)

    # Editor text
    if editing_level:
        pygame.draw.rect(window,(255,0,0),((0,0),(width,height)),10)
        text = "A/D: Cycle through shapes   W/S: Resize    Q/E: Rotate   R: Place    F: Clear    Backspace: Undo    T: Save"
        label = font.render(text, False, (100,200,200), None)
        pos = Vector2(width / 2 - label.get_width()/ 2, height - 20 - label.get_height())
    else:
        text = "Press TAB to toggle editing mode"
        text = ""
        label = font.render(text, False, (100,200,200), None)
        pos = Vector2(20,height - 20 - label.get_height())
        
    window.blit(label, pos)

    # Interactables
    hitCheckpoint = False
    for c in check_points:
        check_contact = contact.generate(player,c,resolve=False)
        check_contact.update()
        if check_contact.overlap > 0:
            cur_checkpoint = check_points.index(c)
            hitCheckpoint = True

    if(not hitCheckpoint):
        for d in death + enemies:
            death_contact = contact.generate(player, d, resolve=False)
            death_contact.update()
            if death_contact.overlap > 0:
                grappleweb_hook = None
                grappleweb_line = None
                grappleweb_proj_hook = None
                grappleweb_proj_line = None
                grappleweb_hooked_line = None # <- May cause issues later
                player.pos = Vector2(check_points[cur_checkpoint].pos)
                player.vel = Vector2(0,0)

    pygame.draw.rect(window, (140,255,25),((0,0),(350,80)))

    flyLabel = font.render(f"Flies Collected: {fliesCollected} / {total_flies}", False, (77,77,255), None)
    window.blit(flyLabel, Vector2(20, 20))


    text = "WASD:move, CLICK:shoot web, S:cut/connect grapple, DELETE:reset webs"
    label = font.render(text, False, (255,25,255), None)
    pos = Vector2(width / 2 - label.get_width()/ 2, height - label.get_height() - 20)
    window.blit(label, pos)

    if len(flies) == 0:
        flyLabel = font.render("All flies collected!", False, (77,77,255), None)
        window.blit(flyLabel, Vector2(20, 40))

    # Endless Pit Death
    if player.pos.y > 2000:
        player.pos = Vector2(check_points[cur_checkpoint].pos)
        player.vel = Vector2(0,0)
        current_camera = Vector2(0,0)

    #DEBUG vvv
    #pygame.draw.line(window, (255,255,0),(player.pos + current_camera),(player.pos + current_camera + player.vel * 20), width=3)

    #surface = pygame.Surface((width/2,height/2))
    #pygame.transform.scale(window,(width / 2,height/2), surface)
    #window.blit(surface, (0,0))