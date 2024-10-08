import copy
import math
import random
import matplotlib.pyplot as plt
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
from collections import deque
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
        horizontal_distance = end_block_column - spawner_column
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

    def count_adjacent_roads(self, row, column):
        adjacent_positions = [
            (row + 1, column),
            (row - 1, column),
            (row, column + 1),
            (row, column - 1)
        ]

        num_of_adjacent_roads = 0
        for r, c in adjacent_positions:
            if self.is_within_bounds(r, c) and self.map_2d[r][c] in ["road", "base", "spawner"]:
                num_of_adjacent_roads += 1

        return num_of_adjacent_roads

    def Num_Of_Spawners_Available(self):
        num_of_spawner_tiles = 0
        for row in self.map_2d:
            for tile in row:
                if tile == "spawner":
                    num_of_spawner_tiles += 1
        return num_of_spawner_tiles

    def Surrounding_tiles(self, tower: Tower, tower_row, tower_column):
        num_of_tiles = 0
        for row in range(max(0, tower_row - tower.attack_range), min(G.Rows, tower_row + tower.attack_range + 1)):
            for column in range(max(0, tower_column - tower.attack_range), min(G.Columns, tower_column + tower.attack_range + 1)):
                if (self.map_2d[row][column] in ["road", "spawner"] or isinstance(self.map_2d[row][column], cl.Enemy)):
                    num_of_tiles += 1
        return num_of_tiles

    def Check_Empty_Tiles(self):
        num_of_empty_tiles = 0
        for row in self.map_2d:
            for tile in row:
                if tile == "empty":
                    num_of_empty_tiles += 1
        return num_of_empty_tiles

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


    def Location(self, game_map : Game_Map, tower : cl.Tower):
        temp_map = copy.deepcopy(game_map.map_2d)
        if (self.Location_Strategy == "Spread"):
            for tower in G.List_Of_Towers:
                temp_map = self.Blocks_In_Range(temp_map,tower)
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
                    elif (self.Location_Strategy == "Tiles"):
                        num_of_tiles = game_map.Surrounding_tiles(tower, row, column)
                        if num_of_tiles > biggest_num_of_tiles:
                            biggest_num_of_tiles = num_of_tiles
                            best_location_row = row
                            best_location_column = column

        if (best_location_row == 0 and best_location_column == 0 and game_map.map_2d[best_location_row][best_location_column] != "empty"):
            if (len(list_of_empty_tiles) == 0):
                print("fasfsdfsdd")
            row, column = list_of_empty_tiles[random.randint(0, len(list_of_empty_tiles) - 1)]
            return row, column
        return best_location_row, best_location_column

    def Place_Tower(self, game_map : Game_Map, Min_Money : float):
        cheapest_tower = cl.MinigunTower(0,0)
        for tower in self.Tower_Strategy:
            if tower.price < cheapest_tower.price:
                cheapest_tower = tower
        if (game_map.Check_Empty_Tiles() == 0): #if no space to place towers, then return the map and dont place a tower
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
        row, column = self.Location(game_map, tower)
        tower.row = row
        tower.column = column
        if (len(self.Tower_Attack_Strategy) > 0):
            Attack_Type_Options = self.Tower_Attack_Strategy
        else:
            Attack_Type_Options = ["first","last","strongest","weakest"]
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
        while G.Player_Money > Min_Money and G.Player_Money >= cheapest_tower_price and  game_map.Check_Empty_Tiles() > 0:
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

        return game_map

    def Blocks_In_Range(self,temp_map,tower):  # this is used to mark blocks in the map as blocks who are in range of the current towers
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
        self.use_rl_agent = use_rl_agent  #A Flag to determine if RL agent is used
        self.rl_agent = rl_agent  #The RL agent, if used
        self.rl_agent : DQNAgent
        self.previous_state = None  #To store the previous state
        self.previous_action = None  #To store the previous action
        self.previous_enemies_killed = 0  #To track the number of enemies killed
    def Run_Game(self):
        global game_number
        '''
        screen, Cell_size = Pygame_animation(self.Game_map.map_2d)
        '''
        while True:
            '''
            draw_grid(self.Game_map.map_2d, screen, Cell_size)
            Run_Animation(screen, self.Game_map.map_2d)
            '''
            num_of_enemies = len(G.List_Of_Enemies)
            temp_num_of_enemies = len(G.List_Of_Enemies)
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
                action, tower_type, location = action_tuple
                #print("action: ", action_tuple)

                reward = self.execute_action(action, tower_type, location) #doing the agent's action and giving a reward for the action
                next_state = self.collect_state()

                reward += self.calculate_reward(G.enemies_killed - initial_enemies_killed)  #Calculating the reward based on the game state
                reward += self.calculate_reward_according_to_rounds()

                #
                if (reward > self.rl_agent.biggest_reward):
                    self.rl_agent.biggest_reward = reward
                #

                #Saving the experience to the agent's memory
                self.rl_agent.remember(current_state, action_tuple, reward, next_state, False)
                #print("reward:", reward)
                #Updating the previous state and action
                self.previous_state = current_state
                self.previous_action = action_tuple
            self.Game_map.map_2d = self.Enemy_Algorithm(self.Game_map)
        if (G.num_of_rounds % 40 == 0):
            if not self.use_rl_agent:
                #Using the regular tower_algorithm
                self.Game_map = self.Tower_Algorithm.Do_Turn(self.Game_map)
            G.Enemy_Money = G.Enemy_Money + 20 * float(G.num_of_rounds / 100)
            G.Player_Money = G.Player_Money + 20 * float(G.num_of_rounds / 100)
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

    def execute_action(self, action, tower_type=None, location=None):
        reward = 0
        if action == 'place_tower' or action == 0:
            if (tower_type is not None and location is not None):
                tower = tower_type(0,0)
                tower.row, tower.column = location
            else:
                tower = random.choice(cl.List_Of_Towers_Options)(0, 0)  # Choose a random tower
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                tower.row,tower.column = row, column
            if G.Player_Money >= tower.price:  # Check if the player can afford the tower
                if (self.Game_map.map_2d[tower.row][tower.column] != "empty"):
                    reward -= 15 #if the agent places a tower in an invalid location get a big punishment
                else:
                    self.Game_map.map_2d[tower.row][tower.column] = tower
                    G.List_Of_Towers.append(tower)
                    G.Player_Money -= tower.price
                    reward += 10 #if the agent places a tower in a valid location get a major reward
                    reward += self.calculate_reward_based_on_tower_location(tower) #calulates an extra reward based on how good the location of the tower is (how many tiles is in the tower's attack range)
            else:
                reward -= 10 #if agent chooses a tower it doesnt have money for get a big punishment
        elif action == 'upgrade_tower' or action == 1:
            if len(G.List_Of_Towers) > 0:
                tower = random.choice(G.List_Of_Towers)  # Choose a random existing tower to upgrade
                if tower.upgrade_2:
                    reward -= 5 #if the agent chooses to upgrade a tower that has already been upgraded to the maximum get a big punishment
                if tower.upgrade_1:
                    upgrade_cost = tower.upgrade_2_cost
                else:
                    upgade_cost = tower.upgrade_1_cost
                if G.Player_Money >= tower.upgrade_2_cost:  # Check if the player can afford the upgrade
                    tower.Upgrade_Tower()
                    reward += 10 #if the agent upgrades a tower get a major reward
                else:
                    reward -= 5 #if the agent tries to upgrade a tower but it doesnt have enough money get a big punishment
            else:
                reward -= 5 #if the agent chooses to upgrade a tower but there are no towers available to upgrade get a big punishment
        elif action == 'skip_turn' or action == 2:
            pass
        return reward

    def calculate_reward(self, initial_enemies_killed):
        #Calculate how many enemies were killed during this round
        enemies_killed_this_round = G.enemies_killed - initial_enemies_killed
        reward = enemies_killed_this_round * 5  # Reward is based on enemies killed during this round
        if G.Player_HP > 0:
            reward += G.Player_HP * 5  #Bonus reward for keeping the player alive

        return reward

    def calculate_reward_based_on_tower_location(self, tower : cl.Tower): #this function rewards the agent for each tile that the tower he places can reach and a big punishment for placing the tower in a place with no tiles that are in it's attack_range
        tiles_in_tower_range = self.Game_map.Surrounding_tiles(tower,tower.row,tower.column)
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
            reward = 1 + (G.num_of_rounds / 100) * 2
        elif G.num_of_rounds <= 200:
            # More significant increase in the medium rounds
            reward = 3 + ((G.num_of_rounds - 100) / 100) * 5
        else:
            # Slower increase in the later rounds
            reward = 8 + (G.num_of_rounds - 200) / 200  #Reward grows slowly after 200 rounds
        return reward

    def collect_state(self):
        #Collect the current state for the RL agent
        return [
            G.Player_Money / 100.0,
            G.Player_HP,
            len(G.List_Of_Towers) / 10.0,
            len(G.List_Of_Enemies) / 10.0
        ]

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
        actual_game = Game(game_map, algorithm, self.enemy_algorithm)
        start_time = time.time()
        actual_game.Run_Game()
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
        current_algorithm = Tower_Algorithm(
            Location_Strategy="Tiles",
            Money_Strategy=1.0,
            Tower_Strategy=copy.deepcopy(cl.towers_list),
            Upgrade_Strategy=0,
            Tower_Attack_Strategy=["first", "last", "weakest", "strongest"],
            Name="Local_Search_Algorithm"
        )

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
            if new_performance["enemies_killed"] > self.best_performance["enemies_killed"]:
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

    def initialize_population(self):
        # Initialize a population of random Tower_Algorithms
        population = []
        for i in range(self.population_size):
            algorithm = Tower_Algorithm(
                Location_Strategy=random.choice(["Spread", "Base", "Spawner", "Tiles"]),
                Money_Strategy=round(random.uniform(0, 1), 2),
                Tower_Strategy=random.sample(cl.towers_list, random.randint(1, len(cl.towers_list))),
                Upgrade_Strategy=random.choice([0, 1, 2]),
                Tower_Attack_Strategy=random.sample(["first", "last", "strongest", "weakest"], random.randint(1, 4)),
                Name="GA_Algorithm"
            )
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
        performance_data.sort(key=lambda x: x["enemies_killed"], reverse=True)
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
                if item["enemies_killed"] > self.Best_Performance:
                    self.Best_Performance = item["enemies_killed"]
            self.evolve_population(performance_data)

        #Returning the best algorithm from the final population
        best_performance = self.evaluate_population()[0]
        best_algorithm = best_performance["algorithm"]
        best_performance.pop("algorithm")
        best_stats = best_performance
        filename = "genetic_algorithm_all_results.json"
        with open(filename, "w") as f:
            json.dump(self.Best_Performance, f)
            f.write("\n")
        return best_algorithm, best_stats



class Simulated_Annealing_Algorithm:
    def __init__(self, game_map_template: Game_Map, enemy_algorithm, initial_algorithm: Tower_Algorithm,
                 initial_temperature: float, cooling_rate: float, iterations: int):
        self.game_map_template = game_map_template
        self.enemy_algorithm = enemy_algorithm
        self.current_algorithm = initial_algorithm
        self.best_algorithm = copy.deepcopy(initial_algorithm)
        self.current_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.iterations = iterations

    def acceptance_probability(self, current_score, new_score):
        if new_score > current_score:
            return 1.0
        return math.exp((new_score - current_score) / self.current_temperature)

    def evaluate_algorithm(self, algorithm: Tower_Algorithm):
        global game_number
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
            "rounds_survived": rounds_survived,
            "duration_seconds": game_duration
        }
        return performance_score

    def run(self):
        best_performance = self.evaluate_algorithm(self.best_algorithm)

        for i in range(self.iterations):
            new_algorithm = copy.deepcopy(self.current_algorithm)
            modify_random_attribute(new_algorithm)

            current_performance = self.evaluate_algorithm(self.current_algorithm)

            '''
            with open("simulated_annealing_algorithm_all_results.json", 'a') as f:
                json.dump({"best_algorithm": serialize_algorithm(new_algorithm), "best_performance": current_performance}, f)
                f.write("\n")
                
                
            '''

            new_performance = self.evaluate_algorithm(new_algorithm)
            '''
            print("iteration: ", i, ", current performance: ", current_performance, " new performance:", new_performance)
            '''
            current_score = new_performance["enemies_killed"]
            best_score = best_performance["enemies_killed"]
            new_score = current_performance["enemies_killed"]

            if self.acceptance_probability(current_score, new_score) >= random.random():
                self.current_algorithm = new_algorithm
                current_performance = new_performance

                if new_score > best_score:
                    self.best_algorithm = copy.deepcopy(new_algorithm)
                    best_performance = new_performance

            self.current_temperature *= self.cooling_rate

        return self.best_algorithm, best_performance


class DQNAgent:#Deep Q-Network (DQN) Agent using PyTorch
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=50000)  #Limit the memory size to 2000
        self.gamma = 0.95    #Discount rate
        self.epsilon = 1.0   #Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.999
        self.learning_rate = 0.0005
        self.batch_size = 64
        self.model = self._build_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.best_performance = {
            "max_cumulative_reward": float('-inf'),
            "max_rounds_survived": 0
        }
        self.biggest_reward = 0

    def _build_model(self):
        total_tower_types = len(cl.List_Of_Towers_Options)
        map_size = G.Rows * G.Columns  # total number of possible locations on the game_map
        total_action_space_size = (total_tower_types * map_size) + 2  #2 for the actions "upgrade_tower" and "skip_turn"
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
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if random.random() <= self.epsilon:
            # Exploration
            action = random.choice(["place_tower", "upgrade_tower", "skip_turn"])
            if action == "place_tower":
                tower_type = random.choice(cl.List_Of_Towers_Options)
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                return (action, tower_type, (row, column))
            else:
                return (action, None, None)
        else:
            # Exploitation
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.model(state_tensor)
            max_q_index = torch.argmax(q_values[0]).item()

            # Decode the index to get the action, tower type, and location
            return self.decode_action(max_q_index)

    def replay(self, batch_size):
        action_map = {
            "place_tower": 0,
            "upgrade_tower": 1,
            "skip_turn": 2
        }

        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, (action, tower_type, location), reward, next_state, done in minibatch:
            action_index = self.encode_action(action, tower_type, location)
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)

            target = reward
            if not done:
                target = reward + self.gamma * torch.max(self.model(next_state_tensor)[0]).item()

            target_f = self.model(state_tensor)
            target_f = target_f.flatten()
            target_f[action_index] = target

            self.optimizer.zero_grad()
            loss = F.mse_loss(target_f, self.model(state_tensor).flatten())
            loss.backward()
            self.optimizer.step()


        #Decay epsilon after each replay to reduce exploration over time
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)



    def update_performance(self, cumulative_reward, rounds_survived):
        if cumulative_reward > self.best_performance["max_cumulative_reward"]:
            self.best_performance["max_cumulative_reward"] = cumulative_reward
        if rounds_survived > self.best_performance["max_rounds_survived"]:
            self.best_performance["max_rounds_survived"] = rounds_survived

    def save(self, name):
        torch.save(self.model.state_dict(), name)

    def load(self, name):
        self.model.load_state_dict(torch.load(name))

    def encode_action(self, action, tower_type, location):
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
            location_index = location[0] * G.Columns + location[1]  # Encode location as a single number
            total_tower_types = len(cl.List_Of_Towers_Options)
            grid_size = G.Rows * G.Columns

            #Combininges the indices into a single index
            index = (action_type_index * total_tower_types * grid_size) + (
                        tower_type_index * grid_size) + location_index
        else:
            index = action_type_index  # "upgrade_tower" and "skip_turn" do not depend on tower type and location

        return index

    def decode_action(self, index):
        action_dict = {0: "place_tower", 1: "upgrade_tower", 2: "skip_turn"}

        total_tower_types = len(cl.List_Of_Towers_Options)
        map_size = G.Rows * G.Columns

        #Decoding action type
        if (index >= (total_tower_types*map_size)): #if index is upgrade_tower or skip_turn
            action = action_dict[index-(total_tower_types*map_size)+1] #if index is 500 or 501 (upgrade_tower or skip_turn) set the action accordingly
        else:
            action = "place_tower"

        if action == "place_tower":
            #Decoding tower type and location
            tower_type_index = int(index / map_size) #normal tower for indexes 0-99, shotgun tower for indexes 100-199 ect...
            location_index = index - (tower_type_index * map_size)

            #Converting location index back to (row, column)
            row = location_index // G.Columns
            column = location_index % G.Columns
            location = (row, column)
            tower_type = cl.List_Of_Towers_Options[tower_type_index]

            return (action, tower_type, location)
        else:
            return (action, None, None)  # "upgrade_tower" and "skip_turn" do not need tower type and location


class TowerDefenseEnvironment:#Environment simulation for the tower defense game
    def __init__(self, game_map : Game_Map):
        self.state = self.reset()
        self.max_rounds = G.num_of_rounds  # Use the actual round counter from the game
        self.game_map = game_map

    def reset(self):
        #Reset the environment to its initial state (reseting the basic Game settings)
        G.Player_HP = 1
        G.num_of_rounds = 0
        G.List_Of_Enemies = []
        G.List_Of_Towers = []
        G.Player_Money = 100

        self.collect_state()
        return self.state
    def collect_state(self):
        self.state = [ #Need to normalize everythng in the state (turn all the numbers into floats between 0 and 1) so we divide each variable correspondingly
            G.Player_Money / 100.0,
            G.Player_HP / 1.0,
            len(G.List_Of_Towers) / 100.0,
            len(G.List_Of_Enemies) / 100.0
        ]



def train_agent(episodes, state_size, action_size, Game_map : Game_Map, agent : DQNAgent, simulation_number):#Training the DQN agent

    for episode in range(episodes):
        print("episode: ", episode)
        environment = TowerDefenseEnvironment(Game_map)
        state = environment.reset()
        cumulative_reward = 0
        done = False

        #Initializing the game with the RL agent
        game = Game(environment.game_map, None, Random_Enemy_Algorithm, use_rl_agent=True, rl_agent=agent)
        game.previous_state = game.collect_state()  #Initializing the previous state

        while not done:
            #Reseting all the variables and making a new Game_map and list of enemies each time
            Reset_Game_Settings()
            map_gen_attributes = next(map_settings_generator("simulations.json"))
            Game_map.map_2d = game_map
            list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Spawner_Order = map_gen_attributes
            Game_map.map_2d = next(enemy_options_generator("simulations.json"))

            G.Rows = len(Game_map.map_2d)
            G.Columns = len(Game_map.map_2d[0])
            Game_map.list_of_spawner_rows = list_of_spawner_rows
            Game_map.list_of_spawner_columns = list_of_spawner_columns
            Game_map.num_spawners = num_spawners
            Game_map.Spawner_Order = Spawner_Order
            game.Game_map = Game_map
            game.Run_Game()  #Run the game with the RL agent controlling the actions
            performance = {"enemies killed: " : G.enemies_killed, "rounds_survived: " : G.num_of_rounds}
            save_performance(performance, filename='rl_algorithm_results.json')
            #After running the game, we calculate the performance and reward
            reward = game.calculate_reward(game.previous_enemies_killed)
            state = game.collect_state()
            cumulative_reward += reward

            #Checking if the game is done
            done = G.Player_HP <= 0

            #If done, store the final experience
            if done:
                agent.remember(game.previous_state, game.previous_action, reward, state, done)

            #Experience replay to train the agent
            agent.replay(agent.batch_size)

        #Updating the best performance
        agent.update_performance(cumulative_reward, G.num_of_rounds)

        if episode % 100 == 0:
            print(f"Episode {episode} completed - Cumulative Reward: {cumulative_reward}")
            print(agent.biggest_reward, agent.best_performance)

    save_model(agent)
    save_performance(agent.best_performance)
    return agent
def save_performance(best_performance, filename='rl_algorithm_results.json'):
    with open(filename, 'a') as f:
        json.dump(best_performance, f)
        f.write("\n")
    print(f"Best performance saved to {filename}", "best performance: ", best_performance)

#Saving the model
def save_model(agent, filename='dqn_model.pth'):
    agent.save(filename)
    print(f"Model saved to {filename}")


#Loading the model
def load_model(agent, filename='dqn_model.pth'):
    agent.load(filename)
    print(f"Model loaded from {filename}")




def Random_Enemy_Generator_Algorithm(game_map):
    Predetermined_List_Of_Enemies = [] #in order to truly check the effectiveness of each algorithm we must make sure that every time we run the algorithms we use the same map and enemies. Thats why at the start of every "simulation" we will make a predetermined random list of enemies
    Enemy_Options = cl.List_Of_Enemies_Options
    enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options) - 1)]
    enemy_instance: cl.Enemy
    for rounds in range(0,1000):
        enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options) - 1)]
        enemy_name = enemy_instance.name
        Predetermined_List_Of_Enemies.append(enemy_name)
    return Predetermined_List_Of_Enemies

def Random_Enemy_Algorithm(Game_map : Game_Map):
    normal_enemy_instance = NormalEnemy(0, 0)
    i = 0
    enemy = 0
    if (G.num_of_rounds >= 10):
        while (normal_enemy_instance.price < G.Enemy_Money and Game_map.Num_Of_Spawners_Available() > 0):
            Enemies = copy.deepcopy(cl.List_Of_Enemies_Options)
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
    enemy.OnSpawner = True
    enemy_health_increase_rate = 0.01
    a = enemy_health_increase_rate
    r = max(G.num_of_rounds//100,1)
    enemy.health = round(enemy.initial_health * (1.2)**(r))
    G.List_Of_Enemies.append(enemy)
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
        new_money_strategy = algorithm.Money_Strategy
        while new_money_strategy == algorithm.Money_Strategy or new_money_strategy > 1 or new_money_strategy < 0:
            new_money_strategy = round(random.uniform(0, 1), 2)
        algorithm.Money_Strategy = new_money_strategy

    elif chosen_attribute == 'Upgrade_Strategy':
        new_upgrade_strategy = algorithm.Upgrade_Strategy
        while new_upgrade_strategy == algorithm.Upgrade_Strategy:
            new_upgrade_strategy = random.choice([0, 1, 2])
        algorithm.Upgrade_Strategy = new_upgrade_strategy

    elif chosen_attribute == 'Tower_Strategy':
        tower_types = copy.deepcopy(cl.towers_list)
        action = random.choice(['add', 'remove'])
        if action == 'add' and len(algorithm.Tower_Strategy) < len(tower_types):
            available_towers = list(set(tower_types) - set(algorithm.Tower_Strategy))
            algorithm.Tower_Strategy.append(random.choice(available_towers))
        elif action == 'remove' and len(algorithm.Tower_Strategy) > 0:
            algorithm.Tower_Strategy.remove(random.choice(algorithm.Tower_Strategy))

    elif chosen_attribute == 'Tower_Attack_Strategy':
        strategies = ["first", "last", "strongest", "weakest"]
        action = random.choice(['add', 'remove'])
        if action == 'add' and len(algorithm.Tower_Attack_Strategy) < len(strategies):
            available_strategies = list(set(strategies) - set(algorithm.Tower_Attack_Strategy))
            algorithm.Tower_Attack_Strategy.append(random.choice(available_strategies))
        elif action == 'remove' and len(algorithm.Tower_Attack_Strategy) > 1:
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

def Pygame_animation(game_map):
    pygame.init()

    #Visual Constants
    CELL_SIZE = 50
    WIDTH, HEIGHT = G.Columns * CELL_SIZE, G.Rows * CELL_SIZE

    #Setting up the display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Matrix Animation")

    #Initializing the grid
    grid = [[0 for _ in range(G.Columns)] for _ in range(G.Rows)]

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
        Actual_Game = Game(Game_map, algorithm, Random_Enemy_Algorithm)
        game_number = 0 #an index used to choose which simulation from the list of simulations
        for game in range(0, 100):
            total_enemies_killed = 0
            total_rounds_survived = 0
            total_time_survived = 0
            for avg in range(0, 10):
                if (game_number == 100):
                    print("asds")
                print("game number = ",game_number)
                # Reset Variables
                Reset_Game_Settings()

                map_gen_attributes= next(map_settings_generator("simulations.json"))
                list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Spawner_Order  = map_gen_attributes
                Enemy_Options = next(enemy_options_generator("simulations.json"))

                Game_map.map_2d = game_map
                Game_map.Enemy_Order = Enemy_Options
                Game_map.Enemy_Order_Copy = copy.copy(Enemy_Options)
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

def Run_Algorithms():
    for money_category in range(0, 2):
        for health_category in range(0, 3):
            Set_Game_Settings(10 ** (money_category + 1),
                              10 ** health_category)  # this way we can run all the different maps on 6 different game modes
            for game_number in range(0, 20):
                if (game_number == 0):
                    saving_style = "w"
                else:
                    saving_style = "a"

                Game_map = Game_Map()
                Reset_Game_Settings()

                map_gen_attributes = next(map_settings_generator("simulations.json"))
                list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Spawner_Order = map_gen_attributes
                Enemy_Options = next(enemy_options_generator("simulations.json"))

                Game_map.map_2d = game_map
                Game_map.Enemy_Order = Enemy_Options
                Game_map.Enemy_Order_Copy = copy.copy(Enemy_Options)
                G.Rows = len(Game_map.map_2d)
                G.Columns = len(Game_map.map_2d[0])
                Game_map.list_of_spawner_rows = list_of_spawner_rows
                Game_map.list_of_spawner_columns = list_of_spawner_columns
                Game_map.num_spawners = num_spawners
                Game_map.Spawner_Order = Spawner_Order

                ga = Genetic_Tower_Algorithm(
                    population_size=10,
                    generations=10,
                    mutation_rate=0.1,
                    game_map=Game_map,
                    enemy_algorithm=Random_Enemy_Algorithm
                )

                best_algorithm, best_stats = ga.run()
                print("Best algorithm found:", best_algorithm.__dict__)
                print("Best stats:", best_stats)
                with open("genetic_algorithm_results.json", saving_style) as f:
                    json.dump({"best_algorithm": serialize_algorithm(best_algorithm), "best_performance": best_stats},
                              f)
                    f.write("\n")

                Game_map = Game_Map()
                Reset_Game_Settings()

                map_gen_attributes = next(map_settings_generator("simulations.json"))
                list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Spawner_Order = map_gen_attributes
                Enemy_Options = next(enemy_options_generator("simulations.json"))

                Game_map.map_2d = game_map
                Game_map.Enemy_Order = Enemy_Options
                Game_map.Enemy_Order_Copy = copy.copy(Enemy_Options)
                G.Rows = len(Game_map.map_2d)
                G.Columns = len(Game_map.map_2d[0])
                Game_map.list_of_spawner_rows = list_of_spawner_rows
                Game_map.list_of_spawner_columns = list_of_spawner_columns
                Game_map.num_spawners = num_spawners
                Game_map.Spawner_Order = Spawner_Order

                simulated_annealing = Simulated_Annealing_Algorithm(
                    game_map_template=Game_map,
                    enemy_algorithm=Random_Enemy_Algorithm,
                    initial_algorithm=All_Money_Algorithm_instance,
                    # this doesnt matter which algorithm we use for the start i just used this one because its the basic one
                    initial_temperature=100.0,
                    cooling_rate=0.95,
                    iterations=100  # Need to change this number
                )

                best_algorithm, best_performance = simulated_annealing.run()
                print("Best algorithm found:", best_algorithm.__dict__)
                print("Best performance:", best_performance)

                with open("simulated_annealing_results.json", saving_style) as f:
                    json.dump(
                        {"best_algorithm": serialize_algorithm(best_algorithm), "best_performance": best_performance},
                        f)
                    f.write("\n")

                Game_map = Game_Map()
                Reset_Game_Settings()

                map_gen_attributes = next(map_settings_generator("simulations.json"))
                list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Spawner_Order = map_gen_attributes
                Enemy_Options = next(enemy_options_generator("simulations.json"))

                Game_map.map_2d = game_map
                Game_map.Enemy_Order = Enemy_Options
                Game_map.Enemy_Order_Copy = copy.copy(Enemy_Options)
                G.Rows = len(Game_map.map_2d)
                G.Columns = len(Game_map.map_2d[0])
                Game_map.list_of_spawner_rows = list_of_spawner_rows
                Game_map.list_of_spawner_columns = list_of_spawner_columns
                Game_map.num_spawners = num_spawners
                Game_map.Spawner_Order = Spawner_Order

                local_search = Local_Search_Algorithm(
                    game_map_template=Game_map,
                    enemy_algorithm=Random_Enemy_Algorithm,
                    iterations=100  # Need to change this number
                )

                best_algorithm, best_performance = local_search.run()
                print("Best algorithm found:", best_algorithm.__dict__)
                print("Best performance:", best_performance)
                with open("local_search_results.json", saving_style) as f:
                    json.dump(
                        {"best_algorithm": serialize_algorithm(best_algorithm), "best_performance": best_performance},
                        f)
                    f.write("\n")

def Run_RLA():
    for j in range(0, 5):
        for i in range(0, 20):
            state_size = 4  # The size of each state
            action_size = 3  # The number of actions the agent can take
            game_number = i

            Game_map = Game_Map()
            Set_Game_Settings(50, 10)
            Reset_Game_Settings()

            map_gen_attributes = next(map_settings_generator("simulations.json"))
            list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Spawner_Order = map_gen_attributes
            Enemy_Options = next(enemy_options_generator("simulations.json"))

            Game_map.map_2d = game_map
            Game_map.Enemy_Order = Enemy_Options
            Game_map.Enemy_Order_Copy = copy.copy(Enemy_Options)
            G.Rows = len(Game_map.map_2d)
            G.Columns = len(Game_map.map_2d[0])
            Game_map.list_of_spawner_rows = list_of_spawner_rows
            Game_map.list_of_spawner_columns = list_of_spawner_columns
            Game_map.num_spawners = num_spawners
            Game_map.Spawner_Order = Spawner_Order
            # Loading the trained model for future use
            loaded_agent = DQNAgent(state_size, action_size)
            load_model(loaded_agent)
            loaded_agent.epsilon = 0.1
            trained_agent = train_agent(1000, state_size, action_size, Game_map, loaded_agent, game_number)

            # Saving the trained model
            save_model(trained_agent)


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
        Algorithms = ["simulated_annealing_results", "genetic_algorithm_results", "local_search_results","simulated_annealing_algorithm_all_results", "genetic_algorithm_all_results","local_search_algorithm_all_results"]
        for algorithm in Algorithms:
            with open(f"D:/Alpha-project/{algorithm}.json", 'w') as f:
                pass
    print("THE CODE RUN SUCCESFULLY")