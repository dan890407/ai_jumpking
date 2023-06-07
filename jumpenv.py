import gym
from gym import spaces
import numpy as np
# ... include your imports here ...
import pygame
import random
import sys

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SCROLL_THRESH = 200
GRAVITY = 1
MAX_PLATFORMS = 10
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PANEL = (153, 217, 234)
FPS = 60
# define font



class Player():
    def __init__(self, x, y,image, sc):
        self.image = pygame.transform.scale(image, (45, 45))
        self.width = 25
        self.height = 40
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.vel_y = 0
        self.flip = False
        self.sc = sc
        self.first=True
        self.maxheight=0
    def move(self, action,platform_group):
		# reset variables
        scroll = 0
        dx = 0
        dy = 0
        if action == 0:
            dx = -10
            self.flip = True
        if action == 1:
            dx = 10
            self.flip = False

		# gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # ensure player doesn't go off the edge of the screen
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > SCREEN_WIDTH:
            dx = SCREEN_WIDTH - self.rect.right

		# check collision with platforms
        for platform in platform_group:
            # collision in the y direction
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if above the platform
                if self.rect.bottom < platform.rect.centery:
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = -20

        # check if the player has bounced to the top of the screen
        if self.rect.top <= SCROLL_THRESH:
            # if player is jumping
            if self.vel_y < 0:
                scroll = -dy
                self.first=False
            elif self.vel_y==0:
                self.point=self.rect.y

        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy + scroll
        point=0
        if 600-self.rect.y>self.maxheight:
            point = 600-self.rect.y-self.maxheight
            self.maxheight=600-self.rect.y
        # update mask
        self.mask = pygame.mask.from_surface(self.image)

        return scroll,point,self.first

    def draw(self):
        self.sc.blit(pygame.transform.flip(self.image, self.flip, False),
                    (self.rect.x - 12, self.rect.y - 5))

# platform class


class Platform(pygame.sprite.Sprite):
	def __init__(self, x, y, width, moving,image):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.transform.scale(image, (width, 30))
		self.moving = moving
		self.move_counter = random.randint(0, 50)
		self.direction = random.choice([-1, 1])
		self.speed = random.randint(1, 2)
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

	def update(self, scroll):
		# moving platform side to side if it is a moving platform
		if self.moving == True:
			self.move_counter += 1
			self.rect.x += self.direction * self.speed

		# change platform direction if it has moved fully or hit a wall
		if self.move_counter >= 100 or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
			self.direction *= -1
			self.move_counter = 0

		# update platform's vertical position
		self.rect.y += scroll

		# check if platform has gone off the screen
		if self.rect.top > SCREEN_HEIGHT:
			self.kill()

class JumpyGameEnv(gym.Env):
    """
    Custom Environment that follows gym interface.
    This is a simple env where the agent must learn to go always left.
    """

    def __init__(self):
        super(JumpyGameEnv, self).__init__()

        # Set the action and observation space
        # They must be gym.spaces objects
        # Example when using discrete actions, Box for continuous action
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(SCREEN_WIDTH, SCREEN_HEIGHT,  3), dtype=np.uint8)

        # game variable
        self.scroll = 0
        self.bg_scroll = 0
        self.game_over = False
        self.score = 0
        self.fade_counter = 0
        self.high_score = 0

        # Define the game here...
        # self.game = ...
        pygame.init()
        # create game window
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Jumpy')
        # set frame rate
        self.clock = pygame.time.Clock()
        #set fonts and images
        self.font_small = pygame.font.SysFont('Lucida Sans', 20)
        self.font_big = pygame.font.SysFont('Lucida Sans', 24)

        # load images
        self.jumpy_image = pygame.image.load('assets/jumping.png').convert_alpha()
        self.bg_image = pygame.image.load('assets/forest.jpg').convert_alpha()
        self.platform_image = pygame.image.load('assets/wood.png').convert_alpha()

        # initial objects
        self.jumpy = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150,self.jumpy_image,self.screen)

        # create sprite groups
        self.platform_group = pygame.sprite.Group()

        # create starting platform
        self.platform = Platform(SCREEN_WIDTH // 2 - 50,
                            SCREEN_HEIGHT - 50, 100, False,self.platform_image)
        self.platform_group.add(self.platform)
        # reward first phase
        self.firstmap = True
        self.firstreward = 0

    def step(self, action):
        self.scroll,pt,first = self.jumpy.move(action,self.platform_group)

		#draw background
        self.bg_scroll += self.scroll
        if self.bg_scroll >= 600:
            self.bg_scroll = 0
        else:
            if self.firstmap == True:
                pass

        #generate platforms
        if len(self.platform_group) < MAX_PLATFORMS:
            p_w = random.randint(40, 60)
            p_x = random.randint(0, SCREEN_WIDTH - p_w)
            p_y = self.platform.rect.y - random.randint(80, 120)
            p_type = random.randint(1, 2)
            if p_type == 1 and self.score > 500:
                p_moving = True
            else:
                p_moving = False
            self.platform = Platform(p_x, p_y, p_w, p_moving,self.platform_image)
            self.platform_group.add(self.platform)

        #update platforms
        self.platform_group.update(self.scroll)

        #update score
        if self.scroll > 0:
            self.score += self.scroll
        if first==True:
            self.score+=pt
        #firstmap
        self.score+=self.firstreward
        #check game over
        if self.jumpy.rect.top > SCREEN_HEIGHT:
            self.game_over = True
        #reward
        reward=self.score
        #observation space
        observation = pygame.surfarray.array3d(pygame.display.get_surface())
        observation = observation.astype('float32') / 255.0

        return observation, reward, self.game_over, {}

    def reset(self):
        """
        Reset the state of the environment to an initial state.
        """
        print("reset")
        self.game_over = False
        self.score = 0
        self.scroll = 0 
        #reposition jumpy
        self.jumpy.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        self.jumpy.first=True
        self.jumpy.maxheight=0
        #reset platforms
        self.platform_group.empty()
        #create starting platform
        self.platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50, 100, False,self.platform_image)
        self.platform_group.add(self.platform)
        observation = pygame.surfarray.array3d(pygame.display.get_surface())
        observation = observation.astype('float32') / 255.0

        return observation
    
    def render(self, mode='human'):

        #draw sprites
        self.draw_bg(self.bg_scroll)
        self.platform_group.draw(self.screen)
        self.jumpy.draw()

        #draw panel
        self.draw_panel()
        # Refresh game screen
        pygame.display.update()
        # Refresh rate
        self.clock.tick(FPS)
    def close(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def draw_panel(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, SCREEN_WIDTH, 30))
        pygame.draw.line(self.screen, WHITE, (0, 30), (SCREEN_WIDTH, 30), 2)
        img = self.font_small.render('SCORE: ' + str(self.score), True, WHITE)
        self.screen.blit(img, (0, 0))

    def draw_text(self,text, font, text_col, x, y):
        img = font.render(text, True, text_col)
        self.screen.blit(img, (x, y))

    #function for drawing info panel
    def draw_panel(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, SCREEN_WIDTH, 30))
        pygame.draw.line(self.screen, WHITE, (0, 30), (SCREEN_WIDTH, 30), 2)
        self.draw_text('SCORE: ' + str(self.score), self.font_small, WHITE, 0, 0)


    #function for drawing the background
    def draw_bg(self,bg_scroll):
        self.screen.blit(self.bg_image, (0, 0 + bg_scroll))
        self.screen.blit(self.bg_image, (0, -600 + bg_scroll))

from stable_baselines3 import PPO
env=JumpyGameEnv()

print(type(env.action_space))

"""episodes = 10

for ep in range(episodes):
    obs = env.reset()
    done = False
    while not done:
        env.render()
        obs, reward, done, info =env.step(env.action_space.sample())
env.close()"""
episodes = 10

for ep in range(episodes):
    obs = env.reset()
    done = False
    while not done:
        env.render()
        obs, reward, done, info = env.step(env.action_space.sample())
env.close()