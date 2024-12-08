import copy
import math
import os
import random
import sys
import Game_Settings as G
import classes as cl
from classes import NormalEnemy, Tower, Enemy
import json
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import time
import collections
import pygame

class Game_Map:
    def __init__(self):
        self.list_of_spawner_rows = []
        self.list_of_spawner_columns = []
        self.num_spawners = 0
        self.map_2d = self.create_map(rows=G.Rows,columns=G.Columns,difficulty=G.difficulty_level)
        self.Enemy_Order = []
        self.Enemy_Order_Copy = []
        self.Spawner_Order = self.Create_Spawner_Order()

    def to_dict(self):
        return self.__dict__

    def create_map(self, rows, columns, difficulty):
        self.map_2d = [["empty" for _ in range(columns)] for _ in range(rows)]
        self.num_spawners = difficulty
        if self.num_spawners < 1:
            self.num_spawners = 1
        if self.num_spawners == 1:
            column_distance = int(columns // 2 - (columns // 2 -2))
        elif difficulty < 5:
            column_distance = int(columns // 2 -(columns // 2 -3))
        else:
            column_distance = int(columns // 2 - (columns // 2 -4))

        self.list_of_spawner_rows = []
        self.list_of_spawner_columns = []

        for _ in range(self.num_spawners):
            while True:
                row = random.randint(0, G.Rows - 1)
                col = random.randint(0, column_distance)
                if self.map_2d[row][col] == "empty" and all(self.map_2d[row][i] != "spawner" for i in range(columns)):
                    self.map_2d[row][col] = "spawner"
                    break

            self.list_of_spawner_rows.append(row)
            self.list_of_spawner_columns.append(col)


        for spawner in range(self.num_spawners):
            end_row = rows // 2
            end_column = columns - 1
            self.map_2d = self.Create_Path(self.list_of_spawner_rows[spawner], self.list_of_spawner_columns[spawner], end_row, end_column)

        self.map_2d[rows // 2][columns - 1] = "base"

        return self.map_2d

    def Create_Path(self, spawner_row, spawner_column, end_block_row, end_block_column):
        road_row = spawner_row
        vertical_distance_from_base = end_block_row - spawner_row
        change_direction_counter = 0
        square = spawner_column + 1
        while (road_row != end_block_row or square - change_direction_counter != end_block_column):
            if self.is_within_bounds(road_row, square - change_direction_counter):
                self.map_2d[road_row][square - change_direction_counter] = "road"

            if vertical_distance_from_base != 0:
                direction = random.randint(0, 1)  # 1 means vertical, 0 means horizontal
            else:
                direction = 0
            if square - change_direction_counter == end_block_column:
                direction = 1

            if direction == 1 and vertical_distance_from_base != 0:
                change_direction_counter += 1
                if vertical_distance_from_base > 0 and self.is_within_bounds(road_row + 1, square - change_direction_counter):
                    road_row += 1
                    vertical_distance_from_base -= 1
                elif vertical_distance_from_base < 0 and self.is_within_bounds(road_row - 1, square - change_direction_counter):
                    road_row -= 1
                    vertical_distance_from_base += 1
            square = square + 1
        return self.map_2d

    def is_within_bounds(self, row, column):
        return 0 <= row < len(self.map_2d) and 0 <= column < len(self.map_2d[0])


    def Num_Of_Spawners_Available(self):
        num_of_spawner_tiles = 0
        for row in self.map_2d:
            for tile in row:
                if tile == "spawner":
                    num_of_spawner_tiles += 1
        return num_of_spawner_tiles

    def count_surrounding_tiles(self, tower: Tower, tower_row, tower_column):
        num_of_tiles = 0
        for row in range(max(0, tower_row - tower.attack_range), min(G.Rows, tower_row + tower.attack_range + 1)):
            for column in range(max(0, tower_column - tower.attack_range), min(G.Columns, tower_column + tower.attack_range + 1)):
                if (self.map_2d[row][column] in ["road", "spawner"] or isinstance(self.map_2d[row][column], cl.Enemy)):
                    num_of_tiles += 1
        return num_of_tiles

    def Check_num_of_Tiles(self,tile_type):
        num_of_tiles = 0
        for row in self.map_2d:
            for tile in row:
                if tile == tile_type:
                    num_of_tiles += 1
                if (tile_type == cl.Enemy or tile_type == cl.Tower):
                    if isinstance(tile, tile_type):
                        num_of_tiles += 1
        return num_of_tiles

    def Check_Adjecent_To_Spawner(self, row, column):
        for spawner in range(0,self.num_spawners):
            for r in range(max(0,self.list_of_spawner_rows[spawner]-1), min(G.Rows, self.list_of_spawner_rows[spawner]+1)):
                for c in range(max(0,self.list_of_spawner_columns[spawner]-1), min(G.Rows, self.list_of_spawner_columns[spawner]+1)):
                    if (r == row and c == column):
                        return True

    def Check_Adjecent_To_Base(self, row, column):
        for r in range(G.Rows//2 -1, G.Rows // 2 + 2):
            for c in range(G.Columns-2, G.Columns):
                if (r == row and c == column):
                    return True

    def Create_Spawner_Order(self):
        List_Of_Spawn_Order = []
        for enemy in range(0,1000):
            List_Of_Spawn_Order.append(random.randint(0,self.num_spawners-1))
        return List_Of_Spawn_Order

class Tower_Algorithm:

    def __init__(self, Location_Strategy : str, Money_Strategy : float, Tower_Strategy : [cl.Tower], Upgrade_Strategy : int, Tower_Attack_Strategy : [str], Name):
        self.Location_Strategy = Location_Strategy #Options: "Spread", "Base", "Spawner", "Tiles"
        self.Money_Strategy = Money_Strategy #Options: 0.0-1.0
        self.Tower_Strategy = Tower_Strategy #a list of objects of the subcalss of towers the algorithm will prioritise placing
        self.Upgrade_Strategy = Upgrade_Strategy #Options: 0,1,2
        self.Tower_Attack_Strategy = Tower_Attack_Strategy #Options: "first", "last", "strongest", "weakest"
        self.Name = Name


    def choose_tower_location(self, game_map : Game_Map, tower : cl.Tower):
        temp_map = copy.deepcopy(game_map.map_2d)
        if (self.Location_Strategy == "Spread"):
            for tower in G.List_Of_Towers:
                temp_map = self.check_blocks_in_range(temp_map,tower)
            if not ("spawner" in temp_map or "road" in temp_map):
                temp_map = game_map.map_2d
        best_location_row = 0
        best_location_column = 0
        num_of_tiles = 0
        biggest_num_of_tiles = 0
        list_of_empty_tiles = []
        for row in range(0, G.Rows):
            for column in range(0, G.Columns):
                if (temp_map[row][column] == "empty"):
                    list_of_empty_tiles.append((row, column))
                    if (self.Location_Strategy == "Base"):
                        if (game_map.Check_Adjecent_To_Base(row, column)):
                            return row, column
                    elif (self.Location_Strategy == "Spawner"):
                        if (game_map.Check_Adjecent_To_Spawner(row, column)):
                            return row, column
                    else: #if self.Location_Strategy == "Tiles" or "Spread":
                        num_of_tiles = game_map.count_surrounding_tiles(tower, row, column)
                        if num_of_tiles > biggest_num_of_tiles:
                            biggest_num_of_tiles = num_of_tiles
                            best_location_row = row
                            best_location_column = column

        if (best_location_row == 0 and best_location_column == 0 and game_map.map_2d[best_location_row][best_location_column] != "empty"):
            row, column = list_of_empty_tiles[random.randint(0, len(list_of_empty_tiles) - 1)]
            return row, column
        return best_location_row, best_location_column

    def Place_Tower(self, game_map : Game_Map, Min_Money : float):
        cheapest_tower = cl.MinigunTower(0,0)
        for tower in self.Tower_Strategy:
            if tower.price < cheapest_tower.price:
                cheapest_tower = tower
        if (game_map.Check_num_of_Tiles("empty") == 0): #if no space to place towers, then return the map and dont place a tower
            return game_map.map_2d
        if G.Player_Money < cheapest_tower.price: #if Player money is smaller than the price of the cheapest tower, then return the map and dont place a tower
            return game_map.map_2d
        if (G.Player_Money - cheapest_tower.price < Min_Money): #if Player money minus the price of the cheapest unit will be smaller than the minimum amount of money the Player must have left at the end of the turn, then return the map and dont place a tower
            return game_map.map_2d
        if (len(self.Tower_Strategy) > 0 ):
            Tower_Options = copy.deepcopy(self.Tower_Strategy)
        else:
            Tower_Options = copy.deepcopy(cl.towers_list)
        tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
        while (G.Player_Money < tower.price or G.Player_Money-tower.price < Min_Money):
            tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
        row, column = self.choose_tower_location(game_map, tower)
        tower.row = row
        tower.column = column
        if (len(self.Tower_Attack_Strategy) > 0):
            Attack_Type_Options = self.Tower_Attack_Strategy
        else:
            Attack_Type_Options = cl.towers_attack_types
        tower.attack_type = Attack_Type_Options[random.randint(0,len(Attack_Type_Options)-1)]
        game_map.map_2d[tower.row][tower.column] = tower
        G.List_Of_Towers.append(tower)
        G.Player_Money -= tower.price
        return game_map.map_2d
    def Do_Turn(self, game_map : Game_Map):
        total_money = G.Player_Money
        Normal_Tower_Instance = cl.NormalTower(0,0)
        cheapest_tower_price = 1000
        if len(self.Tower_Strategy) == 0:
            self.Tower_Strategy = copy.deepcopy(cl.towers_list)
        for tower in self.Tower_Strategy:
            if tower.price < cheapest_tower_price:
                cheapest_tower_price = tower.price
                cheapest_tower = tower
        Min_Money = total_money * (1-self.Money_Strategy)#the minimum amount of money that must be left at the end of the turn (according to the Money_strategy)
        while G.Player_Money > Min_Money and G.Player_Money >= cheapest_tower_price and  game_map.Check_num_of_Tiles("empty") > 0:
            Upgrades_Available = False
            if (G.Player_Money- cheapest_tower_price < Min_Money and G.Player_Money - cheapest_tower.upgrade_1_cost < Min_Money): #if the player doesnt have enough money to spend even on the cheapest things then end the function and return the game_map
                return game_map

            temp_list_of_towers = copy.deepcopy(G.List_Of_Towers)
            Upgrades_Available_1 = False
            Upgrades_Available_2 = False
            for t in temp_list_of_towers: #check if there are any towers that can be upgraded
                t : cl.Tower
                if not t.upgrade_1:
                    Upgrades_Available1 = True
                if not t.upgrade_2 and t.upgrade_1:
                    Upgrades_Available_2 = True


            if (self.Upgrade_Strategy == 1 and not Upgrades_Available_1): #i the tower_algorithm prioretises upgrading towers but there arent any available to upgrade, place a tower instead
                game_map.map_2d = self.Place_Tower(game_map,Min_Money)

            elif (self.Upgrade_Strategy == 0 and G.Player_Money >= Normal_Tower_Instance.price and G.Player_Money-cheapest_tower_price >= Min_Money):
                game_map.map_2d = self.Place_Tower(game_map, Min_Money)

            elif (self.Upgrade_Strategy == 1):
                if (G.Player_Money - cheapest_tower.upgrade_1_cost < Min_Money):
                    return game_map
                else:
                    tower = G.List_Of_Towers[random.randint(0,len(G.List_Of_Towers)-1)]
                    while (G.Player_Money - tower.upgrade_1_cost < Min_Money or tower.upgrade_1 and tower.upgrade_1):
                        tower = G.List_Of_Towers[random.randint(0,len(G.List_Of_Towers)-1)]
                    tower.Upgrade_Tower()

            elif (self.Upgrade_Strategy == 2):
                if (not Upgrades_Available_2 and not Upgrades_Available_1):
                    game_map.map_2d = self.Place_Tower(game_map, Min_Money)
                elif (not Upgrades_Available_2 and Upgrades_Available_1):
                    while (G.Player_Money - tower.upgrade_1_cost < Min_Money or tower.upgrade_1 and tower.upgrade_1):
                        tower = G.List_Of_Towers[random.randint(0, len(G.List_Of_Towers) - 1)]
                    tower.Upgrade_Tower()
                else:
                    tower = G.List_Of_Towers[random.randint(0, len(G.List_Of_Towers) - 1)]
                    while (G.Player_Money - tower.upgrade_2_cost < Min_Money or tower.upgrade_2 and not tower.upgrade_1):
                        tower = G.List_Of_Towers[random.randint(0,len(G.List_Of_Towers)-1)]
                    tower.Upgrade_Tower()


            if (not Upgrades_Available_1 and not Upgrades_Available_2 and G.Player_Money >= Normal_Tower_Instance.price):
                if (G.Player_Money - cheapest_tower_price < Min_Money):
                    break
                else:
                    game_map.map_2d = self.Place_Tower(game_map, Min_Money)


    def check_blocks_in_range(self,temp_map,tower):  # this is used to mark blocks in the map as blocks who are in range of the current towers
        for row in range(max(tower.row - tower.attack_range, 0), min(tower.row + tower.attack_range + 1, G.Rows)):
            for column in range(max(tower.column - tower.attack_range, 0),
                                min(tower.column + tower.attack_range + 1, G.Columns)):
                if (temp_map[row][column] in ["road", "spawner"] or isinstance(temp_map[row][column], cl.Enemy)):
                    temp_map[row][column] = "marked"
        return temp_map

class Game:
    def __init__(self, Game_map: Game_Map, Tower_Algorithm: Tower_Algorithm, Enemy_Algorithm, use_rl_agent=False,
                 rl_agent=None):
        self.Game_map = Game_map
        self.Tower_Algorithm = Tower_Algorithm
        self.Enemy_Algorithm = Enemy_Algorithm
        self.use_rl_agent = use_rl_agent  # A Flag to determine if RL agent is used
        self.rl_agent = rl_agent  # The RL agent, if used
        self.rl_agent : DQLAgent
        self.state = None  # To store the current state
        self.previous_state = None
        self.current_reward = None # To store the reward for the action
        self.current_action = None # To store the current action
        self.previous_enemies_killed = 0  # To track the number of enemies killed
    def Run_Game(self):

        # screen, Cell_size = Pygame_animation(self.Game_map.map_2d)
        while True:
            if (G.num_of_rounds > 2000):
                print("ERROR")
            # draw_grid(self.Game_map.map_2d, screen, Cell_size)
            # Run_Animation(screen, self.Game_map.map_2d)
            Remake_Enemy_list(self.Game_map)
            for Tower in range(0, len(G.List_Of_Towers)):
                self.Game_map.map_2d = G.List_Of_Towers[Tower].Check_Attack(self.Game_map.map_2d)
            num_of_enemies = len(G.List_Of_Enemies)
            for enemy in range(0, len(G.List_Of_Enemies)):
                if enemy < len(G.List_Of_Enemies):
                    self.Game_map.map_2d = G.List_Of_Enemies[enemy].Move(self.Game_map.map_2d)
                if (G.Player_HP <= 0):
                    break
                if (len(G.List_Of_Enemies) < num_of_enemies and len(G.List_Of_Enemies) > 0 and enemy < len(
                        G.List_Of_Enemies)):
                    self.Game_map.map_2d = G.List_Of_Enemies[enemy].Move(self.Game_map.map_2d)
                    num_of_enemies = len(G.List_Of_Enemies)


            if (self.previous_state != None):
                self.state = self.collect_state()  # except for the first time, this state is collected after the agent takes his action and all the towers and enemies take their actions
                self.rl_agent.remember(self.previous_state,self.current_action,self.current_reward,self.state,G.Player_HP>0)

            if (G.Player_HP > 0):
                self.Rounds()
            else:
                '''
                print("enemies killed", G.enemies_killed, "rounds survived:", G.num_of_rounds)
                '''
                break

    def Rounds(self):
        #Track enemies killed before this round
        initial_enemies_killed = G.enemies_killed

        if G.num_of_rounds % 4 == 0:
            if self.use_rl_agent and self.rl_agent:
                current_state = self.collect_state()
                action_tuple = self.rl_agent.act(current_state)
                action, tower_type, tower_attack_type, location = action_tuple
                prev_money = G.Player_Money
                reward = self.execute_action(action, tower_type, tower_attack_type, location) #doing the agent's action and giving a reward for the action

                reward += self.calculate_reward_according_to_rounds()

                self.current_action = action_tuple
                self.current_reward = reward
                self.previous_state = current_state
                #print("epsilon: ",{self.rl_agent.epsilon}, "action: " ,{action_tuple}, " reward: ", {self.current_reward}, "prev_money: ", {prev_money}, "money: ",{G.Player_Money})

            self.Game_map.map_2d = self.Enemy_Algorithm(self.Game_map)

            if (G.num_of_rounds % 100 == 0):
                self.rl_agent.replay(self.rl_agent.batch_size)
        if (G.num_of_rounds % 40 == 0):
            if not self.use_rl_agent:
                #Using the regular tower_algorithm
                self.Tower_Algorithm.Do_Turn(self.Game_map)
            G.Enemy_Money = G.Enemy_Money + 10 * float(G.num_of_rounds / 100)
            G.Player_Money = G.Player_Money + 50 + (G.num_of_rounds/10)
        G.num_of_rounds = G.num_of_rounds + 1

    def Fix_Map_Error(self):
        for row in self.Game_map.map_2d:
            for tile in row:
                if isinstance(tile, cl.Enemy):
                    if tile in G.List_Of_Enemies:
                        pass
                    else:
                        self.Game_map.map_2d[tile.row][tile.column] = "road"
        for i in range(0, self.Game_map.num_spawners):
            if isinstance(self.Game_map.map_2d[self.Game_map.list_of_spawner_rows[i]][self.Game_map.list_of_spawner_columns[i]], Enemy) or \
                    self.Game_map.map_2d[self.Game_map.list_of_spawner_rows[i]][self.Game_map.list_of_spawner_columns[i]] == "spawner":
                pass
            else:
                self.Game_map.map_2d[self.Game_map.list_of_spawner_rows[i]][self.Game_map.list_of_spawner_columns[i]] = "spawner"

    def Check_Towers(self):
        num = 0
        for row in self.Game_map.map_2d:
            for tile in row:
                if isinstance(tile, cl.Tower):
                    num+=1
        return num

    def execute_action(self, action, tower_type=None, tower_attack_type = None, location=None):
        reward = 0
        if action == 'place_tower' or action == 0:
            if (tower_type is not None and location is not None):
                tower = tower_type(0,0)
                tower.attack_type = tower_attack_type
                if len(location) != 2:
                    print("ds")
                tower.row, tower.column = location
            else:
                tower = random.choice(cl.List_Of_Towers_Options)(0, 0)  # Choose a random tower
                tower.attack_type = random.choice(cl.towers_attack_types)
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                tower.row,tower.column = row, column
            if G.Player_Money >= tower.price:  # Check if the player can afford the tower
                if (self.Game_map.map_2d[tower.row][tower.column] == "empty"):
                    self.Game_map.map_2d[tower.row][tower.column] = tower
                    G.List_Of_Towers.append(tower)
                    reward += self.calculate_reward(action, tower, (tower.row, tower.column))
                    G.Player_Money -= tower.price
                else:
                    reward += self.calculate_reward(action, tower, (tower.row, tower.column))
            else:
                reward += self.calculate_reward(action, tower, (tower.row, tower.column))
        elif action == 'upgrade_tower' or action == 1:
            if location:
                row, col = location
            else:
                row = random.randint(0,G.Rows-1)
                col = random.randint(0,G.Columns-1)
                tower_type = random.choice(cl.List_Of_Towers_Options)
            if isinstance(self.Game_map.map_2d[row][col],tower_type):
                tower = self.Game_map.map_2d[row][col]
                upgrade_cost = None
                if tower.upgrade_2:
                    upgrade_cost = None
                elif tower.upgrade_1:
                    upgrade_cost = tower.upgrade_2_cost
                else:
                    upgrade_cost = tower.upgrade_1_cost
                if upgrade_cost:
                    if G.Player_Money >= upgrade_cost:  # Check if the player can afford the upgrade
                        tower.Upgrade_Tower()
                        reward += self.calculate_reward(action, tower, location, True)
                    else:
                        reward += self.calculate_reward(action, tower, location)
                else:
                    reward += self.calculate_reward(action, tower, location)
            else:
                reward += self.calculate_reward(action)
        elif action == 'skip_turn' or action == 2:
            reward += self.calculate_reward(action)
            pass

        return reward

    def calculate_reward(self, action, tower= None, tower_location=None, upgrade_tower=False):
        # This function calculates the base reward for the action the agent took

        action_dict = {0:"place_tower",1:"upgrade_tower",2:"skip_turn"}
        reward = 0
        if isinstance(action,int):
            action = action_dict[action]
        if action == "place_tower":
            if (self.Game_map.map_2d[tower.row][tower.column] != tower):
                reward -= 150
            elif G.Player_Money < tower.price:
                reward -= 100  # Not enough money
            elif self.Game_map.count_surrounding_tiles(tower,tower.row,tower.column) == 0:
                reward -= 100  # No places where enemies can be, are in the tower's range
            else:
                # Reward for beneficial placements
                if (len(G.List_Of_Towers) == 1):
                    reward += 100  # A large reward for placing down the first tower
                reward += 50  # A medium reward for placing a tower in a valid location
                reward += 5 * self.Game_map.count_surrounding_tiles(tower,tower.row,tower.column)
                reward += 10 * tower.Check_Surrounding_Enemies(self.Game_map.map_2d)

        elif action == "upgrade_tower":
            # Non-existent or insufficient funds
            if not tower:
                reward -= 100  # Non-existent tower
            else:
                if upgrade_tower:  # If successful upgrade occured
                    reward += 100
                    # Reward for upgrading a tower in a benefiticial location
                    reward += 5 * self.Game_map.count_surrounding_tiles(tower, tower.row, tower.column)
                    reward += 10 * tower.Check_Surrounding_Enemies(self.Game_map.map_2d)
                else:  # If not enough money to upgrade
                    reward -= 50

        elif action == "skip_turn":
            # Reward or punish based on money level
            if self.Game_map.Check_num_of_Tiles("empty") != 0:
                if G.Player_Money > cl.MinigunTower(0,0).price: #the most expensive thing in the game is upgrading a minigun tower to level 2 or buying a minigun tower.
                    reward -= 200 # If the agent has enough money to do the most expensive action but chooses to not take any action then I give him a negative reward

            for tower in cl.towers_list[:-1]:
                if G.Player_Money < tower.price:
                    reward += 10
            # Reward or punish based on health and risk level
            reward += self.calculate_risk_level()
        return reward

    def calculate_risk_level(self):
        risk_level = 0.0
        max_possible_distance = (G.Rows / 2 + G.Columns - 1)

        for enemy in G.List_Of_Enemies:
            # Calculate the distance of the enemy from the base
            enemy_distance_from_base = abs(G.Rows / 2 - enemy.row) + abs(G.Columns - enemy.column - 1)
            distance_factor = max(0.1,
                                  max_possible_distance / enemy_distance_from_base)


            # Calculate each enemy's risk by combining different factors
            enemy_risk = ((enemy.base_damage * enemy.health * distance_factor)) / G.Player_HP

            # Add enemy risk to total risk level
            risk_level += enemy_risk
            #print(enemy, f"damage : {enemy.base_damage}. health : {enemy.health}, distance : {distance_factor}. Player hp: {G.Player_HP}. risk : {enemy_risk}")
        #print(f"{G.List_Of_Enemies}: risk level ",risk_level)

        # Cap risk level to avoid extremely large values
        risk_level = min(risk_level, 500)

        # Determine if the risk level should be a reward or punishment
        if risk_level < 50:
            # If there is a low risk - Small positive reward
            reward = (50-risk_level)
        elif risk_level < 200:
            # If there is a moderate risk - Negative reward
            reward = (50 - risk_level) / 2
        else:
            # If there is a high risk - large negative reward
            reward = -risk_level / 2

        if (G.List_Of_Enemies == 0):
            reward = 50 # A reward for skipping the turn if no enemies on the map
        #print("the reward for skipping the turn is: ", reward)
        return reward

    def calculate_reward_based_on_enemies_killed(self, initial_enemies_killed):

        #Calculate how many enemies were killed during this round
        enemies_killed_this_round = G.enemies_killed - initial_enemies_killed
        reward = enemies_killed_this_round * 5  # Reward is based on enemies killed during this round
        if G.Player_HP > 0:
            reward += G.Player_HP #Bonus reward for keeping the player alive

        return reward

    def calculate_reward_based_on_tower_location(self, tower : cl.Tower): #this function rewards the agent for each tile that the tower he places can reach and a big punishment for placing the tower in a place with no tiles that are in it's attack_range
        tiles_in_tower_range = self.Game_map.count_surrounding_tiles(tower,tower.row,tower.column)
        reward = 0
        if (tiles_in_tower_range == 0):
            reward = -15
        else:
            reward += tiles_in_tower_range * 2
            for row in self.Game_map.map_2d:
                for tile in row:
                    if isinstance(tile, cl.Enemy):
                        reward += 5 #get a bigger reward for placing a tower in range of enemies rather than in range of roads or spawners
        return reward

    def calculate_reward_according_to_rounds(self):
        if G.num_of_rounds <= 100:
            # Gradual increase in the early rounds
            reward = 1 + (G.num_of_rounds / 100) * 5
        elif G.num_of_rounds <= 200:
            # More significant increase in the medium rounds
            reward = 3 + ((G.num_of_rounds - 100) / 10) * 5
        else:
            # Slower increase in the later rounds
            reward = 8 + ((G.num_of_rounds - 200) / 20) * 5  #Reward grows slowly after 200 rounds
        return reward

    def collect_state(self):
        state = [copy.deepcopy(self.Game_map.map_2d),copy.deepcopy(G.List_Of_Towers),copy.deepcopy(G.List_Of_Enemies),copy.copy(G.Player_HP),copy.copy(G.Player_Money)]
        return state


class All_Money_Algorithm(Tower_Algorithm):
    def __init__(self):
        super().__init__(Location_Strategy="Tiles", Money_Strategy=1, Tower_Strategy= copy.deepcopy(cl.towers_list), Upgrade_Strategy=0, Tower_Attack_Strategy=[], Name= "All_Money_Algorithm")

class Spread_Algorithm(Tower_Algorithm):
    def __init__(self):
        super().__init__(Location_Strategy="Spread", Money_Strategy=0.5, Tower_Strategy= copy.deepcopy(cl.towers_list), Upgrade_Strategy=0, Tower_Attack_Strategy=[], Name= "Spread_Algorithm")

class Upgrade_Algorithm(Tower_Algorithm):
    def __init__(self):
        super().__init__(Location_Strategy="Tiles", Money_Strategy=0.5, Tower_Strategy=copy.deepcopy(cl.towers_list), Upgrade_Strategy=2, Tower_Attack_Strategy=[], Name= "Upgrade_Algorithm")

class Local_Search_Algorithm:

    def __init__(self, game_map_template, enemy_algorithm, iterations=100):
        self.game_map_template = game_map_template
        self.enemy_algorithm = enemy_algorithm
        self.iterations = iterations
        self.best_algorithm = None
        self.best_performance = None

    def evaluate_algorithm(self, algorithm):
        global game_number
        Reset_Game_Settings()
        game_map = copy.deepcopy(self.game_map_template)
        game_map.Enemy_Order = copy.copy(game_map.Enemy_Order_Copy)
        game = Game(game_map, algorithm, self.enemy_algorithm)
        start_time = time.time()
        game.Run_Game()
        end_time = time.time()
        game_duration = end_time - start_time

        #Save the game stats
        game_stats = {
            "enemies_killed": G.enemies_killed,
            "rounds": G.num_of_rounds,
            "duration_seconds": game_duration
        }
        return game_stats

    def modify_algorithm(self, algorithm):
        modify_random_attribute(algorithm)
        return algorithm

    def run(self):
        #Initialize with a predetermined algorithm i made
        current_algorithm = Create_Random_Tower_Algorithm("Local_Search_Algorithm")

        self.best_algorithm = copy.deepcopy(current_algorithm)
        self.best_performance = self.evaluate_algorithm(self.best_algorithm)

        for iteration in range(self.iterations):


            #Changing and modifying the current algorithm to make a new one
            new_algorithm = self.modify_algorithm(copy.deepcopy(current_algorithm))
            new_performance = self.evaluate_algorithm(new_algorithm)

            '''
            print(f"Iteration {iteration + 1}/{self.iterations}")
            
            with open("local_search_algorithm_all_results.json", 'a') as f:
                json.dump({"best_algorithm": serialize_algorithm(new_algorithm), "best_performance": new_performance}, f)
                f.write("\n")


            print("current iteration: ", iteration, "performance:", new_performance)
            '''
            #Comparing the new performance with the best performance so far
            if new_performance["rounds"] > self.best_performance["rounds"]:
                self.best_algorithm = copy.deepcopy(new_algorithm)
                self.best_performance = new_performance
                current_algorithm = copy.deepcopy(new_algorithm)

            '''
            print(f"Best performance so far: {self.best_performance}")
            print(f"Current algorithm configuration: {self.best_algorithm.__dict__}")
            '''
        return self.best_algorithm, self.best_performance


class Genetic_Tower_Algorithm(Tower_Algorithm):
    def __init__(self, population_size, generations, mutation_rate, game_map, enemy_algorithm):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.game_map = game_map
        self.enemy_algorithm = enemy_algorithm
        self.population = self.initialize_population()
        self.Best_Performance = 0
        self.Best_Algorithm = None

    def initialize_population(self):
        # Initialize a population of random Tower_Algorithms
        population = []
        for i in range(self.population_size):
            algorithm = Create_Random_Tower_Algorithm("Genetic_Algorithm")
            population.append(algorithm)
        return population

    def evaluate_population(self):
        global game_number
        #Evaluate the performance of each algorithm by running a game and recording its performance
        performance_data = []
        for algorithm in self.population:
            Reset_Game_Settings()
            game_map = copy.deepcopy(self.game_map)
            game_map.Enemy_Order = copy.copy(game_map.Enemy_Order_Copy)
            actual_game = Game(game_map, algorithm, self.enemy_algorithm)
            start_time = time.time()
            actual_game.Run_Game()
            end_time = time.time()
            game_duration = end_time - start_time

            #Evaluating the performance of the algorithm
            game_stats = {
                "algorithm": algorithm,
                "enemies_killed": G.enemies_killed,
                "rounds": G.num_of_rounds,
                "duration_seconds": game_duration
            }
            performance_data.append(game_stats)

            '''
            print(game_stats)
            print(len(Enemy_Options))

            with open("genetic_algorithm_all_results.json", 'a') as f:
                json.dump({"best_algorithm": serialize_algorithm(game_stats["algorithm"]), "best_performance": dict(list(game_stats.items())[1:])}, f)
                f.write("\n")
            '''

        #Sorting the algorithms by performance (by enemies_killed, rounds survived, etc.) so that we can choose the best ones out of them
        performance_data.sort(key=lambda x: x["rounds"], reverse=True)
        return performance_data

    def select_best_algorithms(self, performance_data, top_n=2):
        #Select the top_n algorithms based on performance
        best_algorithms = [data["algorithm"] for data in performance_data[:top_n]]
        return best_algorithms

    def mutate_algorithm(self, algorithm):
        modify_random_attribute(algorithm)

    def crossover_algorithms(self, parent1, parent2):
        #Creating a new algorithm by combining attributes from two parent algorithms
        child = Tower_Algorithm(
            Location_Strategy=random.choice([parent1.Location_Strategy, parent2.Location_Strategy]),
            Money_Strategy=random.choice([parent1.Money_Strategy, parent2.Money_Strategy]),
            Tower_Strategy=random.choice([parent1.Tower_Strategy, parent2.Tower_Strategy]),
            Upgrade_Strategy=random.choice([parent1.Upgrade_Strategy, parent2.Upgrade_Strategy]),
            Tower_Attack_Strategy=random.choice([parent1.Tower_Attack_Strategy, parent2.Tower_Attack_Strategy]),
            Name="GA_Algorithm"
        )
        return child

    def evolve_population(self, performance_data):
        #Selecting the best algorithms
        best_algorithms = self.select_best_algorithms(performance_data)

        #Creating a new population by mutating and crossing over the best algorithms
        new_population = []
        parent1, parent2 = random.sample(best_algorithms, 2)
        for _ in range(self.population_size):
            if random.random() < self.mutation_rate:
                # Mutation
                algorithm = random.choice(best_algorithms)
                self.mutate_algorithm(algorithm)
            else:
                #Crossover
                algorithm = self.crossover_algorithms(parent1, parent2)
            new_population.append(algorithm)

        self.population = new_population

    def run(self):
        #Here we run the genetic algorithm over several generations
        for generation in range(self.generations):
            '''
            print(f"Generation {generation + 1}")
            '''
            performance_data = self.evaluate_population()
            for item in performance_data:
                if item["rounds"] > self.Best_Performance:
                    self.Best_Performance = item["rounds"]
                    self.Best_Algorithm = copy.deepcopy(item["algorithm"])
            self.evolve_population(performance_data)

        # Returning the best algorithm
        return self.Best_Algorithm



class Simulated_Annealing_Algorithm:
    def __init__(self, game_map_template: Game_Map, enemy_algorithm,
                 initial_temperature: float, cooling_rate: float, iterations: int):
        self.game_map_template = game_map_template
        self.enemy_algorithm = enemy_algorithm
        self.current_algorithm = Create_Random_Tower_Algorithm("Simulated_Annealing_Algorithm")
        self.current_performance = None
        self.best_algorithm = self.current_algorithm
        self.current_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.iterations = iterations

    def acceptance_probability(self, current_performance, new_performance):
        current_score = current_performance["rounds"]
        new_score = new_performance["rounds"]
        if new_score >= current_score:
            if (new_performance["enemies_killed"] >= current_performance["enemies_killed"]):
                return 1.0
            else:
                return math.exp((new_performance["enemies_killed"] - current_performance["enemies_killed"]) / self.current_temperature)
        return math.exp((new_score - current_score) / self.current_temperature)

    def evaluate_algorithm(self, algorithm: Tower_Algorithm):
        Reset_Game_Settings()
        game_map = copy.deepcopy(self.game_map_template)
        game_map.Enemy_Order = copy.copy(game_map.Enemy_Order_Copy)
        actual_game = Game(game_map, algorithm, self.enemy_algorithm)
        start_time = time.time()
        actual_game.Run_Game()
        end_time = time.time()

        game_duration = end_time - start_time
        enemies_killed = G.enemies_killed
        rounds_survived = G.num_of_rounds

        performance_score = {
            "enemies_killed": enemies_killed,
            "rounds": rounds_survived,
            "duration_seconds": game_duration
        }
        return performance_score

    def run(self):
        best_performance = self.evaluate_algorithm(self.best_algorithm)

        for i in range(self.iterations):
            new_algorithm = copy.deepcopy(self.current_algorithm)
            modify_random_attribute(new_algorithm)

            if not self.current_performance:
                self.current_performance = self.evaluate_algorithm(self.current_algorithm)

            '''
            with open("simulated_annealing_algorithm_all_results.json", 'a') as f:
                json.dump({"best_algorithm": serialize_algorithm(new_algorithm), "best_performance": current_performance}, f)
                f.write("\n")
                
                
            '''

            new_performance = self.evaluate_algorithm(new_algorithm)
            '''
            print(f"current: {current_performance}.  next: {new_performance}")
            
            print("iteration: ", i, ", current performance: ", current_performance, " new performance:", new_performance)
            '''
            current_score = self.current_performance["rounds"]
            new_score = new_performance["rounds"]

            acceptance_probability = self.acceptance_probability(self.current_performance, new_performance)
            if acceptance_probability >= random.random():

                self.current_algorithm = new_algorithm
                self.current_performance = new_performance

                # If the new algorithm is accepted, save it as the best algorithm to later return it
                self.best_algorithm = copy.deepcopy(new_algorithm)
                best_performance = self.current_performance

            self.current_temperature *= self.cooling_rate
            self.current_temperature = max(self.current_temperature,0.0001)  # Make sure the temperature is never 0

        return self.best_algorithm, best_performance


class DQLAgent:#Deep Q-Learning (DQL) Agent using PyTorch
    def __init__(self, state_size, action_size):
        self.memory = collections.deque(maxlen=50000)  # Limit the memory size to 50000
        self.state_size = state_size
        self.gamma = 0.95    #Discount rate
        self.epsilon = 1   #Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        self.learning_rate = 0.0005
        self.batch_size = 16
        self.model = self._build_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=1e-5)
        self.best_performance = {
            "enemies_killed": 0,
            "rounds_survived": 0
        }

    def _build_model(self):
        total_tower_types = len(cl.List_Of_Towers_Options)
        map_size = G.Rows * G.Columns  # total number of possible locations on the game_map
        tower_attack_types = 4  # The only special attribute that a tower has that isnt default is its attack_type (first,last,weakest,strongest)
        place_tower_options_size = (map_size*total_tower_types*tower_attack_types)
        upgrade_tower_options_size = (map_size*total_tower_types)
        total_action_space_size = place_tower_options_size+upgrade_tower_options_size+1 # 1 represents skipping turn
        #Making a Neural network with two hidden layers
        model = nn.Sequential(
            nn.Linear(self.state_size, 512),
            nn.ReLU(),
            nn.Linear(512,512),
            nn.ReLU(),
            nn.Linear(512, total_action_space_size)
        )
        return model

    def remember(self, state, action, reward, next_state, done):
        encoded_state = self.encode_state(state)  # Encode current state
        encoded_next_state = self.encode_state(next_state)  # Encode next state
        self.memory.append((encoded_state, action, reward, encoded_next_state, done))  # Store experience

    def act(self, state):
        encoded_state = self.encode_state(state)
        state_tensor = torch.FloatTensor(encoded_state).unsqueeze(0)

        if random.random() <= self.epsilon:
            # Exploration
            action = random.choice(["place_tower", "upgrade_tower", "skip_turn"])
            if action == "place_tower":
                tower_type = random.choice(cl.List_Of_Towers_Options)
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                tower_attack_type = random.choice(cl.towers_attack_types)
                return (action, tower_type, tower_attack_type, (row, column))
            elif action == "upgrade_tower":
                tower_type = random.choice(cl.List_Of_Towers_Options)
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                return (action, tower_type, None, (row,column))
            else:
                return (action, None, None, None)
        else:
            # Exploitation
            q_values = self.model(state_tensor)
            action_index = torch.argmax(q_values[0]).item()  #Get the action with the highest Q-value
            action = self.decode_action(action_index)  #Decode the action back into a usable form
            print(action)
        return action

    def replay(self, batch_size):
        action_map = {
            "place_tower": 0,
            "upgrade_tower": 1,
            "skip_turn": 2
        }

        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        minibatch_predicted_q_values = []  # the predicted q values
        minibatch_target_q_values = []  # the accurate/targeted q values
        for state, (action, tower_type, tower_attack_type, location), reward, next_state, done in minibatch:
            action_index = self.encode_action(action, tower_type, tower_attack_type, location)

            # Converting the encoded state and next state into tensors
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)

            q_values = self.model(state_tensor)
            q_value_for_action = q_values.flatten()[action_index]

            # target is the targeted reward, meaning the desired reward we want the network to predict
            target_q_value = reward
            if not done:
                next_q_values = self.model(next_state_tensor).max(1)[0].item()
                target_q_value += self.gamma * next_q_values

            minibatch_predicted_q_values.append(q_value_for_action)
            minibatch_target_q_values.append(target_q_value)

            # Convert lists to tensors
        minibatch_predicted_q_values = torch.stack(minibatch_predicted_q_values)  # Shape: (batch_size,)
        minibatch_target_q_values = torch.tensor(minibatch_target_q_values, requires_grad=False)  # Shape: (batch_size,)

        # Calculate loss
        loss = F.mse_loss(minibatch_predicted_q_values, minibatch_target_q_values)
        print("loss: ",loss)
        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()  # Ensure all tensors require gradients
        self.optimizer.step()
        # We decay the epsilon after each replay to reduce exploration over time
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)



    def update_performance(self, enemies_killed, rounds_survived):
        if rounds_survived > self.best_performance["rounds_survived"]:
            self.best_performance["rounds_survived"] = rounds_survived
            self.best_performance["enemies_killed"] = enemies_killed

    def save(self, name):
        torch.save(self.model.state_dict(), name)

    def load(self, name):
        self.model.load_state_dict(torch.load(name))

    def encode_action(self, action, tower_type, tower_attack_type, location):
        #Define indices for action types
        action_dict = {"place_tower": 0, "upgrade_tower": 1, "skip_turn": 2}

        #Encoding action type
        if (isinstance(action,str)):
            action_type_index = action_dict[action]
        else:
            action_type_index = action

        #We only need to encode tower type and location for "place_tower"
        if action == "place_tower":
            tower_type_index = cl.List_Of_Towers_Options.index(tower_type)  # Get index of tower type
            tower_attack_type_index = cl.towers_attack_types.index(tower_attack_type)
            location_index = location[0] * G.Columns + location[1]  # Encode location as a single number
            total_tower_types = len(cl.List_Of_Towers_Options)
            total_attack_types = len(cl.towers_attack_types)
            map_size = G.Rows * G.Columns

            #Combininges the indices into a single index
            index = tower_type_index*total_attack_types*map_size+tower_attack_type_index*map_size+location_index
        elif action == "upgrade_tower":
            tower_type_index = cl.List_Of_Towers_Options.index(tower_type)  # Get index of tower type
            location_index = location[0] * G.Columns + location[1]  # Encode location as a single number
            total_tower_types = len(cl.List_Of_Towers_Options)
            total_attack_types = len(cl.towers_attack_types)
            map_size = G.Rows * G.Columns

            # Combininges the indices into a single index
            index = (total_attack_types*total_tower_types*map_size) + (tower_type_index*map_size+location_index)
        else:
            total_tower_types = len(cl.List_Of_Towers_Options)
            total_attack_types = len(cl.towers_attack_types)
            map_size = G.Rows * G.Columns
            index = (total_attack_types*total_tower_types*map_size) + (total_tower_types*map_size)
        return index


    def decode_action(self, index):
        action_dict = {0: "place_tower", 1: "upgrade_tower", 2: "skip_turn"}
        total_tower_types = len(cl.List_Of_Towers_Options)
        tower_attack_types = 4
        map_size = G.Rows * G.Columns
        place_tower_options_size = (map_size*total_tower_types*tower_attack_types)
        upgrade_tower_options_size = (map_size*total_tower_types)
        total_actions = place_tower_options_size+upgrade_tower_options_size+1

        #Decoding action type
        action = None
        if (index >= (place_tower_options_size)): #if index is upgrade_tower or skip_turn
            if (index == total_actions-1):
                action = "skip_turn"
            else:
                action = "upgrade_tower"
        else:
            action = "place_tower"

        if action == "place_tower":
            # Decoding tower type and location
            tower_type_index = int(index / (map_size*tower_attack_types))
            tower_attack_type_index = int(index/map_size)-(tower_type_index*tower_attack_types)
            location_index = index - ((tower_type_index*(map_size*tower_attack_types)+(tower_attack_type_index* map_size)))

            # Converting indexes to values
            row = location_index // G.Columns
            column = location_index % G.Columns
            location = (row, column)
            tower_type = cl.List_Of_Towers_Options[tower_type_index]
            tower_attack_type = cl.towers_attack_types[tower_attack_type_index]
            return (action, tower_type, tower_attack_type, location)

        elif action == "upgrade_tower":
            # Decoding tower type and location
            index = index-place_tower_options_size
            tower_type_index = int(index / map_size)
            location_index = index - (tower_type_index*map_size)

            # Converting location index back to (row, column)
            row = location_index // G.Columns
            column = location_index % G.Columns
            location = (row, column)
            tower_type = cl.List_Of_Towers_Options[tower_type_index]
            return (action, tower_type, None, location)
        else:
            return (action, None, None, None)  # "upgrade_tower" and "skip_turn" do not need tower type and location

    def encode_state(self,state):
        game_map = state[0] #the game map (the grid map itself not the object of the class Game_Map)
        towers_list = state[1] #The List_Of_Towers
        enemies_list = state[2] #The List_Of_Enemies
        Player_HP = state[3] #The player's health
        Player_Money = state[4] #The player's money

        encoded_map = []
        encoded_towers = []
        encoded_enemies = []
        #every object in the state must be a numerical value, therefore, we encode all class object and other things into numerical values and later decode them


        # Encoding the map
        encoded_map = [G.tile_to_value[tile] for row in game_map for tile in row if isinstance(tile,str)]
        # We need to pad the map to ensure fixed size
        expected_map_size = G.Max_Map_Size
        encoded_map += [0] * (expected_map_size - len(encoded_map))  # Pad with '0' (neutral value)

        for tower in towers_list:
            # Encode the tower type as a number according to the price of the tower (1 = NormalTower, 2 = ShotgunTower...) and the tower's row and column.
            tower_type = cl.List_Of_Towers_Options.index(type(tower))
            if tower.upgrade_2:
                tower_level = 2
            elif tower.upgrade_1:
                tower_level = 1
            else:
                tower_level = 0
            tower_attack_type = cl.towers_attack_types.index(tower.attack_type)
            encoded_towers.append((tower_type + 1, tower.row + 1, tower.column + 1, tower_level + 1,
                                   tower_attack_type + 1))  # we add 1 to all the enemy and tower values
            # because in order to use padding in the neural network we cant represent the values like row and column with a 0 therefore in encoding and decoding the state the enemy and tower locations will be according to the row and column NUMBERS and not INDEX

        for enemy in enemies_list:
            # Encode the enemy type as a number according to the price of the enemy (1 = NormalEnemy, 2 = FastEnemy...) and the enemy's row and column.
            enemy_type = cl.List_Of_Enemies_Options.index(type(enemy))
            encoded_enemies.append((enemy_type + 1, enemy.row + 1, enemy.column + 1,
                                    enemy.health))  # we add 1 to all the enemy and tower values
            # because in order to use padding in the neural network we cant represent the values like row and column with a 0 therefore in encoding and decoding the state the enemy and tower locations will be according to the row and column NUMBERS and not INDEX

        encoded_towers, encoded_enemies = self.pad_encode_state(encoded_towers,encoded_enemies,G.Max_Towers,G.Max_Enemies) #Need to pad the non existent enemies and towers so the state size always remains the same

        flattened_towers = [attribute for attributes in encoded_towers for attribute in attributes]
        flattened_enemies = [attribute for attributes in encoded_enemies for attribute in attributes]

        encoded_state = encoded_map + flattened_towers + flattened_enemies + [Player_HP] + [Player_Money] #turning the state into a 1D list
        return encoded_state

    def pad_encode_state(self, encoded_towers, encoded_enemies, max_towers, max_enemies):
        # We need to fill in the state with empty towers and enemies in order to ensure the state size is always the same (meaning the state size is always the max size)
        # Padding towers: each tower has 5 attributes (type, row, column, upgrade_level, attack_type)
        padded_towers = encoded_towers + [(0, 0, 0, 0, 0)] * (max_towers - len(encoded_towers))
        padded_towers = padded_towers[:max_towers]  # Ensure no overflow

        # Padding enemies: each enemy has 4 attributes (type, row, column, health)
        padded_enemies = encoded_enemies + [(0, 0, 0, 0)] * (max_enemies - len(encoded_enemies))
        padded_enemies = padded_enemies[:max_enemies]  # Ensure no overflow

        return padded_towers, padded_enemies

    def decode_state(self, state):
        encoded_map = state[0]
        encoded_towers = state[1]
        encoded_enemies = state[2]

        decoded_map = [["" for column in range(G.Columns)] for row in range(G.Rows)]
        decoded_towers = []
        decoded_enemies = []
        for encoded_tower in encoded_towers:
            if (encoded_tower[0] != 0): #if the tower is real and not padding
                tower_row = encoded_tower[1]-1
                tower_column = encoded_tower[2]-1
                tower_level = encoded_tower[3]-1
                tower_attack_type = encoded_tower[4]-1

                #we lower the row and column and type values of the towers and enemies by 1because of the previous explanation in the encode_State function
                tower = cl.List_Of_Towers_Options[encoded_tower[0]-1](tower_row,tower_column)
                tower.attack_type = cl.towers_attack_types[tower_attack_type]

                temp_Player_Money = G.Player_Money #the upgrade tower function reduces the G.Player_money so we temporarly save it and load it later on

                if tower_level == 1:
                    tower.Upgrade_Tower()
                elif tower_level == 2:
                    tower.Upgrade_Tower()
                    tower.Upgrade_Tower()

                G.Player_Money = temp_Player_Money #we load the player money back

                decoded_towers.append(tower)
                decoded_map[tower.row][tower.column] = tower

        for encoded_enemy in encoded_enemies:
            if (encoded_enemy[0] != 0): #if the enemy is real and not padding
                enemy_row = encoded_enemy[1]-1
                enemy_column = encoded_enemy[2]-1
                # we lower the row and column and type values of the towers and enemies by 1 because of the previous explanation in the encode_State function
                enemy_health = encoded_enemy[3]
                enemy = cl.List_Of_Enemies_Options[encoded_enemy[0]-1](enemy_row,enemy_column)
                enemy.health = enemy_health

                decoded_enemies.append(enemy)
                decoded_map[enemy.row][enemy.column] = enemy

        tile_index = 0
        for row in range(len(decoded_map)):
            for column in range(len(decoded_map[row])):
                tile = decoded_map[row][column]
                if tile == "":
                    decoded_map[row][column] = encoded_map[tile_index]
                    tile_index+=1

        player_hp = state[3]
        player_money = state[4]
        decoded_state =[decoded_map,decoded_towers,decoded_enemies,player_hp,player_money]

        return decoded_state



def train_agent(episodes, Game_map : Game_Map, agent : DQLAgent):#Training the DQL agent
    training_Game_map = Game_map
    for episode in range(episodes):
        episode_game_map = copy.deepcopy(training_Game_map) #every episode will use the exact same game_map
        #Initializing the game with the RL agent
        game = Game(episode_game_map, None, Enemy_Algorithm_function, use_rl_agent=True, rl_agent=agent)

        Reset_Game_Settings() #Reseting all the game variables
        G.Rows = len(episode_game_map.map_2d)
        G.Columns = len(episode_game_map.map_2d[0])

        game.Run_Game()  #Run the game with the RL agent controlling the actions

        #Experience replay to train the agent after every game
        agent.replay(agent.batch_size)

        #Updating the best performance
        print(f"episode: {episode}, enemies killed: {G.enemies_killed}, num_of_rounds: {G.num_of_rounds}")
        agent.update_performance(G.enemies_killed, G.num_of_rounds)

    return agent, agent.best_performance

def save_performance(best_performance, filename='rl_algorithm_results.json'):
    with open(filename, 'a') as f:
        json.dump(best_performance, f)
        f.write("\n")
    print(f"Best performance saved to {filename}", "best performance: ", best_performance)

#Saving the model
def save_model(agent, filename='dql_model.pth'):
    agent.save(filename)
    print(f"Model saved to {filename}")


#Loading the model
def load_model(agent, filename='dql_model.pth'):
    agent.load(filename)
    print(f"Model loaded from {filename}")




def Random_Enemy_Generator_Algorithm(game_map):
    Predetermined_List_Of_Enemies = [] #in order to truly check the effectiveness of each algorithm we must make sure that every time we run the algorithms we use the same map and enemies. Thats why at the start of every "simulation" we will make a predetermined random list of enemies
    Enemy_Options = cl.List_Of_Enemies_Instances
    enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options) - 1)]
    enemy_instance: cl.Enemy
    for rounds in range(0,1000):
        enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options) - 1)]
        enemy_name = enemy_instance.name
        Predetermined_List_Of_Enemies.append(enemy_name)
    return Predetermined_List_Of_Enemies

def Enemy_Algorithm_function(Game_map : Game_Map):
    normal_enemy_instance = NormalEnemy(0, 0)
    i = 0
    enemy = 0
    if (G.num_of_rounds >= 10):
        while (normal_enemy_instance.price < G.Enemy_Money and Game_map.Num_Of_Spawners_Available() > 0):
            Enemies = copy.deepcopy(cl.List_Of_Enemies_Instances)
            if (i == len(Game_map.Enemy_Order)):
                break
            enemy_name = Game_map.Enemy_Order[i]
            for e in Enemies:
                e : cl.Enemy
                if (enemy_name == e.name):
                    enemy = e
                    break
            if (enemy.price > G.Enemy_Money):
                i = i +1
            else:
                game_map = Create_Enemy(Game_map, enemy)
                G.Enemy_Money = G.Enemy_Money - enemy.price
                Game_map.Enemy_Order.pop(i)
    return Game_map.map_2d

def Remake_Enemy_list(Game_map : Game_Map):
    if (len(Game_map.Enemy_Order) == 0):
        Game_map.Enemy_Order = copy.copy(Game_map.Enemy_Order_Copy)
        print("HAD TO REMAKE THE LIST")
    if (len(Game_map.Spawner_Order) == 0):
        Game_map.Spawner_Order = Game_map.Create_Spawner_Order()

def Create_Enemy(Game_map : Game_Map, enemy):
    enemy_location_index = Game_map.Spawner_Order[0]
    Game_map.Spawner_Order.pop(0)
    enemy.row = Game_map.list_of_spawner_rows[enemy_location_index]
    enemy.column = Game_map.list_of_spawner_columns[enemy_location_index]
    while (Game_map.map_2d[enemy.row][enemy.column] != "spawner"):
        enemy_location_index = random.randint(0, Game_map.num_spawners - 1)
        enemy.row = Game_map.list_of_spawner_rows[enemy_location_index]
        enemy.column = Game_map.list_of_spawner_columns[enemy_location_index]
    Game_map.map_2d[enemy.row][enemy.column] = enemy
    G.List_Of_Enemies.append(enemy)
    enemy.OnSpawner = True
    enemy_health_increase_rate = 0.01
    a = enemy_health_increase_rate
    r = G.num_of_rounds//100
    enemy.health = round(enemy.initial_health * (1.2)**(r))
    return Game_map.map_2d

def save_matrices_to_json(matrices, filename):
    with open(filename, 'w') as file:
        json.dump(matrices, file)



def Reset_Game_Settings():
    G.num_of_rounds = 0
    G.List_Of_Towers = []
    G.List_Of_Enemies = []
    G.Player_Money = G.Perm_Player_Money
    G.enemies_killed = 0
    G.Enemy_Money = G.Perm_Enemy_Money
    G.Player_HP = G.Perm_Player_HP

def Create_Random_Tower_Algorithm(name):
    Location_Strategy = random.choice(["Spread", "Base", "Spawner", "Tiles"])
    Money_Strategy = float(random.randint(1, 100)) / 100
    Tower_Strategy = random.sample(copy.deepcopy(cl.towers_list),random.randint(1,len(cl.towers_list)))
    Upgrade_Strategy = random.randint(0,2)
    strategies = ["first", "last", "weakest", "strongest"]
    Tower_Attack_Strategy = random.sample(strategies,random.randint(1,len(strategies)))
    Name = name

    random_algorithm = Tower_Algorithm(
        Location_Strategy=Location_Strategy,
        Money_Strategy=Money_Strategy,
        Tower_Strategy=Tower_Strategy,
        Upgrade_Strategy=Upgrade_Strategy,
        Tower_Attack_Strategy=Tower_Attack_Strategy,
        Name=Name
    )
    return random_algorithm

def modify_random_attribute(algorithm : Tower_Algorithm):
    # List of attributes that can be modified
    attributes = ['Location_Strategy', 'Money_Strategy', 'Tower_Strategy', 'Upgrade_Strategy', 'Tower_Attack_Strategy']

    # Choose a random attribute
    chosen_attribute = random.choice(attributes)
    if chosen_attribute == 'Location_Strategy':
        strategies = ["Spread", "Base", "Spawner", "Tiles"]
        available_strategies = list(set(strategies) - {algorithm.Location_Strategy})
        algorithm.Location_Strategy = random.choice(available_strategies)

    elif chosen_attribute == 'Money_Strategy':
        money_change = float(random.randint(-10,10)/100) #increase or decrease by -0.1 to 0.1
        new_money_strategy = algorithm.Money_Strategy + money_change
        new_money_strategy = max(0.01,new_money_strategy) #ensuring the algorithm spends more than 0%
        new_money_strategy = min(1,new_money_strategy)  # ensuring the algorithm doesn't spend more than 100%
        algorithm.Money_Strategy = new_money_strategy

    elif chosen_attribute == 'Upgrade_Strategy':
        new_upgrade_strategy = algorithm.Upgrade_Strategy
        while new_upgrade_strategy == algorithm.Upgrade_Strategy:
            new_upgrade_strategy = random.choice([0, 1, 2])
        algorithm.Upgrade_Strategy = new_upgrade_strategy

    elif chosen_attribute == 'Tower_Strategy':
        max_towers_list = 100 # The Maximum size of the list
        tower_types = copy.deepcopy(cl.towers_list)
        action = random.choice(['add', 'remove'])
        if (action == 'add' and len(algorithm.Tower_Strategy) < max_towers_list) or (action == 'remove' and len(algorithm.Tower_Strategy) <= 1):
            available_towers = tower_types
            '''for t in tower_types:
                append_tower = True
                for tower in algorithm.Tower_Strategy:
                    if (type(t) == type(tower)):
                        append_tower = False
                if (append_tower):
                    available_towers.append((t))'''
            algorithm.Tower_Strategy.append(random.choice(available_towers))
        else:
            algorithm.Tower_Strategy.remove(random.choice(algorithm.Tower_Strategy))

    elif chosen_attribute == 'Tower_Attack_Strategy':
        strategies = ["first", "last", "strongest", "weakest"]
        action = random.choice(['add', 'remove'])
        max_strategies_list = 100 # The maximum size of the list
        if (action == 'add' and len(algorithm.Tower_Attack_Strategy) < max_strategies_list) or (action == 'remove' and len(algorithm.Tower_Attack_Strategy) <= 1):
            available_strategies = strategies
            '''for s in strategies:
                append_strategy = True
                for strategy in algorithm.Tower_Attack_Strategy:
                    if (s == strategy):
                        append_strategy = False
                if (append_strategy):
                    available_strategies.append((s))'''
            algorithm.Tower_Attack_Strategy.append(random.choice(available_strategies))
        else:
            algorithm.Tower_Attack_Strategy.remove(random.choice(algorithm.Tower_Attack_Strategy))

def serialize_algorithm(algorithm): #there was an error when trying to dump data into a JSON file where the data had objects of classes which cannot be inserted in a JSON file so we use this function to fix it so we put the data in the file
    algorithm_dict = algorithm.__dict__.copy()
    for key, value in algorithm_dict.items():
        if isinstance(value, list):
            algorithm_dict[key] = [v.__class__.__name__ if not isinstance(v, str) else v for v in value]

    return algorithm_dict


def map_settings_generator(simulations_file):
    with open(simulations_file, 'r') as f:
        simulations = json.load(f)
    for simulation in range(0,len(simulations[0])):
        map_gen = copy.deepcopy(simulations[0][simulation][0])
        map_gen: dict
        map_gen_atributes = list(map_gen.values())

        yield map_gen_atributes #Yields the map and map settings part of the simulation

def enemy_options_generator(simulations_file):
    with open(simulations_file, 'r') as f:
        simulations = json.load(f)
        for simulation in range(0,len(simulations[0])):
            yield copy.deepcopy(simulations[0][simulation][1])  # Yield the Enemy_Options part of the simulation

def Set_Game_Settings(Player_money, Player_health, Enemy_Money = 10):
    G.Perm_Player_Money = Player_money
    G.Perm_Player_HP = Player_health
    G.Perm_Enemy_Money = Enemy_Money


def Create_Image(file_name, CELL_SIZE):
    image1 = pygame.image.load(f"D:/Alpha-project/{file_name}.png").convert_alpha()
    image1 = pygame.transform.scale(image1, (CELL_SIZE, CELL_SIZE))
    return image1

def draw_grid(game_map, screen, CELL_SIZE):
    #Clear the screen
    screen.fill((255, 255, 255))

    matrix = [[0 for _ in range(G.Columns)] for _ in range(G.Rows)]

    #Place the correct image according to every tile in the game
    for row in range(G.Rows):
        for column in range(G.Columns):
            x = column * CELL_SIZE
            y = row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            if game_map[row][column] == "empty":
                pygame.draw.rect(screen, (200, 200, 200), rect)
            elif game_map[row][column] == "road":
                screen.blit(Create_Image("road_picture", CELL_SIZE), (x, y))
            elif game_map[row][column] == "spawner":
                screen.blit(Create_Image("spawner_picture", CELL_SIZE), (x, y))
            elif isinstance(game_map[row][column], cl.Enemy):
                screen.blit(Create_Image(f"{game_map[row][column].name}_picture", CELL_SIZE), (x, y))
            elif isinstance(game_map[row][column], cl.Tower):
                screen.blit(Create_Image(f"{game_map[row][column].name}_picture", CELL_SIZE), (x, y))
            elif game_map[row][column] == "base":
                screen.blit(Create_Image("base_picture", CELL_SIZE), (x, y))

            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

def Pygame_animation():
    pygame.init()

    #Visual Constants
    CELL_SIZE = 50
    WIDTH, HEIGHT = G.Columns * CELL_SIZE, G.Rows * CELL_SIZE

    #Setting up the display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game animation")

    return screen, CELL_SIZE


def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

def Run_Animation(screen, game_map):
    clock = pygame.time.Clock()
    handle_events()

    # Update the display
    pygame.display.flip()
    clock.tick(60)
    time.sleep(1)



def Run_Basic_Strategies(algorithms): #to run the most basic strategy in case needed
    with open('simulations.json', 'r') as f:
        simulations = json.load(f)
    for algorithm in algorithms:
        Game_map = Game_Map()
        Actual_Game = Game(Game_map, algorithm, Enemy_Algorithm_function)
        game_number = 0 #an index used to choose which simulation from the list of simulations
        for game in range(0, 100):
            total_enemies_killed = 0
            total_rounds_survived = 0
            total_time_survived = 0
            for avg in range(0, 10):
                print("game number = ",game_number)
                # Reset Variables
                Reset_Game_Settings()

                map_gen_attributes = next(map_settings_generator("simulations.json"))
                list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Enemy_Options, Enemy_Options_Copy, Spawner_Order  = map_gen_attributes

                Game_map.map_2d = game_map
                Game_map.Enemy_Order = Enemy_Options
                Game_map.Enemy_Order_Copy = Enemy_Options_Copy
                G.Rows = len(Game_map.map_2d)
                G.Columns = len(Game_map.map_2d[0])
                Game_map.list_of_spawner_rows = list_of_spawner_rows
                Game_map.list_of_spawner_columns = list_of_spawner_columns
                Game_map.num_spawners = num_spawners
                Game_map.Spawner_Order = Spawner_Order
                Actual_Game.Game_map = Game_map

                start_time = time.time()
                Actual_Game.Run_Game()
                # Save game stats to JSON
                end_time = time.time()
                game_duration = end_time - start_time
                total_time_survived += game_duration
                total_enemies_killed += G.enemies_killed
                total_rounds_survived += G.num_of_rounds
                game_number = game_number +1

            average_enemies_killed = total_enemies_killed / 10
            average_time_survived = total_time_survived / 10
            average_rounds_survived = total_rounds_survived / 10
            game_stats = {
                "difficulty": G.difficulty_level,
                "rounds": average_rounds_survived,
                "enemies_killed": average_enemies_killed,
                "duration_seconds": average_time_survived
            }
            print(game_stats)
            if (game == 0):
                writing_style = "w"
            else:
                writing_style = "a"
            filename = f"game_results_{algorithm.Name}.json"
            with open(filename, writing_style) as f:
                json.dump(game_stats, f)
                f.write("\n")

def Average_Results(algorithm : Tower_Algorithm, game_map: Game_Map, iterations=10):
    total_enemies_killed = 0
    total_rounds_survived = 0
    for i in range(iterations):
        Reset_Game_Settings()
        game = Game(copy.deepcopy(game_map),algorithm,Enemy_Algorithm_function)
        game.Run_Game()
        total_rounds_survived += G.num_of_rounds
        total_enemies_killed += G.enemies_killed
    return (float(total_rounds_survived/iterations), float(total_enemies_killed/iterations))

def Run_Algorithms():
    saving_style = "a"
    for health_category in range(0, 11):
        Set_Game_Settings(100,
                          max(1,10 * health_category))  # this way we can run all the different maps on different game settings
        for game_number in range(0, 5):
            simulation_game_attibutes = next(map_settings_generator("simulations.json"))

            simulation_game_map = Game_Map()
            Reset_Game_Settings()
            list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Enemy_Options, Enemy_Options_Copy, Spawner_Order = simulation_game_attibutes

            simulation_game_map.map_2d = game_map
            simulation_game_map.Enemy_Order = Enemy_Options
            simulation_game_map.Enemy_Order_Copy = Enemy_Options_Copy
            G.Rows = len(simulation_game_map.map_2d)
            G.Columns = len(simulation_game_map.map_2d[0])
            simulation_game_map.list_of_spawner_rows = list_of_spawner_rows
            simulation_game_map.list_of_spawner_columns = list_of_spawner_columns
            simulation_game_map.num_spawners = num_spawners
            simulation_game_map.Spawner_Order = Spawner_Order


            Reset_Game_Settings()
            ga = Genetic_Tower_Algorithm(
                population_size=10,
                generations=10,
                mutation_rate=0.05,
                game_map=copy.deepcopy(simulation_game_map),
                enemy_algorithm=Enemy_Algorithm_function
            )

            best_algorithm = ga.run()
            print("Best algorithm found:", best_algorithm.__dict__)
            with open(f"GA_results{game_number+1}.json", saving_style) as f:
                results = Average_Results(best_algorithm,copy.deepcopy(simulation_game_map))
                json.dump({f"game_num:{game_number+1},health:{health_category+1}: best_algorithm: ": serialize_algorithm(best_algorithm),
                "average_performance": results}, f)
                f.write("\n")

            Reset_Game_Settings()
            simulated_annealing = Simulated_Annealing_Algorithm(
                game_map_template=copy.deepcopy(simulation_game_map),
                enemy_algorithm=Enemy_Algorithm_function,
                initial_temperature=1,
                cooling_rate=0.965,
                iterations=100
            )
            best_algorithm, best_performance = simulated_annealing.run()
            print("Best algorithm found:", best_algorithm.__dict__)
            print("Best performance:", best_performance)

            with open(f"SA_results{game_number+1}.json", saving_style) as f:
                results = Average_Results(best_algorithm,copy.deepcopy(simulation_game_map))
                json.dump(
                    {f"game_num:{game_number+1},health:{health_category+1}: best_algorithm: ": serialize_algorithm(best_algorithm), "average_performance": results},
                    f)
                f.write("\n")

            Reset_Game_Settings()
            local_search = Local_Search_Algorithm(
                game_map_template=copy.deepcopy(simulation_game_map),
                enemy_algorithm=Enemy_Algorithm_function,
                iterations=100  # Need to change this number
            )

            best_algorithm, best_performance = local_search.run()
            print("Best algorithm found:", best_algorithm.__dict__)
            print("Best performance:", best_performance)
            with open(f"LS_results{game_number+1}", saving_style) as f:
                results = Average_Results(best_algorithm,copy.deepcopy(simulation_game_map))
                json.dump(
                    {f"game_num:{game_number+1},health:{health_category+1}: best_algorithm: ": serialize_algorithm(best_algorithm), "average_performance": results},
                    f)
                f.write("\n")

def Run_RLA():
    for health_category in range(0, 11):
        for game_number in range(0, 5):
            Game_map = Game_Map()
            Set_Game_Settings(100, max(1,10*health_category))
            Reset_Game_Settings()
            map_gen_attributes = next(map_settings_generator("simulations.json"))
            list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Enemy_Options, Enemy_Options_Copy, Spawner_Order = map_gen_attributes


            Game_map.map_2d = game_map
            Game_map.Enemy_Order = Enemy_Options
            Game_map.Enemy_Order_Copy = Enemy_Options_Copy
            G.Rows = len(Game_map.map_2d)
            G.Columns = len(Game_map.map_2d[0])
            Game_map.list_of_spawner_rows = list_of_spawner_rows
            Game_map.list_of_spawner_columns = list_of_spawner_columns
            Game_map.num_spawners = num_spawners
            Game_map.Spawner_Order = Spawner_Order


            Max_map_size = G.Max_Map_Size
            Max_Towers = G.Max_Towers
            Max_Enemies = G.Max_Enemies

            Towers_state_attributes = 5 #the number of attributes of the tower we represent in the state (type, row, column, level/how many upgrades and attack type)
            Enemies_state_attributes = 4 #the number of attributes of the enemy we represent in the state (type, row, column, health)
            action_size = 3  # The number of actions the agent can take

            state_size = Max_map_size + (Max_Towers*Towers_state_attributes) + (Max_Enemies*Enemies_state_attributes) + len([G.Player_HP,G.Player_Money]) #the maximum size of the state

            agent = DQLAgent(state_size, action_size)
            if os.path.exists(path="updated_dql_model2.pth"):
                load_model(agent,filename="updated_dql_model2.pth")
            trained_agent, best_performance = train_agent(100, Game_map, agent)
            with open(f"RL_results{game_number+1}.json", 'a') as f:
                json.dump(
                    {f"game_num:{game_number+1},health:{health_category+1}: average_performance: ": best_performance},f)
                f.write("\n")

            # Saving the trained model
            save_model(trained_agent,filename="updated_dql_model2.pth")


Upgrade_Algorithm_instance = Upgrade_Algorithm()
All_Money_Algorithm_instance = All_Money_Algorithm()
Spread_Algorithm_instance = Spread_Algorithm()
algorithms = [All_Money_Algorithm_instance, Spread_Algorithm_instance, Upgrade_Algorithm_instance]

if __name__ == "__main__":
    Which_Simulation = input("write what simulation you want to run").lower()
    if (Which_Simulation == "strategies"):
        Run_Basic_Strategies(algorithms)
    elif (Which_Simulation == "algorithms"):
       Run_Algorithms()
    elif (Which_Simulation == "rla"):
        Run_RLA()
    elif ("reset"):
        Algorithms = ["simulated_annealing_results", "genetic_algorithm_results", "local_search_results","simulated_annealing_algorithm_all_results", "genetic_algorithm_all_results","local_search_algorithm_all_results","rl_algorithm_results"]
        for algorithm in Algorithms:
            with open(f"D:/Alpha-project/{algorithm}.json", 'w') as f:
                pass
    print("THE CODE RUN SUCCESFULLY")