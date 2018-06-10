import os
import sys
import random
import pygame as pg
from pygame import *
import inputbox
from math import floor
import numpy as np
import copy
from tkinter import filedialog
import tkinter
import argparse
import pdb  

# Todo: Draw method


#	https://stackoverflow.com/questions/14354171/add-scrolling-to-a-platformer-in-pygame
class Camera(object):
	def __init__(self, camera_func, width, height):
		self.camera_func = camera_func
		self.state = pg.Rect(0, 0, width, height)

	def apply(self, target):
		return target.move(self.state.topleft)
		
	def inv_apply(self, target):
		return target.move(self.state.topleft)
		#return target.move(self.inv_state.topleft)

	def update(self, target, WIDTH, HEIGHT, TILESIZE):
		self.state = self.camera_func(self.state, target, WIDTH, HEIGHT, TILESIZE)
		print(self.state)
		
	def getX(self):
		return self.state.left
		
	def getY(self):
		return self.state.top
		
def complex_camera(camera, target_rect, WIDTH, HEIGHT, TILESIZE):
	l, t, _, _ = target_rect
	_, _, w, h = camera
	l, t, _, _ = -l+WIDTH//2, -t+HEIGHT//2, w, h # center player

	l = min(0, l)						   # stop scrolling at the left edge
	l = max(-(camera.width-WIDTH), l)   # stop scrolling at the right edge
	t = max(-(camera.height-HEIGHT), t) # stop scrolling at the bottom
	t = min(0, t)						   # stop scrolling at the top

	return Rect(l*TILESIZE, t*TILESIZE, w, h)
	
def main():
	parser = argparse.ArgumentParser(description='Process some integers.')
	parser.add_argument('-px', '--PixelScreenWidth', type=int, help='Screen width in pixel', default=1895)
	parser.add_argument('-py', '--PixelScreenHeight', type=int, help='Screen height in pixel', default=1000)
	parser.add_argument('-tx', '--TileScreenWidth', type=int, help='Screen width in tiles', default=-1)
	parser.add_argument('-ty', '--TileScreenHeight', type=int, help='Screen height in tiles', default=-1)
	parser.add_argument('-mx', '--MapScreenWidth', type=int, help='Map width in tiles', default=53)
	parser.add_argument('-my', '--MapScreenHeight', type=int, help='Map height in tiles', default=27)
	parser.add_argument('-ts', '--TileSize', type=int, help='Tile size in pixel', default=35)
	parser.add_argument('-z', '--levels', type=int, help='Levels', default=8)
	parser.add_argument('-lm', '--loadMap', type=str, help='Load map xyz.npy on startup')
	parser.add_argument('--OverlayImage', type=str, help='Overlay map with images in LevelOverlay/*.* Needs tweaking...', default='')
	args = parser.parse_args()

	#some off/on
	generate_ship = False
	
	#useful game dimensions
	#Tiles are 3-4m each
	pixelScreenWidth = args.PixelScreenWidth
	pixelScreenHeight = args.PixelScreenHeight
	TILESIZE  = args.TileSize
	if args.TileScreenWidth == -1:
		SCREENWIDTH = round(pixelScreenWidth/TILESIZE) #how many tiles are shown on the screen
	else: 
		SCREENWIDTH = args.TileScreenWidth
	if args.TileScreenHeight == -1:
		SCREENHEIGHT = round(pixelScreenHeight/TILESIZE) #how many tiles are shown on the screen
	else: 
		SCREENHEIGHT = args.TileScreenHeight
	SCREENHEIGHT = round(pixelScreenHeight/TILESIZE) #above
	MAPWIDTH  = args.MapScreenWidth									#how many tiles does the map have.
	MAPHEIGHT = args.MapScreenHeight									#above
	LEVELS = args.levels

	#set up the display
	os.environ['SDL_VIDEO_WINDOW_POS'] = "0,20"

	pg.init()
	screen = pg.display.set_mode(((SCREENWIDTH+1)*TILESIZE,SCREENHEIGHT*TILESIZE))
	pg.display.set_caption('Station Sigma Omega Theta')

	#constants representing colours
	BLACK = (0,   0,   0  )
	GREY0 = (37,37,37)
	GREY1 = (99,99,99  )
	GREY2 = (150,150,150)
	GREY3  = (189,189,189)
	GREY4 = (217,217,217)
	WHITE = (255,255,255)
	active_selection = pg.Surface((TILESIZE, TILESIZE),pg.SRCALPHA)
	active_selection.fill((0, 255, 0, 50))
	fog_tile = pg.Surface((TILESIZE, TILESIZE),pg.SRCALPHA)
	fog_tile.fill((0, 0, 0))
	
	
	filename_prefix = 'tex_'
	#constants representing the different resources
	SPACE  = 0
	WALL = 1
	BIGT = 2
	SMALLT  = 3
	ROOM = 4
	CORRIDOR = 5
	AIRLOCK = 10
	BLASTDOORS_C = 7
	BIGTC = 8
	SMALLTC = 9
	CORRIDORC = 6
	BLASTDOORS_C_O = 11
	HULL = -1
	EMPTY = -2
	if args.OverlayImage is not '':
		overlay_images = ['5','6','7','8','9']
		overlay_image = [pg.image.load('LevelOverlay/Starship-Karokh-Orthos-%s-1991.jpg' % na_add) for na_add in overlay_images]
		overlay_image = [pg.transform.scale(overlay_image[i], (pixelScreenWidth,pixelScreenHeight)).convert() for i in range(len(overlay_images))]
	
	#BLASTDOORS_B = 8
	#BLASTDOORS_S = 9
	# 1, 2, 2, 3, 4 openings...
	namin_add = ['_x', '_I', '_L', '_T', '']
	tex_space = pg.image.load('Images/SPACE.png')
	tex_wall = pg.image.load('Images/WALL.png')
	tex_bigt = [pg.image.load('Images/BIGT%s.png' % na_add) for na_add in namin_add]
	tex_smallt = [pg.image.load('Images/SMALLT%s.png' % na_add) for na_add in namin_add]
	tex_room = pg.image.load('Images/ROOM.png')
	tex_corridor = [pg.image.load('Images/CORRIDOR%s.png' % na_add) for na_add in namin_add]
	tex_airlock = [pg.image.load('Images/AIRLOCK%s.png' % na_add) for na_add in namin_add]
	
	tex_blastdoors_c = [pg.image.load('Images/BLASTDOORSC%s.png' % na_add) for na_add in namin_add]
	tex_smallt_c = [pg.image.load('Images/SMALLTC%s.png' % na_add) for na_add in namin_add]
	tex_bigt_c = [pg.image.load('Images/BIGTC%s.png' % na_add) for na_add in namin_add]
	tex_corridor_c = [pg.image.load('Images/CORRIDORC%s.png' % na_add) for na_add in namin_add]
	tex_blastdoors_c_o = [pg.image.load('Images/BLASTDOORSC%s_O.png' % na_add) for na_add in namin_add]
	
	tex_hull = pg.image.load('Images/HULL.png')
	
	

	tex_space = [pg.transform.scale(tex_space, (TILESIZE,TILESIZE)).convert()]
	tex_wall = [pg.transform.scale(tex_wall, (TILESIZE,TILESIZE)).convert()]
	tex_bigt = [pg.transform.scale(tex_bigt[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	tex_smallt = [pg.transform.scale(tex_smallt[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	tex_room = [pg.transform.scale(tex_room, (TILESIZE,TILESIZE)).convert()]
	tex_corridor = [pg.transform.scale(tex_corridor[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	tex_airlock = [pg.transform.scale(tex_airlock[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	
	tex_blastdoors_c = [pg.transform.scale(tex_blastdoors_c[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	tex_smallt_c = [pg.transform.scale(tex_smallt_c[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	tex_bigt_c = [pg.transform.scale(tex_bigt_c[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	tex_corridor_c = [pg.transform.scale(tex_corridor_c[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	tex_blastdoors_c_o = [pg.transform.scale(tex_blastdoors_c_o[i], (TILESIZE,TILESIZE)).convert() for i in range(5)]
	
	tex_hull = [pg.transform.scale(tex_hull, (TILESIZE,TILESIZE)).convert()]
	
	
	print('Map Dimensions: '+str(MAPWIDTH*3.5)+'m * ' +str(MAPHEIGHT*3.5)+'m')
	print('Map Dimensions: '+str(MAPWIDTH)+' * ' +str(MAPHEIGHT)+'')
	print('Screen Dimensions: '+str(SCREENWIDTH)+' * ' +str(SCREENHEIGHT)+'')
	#a dictionary linking resources to colours
	#colours =   {
	#				SPACE  : BLACK,
	#				WALL : GREY0,
	#				ROOM : WHITE,
	#				CORRIDOR : GREY4,
	#				BIGT : GREY3,
	#				SMALLT  : GREY2
	#            }

	#a dictonary linking tiles to images
	images =   {
					SPACE  : tex_space,
					WALL : tex_wall,
					ROOM : tex_room,
					CORRIDOR : tex_corridor,
					BIGT : tex_bigt,
					SMALLT  : tex_smallt,
					AIRLOCK : tex_airlock, 
					CORRIDORC : tex_corridor_c, 
					BIGTC : tex_bigt_c, 
					SMALLTC : tex_smallt_c,
					BLASTDOORS_C : tex_blastdoors_c,
					HULL : tex_hull,
					EMPTY : tex_space, 
					BLASTDOORS_C_O : tex_blastdoors_c_o
				}



	#a list representing our tilemap
	random.seed(1000)

	tilemap =[[[-2 for i in range(LEVELS)] for j in range(MAPHEIGHT)] for z in range(MAPWIDTH)]
	#helper variables
	#airlock from which ship building will starts
	airlock = [0,0,0]
	airlock_x = 0
	airlock_y = 0
	airlock_z = 0
	cur =  [0,0,0]
	cur_x = 0
	cur_y = 0
	cur_z = 0
	
	generate_ship = False
	
	if generate_ship:
		ship_limit = (MAPHEIGHT-3)*(MAPHEIGHT-3)/4
		print('ship_limit :'+str(ship_limit))
		for iz in range(0, LEVELS):
			for iy in range(0, MAPHEIGHT, 1):
				for ix in range(0, MAPWIDTH, 1):
					#Corner is space
					if(iy == 0 or ix == 0 or iy == MAPHEIGHT-1 or ix == MAPWIDTH-1 or iz == 0 or iz == LEVELS-1):
						tilemap[ix][iy][iz] = SPACE
					else:
						fx = ix-round(MAPWIDTH/2)
						fy = iy-round(MAPHEIGHT/2)
						fz = iz-round(LEVELS/2)
						ff = fx*fx+fy*fy #ship form: Circle
						ff = fx*fx/4+fy*fy
						#print('FF: '+str(ff))
						if ff <= ship_limit+10 and ff >= ship_limit-20:
							tilemap[ix][iy][iz] = HULL
							if fz == 1 or fz == LEVELS-2:
								tilemap[ix][iy][iz] = HULL
							#elif airlock_x == 0 and airlock_y == 0 and airlock_z == 0:
								#print('Did Airlock')
								#tilemap[ix][iy][iz] = AIRLOCK
								#airlock = [ix, iy, iz]
								#airlock_x = ix
								#airlock_y = iy 
								#airlock_z = iz

		tilemap[14][2][2] = AIRLOCK
		makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, [14,3,2], 'down')
	
		#End of generation: Fill all holes with walls
		for iz in range(0, LEVELS, 1):
			for iy in range(0, MAPHEIGHT, 1):
				for ix in range(0, MAPWIDTH, 1):
					fx = ix-round(MAPWIDTH/2)
					fy = iy-round(MAPHEIGHT/2)
					fz = iz-round(LEVELS/2)
					#ff = fx*fx+fy*fy #ship form: Circle
					ff = fx*fx/4+fy*fy
					print('FF: '+str(ff))
					if ff <= ship_limit+10 and tilemap[ix][iy][iz] == -2:
						tilemap[ix][iy][iz] = WALL
		
	ren_text = [' ' for z in range(11)]
	font = pg.font.Font(None, 20)
	for i in range(0, 11):
		ren_text[i] = font.render(str(i), True, pg.Color(173,255,47))
	ren_text_t = font.render('t', True, pg.Color(173,255,47))
	ren_text_z = font.render('z', True, pg.Color(173,255,47))
	ren_text_quit = font.render('q Quit', True, pg.Color(173,255,47))
	ren_text_desel = font.render('d Deselect', True, pg.Color(173,255,47))
	ren_text_load = font.render('x Load', True, pg.Color(173,255,47))
	ren_text_save = font.render('s Save', True, pg.Color(173,255,47))
	ren_text_lvlup = font.render('o Lvl Up', True, pg.Color(173,255,47))
	ren_text_lvldown = font.render('l LvL Down', True, pg.Color(173,255,47))
	active_paint = -3		
	cur_level = 2
				# col row lvl
	playMode_cur = [1, 10, cur_level]
	playMode = False
	playMode_changed = True
	playMode_list = [-1,-1]
	last_playMode_list = [[0, 0]]
	
	level_changed = False
	process_mouse = False
	saveImage = False
	insert_level_above = 0
	pos = 0
	
	camera = Camera(complex_camera, MAPWIDTH, MAPHEIGHT)
	
	
	##########
	if args.loadMap is not None:
		tilemap = loadMap(args.loadMap)
	#tilemap[tilemap==-1] = 10
	clock = pg.time.Clock()
	##########
	
	#Main Game Loop
	while True:
		clock.tick(24)
		#get all the user events
		for event in pg.event.get():
			#if the user wants to quit
			if event.type == QUIT:
				#end the game and close the window
				pg.quit()
				sys.exit()
			elif event.type == pg.KEYDOWN:
			
				if event.key == pg.K_q:
					pg.quit()
					sys.exit()
				elif event.key == pg.K_o:
					if playMode == False or isConnector(tilemap, playMode_cur) and isConnector(tilemap, playMode_cur, 0, 0, +1):
						cur_level = cur_level + 1
						level_changed = True
				elif event.key == pg.K_b:
					pdb.set_trace()
				elif event.key == pg.K_l:
					if playMode == False or isConnector(tilemap, playMode_cur) and isConnector(tilemap, playMode_cur, 0, 0, -1):
						cur_level = cur_level - 1
						level_changed = True
				elif event.key == pg.K_s:
					saveMap(tilemap)
				elif event.key == pg.K_x:
					tilemap = loadMap('map.map')
				elif event.key == pg.K_m:
					saveImage = True
					saveImageLevelName = saveImageLevelPart1(screen, cur_level)
				elif event.key == pg.K_p: #Toggle playmode
					playMode = not playMode
				elif not playMode:		
					if event.key == pg.K_1:
						active_paint = 1
					elif event.key == pg.K_2:
						active_paint = 2
					elif event.key == pg.K_3:
						active_paint = 3
					elif event.key == pg.K_4:
						active_paint = 4
					elif event.key == pg.K_5:
						active_paint = 5
					elif event.key == pg.K_6:
						active_paint = 6
					elif event.key == pg.K_7:
						active_paint = 7
					elif event.key == pg.K_8:
						active_paint = 8
					elif event.key == pg.K_9:
						active_paint = 9
					elif event.key == pg.K_0:
						active_paint = 10
					elif event.key == pg.K_t:
						active_paint = -1 #HULL
					elif event.key == pg.K_z:
						active_paint = -2 #EMPTy
					elif event.key == pg.K_d: 
						active_paint = -3
					elif event.key == pg.K_INSERT:
						if insert_level_above == 0:
							insert_level_above = 1
						elif insert_level_above == 1:
							insert_level_above =2
				elif playMode:
					if event.key == pg.K_LEFT:
						if playMode_cur[0] > 0:
							playMode_cur[0] -= 1
							playMode_changed = True
					elif event.key == pg.K_UP:
						if playMode_cur[1] > 0:
							playMode_cur[1] -= 1
							playMode_changed = True
					elif event.key == pg.K_RIGHT:
						if playMode_cur[0] < MAPWIDTH-1:
							playMode_cur[0] += 1
							playMode_changed = True
					elif event.key == pg.K_DOWN:
						if playMode_cur[1] < MAPHEIGHT-1:
							playMode_cur[1] += 1
							playMode_changed = True
					if playMode_changed == True and tiletype(tilemap, [playMode_cur[0], playMode_cur[1], cur_level]) == 7:
						changetype(tilemap, [playMode_cur[0], playMode_cur[1], cur_level], 0, 0, 0, 11)
						
						
			elif event.type == MOUSEBUTTONUP and event.button == 1: # is LEFT
				pos = pg.mouse.get_pos()
				if not active_paint == -3: 
					tempvarx, tempvary = pos
					#print(tempvarx/TILESIZE, tempvary/TILESIZE)
					#tile_pos = camera.inv_apply(Rect(tempvarx/TILESIZE, tempvary/TILESIZE, TILESIZE, TILESIZE))
					tile_pos = floor(tempvarx/TILESIZE) - camera.getX()//TILESIZE, floor(tempvary/TILESIZE) - camera.getY()//TILESIZE
					
					#tile_pos = camera.inv_apply(Rect(floor(tempvarx/TILESIZE),floor(tempvary/TILESIZE), TILESIZE, TILESIZE))
					#print(tile_pos)
					if tile_pos[0] < MAPWIDTH and tile_pos[1] < MAPHEIGHT:
						changetype(tilemap, [tile_pos[0], tile_pos[1], cur_level], 0, 0, 0, active_paint)
				if playMode:
					tempvarx, tempvary = pos
					tile_pos = floor(tempvarx/TILESIZE) - camera.getX()//TILESIZE, floor(tempvary/TILESIZE) - camera.getY()//TILESIZE
					playMode_cur = [ tile_pos[0], tile_pos[1], cur_level]
					if tiletype(tilemap, playMode_cur) == 7: #If door closed, open
						changetype(tilemap, [playMode_cur[0], playMode_cur[1], cur_level], 0, 0, 0, 11)
					print(playMode_cur) #Column Row Level
					playMode_changed = True
					process_mouse = True
			elif event.type == MOUSEBUTTONUP and event.button == 3: # is RIGHT
				#Change door to open
				tempvarx, tempvary = pg.mouse.get_pos()
				tile_pos = floor(tempvarx/TILESIZE) - camera.getX()//TILESIZE, floor(tempvary/TILESIZE) - camera.getY()//TILESIZE
				#tile_pos = camera.inv_apply(Rect(floor(tempvarx/TILESIZE),floor(tempvary/TILESIZE), TILESIZE, TILESIZE))
				if tiletype(tilemap, [tile_pos[0], tile_pos[1], cur_level]) == 7:
					changetype(tilemap, [tile_pos[0], tile_pos[1], cur_level], 0, 0, 0, 11)
				elif tiletype(tilemap, [tile_pos[0], tile_pos[1], cur_level]) == 11:
					changetype(tilemap, [tile_pos[0], tile_pos[1], cur_level], 0, 0, 0, 7)
				print('Rightclick at '+str([tile_pos[0], tile_pos[1], cur_level]))
				playMode_changed = True
			elif event.type == MOUSEBUTTONUP and event.button == 2: # is MIDDLE
				tempvarx, tempvary = pg.mouse.get_pos()
				tile_pos = floor(tempvarx/TILESIZE) - camera.getX()//TILESIZE, floor(tempvary/TILESIZE) - camera.getY()//TILESIZE
				camera.update(pg.Rect(tile_pos[0], tile_pos[1], TILESIZE, TILESIZE), SCREENWIDTH, SCREENHEIGHT, TILESIZE)
		if level_changed:
			playMode_changed = True
			last_playMode_list = [[0, 0]]
			if cur_level <0:
				cur_level = 0
			if cur_level >= LEVELS:
				cur_level = LEVELS-1
			print('Level changed to: ' +str(cur_level))
			level_changed = False
			playMode_cur[2] = cur_level
		if process_mouse:
			process_mouse = False

		if insert_level_above == 2:
			insert_level_above = 0
			LEVELS = LEVELS+1
			new_tilemap = [[[-2 for i in range(LEVELS)] for j in range(MAPHEIGHT)] for z in range(MAPWIDTH)]
			for iz in range(0, LEVELS, 1):
				for iy in range(0, MAPHEIGHT, 1):
					for ix in range(0, MAPWIDTH, 1):
						if iz == cur_level:
							new_tilemap[ix][iy][iz] = EMPTY
						elif iz < cur_level:
							new_tilemap[ix][iy][iz] = tilemap[ix][iy][iz]
						elif iz > cur_level:
							new_tilemap[ix][iy][iz] = tilemap[ix][iy][iz-1]
			tilemap = copy.copy(new_tilemap)
			
#DRAWING HERE DRAWING HERE DRAWING HERE

		if playMode:
			if playMode_changed:
				camera.update(pg.Rect(playMode_cur[0], playMode_cur[1], TILESIZE, TILESIZE), SCREENWIDTH, SCREENHEIGHT, TILESIZE)
				
				print('PlayMode changed. Printing for: ')
				print(str(playMode_cur) + ' type ' + str(tiletype(tilemap, playMode_cur)))
				playMode_list = what_should_i_draw(tilemap, playMode_cur, MAPHEIGHT, MAPWIDTH)
				playMode_changed = False
				for row in range(MAPHEIGHT):
					for column in range(MAPWIDTH):
						if tiletype(tilemap, [column, row, cur_level]) > 0:
							screen.blit(fog_tile, camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
						else:
							screen.blit((images[0])[0], camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
				use_list = np.unique(np.asarray(playMode_list+last_playMode_list), axis=0).tolist()
				for col_row in use_list:
					big_draw_method(screen, tilemap, images, MAPHEIGHT, MAPWIDTH, [col_row[0], col_row[1], cur_level], TILESIZE, camera)
					
				screen.blit(active_selection, camera.apply(Rect(playMode_cur[0]*TILESIZE,playMode_cur[1]*TILESIZE,TILESIZE,TILESIZE)))
				last_playMode_list = copy.deepcopy(playMode_list)
		else:
			for row in range(MAPHEIGHT):
				for column in range(MAPWIDTH):
					big_draw_method(screen, tilemap, images, MAPHEIGHT, MAPWIDTH, [column, row, cur_level], TILESIZE, camera)
		for ii in [0,1,2,3,4,5,6,7,8,9,10,-1, -2, -3, -4, -5]:
			
			if ii >= 0:
				screen.blit((images[ii])[-1], ((SCREENWIDTH)*TILESIZE, (ii+0)*TILESIZE, TILESIZE, TILESIZE))			
				screen.blit(ren_text[ii], ((SCREENWIDTH)*TILESIZE, (ii+0)*TILESIZE, TILESIZE, TILESIZE))
			elif ii == -1:
				screen.blit((images[ii])[0], ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))		
				screen.blit(ren_text_t, ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))				
			elif ii == -2:
				screen.blit((images[ii])[0], ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))		
				screen.blit(ren_text_z, ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))
			elif ii == -3:
				screen.blit(ren_text_desel, ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))
			elif ii == -4:
				screen.blit(ren_text_save, ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))
			elif ii == -5:
				screen.blit(ren_text_load, ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))
			elif ii == -6:
				screen.blit(ren_text_lvlup, ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))
			elif ii == -7:
				screen.blit(ren_text_lvldown, ((SCREENWIDTH)*TILESIZE, (ii+17)*TILESIZE, TILESIZE, TILESIZE))
			
		if not active_paint == -3: 
			#pg.draw.rect(screen, pg.Color(0, 255, 0, 50), ((MAPWIDTH)*TILESIZE, (active_paint+2)*TILESIZE, TILESIZE, TILESIZE))
			screen.blit(active_selection, ((SCREENWIDTH)*TILESIZE, (active_paint)*TILESIZE, TILESIZE, TILESIZE))
		#update the display
		pg.display.update()
		if saveImage:
			saveImage = False
			saveImageLevelPart2(screen, saveImageLevelName, cur_level)
	
	
	#Append 
def saveMap(tilemap):
	tkinter.Tk().withdraw()
	mapname = filedialog.asksaveasfilename(initialdir=r"./")
	np.save(mapname, tilemap)
	print('Map saved as '+mapname)

def loadMap(mapname):
	print('Map loading...')
	mapname = "map.map.npy"
	tkinter.Tk().withdraw()
	mapname = filedialog.askopenfilename(initialdir=r"./", filetypes=[("Map files","*.npy")])
	return np.load(mapname)
	
def saveImageLevelPart1(screen, cur_level):
	mapname = str(inputbox.ask(screen, 'Message'))
	return mapname
	
def saveImageLevelPart2(screen, mapname, cur_level):
	pg.image.save(screen, mapname+'-l'+str(cur_level)+'.jpeg')
	print('Image saved as mapname-l'+str(cur_level)+'.jpeg')
	
def checkRoomTileOverwrite(tilemap, cur, xoff=0, yoff=0, zoff=0):
	if tiletype(tilemap, cur, xoff, yoff, zoff) == 1 or tiletype(tilemap, cur, xoff, yoff, zoff) == 2 or tiletype(tilemap, cur, xoff, yoff, zoff) == 3 or tiletype(tilemap, cur, xoff, yoff, zoff) == 4 or tiletype(tilemap, cur, xoff, yoff, zoff) == 5 or tiletype(tilemap, cur, xoff, yoff, zoff) == -2:
		return True
	else:
		return False
	
def isWalkable(tilemap, cur, MAPHEIGHT=27, MAPWIDTH=53, xoff=0, yoff=0, zoff=0):
	if cur[0]+xoff < 0 or cur[0]+xoff > MAPWIDTH-1 or cur[1]+yoff < 0 or cur[1]+yoff > MAPHEIGHT-1:
		return False
	tiletype=tilemap[cur[0]+xoff][cur[1]+yoff][cur[2]+zoff]
	if tiletype > 1:
		#print(tiletype)
		return True
	else: 
		return False
		
def getLURD(tilemap, cur, MAPHEIGHT, MAPWIDTH):
	cur_tiletype=tilemap[cur[0]][cur[1]][cur[2]]
	#Tile is just one tile.
	if cur_tiletype < 2 or cur_tiletype==4:
		lurd = [False, False, False, False]
		return lurd
		
	lurd_tt = [-4, -4, -4, -4]
	if cur[0]-1 >= 0:
		lurd_tt[0] = tilemap[cur[0]-1][cur[1]][cur[2]]
	else:
		lurd_tt[0] = 0
		
	if cur[1]-1 >= 0:
		lurd_tt[1] = tilemap[cur[0]][cur[1]-1][cur[2]]
	else:
		lurd_tt[1] = 0
		
	if cur[0]+1 < MAPWIDTH:
		lurd_tt[2] = tilemap[cur[0]+1][cur[1]][cur[2]]
	else:
		lurd_tt[2] = 0
		
	if cur[1]+1 < MAPHEIGHT:
		lurd_tt[3] = tilemap[cur[0]][cur[1]+1][cur[2]]
	else:
		lurd_tt[3] = 0		
		
	#If current tiletype is walkable but no airlock
	if cur_tiletype > 1 and cur_tiletype != 10: 
		lurd = [1 if tt > 1 else 0 for tt in lurd_tt]
		return lurd
	#If is airlock (space is an okay exit, too)
	elif cur_tiletype == 10:
		lurd = [1 if tt > 1 or tt == 10 else 0 for tt in lurd_tt]
		return lurd
		
def what_should_i_draw(tilemap, playMode_cur, MAPHEIGHT, MAPWIDTH):
	retList = [[playMode_cur[0], playMode_cur[1]] , [playMode_cur[0], playMode_cur[1]]]
	cur_tiletype = tilemap[playMode_cur[0]][playMode_cur[1]][playMode_cur[2]]
	inSpace = False
	if tiletype(tilemap, playMode_cur) == 0 or tiletype(tilemap, playMode_cur) == -2:
		print('Space tile')
		inSpace = True
	elif not isWalkable(tilemap, [playMode_cur[0], playMode_cur[1], playMode_cur[2]], MAPHEIGHT, MAPWIDTH):
		print('Wall tile')
		return retList
	#Walk around the edge of the map and calculate line list
	#Then go thru every line list and stop when invisible hit
	big_list = []
	for x in range(0,MAPWIDTH-1):
		#y is 0
		small_list1 = get_bresenham_line([playMode_cur[0], playMode_cur[1]],[x,0])
		big_list.append(small_list1)
		#y is MAPHEIGHT
		small_list2 = get_bresenham_line([playMode_cur[0], playMode_cur[1]],[x,MAPHEIGHT-1])
		big_list.append(small_list2)
	for y in range(0,MAPHEIGHT-1):
		#x is 0
		small_list3 = get_bresenham_line([playMode_cur[0], playMode_cur[1]],[0,y])
		big_list.append(small_list3)
		#x is MAPWIDTH
		small_list4 = get_bresenham_line([playMode_cur[0], playMode_cur[1]],[MAPWIDTH-1,y])
		big_list.append(small_list4)
	
	for line in big_list:
		for tile in line:
			tile_tiletype = tiletype(tilemap, [tile[0], tile[1], playMode_cur[2]])
			#if tile_tiletype == 11:
				#pdb.set_trace()
			if tile_tiletype < 1 and not inSpace: #not walkable
				#retList.append(tile)
				break
			elif tile_tiletype == 1:	
				retList.append(tile)
				break
			elif tile_tiletype == 10 or tile_tiletype == 7: #Doorlike and closed. Draw door but then stop
				retList.append(tile)
				break
			else: #Tiletype is walkable and not a door
				if cur_tiletype == 4 or cur_tiletype == 5 or cur_tiletype == 6 or cur_tiletype == 11: #Cooridorlike / Room / Doorlike open
					if tile_tiletype == 4 or tile_tiletype == 5 or tile_tiletype == 6 or tile_tiletype == 11:
						retList.append(tile)
					else:
						retList.append(tile)
						break
				elif cur_tiletype == 2 or cur_tiletype == 8: #Big Tube
					if tile_tiletype == 2 or tile_tiletype == 8 or tile_tiletype == 3 or tile_tiletype == 9:
						retList.append(tile)
					else:
						retList.append(tile)
						break
				elif cur_tiletype == 3 or cur_tiletype == 9: #Small Tube
					if tile_tiletype == 3 or tile_tiletype == 9:
						retList.append(tile)
					else:
						retList.append(tile)
						break
			#if isWalkable(tilemap, [tile[0], tile[1], playMode_cur[2]], MAPHEIGHT, MAPWIDTH):
			#	retList.append(tile)
				#if(tile[1] > 0 and tiletype(tilemap, [tile[0], tile[1] - 1, playMode_cur[2]]) == 1): #left
				#	retList.append([tile[0], tile[1] - 1])
				#if(tile[1] < MAPWIDTH and tiletype(tilemap, [tile[0], tile[1] + 1, playMode_cur[2]]) == 1): #right
				#	retList.append([tile[0], tile[1] + 1])
				#if(tile[0] < MAPHEIGHT and tiletype(tilemap, [tile[0] - 1, tile[1], playMode_cur[2]]) == 1): #up
				#	retList.append([tile[0] - 1, tile[1]])
				#if(tile[0] < MAPHEIGHT and tiletype(tilemap, [tile[0] + 1, tile[1], playMode_cur[2]]) == 1): #down
				#	retList.append([tile[0] + 1, tile[1]])
			#else: 
			#	break
#	retList = np.unique(np.asarray(retList)).tolist()
	retList = np.unique(np.asarray(retList), axis=0).tolist()
	
	#print(retList)
			
	
	
	break_condition = False
	cntr = 0
#	if not break_condition:
#		cntr += 1
		
		
#	playMode_cur
	#print(type(retList))
	#print(retList)
	return retList

def get_bresenham_line(start, end):
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end
 
    >>> points1 = get_line((0, 0), (3, 4))
    >>> points2 = get_line((3, 4), (0, 0))
    >>> assert(set(points1) == set(points2))
    >>> print points1
    [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
    >>> print points2
    [(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
 
    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)
 
    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
 
    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True
 
    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1
 
    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1
 
    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx
 
    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points
	
def big_draw_method(screen, tilemap, images, MAPHEIGHT, MAPWIDTH, cur, TILESIZE, camera):
	column, row, cur_level = cur
	lurd = getLURD(tilemap, [column, row, cur_level], MAPHEIGHT, MAPWIDTH) #left up right down: 0 is wall-like, 1 is walkable
	lurd_amnt = sum(lurd)
	if lurd_amnt == 0:
		#if playMode and True:
		#	screen.blit((images[0])[0], (column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE))
		#else:
			screen.blit((images[tilemap[column][row][cur_level]])[0], camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
	elif lurd_amnt == 1: 
		#Default connection is bottom. Therefore x 90 deg rotation are needed
		index = lurd.index(1) #If left: index 0, up index1, right index2 down index3
		#left: 0 1 rotate
		#up: 1 2 rotate
		#right: 2 3 rotate
		#down: 3 0 rotate
		screen.blit(pg.transform.rotate((images[tilemap[column][row][cur_level]])[0], 90*((index+1) % 4)), camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
	elif lurd_amnt == 2:
		#If opposing are equal, its an I
		if lurd[0] == lurd[2]:
			if lurd[0] == 1:
				#Default is up down connected
				screen.blit(pg.transform.rotate((images[tilemap[column][row][cur_level]])[1], 90), camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
			else: 
				screen.blit(pg.transform.rotate((images[tilemap[column][row][cur_level]])[1], 0), camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
		#Else its an L
		else:
			#Default is open bottom and right
			index = lurd.index(0)
			if index == 0 and lurd[-1] == 0: #Special case: L is open bottom and left
				index = 3
			screen.blit(pg.transform.rotate((images[tilemap[column][row][cur_level]])[2], -90*index), camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
			
			
	elif lurd_amnt == 3:
		#Default non-connection is left 
		index = lurd.index(0)
		screen.blit(pg.transform.rotate((images[tilemap[column][row][cur_level]])[3], -90*index), camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
	elif lurd_amnt == 4:
		screen.blit((images[tilemap[column][row][cur_level]])[4], camera.apply(Rect(column*TILESIZE,row*TILESIZE,TILESIZE,TILESIZE)))
	
def makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur, favored_dir): 
	sx = cur[0]
	sy = cur[1]
	room_size = 0
	max_room_size = random.randint(2,3)
	expand_up = True
	expand_down = True
	expand_left = True
	expand_right = True
	cells_up = 0
	cells_down = 0
	cells_left = 0
	cells_right = 0

	while(expand_up or expand_down or expand_left or expand_right):
		if expand_up:
			for i in range(0-cells_left, 0+cells_right+1):#+1 bc range 
				if not checkRoomTileOverwrite(tilemap, cur, i, -cells_up-1, 0) or cells_up >= max_room_size:
					expand_up = False
			if expand_up: 
				cells_up = cells_up + 1
		if expand_down:
			for i in range(0-cells_left, 0+cells_right+1):#+1 bc range 
				if not checkRoomTileOverwrite(tilemap, cur, i, +cells_down+1, 0)or cells_down >= max_room_size:
					expand_down = False
			if expand_down: 
				cells_down = cells_down + 1
		if expand_left:
			for i in range(0-cells_down, 0+cells_up+1):#+1 bc range 
				if not checkRoomTileOverwrite(tilemap, cur, -cells_left-1, i, 0)or cells_left >= max_room_size:
					expand_left = False
			if expand_left: 
				cells_left = cells_left + 1	
		if expand_right:
			for i in range(0-cells_down, 0+cells_up+1):#+1 bc range 
				if not checkRoomTileOverwrite(tilemap, cur, +cells_right+1, i, 0)or cells_right >= max_room_size:
					expand_right = False
			if expand_right: 
				cells_right = cells_right + 1	
	
	#print('cellsup: '+str(cells_up))
	#print('cellsdown: '+str(cells_down))
	#print('cellsleft: '+str(cells_left))
	#print('cellsright: '+str(cells_right))
	print('Roomsize: '+str((cells_up + cells_down)*(cells_left + cells_right)))
	#when ended, cells_xyz should state how big the room can be
	#room_size = random.randint(0,)
	
	
	for ix in range(0-cells_left, cells_right+1):
		for iy in range(0-cells_up, cells_down+1):
			tilemap[sx+ix][sy+iy][cur[2]] = 4
	
	#Now put corridors and such onto the room? Or walls
	base_prob_junc = 75
	
	if random.randint(0,100) < base_prob_junc:
		#left side: 
		rInt = random.randint(0,100)
		dir = 'left'
		cur2 = [cur[0]-cells_left-1, cur[1], cur[2]]
		if rInt < 50: 
			makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 75: 
			makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 101: 
			makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
	if random.randint(0,100) < base_prob_junc:
		#right side: 
		rInt = random.randint(0,100)
		dir = 'right'
		cur2 = [cur[0]+cells_right+1, cur[1], cur[2]]
		if rInt < 50: 
			makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 75: 
			makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 101: 
			makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			
	if random.randint(0,100) < base_prob_junc:
		#up side: 
		rInt = random.randint(0,100)
		dir = 'up'
		cur2 = [cur[0], cur[1]-cells_up-1, cur[2]]
		if rInt < 50: 
			makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 75: 
			makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 101: 
			makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
	if random.randint(0,100) < base_prob_junc:
		#down side: 
		rInt = random.randint(0,100)
		dir = 'down'
		cur2 = [cur[0], cur[1]+cells_down+1, cur[2]]
		if rInt < 50: 
			makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 75: 
			makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
		elif rInt < 101: 
			makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
	
	print('Room')

def makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur, favored_dir, forceConnector=False):
	updown = False

	base_prob = 25
	base_prob_connector = 10
	favor_dir_prob = 100-base_prob-20
	room_prob = 10
	bigT_prob = 10
	smallT_prob = 5
	airlock_prob = 10
	lmod = 0
	rmod = 0
	umod = 0
	dmod = 0
	if favored_dir=='left':
		lmod = favor_dir_prob
	elif favored_dir=='right':
		rmod = favor_dir_prob
	elif favored_dir=='up':
		umod = favor_dir_prob
	elif favored_dir=='down':
		dmod = favor_dir_prob
		
	if tiletype(tilemap, cur) == -2: #maybe delete, otherwise checked twice?
		if random.randint(0,100) < 100-base_prob_connector: #90% normal corridor
			changetype(tilemap, cur, 0,0,0, 5)
		else: #10% corridor with connection to upper/lower levels
			changetype(tilemap, cur, 0,0,0,6)
			updown = True
		if forceConnector: 
			changetype(tilemap, cur, 0,0,0,6)
			updown = True

		#left: Example
		# if tile is empty
		# then set working tile cur2
		# if random integer is smaller then base_prob + lmod (favored dir)
		#	then make a corridor there
		# else 
		if tiletype(tilemap, cur, -1, 0, 0) == -2:
			cur2 = [cur[0]-1, cur[1], cur[2]]
			dir = 'left'
			adjmod = umod + dmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+lmod:			
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < room_prob+adjmod: 
				makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		elif tiletype(tilemap, cur, -1, 0, 0) == -1 and random.randint(0,100) < airlock_prob:
			tilemap[cur[0]-1][cur[1]][cur[2]] = 10
			
		#right
		if tiletype(tilemap, cur, +1, 0, 0) == -2:
			cur2 = [cur[0]+1, cur[1], cur[2]]
			dir = 'right'
			adjmod = umod + dmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+rmod:			
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < room_prob+adjmod: 
				makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		elif tiletype(tilemap, cur, +1, 0, 0) == -1 and random.randint(0,100) < airlock_prob:
			tilemap[cur[0]+1][cur[1]][cur[2]] = 10
			
		#up
		if tiletype(tilemap, cur, 0, -1, 0) == -2:
			cur2 = [cur[0], cur[1]-1, cur[2]]
			dir = 'up'
			adjmod = lmod + rmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+umod:			
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < room_prob+adjmod: 
				makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		elif tiletype(tilemap, cur, 0, -1, 0) == -1 and random.randint(0,100) < airlock_prob:
			tilemap[cur[0]][cur[1]-1][cur[2]] = 10
		#down
		if tiletype(tilemap, cur, 0, +1, 0) == -2:
			cur2 = [cur[0], cur[1]+1, cur[2]]
			dir = 'down'
			adjmod = lmod + rmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+dmod:			
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < room_prob+adjmod: 
				makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		elif tiletype(tilemap, cur, 0, +1, 0) == -1 and random.randint(0,100) < airlock_prob:
			tilemap[cur[0]][cur[1]+1][cur[2]] = 10
		
		if updown: #only if current tile is connector	
			#Zup
			if tiletype(tilemap, cur, 0, 0, -1) == -2 or tiletype(tilemap, cur, 0, 0, -1) ==5 or tiletype(tilemap, cur, 0, 0, -1) == 2:
				cur2 = [cur[0], cur[1], cur[2]-1]
				if random.randint(0,100) < base_prob_connector or True:			
					makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, 'up', True) #Make Connector
					updown = False
			#Zdown
			if tiletype(tilemap, cur, 0, 0, +1) == -2 or tiletype(tilemap, cur, 0, 0, +1) ==5 or tiletype(tilemap, cur, 0, 0, +1) == 2:
				cur2 = [cur[0], cur[1], cur[2]+1]
				if random.randint(0,100) < base_prob_connector or True:			
					makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, 'down', True)#Make Connector
					updown = False
					
			if updown: #if updown is NOW False, a connection to another layer was set. If not, then there is a connector without connection, which looks bad...
				changetype(tilemap, cur, 0,0,0, 5) #If there is no possible way to set connector, make it a corridor
	else:
		print('Error in makeCorridor: Tile is not empty')
	print('corridor')

def makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur, favored_dir, forceConnector=False):
	updown = False
	
	base_prob = 15
	base_prob_connector = 20
	favor_dir_prob = 70
	room_prob = 10
	bigT_prob = 10 #is here corridor
	smallT_prob = 5
	airlock_prob = 10
	lmod = 0
	rmod = 0
	umod = 0
	dmod = 0
	if favored_dir=='left':
		lmod = favor_dir_prob
	elif favored_dir=='right':
		rmod = favor_dir_prob
	elif favored_dir=='up':
		umod = favor_dir_prob
	elif favored_dir=='down':
		dmod = favor_dir_prob
		
	if tiletype(tilemap, cur) == -2: #maybe delete, otherwise checked twice?
		if random.randint(0,100) < 100-base_prob_connector: #90% normal corridor
			changetype(tilemap, cur, 0,0,0, 2)
		else: #10% corridor with connection to upper/lower levels
			changetype(tilemap, cur, 0,0,0,8)
			updown = True
		if forceConnector: 
			changetype(tilemap, cur, 0,0,0,8)
			updown = True

		#left: Example
		# if tile is empty
		# then set working tile cur2
		# if random integer is smaller then base_prob + lmod (favored dir)
		#	then make a corridor there
		# else 
		if tiletype(tilemap, cur, -1, 0, 0) == -2:
			cur2 = [cur[0]-1, cur[1], cur[2]]
			dir = 'left'
			adjmod = umod + dmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+lmod:			
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			#elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, -1, 0, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]-1][cur[1]][cur[2]] = 10
			
		#right
		if tiletype(tilemap, cur, +1, 0, 0) == -2:
			cur2 = [cur[0]+1, cur[1], cur[2]]
			dir = 'right'
			adjmod = umod + dmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+rmod:			
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, +1, 0, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]+1][cur[1]][cur[2]] = 10
			
		#up
		if tiletype(tilemap, cur, 0, -1, 0) == -2:
			cur2 = [cur[0], cur[1]-1, cur[2]]
			dir = 'up'
			adjmod = lmod + rmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+umod:			
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, 0, -1, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]][cur[1]-1][cur[2]] = 10
		#down
		if tiletype(tilemap, cur, 0, +1, 0) == -2:
			cur2 = [cur[0], cur[1]+1, cur[2]]
			dir = 'down'
			adjmod = lmod + rmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+dmod:			
				makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < bigT_prob+adjmod:
				makeCorridor(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			elif random.randint(1,100) < smallT_prob+adjmod: 
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, 0, +1, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]][cur[1]+1][cur[2]] = 10
		
		if updown: #only if current tile is connector	
			#Zup
			if tiletype(tilemap, cur, 0, 0, -1) == -2 or tiletype(tilemap, cur, 0, 0, -1) ==5 or tiletype(tilemap, cur, 0, 0, -1) == 2:
				cur2 = [cur[0], cur[1], cur[2]-1]
				if random.randint(0,100) < base_prob_connector or True:			
					makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, 'up', True) #Make Connector
					updown = False
			#Zdown
			if tiletype(tilemap, cur, 0, 0, +1) == -2 or tiletype(tilemap, cur, 0, 0, +1) ==5 or tiletype(tilemap, cur, 0, 0, +1) == 2:
				cur2 = [cur[0], cur[1], cur[2]+1]
				if random.randint(0,100) < base_prob_connector or True:			
					makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, 'down', True)#Make Connector
					updown = False
					
			if updown: #if updown is NOW False, a connection to another layer was set. If not, then there is a connector without connection, which looks bad...
				changetype(tilemap, cur, 0,0,0, 2) #If there is no possible way to set connector, make it a corridor
	else:
		print('Error in makeCorridor: Tile is not empty')
	print('corridor')
	
def makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur, favored_dir, forceConnector=False):
	updown = False
	
	base_prob = 15
	base_prob_connector = 20
	favor_dir_prob = 70
	room_prob = 10
	bigT_prob = 10
	smallT_prob = 5
	airlock_prob = 10
	lmod = 0
	rmod = 0
	umod = 0
	dmod = 0
	if favored_dir=='left':
		lmod = favor_dir_prob
	elif favored_dir=='right':
		rmod = favor_dir_prob
	elif favored_dir=='up':
		umod = favor_dir_prob
	elif favored_dir=='down':
		dmod = favor_dir_prob
		
	if tiletype(tilemap, cur) == -2: #maybe delete, otherwise checked twice?
		if random.randint(0,100) < 100-base_prob_connector: #90% normal corridor
			changetype(tilemap, cur, 0,0,0, 3)
		else: #10% corridor with connection to upper/lower levels
			changetype(tilemap, cur, 0,0,0,9)
			updown = True
		if forceConnector: 
			changetype(tilemap, cur, 0,0,0,9)
			updown = True

		#left: Example
		# if tile is empty
		# then set working tile cur2
		# if random integer is smaller then base_prob + lmod (favored dir)
		#	then make a corridor there
		# else 
		if tiletype(tilemap, cur, -1, 0, 0) == -2:
			cur2 = [cur[0]-1, cur[1], cur[2]]
			dir = 'left'
			adjmod = umod + dmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+lmod:			
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < bigT_prob+adjmod:
				# makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			#elif random.randint(1,100) < smallT_prob+adjmod: 
			#	makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, -1, 0, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]-1][cur[1]][cur[2]] = 10
			
		#right
		if tiletype(tilemap, cur, +1, 0, 0) == -2:
			cur2 = [cur[0]+1, cur[1], cur[2]]
			dir = 'right'
			adjmod = umod + dmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+rmod:			
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < bigT_prob+adjmod:
				# makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			#elif random.randint(1,100) < smallT_prob+adjmod: 
			#	makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, +1, 0, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]+1][cur[1]][cur[2]] = 10
			
		#up
		if tiletype(tilemap, cur, 0, -1, 0) == -2:
			cur2 = [cur[0], cur[1]-1, cur[2]]
			dir = 'up'
			adjmod = lmod + rmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+umod:			
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < bigT_prob+adjmod:
				# makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			#elif random.randint(1,100) < smallT_prob+adjmod: 
			#	makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, 0, -1, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]][cur[1]-1][cur[2]] = 10
		#down
		if tiletype(tilemap, cur, 0, +1, 0) == -2:
			cur2 = [cur[0], cur[1]+1, cur[2]]
			dir = 'down'
			adjmod = lmod + rmod # This modifier is for the junction tiles, room, bigt, and smallT
			adjmod = 0
			if random.randint(0,100) < base_prob+dmod:			
				makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < room_prob+adjmod: 
				# makeRoom(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			# elif random.randint(1,100) < bigT_prob+adjmod:
				# makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			#elif random.randint(1,100) < smallT_prob+adjmod: 
			#	makeSmallT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, dir)
			else: 
				makeWall(tilemap, cur2)
		# elif tiletype(tilemap, cur, 0, +1, 0) == -1 and random.randint(0,100) < airlock_prob:
			# tilemap[cur[0]][cur[1]+1][cur[2]] = 10
		
		if updown: #only if current tile is connector	
			#Zup
			if tiletype(tilemap, cur, 0, 0, -1) == -2 or tiletype(tilemap, cur, 0, 0, -1) ==3 or tiletype(tilemap, cur, 0, 0, -1) == 2:
				cur2 = [cur[0], cur[1], cur[2]-1]
				if random.randint(0,100) < base_prob_connector or True:			
					makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, 'up', True) #Make Connector
					updown = False
			#Zdown
			if tiletype(tilemap, cur, 0, 0, +1) == -2 or tiletype(tilemap, cur, 0, 0, +1) ==3 or tiletype(tilemap, cur, 0, 0, +1) == 2:
				cur2 = [cur[0], cur[1], cur[2]+1]
				if random.randint(0,100) < base_prob_connector or True:			
					makeBigT(tilemap, MAPHEIGHT, MAPWIDTH, LEVELS, cur2, 'down', True)#Make Connector
					updown = False
					
			if updown: #if updown is NOW False, a connection to another layer was set. If not, then there is a connector without connection, which looks bad...
				changetype(tilemap, cur, 0,0,0, 3) #If there is no possible way to set connector, make it a corridor
	else:
		print('Error in makeSmallT: Tile is not empty')

def makeWall(tilemap,cur):
	tilemap[cur[0]][cur[1]][cur[2]] = 1
	
def tiletype(tilemap, cur, xoff=0, yoff=0, zoff=0):
	return tilemap[cur[0]+xoff][cur[1]+yoff][cur[2]+zoff]

def isConnector(tilemap, cur, xoff=0, yoff=0, zoff=0):
	tiletype = tilemap[cur[0]+xoff][cur[1]+yoff][cur[2]+zoff]
	if tiletype == 6 or tiletype == 9 or tiletype == 8 or tiletype == 0 or tiletype == -2: 
		return True
	else:
		return False
	
def changetype(tilemap, cur, xoff, yoff, zoff, type):
	tilemap[cur[0]+xoff][cur[1]+yoff][cur[2]+zoff] = type

main()