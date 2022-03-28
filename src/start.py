
"""
MIT License

Copyright (c) 2022 PhiniteFields@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import curses
import locale
from curses import wrapper
from random import randint, random
from turtle import pos


class Symbols:
    # default symbols
    wall = '#'
    food = ['1', '1', '1', '2', '2', '3', '5', '9']
    bad_guy = 'W'
    snake = 'O'

    
class Map:
    height = 15
    width = 40
    game_speed = 350
    game_map = []
    symbols = Symbols()
    refresh_coords = []  # allows partial re-draw on map refresh
    food_count = 0
    snake_vector = (0, 0)
    snake = []
    snake_size = 0
    bad_guys_vector = []
    bad_guys = []
    obstacles = 0
    badguy_switch_direction_prob = 0.03
    speedup_factor = 0.96
    score = 0
    
    def __init__(self, symbols, height, width, game_speed = 350, max_food = 30, max_obstacles = 12, max_bad_guys = 12):
        self.height = height
        self.width = width
        self.game_speed = game_speed
        
        self.symbols = symbols
        
        self.game_map = [[' ' for x in range(width)] for y in range(height)]
        
        # init map rectangle
        for x in range(self.width - 1):
            for y in range(1, self.height):
                
                self.refresh_coords.append((y, x))  # refresh entire map on init
                
                if (x == 0 or x == width - 2) or (y == 1 or y == height - 1):
                    self.game_map[y][x] = self.symbols.wall
                    
        # init snake
        x_center = self.width // 2
        y_center = self.height // 2
        self.snake_vector = (0, 1)
        self.snake = [(y_center, x_center-1), (y_center, x_center), (y_center, x_center+1)]    
        self.snake_size = len(self.snake)
        
        # init random obstacles (walls)
        while self.obstacles < max_obstacles:
            x = randint(2, self.width - 4)
            y = randint(3, self.height - 3)
            if self.game_map[y][x] == ' ' and not (y, x) in self.snake and self.is_empty_area(y, x):
                self.obstacles += 1
                self.game_map[y][x] = self.symbols.wall
        
        # food
        while self.food_count < max_food:
            x = randint(1, self.width - 3)
            y = randint(2, self.height - 2)
            if self.game_map[y][x] == ' ' and not (y, x) in self.snake and self.is_empty_area(y, x):
                self.food_count += 1
                self.game_map[y][x] = self.symbols.food[randint(0, len(self.symbols.food)-1)]
    
        # bad guys
        while len(self.bad_guys) < max_bad_guys:
            x = randint(2, width - 4)
            y = randint(3, height - 3)
            if self.game_map[y][x] == ' ' and not (y, x) in self.snake:
                self.bad_guys.append((y,x))
                vector = self.pick_random_vector(y, x)
                self.bad_guys_vector.append(vector)
    
    # can move into this position?
    def is_free_pos(self, posy, posx):
        if posx > 0 and posx < self.width - 2 and posy > 1 and posy < self.height - 1:
            ch = self.game_map[posy][posx]
            if ch == ' ' or self.is_food(ch):
                return True
        return False
                
    def is_food(self, ch):
        if ch in self.symbols.food:
            return True
        else:
            return False
        
    def pick_random_vector(self, posy, posx):
        target_vectors = []
        all_vectors = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, 1), (-1, 1), (1, -1)]
        for (dy, dx) in all_vectors:
            if self.is_free_pos(posy+dy, posx+dx):
                target_vectors.append((dy, dx))
    
        if len(target_vectors) > 0:
            return target_vectors[randint(0, len(target_vectors)-1)]
        
        return (0, 0)
    
    def is_empty_area(self, y, x):
        for posy in range(y-1, y+2):
            for posx in range(x-1, x+2):
                if self.game_map[posy][posx] != ' ':
                    return False
        return True
        
    def draw_map(self, screen):
        screen.addstr(0, 0, "Food left:" + str(self.food_count) + " ")
        screen.addstr(0, 15, "Score:" + str(self.score) + " ")
        screen.addstr(0, 27, "Use Arrow keys, eat numbers (q to quit)")
        
        for (y,x) in self.refresh_coords:
            ch = self.game_map[y][x]
            if self.is_food(ch):
                screen.addch(y, x, ch, curses.color_pair(3) | curses.A_BOLD)
            else:
                screen.addch(y, x, ch)
    
        for i, (y,x) in enumerate(self.snake):
            if i == len(self.snake) - 1: 
                screen.addch(y, x, self.symbols.snake, curses.color_pair(5) | curses.A_BOLD)
            else:
                screen.addch(y, x, self.symbols.snake)
            
        for (y,x) in self.bad_guys:
            screen.addch(y, x, self.symbols.bad_guy, curses.color_pair(4) | curses.A_BOLD)
    
    def calc_movement(self, snake_vector):
        self.refresh_coords = []
        
        # new bad guys loc
        for i, (locy, locx) in enumerate(self.bad_guys):
            dy, dx = self.bad_guys_vector[i]
            
            newlocy = locy + dy
            newlocx = locx + dx
            
            ch = self.game_map[newlocy][newlocx]
            if random() < self.badguy_switch_direction_prob: 
                self.bad_guys_vector[i] = self.pick_random_vector(locy, locx)
            elif self.is_free_pos(newlocy, newlocx) and (newlocy, newlocx) not in self.snake:  # can move there
                self.bad_guys[i] = (newlocy, newlocx)
                self.refresh_coords.append((locy, locx))
            else:  # pick another vector
                self.bad_guys_vector[i] = self.pick_random_vector(locy, locx)
        
        # snake vector and new position calc
        if snake_vector:
            (dy, dx) = snake_vector
            (sdy, sdx) = self.snake_vector
            if dy != -sdy or dx != -sdx: # no 180 deg turns allowed
                self.snake_vector = snake_vector
        
        (sdy, sdx) = self.snake_vector

        (posy, posx) = self.snake[-1]
        newposy = posy + sdy
        newposx = posx + sdx
        
        # detect collisions
        ch = self.game_map[newposy][newposx]
        
        if self.is_food(ch): # eat food
            self.game_map[newposy][newposx] = ' '
            self.food_count -= 1
            self.score += int(ch)
            self.snake_size += int(ch)  # grow by the # eaten
            self.game_speed = int(self.game_speed * self.speedup_factor)  # faster when you eat
        
        if ch == self.symbols.wall: # hit a wall
            return (True, False)
        elif (newposy, newposx) in self.snake:  # hit self
            return (True, False)
        elif (newposy, newposx) in self.bad_guys:  # hit bad guy
            return (True, False)
        
        self.snake.append((newposy, newposx))
        
        if len(self.snake) > self.snake_size:
            del_tail = self.snake.pop(0)
            self.refresh_coords.append(del_tail)
        
        if self.food_count == 0: # ate all the food, win
            return (True, True)
        
        return (False, False)


def main(main_screen):
    
    screen = curses.initscr()
    
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
    
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    screen.nodelay(True)
    
    height, width = screen.getmaxyx()
    
    if height < 20 or width < 50:
        print("Window too small")
        return
    
    symbols = Symbols()
    symbols.wall = curses.ACS_CKBOARD  # available only after initscr()
    symbols.snake = curses.ACS_DIAMOND
    symbols.bad_guy = 214
    
    map = Map(symbols, height, width)
    map.draw_map(screen)
    
    game_over = False
    win = False

    while not game_over:
        vector = None
        char = screen.getch()
        
        if char == ord('q'):
            break
        elif char == curses.KEY_RIGHT:
            vector = (0, 1)
        elif char == curses.KEY_LEFT:
            vector = (0, -1)
        elif char == curses.KEY_UP: 
            vector = (-1, 0)
        elif char == curses.KEY_DOWN: 
            vector = (1, 0)
        
        (game_over, win) = map.calc_movement(vector)
        
        map.draw_map(screen)
        
        screen.refresh()
        curses.napms(map.game_speed)
        
    if win:
        screen.addstr(map.height // 2, map.width // 2 - 6, " Y O U   W I N ! ", curses.color_pair(2))
    else:
        screen.addstr(map.height // 2, map.width // 2 - 8, " G A M E  O V E R ", curses.color_pair(1))
    
    screen.refresh()
    curses.napms(3000)
    

locale.setlocale(locale.LC_ALL, '') 

wrapper(main)
