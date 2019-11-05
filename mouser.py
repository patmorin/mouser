"""Some simple skeleton code for a pygame game/animation

This skeleton sets up a basic 800x600 window, an event loop, and a
redraw timer to redraw at 30 frames per second.
"""
import math
import sys
import pygame
import random
import itertools

from enum import Enum


(width, height) = (1920, 1080)

def distance(p, q):
    return math.sqrt(sum([(p[i]-q[i])**2 for i in range(2)]))

class cat_state(Enum):
    NEUTRAL = 0
    LEFT = -1
    RIGHT = +1

def draw_at(img, pos, screen):
    rect = img.get_rect()
    rect = rect.move(pos[0]-rect.width//2, pos[1]-rect.height)
    screen.blit(img, rect)

class Platform(object):
    def __init__(self, rect):
        self.rect = rect

    def draw_on(self, screen):
        pygame.draw.rect(screen, (255,0,0), self.rect, 3)

    def is_under(self, pos):
        x,y = pos
        return self.rect.left <= x and self.rect.right >= x \
            and self.rect.bottom >= y and self.rect.top - y <= 20

class GameObject(object):
    def __init__(self, pos):
        self.pos = pos

    def draw_on(self, screen):
        img = self.image
        draw_at(img, self.pos, screen)

class Animal(GameObject):
    def __init__(self, pos, dx, dy):
        super().__init__(pos)
        self.dx, self.dy = dx, dy

    def update(self):
        self.pos = self.pos[0]+self.dx, self.pos[1]+self.dy
        rect = self.image.get_rect()
        if self.pos[0] + rect.width//2 > width:
            self.dx = -abs(self.dx)
        elif self.pos[0] - rect.width//2 < 0:
            self.dx = abs(self.dx)

    def draw_on(self, screen):
        img = self.image
        if self.dx > 0:
            img = pygame.transform.flip(img, True, False)
        draw_at(img, self.pos, screen)

class Portal(GameObject):
    def __init__(self, pos):
        super().__init__(pos)

    def draw_on(self, screen):
        colour = (128, 128, 128)
        w = 40
        h = 80
        rect = pygame.Rect(self.pos[0]-w//2, self.pos[1]-h, w, h)
        pygame.draw.rect(screen, colour, rect, 0)



class Mouse(Animal):
    mouse_image = pygame.image.load('images/mouse.png')
    rect = mouse_image.get_rect()
    scale = width/(20*rect.width)
    mouse_image = pygame.transform.smoothscale(mouse_image, (int(rect.width*scale), int(rect.height*scale)))

    splat_image = pygame.image.load('images/splat.png')
    rect = splat_image.get_rect()
    scale = width/(20*rect.width)
    splat_image = pygame.transform.smoothscale(splat_image, (int(rect.width*scale), int(rect.height*scale)))

    def __init__(self, pos, dx):
        super().__init__(pos, dx, 0)
        self.image = self.mouse_image
        self.afterdeath = -1

    def kill(self):
        self.afterdeath = 0
        self.dx = 0
        self.image = self.splat_image

    def update(self):
        if self.afterdeath >= 0:
            self.afterdeath += 1
        else:
            super().update()


class Cat(Animal):
    cat_image = pygame.image.load('images/cat1.png')
    rect = cat_image.get_rect()
    scale = width/(15*rect.width)
    cat_image = pygame.transform.smoothscale(cat_image, (int(rect.width*scale), int(rect.height*scale)))
    cat_image = pygame.transform.flip(cat_image, True, False)

    def __init__(self, pos):
        super().__init__(pos, 0, 0)
        self.image = self.cat_image


class MyGame(object):
    def __init__(self):
        """Initialize a new game"""
        pygame.mixer.init()
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()

        # set up a 640 x 480 window
        self.width = 1920
        self.height = 1080
        self.screen = pygame.display.set_mode((self.width, self.height))

        # Setup any internal variables and load any resources
        self.bg_color = 200, 200, 255

        # Create a cat
        self.cat = Cat((self.width//2, self.height))

        # Load sound effects
        self.splat_sound = pygame.mixer.Sound('sounds/splat.wav')

        # Play soundtrack
        pygame.mixer.music.load('audio/soundtrack.wav')
        pygame.mixer.music.set_volume(1/2)
        pygame.mixer.music.play(loops=-1)
        self.mice = set()

        # Create platforms
        self.platforms = list()
        self.portals = list()
        self.portals.append(Portal((30, height)))
        self.platforms.append(Platform(pygame.Rect(0,height,width,20)))
        self.portals.append(Portal((230, 400)))
        self.platforms.append(Platform(pygame.Rect(200,400,400,20)))
        self.portals.append(Portal((1250, 800)))
        self.platforms.append(Platform(pygame.Rect(800,800,500,20)))
        self.portals.append(Portal((1450, 800)))
        self.platforms.append(Platform(pygame.Rect(1400,800,500,20)))

        # Setup a timer to refresh the display FPS times per second
        self.FPS = 30
        self.REFRESH = pygame.USEREVENT+1
        pygame.time.set_timer(self.REFRESH, 1000//self.FPS)


    def run(self):
        """Loop forever processing events"""
        running = True
        while running:
            event = pygame.event.wait()
            # player is asking to quit
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LSHIFT:
                    if self.cat.dy == 0:
                        self.cat.dy = -30
            # time to draw a new frame
            elif event.type == self.REFRESH:
                self.update()
                self.draw()

            else:
                pass # an event type we don't handle

    def update(self):
        # Check for left/right cat movement
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.cat.dx = -10
        elif pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.cat.dx = 10
        else:
            self.cat.dx = 0

        self.cat.update()

        for animal in list(self.mice) + [self.cat]:
            supported = False
            for platform in self.platforms:
                if animal.dy >= 0 and platform.is_under(animal.pos):
                    animal.dy = 0
                    animal.pos = animal.pos[0], platform.rect.top
                    supported = True
            if not supported:
                animal.dy += 1  # gravity

        # generate a new mouse?
        if random.random() < (1/3)/self.FPS:
            portal = random.choice(self.portals)
            self.mice.add(Mouse(portal.pos, random.choice([-5, 5])))

        rotten = list()
        for mouse in self.mice:
            mouse.update()
            if mouse.afterdeath > self.FPS:
                rotten.append(mouse)
            elif mouse.afterdeath < 0 and distance(self.cat.pos, mouse.pos) < 30:
                mouse.kill()
                self.splat_sound.play()

        for mouse in rotten:
            self.mice.remove(mouse)


    def draw(self):
        """Draw the next frame"""
        # everything we draw now is to a buffer that is not displayed
        self.screen.fill(self.bg_color)

        for obj in itertools.chain(self.portals, self.platforms, self.mice, [self.cat]):
            obj.draw_on(self.screen)

        # flip buffers so that everything we have drawn gets displayed
        pygame.display.flip()


game = MyGame()
game.run()
pygame.quit()
sys.exit()
