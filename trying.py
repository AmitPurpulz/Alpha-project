import copy
import random
import sys

import numpy as np
import matplotlib.pyplot as plt
import pickle
import Game_Settings as G
import classes as cl
from classes import NormalTower, NormalEnemy, Tower, Enemy
import plotly as pl
import json
import time
from matplotlib.colors import ListedColormap

#THIS IS THE ALGORITHMS FILE I HAVE A CIRCULAR IMPORT ISSUE SO I TEMPORARILY MOVE THE ALGORITHMS FILE HERE
towers = list(cl.towers.values())
Enemies = (cl.List_Of_Enemies_Options)
cheapest = towers[0]
check_SpreadAlgorithm = False
Enemy_Options = []
Money_Percentage = 0

class Game_Map:
    def __init__(self):
        self.list_of_spawner_rows = []
        self.list_of_spawner_columns = []
        self.num_spawners = 0
        self.map_2d = self.create_map(rows,columns,difficulty_level)

    def to_dict(self):
        return self.__dict__

    def create_map(self, rows, columns, difficulty):
        self.map_2d = [["empty" for _ in range(columns)] for _ in range(rows)]
        self.num_spawners = 1
        valid_difficulties = ["easy", "medium", "hard"]

        while difficulty not in valid_difficulties:
            difficulty = input("Please type the difficulty again (easy, medium, hard): ").lower()

        if difficulty == "easy":
            self.map_2d[rows // 2][0] = "spawner"
        elif difficulty == "medium":
            self.num_spawners = 2
            self.column_distance = int(columns // 2 - 2)
        elif difficulty == "hard":
            self.num_spawners = 3
            self.column_distance = int(columns // 2 - 1)

        self.list_of_spawner_rows = []
        self.list_of_spawner_columns = []

        for _ in range(self.num_spawners):
            while True:
                if difficulty != "easy":
                    row = random.randint(0, rows - 1)
                    col = random.randint(0, self.column_distance)
                    if self.map_2d[row][col] == "empty" and all(self.map_2d[row][i] != "spawner" for i in range(columns)):
                        self.map_2d[row][col] = "spawner"
                        break
                else:
                    row = rows // 2
                    col = 0
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
        for row in range(max(0, tower_row - tower.attack_range), min(rows, tower_row + tower.attack_range + 1)):
            for column in range(max(0, tower_column - tower.attack_range),
                                min(columns, tower_column + tower.attack_range + 1)):
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
        for spawner in range(0,num_spawners):
            for r in range(max(0,list_of_spawner_rows[spawner]-1), min(rows, list_of_spawner_rows[spawner]+1)):
                for c in range(max(0,list_of_spawner_columns[spawner]-1), min(rows, list_of_spawner_columns[spawner]+1)):
                    if (r == row and c == column):
                        return True

    def Check_Adjecent_To_Base(self, row, column):
            for r in range(rows//2 -1, rows // 2 + 2):
                for c in range(columns-2, columns):
                    if (r == row and c == column):
                        return True
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
        for row in range(0, rows):
            for column in range(0, columns):
                if (temp_map[row][column] == "empty"):
                    if (self.Location_Strategy == "Base"):
                        if (game_map.Check_Adjecent_To_Base(row, column)):
                            return row, column
                    elif (self.Location_Strategy == "Spawmer"):
                        if (game_map.Check_Adjecent_To_Spawner(row, column)):
                            return row, column
                    list_of_empty_tiles.append((row, column))
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
        global towers
        if G.Player_Money < cl.NormalTower(0,0).price:
            return game_map.map_2d
        if (len(self.Tower_Strategy) > 0 ):
            Tower_Options = copy.deepcopy(self.Tower_Strategy)
        else:
            Tower_Options = copy.deepcopy(towers)
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
        for tower in self.Tower_Strategy:
            if tower.price < cheapest_tower_price:
                cheapest_tower_price = tower.price
        Min_Money = total_money * (1-self.Money_Strategy)#the minimum amount of money that must be left at the end of the turn (according to the Money_strategy)
        while G.Player_Money > total_money * (1-self.Money_Strategy) and G.Player_Money >= cl.NormalTower(0,0).price and game_map.Check_Empty_Tiles() > 0:
            Upgrades_Available = False
            if (self.Upgrade_Strategy == 0 and G.Player_Money >= Normal_Tower_Instance.price and G.Player_Money-cheapest_tower_price >= Min_Money):
                game_map.map_2d = self.Place_Tower(game_map, Min_Money)
            elif (self.Upgrade_Strategy == 1):
                for tower in G.List_Of_Towers:
                    if (not tower.upgrade_1) and G.Player_Money >= tower.upgrade_1_cost and G.Player_Money-tower.upgrade_1_cost >= Min_Money:
                        tower.Upgrade_Tower()
                        Upgrades_Available = True
                        break
                for tower in G.List_Of_Towers:
                    if (not tower.upgrade_2) and G.Player_Money >= tower.upgrade_2_cost and G.Player_Money-tower.upgrade_2_cost >= Min_Money:
                        tower.Upgrade_Tower()
                        Upgrades_Available = True
                        break
            elif (self.Upgrade_Strategy == 2):
                for tower in G.List_Of_Towers:
                    if (not tower.upgrade_2) and G.Player_Money >= tower.upgrade_2_cost and G.Player_Money-tower.upgrade_2_cost >= Min_Money:
                        tower.Upgrade_Tower()
                        Upgrades_Available = True
                        break
                for tower in G.List_Of_Towers:
                    if (not tower.upgrade_1) and G.Player_Money >= tower.upgrade_1_cost and G.Player_Money-tower.upgrade_1_cost >= Min_Money:
                        tower.Upgrade_Tower()
                        Upgrades_Available = True
                        break
            if (not Upgrades_Available and G.Player_Money >= Normal_Tower_Instance.price):
                if (G.Player_Money - cheapest_tower_price < Min_Money):
                    break
                else:
                    game_map.map_2d = self.Place_Tower(game_map, Min_Money)
        return game_map

    def Blocks_In_Range(self,temp_map,tower):  # this is used to mark blocks in the map as blocks who are in range of the current towers
        for row in range(max(tower.row - tower.attack_range, 0), min(tower.row + tower.attack_range + 1, rows)):
            for column in range(max(tower.column - tower.attack_range, 0),
                                min(tower.column + tower.attack_range + 1, columns)):
                if (temp_map[row][column] in ["road", "spawner"] or isinstance(temp_map[row][column], cl.Enemy)):
                    temp_map[row][column] = "marked"
        return temp_map

class All_Money_Algorithm(Tower_Algorithm):
    def __init__(self):
        super().__init__(Location_Strategy="Tiles", Money_Strategy=1, Tower_Strategy= [], Upgrade_Strategy=0, Tower_Attack_Strategy=[], Name= "All_Money_Algorithm")

class Spread_Algorithm(Tower_Algorithm):
    def __init__(self):
        super().__init__(Location_Strategy="Spread", Money_Strategy=0.5, Tower_Strategy= [], Upgrade_Strategy=0, Tower_Attack_Strategy=[], Name= "Spread_Algorithm")

class Upgrade_Algorithm(Tower_Algorithm):
    def __init__(self):
        super().__init__(Location_Strategy="Tiles", Money_Strategy=0.5, Tower_Strategy=[], Upgrade_Strategy=2, Tower_Attack_Strategy=[], Name= "Upgrade_Algorithm")


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

def Random_Enemy_Algorithm(Game_map):
    global Enemy_Options
    normal_enemy_instance = NormalEnemy(0, 0)
    i = 0
    enemy = 0
    game_map = Game_map.map_2d
    while (normal_enemy_instance.money_drop < G.Enemy_Money and Game_map.Num_Of_Spawners_Available() > 0):
        Enemies = copy.deepcopy(cl.List_Of_Enemies_Options)
        if (i == len(Enemy_Options)):
            break
        enemy_name = Enemy_Options[i]
        for e in Enemies:
            e : cl.Enemy
            if (enemy_name == e.name):
                enemy = e
                break
        if (enemy.money_drop > G.Enemy_Money):
            i = i +1
        else:
            game_map = Create_Enemy(game_map, enemy)
            G.Enemy_Money = G.Enemy_Money - enemy.money_drop
            Enemy_Options.pop(i)
    return game_map
'''
def All_Money_Algorithm(game_map):
    global towers
    while (G.Player_Money > cl.NormalTower(0,0).price and Check_Empty_Tiles(game_map) > 0):
        game_map = Random_Algorithm(game_map)
    return game_map

def Best_Money_Usage_Algorithm(game_map): #this algorithm is a local search algorithm whose purpose is to find the most optimal value of how much percent of the Player's money the algorithm should use every round
    global Money_Percentage
    total_money = G.Player_Money
    while G.Player_Money > total_money * (1-Money_Percentage) and G.Player_Money > cheapest.price and Check_Empty_Tiles(game_map) > 0:
        game_map = Random_Algorithm(game_map)
    return game_map
    
def Random_Algorithm(game_map):
    global towers
    Tower_Options = copy.deepcopy(towers)
    normal_tower_instance = NormalTower(0, 0)
    tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
    if (Check_Empty_Tiles(game_map) == 0):
        return game_map
    while (tower.price > G.Player_Money):
        Tower_Options = copy.deepcopy(towers)
        tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
        if G.Player_Money < normal_tower_instance.price:
            return game_map
    tower.row, tower.column = Best_Location(game_map, tower)
    if (tower.row == rows):
        return game_map
    G.Player_Money = G.Player_Money - tower.price
    tower.attack_type = random.choice(["first","last","strongest","weakest"])
    game_map[tower.row][tower.column] = tower
    G.List_Of_Towers.append(tower)
    return game_map

def Check_No_Towers(game_map):
    global rows, columns
    for row in range(0,rows):
        for column in range(0,columns):
            if isinstance(game_map[row][column], Tower):
                return False
    return True

def Blocks_In_Range(temp_map, tower): # this is used to mark blocks in the map as blocks who are in range of the current towers
    for row in range(max(tower.row - tower.attack_range, 0), min(tower.row + tower.attack_range + 1, rows)):
        for column in range(max(tower.column - tower.attack_range, 0), min(tower.column + tower.attack_range + 1, columns)):
            if (temp_map[row][column] in ["road", "spawner"] or isinstance(temp_map[row][column], cl.Enemy)):
                temp_map[row][column] = "marked"
    return temp_map

def SpreadPlacement_Algorithm(game_map, asmdas : Game_Map):
    global towers, cheapest, check_SpreadAlgorithm
    check_SpreadAlgorithm = True
    num_of_tiles = 0
    temp_map = copy.deepcopy(game_map.map_2d)
    if (Check_Empty_Tiles(game_map) == 0):
        return game_map
    if (Check_No_Towers(game_map)):
        game_map = Random_Algorithm(game_map=game_map)
    else:
        for tower in G.List_Of_Towers:
            temp_map = Blocks_In_Range(temp_map, tower)
        num_of_tiles = 0
        tower = towers[random.randint(0, len(cl.towers) - 1)]
        while (tower.price > G.Player_Money):
            tower = towers[random.randint(0, len(cl.towers) - 1)]
            if G.Player_Money < cheapest.price:
                return game_map
        tower.row, tower.column = Best_Location(temp_map, tower)
        if (tower.row == rows):
            return game_map
        G.Player_Money = G.Player_Money - tower.price
        game_map[tower.row][tower.column] = tower
        G.List_Of_Towers.append(tower)
    print(game_map)
    return game_map



def Expensive_Algorithm(game_map):
    global towers, cheapest
    while (G.Player_Money >= cheapest.price):
        if (Check_Empty_Tiles(game_map) == 0):
            return game_map
        for tower_price in range(len(towers) - 1, -1, -1):
            if (G.Player_Money >= towers[tower_price].price):
                tower = towers[tower_price]
                tower.row, tower.column = Best_Location(game_map, tower)
                if (tower.row == False):
                    return game_map
                G.Player_Money = G.Player_Money - towers[tower_price].price
                game_map[tower.row][tower.column] = tower
                G.List_Of_Towers.append(tower)
                break
    return game_map

def Upgrade_Towers_Algorithm(game_map):
    Upgrades_Available = False
    for tower in G.List_Of_Towers:
        if (not tower.upgrade_1) and G.Player_Money>tower.upgrade_1_cost:
            tower.Upgrade_Tower()
            Upgrades_Available = True
            elif (not tower.upgrade_2) and G.Player_Money > tower.upgrade_2_cost:
            tower.Upgrade_Tower()
            Upgrades_Available = True
    if (not Upgrades_Available):
        game_map = Random_Algorithm(game_map)
    return game_map


def Best_Location(game_map, tower: Tower):
    global check_SpreadAlgorithm
    best_location_row = 0
    best_location_column = 0
    num_of_tiles = 0
    biggest_num_of_tiles = 0
    list_of_empty_tiles = []
    for row in range(0, rows):
        for column in range(0, columns):
            if (game_map[row][column] == "empty"):
                list_of_empty_tiles.append((row,column))
                num_of_tiles = Surrounding_tiles(game_map, tower, row, column)
                if num_of_tiles > biggest_num_of_tiles:
                    biggest_num_of_tiles = num_of_tiles
                    best_location_row = row
                    best_location_column = column

    if (best_location_row == 0 and best_location_column == 0 and game_map[best_location_row][best_location_column] != "empty"):
        row, column = list_of_empty_tiles[random.randint(0,len(list_of_empty_tiles)-1)]
        return row, column
    return best_location_row, best_location_column

def Surrounding_tiles_SpreadAlgorithm(game_map, tower: Tower):
    num_of_tiles = 0
    for row in range(max(0, tower.row - tower.attack_range), min(rows, tower.row + tower.attack_range + 1)):
        for column in range(max(0, tower.column - tower.attack_range), min(columns, tower.column + tower.attack_range + 1)):
            if ((game_map[row][column] in ["road", "spawner"] or isinstance(game_map[row][column], cl.Enemy))):
                num_of_tiles += 1
    if (num_of_tiles == 0):
        pass
    return num_of_tiles
'''

def Remake_Enemy_list():
    global Enemy_Options, game
    if (len(Enemy_Options) == 0):
        Enemy_Options = copy.deepcopy(simulations[game][1])
        print("HAD TO REMAKE THE LIST")
def Create_Enemy(map_2d, enemy):
    enemy_location_index = random.randint(0, num_spawners - 1)
    enemy.row = list_of_spawner_rows[enemy_location_index]
    enemy.column = list_of_spawner_columns[enemy_location_index]
    while (map_2d[enemy.row][enemy.column] != "spawner"):
        enemy_location_index = random.randint(0, num_spawners - 1)
        enemy.row = list_of_spawner_rows[enemy_location_index]
        enemy.column = list_of_spawner_columns[enemy_location_index]
    map_2d[enemy.row][enemy.column] = enemy
    enemy.OnSpawner = True
    enemy_health_increase_rate = 0.01
    a = enemy_health_increase_rate
    r = max(G.num_of_rounds//40,1)
    enemy.health = enemy.initial_health * (1+a)**(r-1)
    G.List_Of_Enemies.append(enemy)
    return map_2d





# Define the dimensions of the map
rows = G.Rows
columns = G.Columns

matrices = []
num_matrices = 1000


#####
def load_matrices(filename):
    with open(filename, 'rb') as file:
        matrices = pickle.load(file)
    return matrices


def save_matrices_to_json(matrices, filename):
    with open(filename, 'w') as file:
        json.dump(matrices, file)


'''
if __name__ == "__main__":
    pickle_filename = 'matrices.pkl'
    json_filename = 'matrices.json'

    # Load matrices from pickle file
    matrices = load_matrices(pickle_filename)
    print(f'Loaded {len(matrices)} matrices from {pickle_filename}')

    # Save matrices to JSON file
    save_matrices_to_json(matrices, json_filename)
    print(f'Saved matrices to {json_filename}')
'''
######
# Set the difficulty level ('easy', 'medium', or 'hard')
difficulty_level = "hard" #input("write the difficulty you want").lower()


# Validate that each spawner has a path to the base
# while not validate_paths(game_map, 3):
# If validation fails, recreate the map until paths are valid
# game_map = create_map(rows, columns, difficulty_level)


def Convert_map_to_visual_map(matrix):
    game_map2 = [["empty" for _ in range(columns)] for _ in range(rows)]
    for _ in range(len(matrix)):
        for i in range(len(matrix[_])):
            game_map2[_][i] = matrix[_][i]
    for row in range(len(game_map2)):
        for space in range(len(game_map2[row])):  ######IT SHOULD BE len(game_map[row])
            if game_map2[row][space] == "spawner":
                game_map2[row][space] = 2
            elif game_map2[row][space] == "empty":
                game_map2[row][space] = 0
            elif game_map2[row][space] == "base":
                game_map2[row][space] = 4
            elif game_map2[row][space] == "road":
                game_map2[row][space] = 3
            elif isinstance(game_map2[row][space], cl.Enemy):
                game_map2[row][space] = 5
            elif isinstance((game_map2[row][space]), cl.Tower):
                game_map2[row][space] = 8
    return game_map2

class Game:

    def __init__(self, Game_map : Game_Map, Tower_Algorithm : Tower_Algorithm, Enemy_Algorithm):
        self.Game_map = Game_map
        self.Tower_Algorithm = Tower_Algorithm
        self.Enemy_Algorithm = Enemy_Algorithm

    def Run_Game(self):
        while True:  # MIGHT HAVE TO PUT A FOR LOOP IN HERE TO FIX IN CASE THE LOOP GETS STUCKED
            num_of_enemies = len(G.List_Of_Enemies)
            temp_num_of_enemies = len(G.List_Of_Enemies)
            Remake_Enemy_list()
            for Tower in range(0, len(G.List_Of_Towers)):
                self.Game_map.map_2d = G.List_Of_Towers[Tower].Check_Attack(self.Game_map.map_2d)
                self.Fix_Map_Error()
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
                self.Fix_Map_Error()
            self.Fix_Map_Error()
            if (G.Player_HP > 0):
                self.Rounds()
            else:
                break

    def Rounds(self):
        if G.num_of_rounds % 4 == 0:
            self.Game_map.map_2d[rows // 2][columns - 1] = "base"
            self.Game_map.map_2d = self.Enemy_Algorithm(self.Game_map)
        if (G.num_of_rounds % 40 == 0):
            self.Game_map= self.Tower_Algorithm.Do_Turn(self.Game_map)
            G.Enemy_Money = G.Enemy_Money + 20 * (G.num_of_rounds / 100)
            G.Player_Money = G.Player_Money + 20 * (G.num_of_rounds / 100)
        G.num_of_rounds = G.num_of_rounds + 1

    def Fix_Map_Error(self):
        for row in self.Game_map.map_2d:
            for tile in row:
                if isinstance(tile, cl.Enemy):
                    if tile in G.List_Of_Enemies:
                        pass
                    else:
                        self.Game_map.map_2d[tile.row][tile.column] = "road"
        for i in range(0, num_spawners):
            if isinstance(self.Game_map.map_2d[list_of_spawner_rows[i]][list_of_spawner_columns[i]], Enemy) or \
                    self.Game_map.map_2d[list_of_spawner_rows[i]][list_of_spawner_columns[i]] == "spawner":
                pass
            else:
                self.Game_map.map_2d[list_of_spawner_rows[i]][list_of_spawner_columns[i]] = "spawner"

def Reset_Game_Settings():
    G.num_of_rounds = 0
    G.List_Of_Towers = []
    G.List_Of_Enemies = []
    G.Player_Money = 50
    G.enemies_killed = 0
    G.Enemy_Money = 10
    G.Player_HP = 1
    list_of_spawner_columns = []
    list_of_spawner_rows = []


def modify_random_attribute(self):
    # List of attributes that can be modified
    attributes = ['Location_Strategy', 'Money_Strategy', 'Tower_Strategy', 'Upgrade_Strategy', 'Tower_Attack_Strategy']

    # Choose a random attribute
    chosen_attribute = random.choice(attributes)

    if chosen_attribute == 'Location_Strategy':
        strategies = ["Spread", "Base", "Spawner", "Tiles"]
        available_strategies = list(set(strategies) - {self.Location_Strategy})
        self.Location_Strategy = random.choice(available_strategies)

    elif chosen_attribute == 'Money_Strategy':
        new_money_strategy = self.Money_Strategy
        while new_money_strategy == self.Money_Strategy:
            new_money_strategy = round(random.uniform(0, 1), 2)  # Ensure it's different
        self.Money_Strategy = new_money_strategy

    elif chosen_attribute == 'Upgrade_Strategy':
        new_upgrade_strategy = self.Upgrade_Strategy
        while new_upgrade_strategy == self.Upgrade_Strategy:
            new_upgrade_strategy = random.choice([0, 1, 2])  # Ensure it's different
        self.Upgrade_Strategy = new_upgrade_strategy

    elif chosen_attribute == 'Tower_Strategy':
        # Assuming there's a predefined list of tower types to choose from
        tower_types = copy.deepcopy(towers)
        action = random.choice(['add', 'remove'])
        if action == 'add' and len(self.Tower_Strategy) < len(tower_types):
            available_towers = list(set(tower_types) - set(self.Tower_Strategy))
            self.Tower_Strategy.append(random.choice(available_towers))
        elif action == 'remove' and len(self.Tower_Strategy) > 0:
            self.Tower_Strategy.remove(random.choice(self.Tower_Strategy))

    elif chosen_attribute == 'Tower_Attack_Strategy':
        strategies = ["first", "last", "strongest", "weakest"]
        action = random.choice(['add', 'remove'])
        if action == 'add' and len(self.Tower_Attack_Strategy) < len(strategies):
            available_strategies = list(set(strategies) - set(self.Tower_Attack_Strategy))
            self.Tower_Attack_Strategy.append(random.choice(available_strategies))
        elif action == 'remove' and len(self.Tower_Attack_Strategy) > 1:
            self.Tower_Attack_Strategy.remove(random.choice(self.Tower_Attack_Strategy))


Upgrade_Algorithm_instance = Upgrade_Algorithm()
All_Money_Algorithm_instance = All_Money_Algorithm()
Spread_Algorithm_instance = Spread_Algorithm()
algorithms = [All_Money_Algorithm_instance, Spread_Algorithm_instance, Upgrade_Algorithm_instance]

if __name__ == "__main__":
    with open('simulations.json', 'r') as f:
        simulations = json.load(f)
    Which_Test = input().lower()
    if (Which_Test == "algorithms"):
        for algorithm in algorithms:
            Game_map = Game_Map()
            Actual_Game = Game([[]], algorithm, Random_Enemy_Algorithm)
            game_number = 0 #an index used to choose which simulation from the list of simulations
            for game in range(0, 100):
                total_enemies_killed = 0
                total_rounds_survived = 0
                total_time_survived = 0
                for avg in range(0, 10):
                    print("game number = ",game_number)
                    # Reset Variables
                    Reset_Game_Settings()
                    map_gen = simulations[game_number][0]
                    map_gen : dict
                    map_gen_atributes = list(map_gen.values())
                    list_of_spawner_rows = map_gen_atributes[0]
                    list_of_spawner_columns = map_gen_atributes[1]
                    num_spawners = map_gen_atributes[2]
                    game_map = map_gen_atributes[3]
                    Game_map.map_2d = game_map
                    Game_map.list_of_spawner_rows = list_of_spawner_rows
                    Game_map.list_of_spawner_columns = list_of_spawner_columns
                    Game_map.num_spawners = num_spawners
                    Actual_Game.Game_map = Game_map
                    Enemy_Options = simulations[game_number][1]
                    start_time = time.time()

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
                    "difficulty": difficulty_level,
                    "rounds": average_rounds_survived,
                    "enemies_killed": average_enemies_killed,
                    "duration_seconds": average_time_survived
                }
                print(game_stats)
                filename = f"game_results_{algorithm.Name}.json"
                with open(filename, "a") as f:
                    json.dump(game_stats, f)
                    f.write("\n")
    else:
        Local_Search_Algorithm = Tower_Algorithm("Tiles",1,copy.deepcopy(towers),0,["first","last","weakest","strongest"],"Local_Search_Algorithm")
        Game_map = Game_Map()
        Actual_Game = Game([[]], Local_Search_Algorithm, Random_Enemy_Algorithm)
        Best_attributes = Local_Search_Algorithm.__dict__
        best_average_enemies_killed = 0
        for i in range(0,100):
            modify_random_attribute(Local_Search_Algorithm)
            print(Local_Search_Algorithm.__dict__)
            total_enemies_killed = 0
            total_rounds_survived = 0
            total_time_survived = 0
            for game in range(0,1000):
                # Reset Variables
                Reset_Game_Settings()
                map_gen = simulations[game][0]
                map_gen: dict
                map_gen_atributes = list(map_gen.values())
                list_of_spawner_rows = map_gen_atributes[0]
                list_of_spawner_columns = map_gen_atributes[1]
                num_spawners = map_gen_atributes[2]
                game_map = map_gen_atributes[3]
                Game_map.map_2d = game_map
                Game_map.list_of_spawner_rows = list_of_spawner_rows
                Game_map.list_of_spawner_columns = list_of_spawner_columns
                Game_map.num_spawners = num_spawners
                Actual_Game.Game_map = Game_map
                Enemy_Options = copy.deepcopy(simulations[game][1])
                start_time = time.time()
                Actual_Game.Run_Game()
                # Save game stats to JSON
                end_time = time.time()
                game_duration = end_time - start_time
                total_time_survived += game_duration
                total_enemies_killed += G.enemies_killed
                total_rounds_survived += G.num_of_rounds

            average_enemies_killed = total_enemies_killed / 1000
            average_time_survived = total_time_survived / 1000
            average_rounds_survived = total_rounds_survived / 1000
            game_stats = {
                "difficulty": difficulty_level,
                "rounds": average_rounds_survived,
                "enemies_killed": average_enemies_killed,
                "duration_seconds": average_time_survived
            }
            print(i, ":",game_stats)
            filename = f"game_results_{Local_Search_Algorithm.Name}.json"
            with open(filename, "a") as f:
                json.dump(game_stats, f)
                f.write("\n")
            if (average_enemies_killed > best_average_enemies_killed):
                best_average_enemies_killed = average_enemies_killed
                Best_attributes = Local_Search_Algorithm.__dict__
        print(Best_attributes)
    print("THE CODE RUN SUCCESFULLY")
