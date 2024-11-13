# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util
import time
from collections import deque

class Grid:
    #Lower ghost negative reward
    # Ghost check negative reward should only happen in the same direction it is moving
    def __init__(self, width, height, walls, food, capsules, ghostsWithLastDirection):
        self.width = width
        self.height = height
        self.utility_grid = [[0 for _ in range(width)] for _ in range(height)]
        self.reward_grid = [[-5 for _ in range(width)] for _ in range(height)] 
        self.ghostReward = -100
        self.foodReward = 50
        self.finalFoodReward = self.foodReward
        self.capsuleReward = 50
        self.walls = walls
        self.furthestDistance = 0
        self.rateIfNotCloser = 0.05
        self.ghostAura = 4
        
        for x in range(width):
            for y in range(height):
                if (x, y) in food:
                    if len(food) == 1:
                        self.updateReward((x, y), self.finalFoodReward)
                    else:
                        self.updateReward((x, y), self.foodReward)   
                elif (x, y) in capsules:
                    self.updateReward((x, y), self.capsuleReward)
                elif (x, y) in walls:
                    self.updateUtility((x, y), '#')      
                    self.updateReward((x, y), '#') 
                # elif (x, y) in ghosts:
                #     self.reward_grid[self.height - y - 1][x] = self.ghostReward
        
        for f in food:
            self.updatePelletsReward(f)
        print self.reward_grid

        firstStep = False
        for ghost in ghostsWithLastDirection:
            if ghost['dir'] == Directions.STOP:
                firstStep = True
                break
        
        if firstStep:
            if ghostsWithLastDirection:
                for ghost in ghostsWithLastDirection:
                    self.firstGetFurthestDistance(ghost['pos'])

                for ghost in ghostsWithLastDirection:
                    self.firstUpdateNeighboursRewards(ghost['pos'])
        else:
            if ghostsWithLastDirection:
                self.getFurthestDistance(ghostsWithLastDirection[0])

            for ghost in ghostsWithLastDirection:
                self.updateNeighboursRewards(ghost)

        print self.reward_grid
        time.sleep(5)


    def updatePelletsReward(self, food):
        x, y = food
        numOfWalls = 0
        if (x - 1, y) in self.walls:
            numOfWalls += 1
        if (x + 1, y) in self.walls:
            numOfWalls += 1
        if (x, y - 1) in self.walls:
            numOfWalls += 1
        if (x, y + 1) in self.walls:
            numOfWalls += 1
        
        self.updateReward((x, y), self.getReward((x, y)) * (1 - (numOfWalls / float(4))) )
            


    def getFurthestDistance(self, ghost):
        visited = set()
        furthestDistance = 0
        x, y = ghost['pos']
        x, y = int(x), int(y)
        initialqueue = deque([((x, y), ghost['dir'], 0)])

        dirToCheck = {
            Directions.NORTH: [Directions.NORTH, Directions.EAST, Directions.WEST],
            Directions.SOUTH: [Directions.SOUTH, Directions.EAST, Directions.WEST],
            Directions.EAST: [Directions.EAST, Directions.NORTH, Directions.SOUTH],
            Directions.WEST: [Directions.WEST, Directions.NORTH, Directions.SOUTH]
        }

        while initialqueue:
            pos, dir, distance = initialqueue.popleft()
            x, y = pos
            if (pos, dir) in visited or pos in self.walls or x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            visited.add((pos, dir))

            furthestDistance = max(furthestDistance, distance)
            for d in dirToCheck[dir]:
                next_pos = self.get_next_position(pos, d)
                if next_pos != pos:
                    initialqueue.append((next_pos, d, distance + 1))
                    
        self.furthestDistance = furthestDistance

    def updateNeighboursRewards(self, ghost):
        x, y = ghost['pos']
        x, y = int(x), int(y)

        direction = ghost['dir']
        visited = set()
        queue = deque([((x, y), direction, 0)])

        dirToCheck = {
            Directions.NORTH: [Directions.NORTH, Directions.EAST, Directions.WEST],
            Directions.SOUTH: [Directions.SOUTH, Directions.EAST, Directions.WEST],
            Directions.EAST: [Directions.EAST, Directions.NORTH, Directions.SOUTH],
            Directions.WEST: [Directions.WEST, Directions.NORTH, Directions.SOUTH]
        }

        while queue:
            pos, dir, distance = queue.popleft()
            x, y = pos
            if (pos, dir) in visited or pos in self.walls or x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            visited.add((pos, dir))

            if distance > self.ghostAura:
                fraction = (1 - (float(distance) / self.furthestDistance)) * self.rateIfNotCloser
            else:
                fraction = (1 - (float(distance) / (self.ghostAura + 1)))

            self.updateReward(pos, int(self.getReward(pos) + (fraction * self.ghostReward)))

            for d in dirToCheck[dir]:
                next_pos = self.get_next_position(pos, d)
                if next_pos != pos and (next_pos, d) not in visited and next_pos not in self.walls:
                    queue.append((next_pos, d, distance + 1))
    
    def firstGetFurthestDistance(self, ghost):
        visited = set()
        furthestDistance = 0
        initialqueue = deque([(ghost, 0)])
        while initialqueue:
            pos, distance = initialqueue.popleft()
            x, y = pos
            if pos in visited or pos in self.walls or x < 0 or x > self.width or y < 0 or y > self.height:
                continue
            visited.add(pos)
            furthestDistance = max(furthestDistance, distance)
            initialqueue.append(((x - 1, y), distance + 1))
            initialqueue.append(((x + 1, y), distance + 1))
            initialqueue.append(((x, y - 1), distance + 1))
            initialqueue.append(((x, y + 1), distance + 1))
        self.furthestDistance = furthestDistance

    def firstUpdateNeighboursRewards(self, ghost):
        x, y = ghost
        x, y = int(x), int(y)
        ghost = (x, y)
        visited = set()
        queue = deque([(ghost, 0)])
        while queue:
            pos, distance = queue.popleft()
            x, y = pos
            if pos in visited or pos in self.walls or x < 0 or x > self.width or y < 0 or y > self.height:
                continue
            visited.add(pos)
            if distance > self.ghostAura:
                fraction = (1 -  (float(distance) / self.furthestDistance)) * self.rateIfNotCloser
            else:
                fraction = (1 -  (float(distance) / (self.ghostAura + 1)))
       
            self.updateReward(pos, int(self.getReward(pos) + (fraction * self.ghostReward)))
            queue.append(((x - 1, y), distance + 1))
            queue.append(((x + 1, y), distance + 1))
            queue.append(((x, y - 1), distance + 1))
            queue.append(((x, y + 1), distance + 1))
    
    def updateReward(self, pos, reward):
        x, y = pos
        self.reward_grid[self.height - int(y) - 1][int(x)] = reward

    def getUtility(self, pos):
        x, y = pos
        return self.utility_grid[self.height - int(y) - 1][int(x)]

    def getReward(self, pos):
        x, y = pos
        return self.reward_grid[self.height - int(y) - 1][int(x)]

    def updateUtility(self, pos, value):
        x, y = pos
        self.utility_grid[self.height - int(y) - 1][int(x)] = value

    def get_next_position(self, current_pos, direction):
        x, y = current_pos
        if direction == Directions.NORTH:
            return (x, y + 1)
        elif direction == Directions.SOUTH:
            return (x, y - 1)
        elif direction == Directions.EAST:
            return (x + 1, y)
        elif direction == Directions.WEST:
            return (x - 1, y)
        else:
            return current_pos


import copy

class MDPAgent(Agent):
    def __init__(self):
        self.initialised = False
        self.width = 0
        self.height = 0
        self.grid = None
        self.discount = 0.8
        self.food = None
        self.capsules = None
        self.walls = None
        self.ghosts = None
        self.ghostsWithLastDirection = []

    
    def final(self, state):
        self.initialised = False
        self.grid = None
        self.food = None
        self.capsules = None
        self.walls = None
        self.ghosts = None

    
    def getWidthHeight(self, state):
        corners = api.corners(state)
        self.width = corners[1][0] - corners[0][0] + 1
        self.height = corners[2][1] - corners[0][1] + 1
    

    def initialise(self, state):
        self.getWidthHeight(state)
        self.food = set(api.food(state))
        self.capsules = set(api.capsules(state))
        self.walls = set(api.walls(state))
        self.initialised = True

    def getBestHelper(self, state, pos, sameDirectionProb, differentDirectionProb):
        best_direction = None
        best_utility = float('-inf')
        directions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]

        outcomes = {
            Directions.NORTH: (Directions.EAST, Directions.WEST),
            Directions.SOUTH: (Directions.EAST, Directions.WEST),
            Directions.EAST: (Directions.NORTH, Directions.SOUTH),
            Directions.WEST: (Directions.NORTH, Directions.SOUTH)
        }

        for direction in directions:
            next_pos = self.get_next_position(pos, direction)

            if next_pos in self.walls:
                next_pos = pos

            utility = self.grid.getUtility(next_pos) * sameDirectionProb
            for other_direction in outcomes[direction]:
                other_pos = self.get_next_position(pos, other_direction)
                if other_pos in self.walls:
                    other_pos = pos 
                utility += self.grid.getUtility(other_pos) * differentDirectionProb

            if utility > best_utility:
                best_utility = utility
                best_direction = direction

        return best_direction, best_utility
    
    def valueIteration(self, state, sameDirectionProb, differentDirectionProb, epsilon=0.01):
        while True:
            delta = 0 
            new_grid = copy.deepcopy(self.grid) 

            for x in range(self.width):
                for y in range(self.height):
                    current_pos = (x, y)
                    current_reward = self.grid.getReward(current_pos)

                    if current_pos in self.walls:
                        continue 
                    else:
                        d, best_utility = self.getBestHelper(state, current_pos, sameDirectionProb, differentDirectionProb)
                        new_value = current_reward + (self.discount * best_utility)
                        delta = max(delta, abs(new_grid.getUtility(current_pos) - new_value))
                        new_grid.updateUtility(current_pos, new_value)


            self.grid = new_grid 


            if delta < epsilon:
                break



    def getAction(self, state):
        if not self.initialised:
            self.initialise(state)
        pos = api.whereAmI(state)
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        sameDirectionProb = 0.8
        differentDirectionProb = 0.1

        if pos in self.food:
            self.food.remove(pos)
        
        if pos in self.capsules:
            self.capsules.remove(pos)

        current_ghosts = api.ghosts(state)

        if not self.ghosts:
            self.ghostsWithLastDirection = [{'pos': g, 'dir': Directions.STOP} for g in current_ghosts]
        else:
            for i, g in enumerate(current_ghosts):
                if i < len(self.ghostsWithLastDirection):
                    prev_g = self.ghostsWithLastDirection[i]['pos']
                    direction = self.compute_direction(prev_g, g)
                    self.ghostsWithLastDirection[i]['pos'] = g
                    self.ghostsWithLastDirection[i]['dir'] = direction
                else:
                    self.ghostsWithLastDirection.append({'pos': g, 'dir': Directions.STOP})

        self.ghosts = current_ghosts
        # do ghosts shadow here to check direction ghosts are moving in
        # pass this into grid - grid should only assign negative reward in the direction the ghost is moving in (ghost doesnt back on itself)

        

        self.grid = Grid(self.width, self.height, self.walls, self.food, self.capsules, self.ghostsWithLastDirection)

        self.valueIteration(state, sameDirectionProb, differentDirectionProb)

        best_direction, _ = self.getBestHelper(state, pos, sameDirectionProb, differentDirectionProb)
        return api.makeMove(best_direction, legal)

    
    def get_next_position(self, current_pos, direction):
        x, y = current_pos
        if direction == Directions.NORTH:
            return (x, y + 1)
        elif direction == Directions.SOUTH:
            return (x, y - 1)
        elif direction == Directions.EAST:
            return (x + 1, y)
        elif direction == Directions.WEST:
            return (x - 1, y)
        else:
            return current_pos
        
    def compute_direction(self, prev, current):
        x1, y1 = prev
        x2, y2 = current
        if x2 == x1 and y2 == y1 + 1:
            return Directions.NORTH
        elif x2 == x1 and y2 == y1 - 1:
            return Directions.SOUTH
        elif x2 == x1 + 1 and y2 == y1:
            return Directions.EAST
        elif x2 == x1 - 1 and y2 == y1:
            return Directions.WEST
        else:
            return Directions.STOP