import gym
from gym import spaces
import numpy as np
# ... include your imports here ...
import pygame
import random
import sys
import math

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
        self.hit=False
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
        self.penalty=0
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
        self.penalty=0
		# check collision with platforms
        self.hit=False
        for platform in platform_group:
            # collision in the y direction
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if above the platform
                if self.rect.bottom < platform.rect.centery:
                    self.hit=True
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = -20
                    if platform.touched == True:
                        self.penalty=-50
                    if platform.touched == False:
                        platform.touched = True
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

        return scroll,point,self.first,self.penalty,self.hit

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
		self.touched = False
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
        self.observation_space = spaces.Box(low=0, high=max(SCREEN_WIDTH, SCREEN_HEIGHT),
                                            shape=(MAX_PLATFORMS + 1, 2), dtype=np.float32)
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
        self.clock = pygame.time.Clock()
        # set frame rate
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
        self.scroll,pt,first,pen, hit= self.jumpy.move(action,self.platform_group)

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
        #draw sprites
        self.draw_bg(self.bg_scroll)
        self.platform_group.draw(self.screen)
        self.jumpy.draw()

        #check game over
        if self.jumpy.rect.top > SCREEN_HEIGHT or self.score>10000:
            self.game_over = True
            if self.jumpy.rect.top > SCREEN_HEIGHT:   
                self.score += -500
            if self.score>10000:
                self.score += 10000
            self.high_score=self.score
        #reward
        self.score+=pen
        reward=self.score
        #observation space
        platform_positions = [[plat.rect.x, plat.rect.y] for plat in self.platform_group]
        while len(platform_positions) < MAX_PLATFORMS:
            platform_positions.append([0, 0])  # Use default value when no platform is present.
    
        sorted_points = self.sort_points_by_distance(platform_positions, [self.jumpy.rect.x, self.jumpy.rect.y])
        observation = np.concatenate(([[self.jumpy.rect.x, self.jumpy.rect.y]], sorted_points), axis=0)    
       
        return observation, reward, self.game_over, {'hit':hit}

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
        
        platform_positions = [[plat.rect.x, plat.rect.y] for plat in self.platform_group]
        while len(platform_positions) < MAX_PLATFORMS:
            platform_positions.append([0, 0])  # Use default value when no platform is present.
    
        sorted_points = self.sort_points_by_distance(platform_positions, [self.jumpy.rect.x, self.jumpy.rect.y])
        observation = np.concatenate(([[self.jumpy.rect.x, self.jumpy.rect.y]], sorted_points), axis=0)    
        
        print(self.high_score)
        self.high_score=0
        return observation
    
    def render(self, mode='human'):
        # Refresh game screen
        self.draw_panel()
        pygame.display.update()
        # Refresh rate
        self.clock.tick(FPS)
    def close(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

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
    
    def distance_between_points(self,point1, point2):
        x1, y1  = point1
        x2, y2  = point2
        return math.sqrt((y2 - y1)**2)

    def sort_points_by_distance(self,points, target_point):
        sorted_points = sorted(points, key=lambda point: self.distance_between_points(point, target_point))
        return sorted_points

from stable_baselines3 import DQN,PPO
env=JumpyGameEnv()



model = DQN.load("logsDQN2\P_jump_norm_model_400000_20668.1.zip", env=env)
import random
# 使用訓練好的模型
obs = env.reset()
if obs[1][0]>obs[0][0]:
    action=1
else:
    action=0
target=obs[2]
obslst=obs
while True:
    p_type = random.randint(1, 20)
    obs, rewards, done, info = env.step(action)
    print(action)
    env.render()
    if info['hit']:
        a=obs[1:]
        if obs[2][1]<obs[0][1]:
            target=obs[2]
        else:
            target=obs[3]
        obslst=obs

    if target[0]>obs[0][0]:
        if p_type>2:
            action=1
        else:
            action=0
    else:
        if p_type>2:
            action=0
        else:
            action=1
    if done:
        obs = env.reset()