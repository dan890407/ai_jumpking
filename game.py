#import libraries
import pygame
import random
import os
import numpy as np
pygame.init()

#game window dimensions
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

#create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Jumpy')

#set frame rate
clock = pygame.time.Clock()
FPS = 60



#game variable
SCROLL_THRESH = 200
GRAVITY = 1
MAX_PLATFORMS = 10
scroll = 0
bg_scroll = 0
game_over = False
score = 0
fade_counter = 0
high_score = 0

#define colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PANEL = (153, 217, 234)

#define font
font_small = pygame.font.SysFont('Lucida Sans', 20)
font_big = pygame.font.SysFont('Lucida Sans', 24)

#load images
jumpy_image = pygame.image.load('assets/jumping.png').convert_alpha()
bg_image = pygame.image.load('assets/forest.jpg').convert_alpha()
platform_image = pygame.image.load('assets/wood.png').convert_alpha()



#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

#function for drawing info panel
def draw_panel():
	pygame.draw.rect(screen, PANEL, (0, 0, SCREEN_WIDTH, 30))
	pygame.draw.line(screen, WHITE, (0, 30), (SCREEN_WIDTH, 30), 2)
	draw_text('SCORE: ' + str(score), font_small, WHITE, 0, 0)


#function for drawing the background
def draw_bg(bg_scroll):
	screen.blit(bg_image, (0, 0 + bg_scroll))
	screen.blit(bg_image, (0, -600 + bg_scroll))

#player class
class Player():
	def __init__(self, x, y):
		self.image = pygame.transform.scale(jumpy_image, (45, 45))
		self.width = 25
		self.height = 40
		self.rect = pygame.Rect(0, 0, self.width, self.height)
		self.rect.center = (x, y)
		self.vel_y = 0
		self.flip = False
		self.first=True
		self.maxheight=0
		self.penalty=0
	def move(self):
		#reset variables
		scroll = 0
		dx = 0
		dy = 0

		#process keypresses
		key = pygame.key.get_pressed()
		if key[pygame.K_a]:
			dx = -10
			self.flip = True
		if key[pygame.K_d]:
			dx = 10
			self.flip = False

		#gravity
		self.vel_y += GRAVITY
		dy += self.vel_y

		#ensure player doesn't go off the edge of the screen
		if self.rect.left + dx < 0:
			dx = -self.rect.left
		if self.rect.right + dx > SCREEN_WIDTH:
			dx = SCREEN_WIDTH - self.rect.right

		self.penalty=0
		#check collision with platforms
		for platform in platform_group:
			#collision in the y direction
			if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#check if above the platform
				if self.rect.bottom < platform.rect.centery:
					if self.vel_y > 0:
						self.rect.bottom = platform.rect.top
						dy = 0
						self.vel_y = -20
					print( platform.touched)
					if platform.touched == True:
						self.penalty=-50
					if platform.touched == False:
						platform.touched = True
		print(self.penalty)

		#check if the player has bounced to the top of the screen
		if self.rect.top <= SCROLL_THRESH:
			#if player is jumping
			if self.vel_y < 0:
				scroll = -dy
				self.first=False
			elif self.vel_y==0:
				self.point=self.rect.y

		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy + scroll
		point=0
		if 600-self.rect.y>self.maxheight:
			point = 600-self.rect.y-self.maxheight
			self.maxheight=600-self.rect.y
		#update mask
		self.mask = pygame.mask.from_surface(self.image)

		return scroll,point,self.first,self.penalty

	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))

#platform class
class Platform(pygame.sprite.Sprite):
	def __init__(self, x, y, width, moving):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.transform.scale(platform_image, (width, 30))
		self.moving = moving
		self.move_counter = random.randint(0, 50)
		self.direction = random.choice([-1, 1])
		self.speed = random.randint(1, 2)
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.touched = False

	def update(self, scroll):
		#moving platform side to side if it is a moving platform
		if self.moving == True:
			self.move_counter += 1
			self.rect.x += self.direction * self.speed

		#change platform direction if it has moved fully or hit a wall
		if self.move_counter >= 100 or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
			self.direction *= -1
			self.move_counter = 0

		#update platform's vertical position
		self.rect.y += scroll

		#check if platform has gone off the screen
		if self.rect.top > SCREEN_HEIGHT:
			self.kill()

#player instance
jumpy = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)

#create sprite groups
platform_group = pygame.sprite.Group()


#create starting platform
platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50, 100, False)
platform_group.add(platform)

#game loop
run = True
while run:

	clock.tick(FPS)

	if game_over == False:
		scroll,pt,first,pen = jumpy.move()

		#draw background
		bg_scroll += scroll
		if bg_scroll >= 600:
			bg_scroll = 0
		
		if first==True:
			score+=pt
		draw_bg(bg_scroll)

		#generate platforms
		if len(platform_group) < MAX_PLATFORMS:
			p_w = random.randint(40, 60)
			p_x = random.randint(0, SCREEN_WIDTH - p_w)
			p_y = platform.rect.y - random.randint(80, 120)
			p_type = random.randint(1, 2)
			if p_type == 1 and score > 500:
				p_moving = True
			else:
				p_moving = False
			platform = Platform(p_x, p_y, p_w, p_moving)
			platform_group.add(platform)

		#update platforms
		platform_group.update(scroll)

		#update score
		if scroll > 0:
			score += scroll
   		# repeat penalty
		score+=pen
		#draw sprites
		platform_group.draw(screen)
		jumpy.draw()

		#draw panel
		draw_panel()

		#check game over
		if jumpy.rect.top > SCREEN_HEIGHT or score>2000:
			game_over = True
		observation = np.concatenate(([[jumpy.rect.x, jumpy.rect.y]],
									[[plat.rect.x, plat.rect.y] for plat in platform_group]),
									axis=0)
      
	else:    #game end
		if fade_counter < SCREEN_WIDTH:
			fade_counter += 5
			for y in range(0, 6, 2):
				pygame.draw.rect(screen, BLACK, (0, y * 100, fade_counter, 100))
				pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - fade_counter, (y + 1) * 100, SCREEN_WIDTH, 100))
		else:
			draw_text('GAME OVER!', font_big, WHITE, 130, 200)
			draw_text('SCORE: ' + str(score), font_big, WHITE, 130, 250)
			draw_text('PRESS SPACE TO PLAY AGAIN', font_big, WHITE, 40, 300)
			if score > high_score:
				high_score = score
				with open('score.txt', 'w') as file:
					file.write(str(high_score))
			key = pygame.key.get_pressed()
			if key[pygame.K_SPACE]:
				game_over = False
				score = 0
				scroll = 0 
				fade_counter = 0
				#reposition jumpy
				jumpy.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
				jumpy.first=True
				jumpy.maxheight=0
				#reset platforms
				platform_group.empty()
				#create starting platform
				platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50, 100, False)
				platform_group.add(platform)


	#event handler
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			#update high score
			if score > high_score:
				high_score = score
				with open('score.txt', 'w') as file:
					file.write(str(high_score))
			run = False


	#update display window
	pygame.display.flip()



pygame.quit()

