import gym
from gym import spaces
import numpy as np
# ... include your imports here ...
import pygame
import random
import sys
from operator import itemgetter
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
        #repeat penalty
        self.penalty=0
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
                    if platform.touched == True:
                        self.penalty+=-500
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

        return scroll,point,self.first,self.penalty

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
        self.width = width
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
                                            shape=(MAX_PLATFORMS + 1, 4), dtype=np.float32)

        # ...
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
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption('Jumpy')
        # set frame rate
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
        self.scroll,pt,first,pen = self.jumpy.move(action,self.platform_group)
        # something magic
        pygame.event.pump()
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
        #firstmap
        if first==True:
            self.score+=pt
        

        #draw sprites
        #self.draw_bg(self.bg_scroll)
        #self.platform_group.draw(self.screen)
        #self.jumpy.draw()

        #check game over
        if self.jumpy.rect.top > SCREEN_HEIGHT or self.score>10000:
            self.game_over = True
            if self.jumpy.rect.top > SCREEN_HEIGHT:   
                self.score += -1000
            if self.score>10000:
                self.score += 10000
            self.high_score=self.score
        #reward
        self.score+=pen
        reward=self.score
        #observation space1
        #observation = pygame.surfarray.array3d(pygame.display.get_surface())
        #obervation space2
        platform_positions = [[plat.rect.x, plat.rect.y,plat.width, 30] for plat in self.platform_group]
        while len(platform_positions) < MAX_PLATFORMS:
            platform_positions.append([0, 0,0,0])  # Use default value when no platform is present.
    
        sorted_points = self.sort_points_by_distance(platform_positions, [self.jumpy.rect.x, self.jumpy.rect.y])
        observation = np.concatenate(([[self.jumpy.rect.x, self.jumpy.rect.y, self.jumpy.width, self.jumpy.height]], sorted_points), axis=0)    
        return observation, reward, self.game_over, {}

    def reset(self):
        """
        Reset the state of the environment to an initial state.
        """
        print("reset")
        pygame.event.pump()
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
        platform_positions = [[plat.rect.x, plat.rect.y,plat.width, 30] for plat in self.platform_group]
        while len(platform_positions) < MAX_PLATFORMS:
            platform_positions.append([0, 0,0,0])  # Use default value when no platform is present.
    
        sorted_points = self.sort_points_by_distance(platform_positions, [self.jumpy.rect.x, self.jumpy.rect.y])
        observation = np.concatenate(([[self.jumpy.rect.x, self.jumpy.rect.y, self.jumpy.width, self.jumpy.height]], sorted_points), axis=0)
        print(self.high_score)
        self.high_score=0
        return observation
    
    def render(self):
        # Refresh game screen
        pygame.display.update()
        # Refresh rate
    def close(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()



    #function for drawing the background
    def draw_bg(self,bg_scroll):
        self.screen.blit(self.bg_image, (0, 0 + bg_scroll))
        self.screen.blit(self.bg_image, (0, -600 + bg_scroll))
    def distance_between_points(self,point1, point2):
        x1, y1 ,_,_ = point1
        x2, y2  = point2
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def sort_points_by_distance(self,points, target_point):
        sorted_points = sorted(points, key=lambda point: self.distance_between_points(point, target_point))
        return sorted_points

# model call back
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.results_plotter import ts2xy,load_results
import numpy as np

class SaveOnBestTrainingRewardCallback(BaseCallback):
    def __init__(self, check_freq: int, log_dir: str, verbose=1):
        super(SaveOnBestTrainingRewardCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.best_mean_reward = -np.inf
        self.count=0
        self.bestmodel = ""
    def _init_callback(self) -> None:
        os.makedirs(self.log_dir, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            x, y = ts2xy(load_results(self.log_dir), 'timesteps')
            if len(x) > 0:
                mean_reward = np.mean(y[-100:])
                if self.verbose > 0:
                    print("Num timesteps: {}".format(self.num_timesteps))
                    print("Best mean reward: {:.2f} - Last mean reward per episode: {:.2f}".format(self.best_mean_reward, mean_reward))

                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    best_model_filename = f"jump_best_model_{self.num_timesteps}.zip"
                    best_model_path = os.path.join(self.log_dir, best_model_filename)
                    if self.verbose > 0:
                        print("Saving new best model to {}".format(best_model_path))
                    self.model.save(best_model_path)
                    self.bestmodel = best_model_path
                else:
                    #self.model = DQN.load(self.bestmodel, env=self.model.get_env())
                    elsemodelname = f"normal_model_{self.num_timesteps}_{mean_reward}.zip"
                    else_model_path = os.path.join(self.log_dir, elsemodelname)
                    print("Saving normal model to {}".format(else_model_path))
                    self.model.save(else_model_path)

        return True



from stable_baselines3 import PPO,DQN,A2C
from stable_baselines3.common.monitor import Monitor


import os
if __name__ == '__main__':
    current_dir = os.getcwd()

    # Specify the log directory path
    log_dir = os.path.join(current_dir, 'logsDQN6')
    os.makedirs(log_dir, exist_ok=True)
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    # Create vectorized environments
    env=JumpyGameEnv()
    env = Monitor(env, log_dir)
    # Define the model
    model = DQN("MlpPolicy", env, verbose=2)
    #model = DQN.load('logsDQN4\jump_best_model_930000.zip', env=env, verbose=2)

    # Train the agent
    callback = SaveOnBestTrainingRewardCallback(check_freq=10000, log_dir=log_dir)
    model.learn(total_timesteps=int(1000000), callback=callback)


    
    