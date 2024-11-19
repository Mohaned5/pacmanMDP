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

""" Class to represent the grid of the game 

Contains the utility grid and reward grid for the game

Varies the rewards based on a number of rules

"""

class Grid:
    def __init__(self, width, height, walls, food, capsules, ghostsWithLastDirection, pacmanPos, ghostStatesWithTimer, ghostSpawnPositions):
        self.width = width
        self.height = height
        self.utility_grid = [[0 for _ in range(width)] for _ in range(height)]
        self.reward_grid = [[-20 for _ in range(width)] for _ in range(height)] 
        self.ghostReward = -250
        self.foodReward = (-self.ghostReward * 0.9) / float(len(food))
        self.capsuleReward = 200
        self.walls = walls
        self.furthestDistance = 0
        self.rateIfNotCloser = 0.05
        self.ghostAura = 5
        self.pacmanAura = 6
        self.pacmanPos = pacmanPos
        self.ghosts = []
        self.highestCapsuleReward = 200
        self.capsules = capsules
        self.edibleGhosts = []
        self.pacmanPoweredUp = False
        self.food = food

        for ghost in ghostsWithLastDirection:
            self.ghosts.append(ghost['pos'])

        for ghost in ghostStatesWithTimer:
            if ghost[1] > 1:
                self.edibleGhosts.append(ghost[0])
        
        
        for x in range(width):
            for y in range(height):
                if (x, y) in food:
                        self.updateReward((x, y), self.foodReward)   
                elif (x, y) in walls:
                    self.updateUtility((x, y), '#')      
                    self.updateReward((x, y), '#') 
        
        # Higher negative rewards for coords with more walls around them
        for x in range(width):
            for y in range(height):
                if (x, y) not in self.walls:
                    self.updateSquareReward((x, y))
        


        firstStep = False
        for ghost in ghostsWithLastDirection:
            if ghost['dir'] == Directions.STOP:
                firstStep = True
                break
        
        # If first step, update rewards for the first time without considering ghosts directions
        if firstStep:
            if ghostsWithLastDirection:
                if ghostsWithLastDirection:
                    self.firstGetFurthestDistance(ghostsWithLastDirection[0]['pos'])

                for ghost in ghostsWithLastDirection:
                    self.firstUpdateNeighboursRewards(ghost['pos'])
        else:
            # If not first step, apply negative rewards based on the direction of the ghosts and distance from ghosts
            if ghostsWithLastDirection:
                self.getFurthestDistance(ghostsWithLastDirection[0])

            for ghost in ghostsWithLastDirection:
                # If ghost is edible and pacman can get to ghost before timer runs out, apply positive rewards
                if ghost['pos'] in self.edibleGhosts and self.getDistanceBetween(pacmanPos, ghost['pos']) <= ghost['timer']:
                    self.pacmanPoweredUp = True
                    self.updateNeighboursRewards(ghost, -0.3)
                    self.applyNegativeRewardToGhostSpawn(ghostSpawnPositions)
                else:
                    self.updateNeighboursRewards(ghost, 1)    

        self.updateCapsuleRewards()
        self.addFoodDistanceRewards()

    """ Add rewards to the grid based on the distance from the food to incentivise Pacman to eat food """
    def addFoodDistanceRewards(self):
        queue = deque()
        for food in self.food:
            queue.append((food, 0))
        visited = set()
        while queue:
            pos, distance = queue.popleft()
            x, y = pos
            if pos in visited or pos in self.walls or x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            visited.add(pos)
            self.updateReward(pos, self.getReward(pos) + (0.8 * self.foodReward * (1 - (float(distance) / self.furthestDistance))))
            queue.append(((x - 1, y), distance + 1))
            queue.append(((x + 1, y), distance + 1))
            queue.append(((x, y - 1), distance + 1))
            queue.append(((x, y + 1), distance + 1))

    """ Get the distance between two positions """
    def getDistanceBetween(self, pos1, pos2):
        x, y = pos2
        pos2 = (int(x), int(y))
        queue = deque([(pos1, 0)])
        visited = set()
        while queue:
            pos, distance = queue.popleft()
            x, y = pos
            if pos in visited or pos in self.walls or x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            visited.add(pos)
            if pos == pos2:
                return distance
            queue.append(((x - 1, y), distance + 1))
            queue.append(((x + 1, y), distance + 1))
            queue.append(((x, y - 1), distance + 1))
            queue.append(((x, y + 1), distance + 1))
        
        return float('inf')

    """ Apply negative rewards to the spawn positions of the ghosts """
    def applyNegativeRewardToGhostSpawn(self, ghostSpawnPositions):
        for ghost in ghostSpawnPositions:
            x, y = ghost
            self.updateReward(ghost, self.getReward(ghost) + (10 * self.ghostReward))
            if (x - 1, y) not in self.walls:
                self.updateReward((x - 1, y), self.getReward((x - 1, y)) + (10 * self.ghostReward))
            if (x + 1, y) not in self.walls:
                self.updateReward((x + 1, y), self.getReward((x + 1, y)) + (10 * self.ghostReward))
            if (x, y - 1) not in self.walls:
                self.updateReward((x, y - 1), self.getReward((x, y - 1)) + (10 * self.ghostReward))
            if (x, y + 1) not in self.walls:
                self.updateReward((x, y + 1), self.getReward((x, y + 1)) + (10 * self.ghostReward))
            

    """ Update the rewards for the capsules based on the distance of the ghosts from the pacman """
    def updateCapsuleRewards(self):
        if self.pacmanPoweredUp:
            for capsule in self.capsules:
                self.updateReward(capsule, self.getReward(capsule) + (self.ghostReward * 0.2))
            return
        queue = deque([(self.pacmanPos, 0)])
        visited = set()
        capsuleReward = 0
        while queue:
            pos, distance = queue.popleft()
            x, y = pos
            if pos in visited or pos in self.walls or x < 0 or x >= self.width or y < 0 or y >= self.height or distance > self.pacmanAura:
                continue
            visited.add(pos)
            if pos in self.ghosts:
                capsuleReward = (1 - (float(distance) / self.pacmanAura)) * self.highestCapsuleReward
            queue.append(((x - 1, y), distance + 1))
            queue.append(((x + 1, y), distance + 1))
            queue.append(((x, y - 1), distance + 1))
            queue.append(((x, y + 1), distance + 1))
        
        for capsule in self.capsules:
            self.updateReward(capsule, self.getReward(capsule) + capsuleReward)


    def updateSquareReward(self, coord):
        x, y = coord
        numOfWalls = 0
        if (x - 1, y) in self.walls:
            numOfWalls += 1
        if (x + 1, y) in self.walls:
            numOfWalls += 1
        if (x, y - 1) in self.walls:
            numOfWalls += 1
        if (x, y + 1) in self.walls:
            numOfWalls += 1
        
        reward = self.getReward(coord)
        if numOfWalls == 3:
            if reward > 0:
                self.updateReward(coord, reward * 0.2)
            else:
                self.updateReward(coord, reward * 5)
        elif numOfWalls == 2:
            if reward > 0:
                self.updateReward(coord, reward * 0.6)
            else:
                self.updateReward(coord, reward * (5.0/3))
        elif numOfWalls == 1:
            if reward > 0:
                self.updateReward(coord, reward * 0.8)
            else:
                self.updateReward(coord, reward * (5.0/4))
    
    """ Get the furthest distance any object can travel from a given position without repeating steps """
    def getFurthestDistance(self, ghost):
        visited = set()
        furthestDistance = 10
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

    """ The closer a square is to a ghost, the higher the negative reward """
    def updateNeighboursRewards(self, ghost, multiplier):
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

        opposite = {
            Directions.NORTH: Directions.SOUTH,
            Directions.SOUTH: Directions.NORTH,
            Directions.EAST: Directions.WEST,
            Directions.WEST: Directions.EAST
        }

        bx, by = self.get_next_position((x, y), opposite[direction])
        if (bx, by) not in self.walls:
            self.updateReward((bx, by), (self.getReward((bx, by)) + (2 * self.ghostReward * multiplier)))

        while queue:
            pos, dir, distance = queue.popleft()
            x, y = pos
            if (pos, dir) in visited or pos in self.walls or x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            visited.add((pos, dir))

            if distance > self.ghostAura:
                fraction = (1 - (float(distance) / self.furthestDistance)) * self.rateIfNotCloser
            else:
                if distance <= 1:
                    fraction = 2
                else:
                    fraction = (1 - (float(distance) / (self.ghostAura + 1)))

            self.updateReward(pos, (self.getReward(pos) + (fraction * self.ghostReward * multiplier)))

            for d in dirToCheck[dir]:
                next_pos = self.get_next_position(pos, d)
                if next_pos != pos and (next_pos, d) not in visited and next_pos not in self.walls:
                    queue.append((next_pos, d, distance + 1))
    
    """ Initial furthest distance """
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

    """ Initial update rewards for the first time without considering the direction of the ghosts """
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
       
            self.updateReward(pos, self.getReward(pos) + (fraction * self.ghostReward))
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
        self.ghostsSpawnPositions = []

    
    def final(self, state):
        self.initialised = False
        self.grid = None
        self.food = None
        self.capsules = None
        self.walls = None
        self.ghosts = None
        self.ghostsWithLastDirection = []
        self.ghostsSpawnPositions = []

    
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
        self.ghostsSpawnPositions = api.ghosts(state)

    """ Get the best direction to move in based on the current position and surrounding utilities"""
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
    
    """ Value iteration algorithm """
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

        current_ghosts = api.ghostStatesWithTimes(state)

        # Gets the ghosts and the direction they are moving in
        if not self.ghosts:
            self.ghostsWithLastDirection = [{'pos': g[0], 'dir': Directions.STOP, 'timer': g[1]} for g in current_ghosts]
        else:
            for i, g in enumerate(current_ghosts):
                if i < len(self.ghostsWithLastDirection):
                    prev_g = self.ghostsWithLastDirection[i]['pos']
                    direction = self.compute_direction(prev_g, g[0])
                    self.ghostsWithLastDirection[i]['pos'] = g[0]
                    self.ghostsWithLastDirection[i]['dir'] = direction
                    self.ghostsWithLastDirection[i]['timer'] = g[1]
                else:
                    self.ghostsWithLastDirection.append({'pos': g[0], 'dir': Directions.STOP, 'timer': g[1]})

        self.ghosts = current_ghosts
        
        ghostsStateWithTimer = api.ghostStatesWithTimes(state)

        self.grid = Grid(self.width, self.height, self.walls, self.food, self.capsules, self.ghostsWithLastDirection, pos, ghostsStateWithTimer, self.ghostsSpawnPositions)

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
        
    """ Compute the direction of the ghost """
    def compute_direction(self, prev, current):
        x1, y1 = prev
        x2, y2 = current
        dx = x2 - x1
        dy = y2 - y1
        epsilon = 0.1  

        if abs(dx) < epsilon and dy > epsilon:
            return Directions.NORTH
        elif abs(dx) < epsilon and dy < -epsilon:
            return Directions.SOUTH
        elif dx > epsilon and abs(dy) < epsilon:
            return Directions.EAST
        elif dx < -epsilon and abs(dy) < epsilon:
            return Directions.WEST
        else:
            return Directions.STOP
