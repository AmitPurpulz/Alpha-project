import copy
import random
import numpy as np
import matplotlib.pyplot as plt
import pickle
import Game
from Game import Enemy_Money, Player_Money
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
def Random_Enemy_Algorithm(game_map):
    global Enemy_Money
    Enemy_Options = cl.List_Of_Enemies_Options
    normal_enemy_instance = NormalEnemy(0, 0)
    enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options) - 1)](0, 0)
    enemy_instance: cl.Enemy
    while (enemy_instance.money_drop > Enemy_Money):
        enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options) - 1)](0, 0)
        if Enemy_Money < normal_enemy_instance.money_drop:
            return game_map
    enemy_instance = NormalEnemy(0,0)
    Enemy_Money = Enemy_Money - enemy_instance.money_drop
    game_map = Create_Enemy(game_map, enemy_instance)
    return game_map


def Random_Algorithm(game_map):
    global Player_Money, towers
    Tower_Options = towers
    normal_tower_instance = NormalTower(0, 0)
    tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
    while (tower.price > Player_Money):
        tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
        if Player_Money < normal_tower_instance.price:
            return game_map
    Player_Money = Player_Money - tower.price
    row, column = Best_Location(game_map, tower)
    tower.row = row
    tower.column = column
    game_map[tower.row][tower.column] = tower
    Game.List_Of_Towers.append(tower)
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

def SpreadPlacement_Algorithm(game_map):
    global towers, cheapest, check_SpreadAlgorithm, Player_Money, temp_map
    check_SpreadAlgorithm = True
    num_of_tiles = 0
    if (Check_No_Towers(game_map)):
        game_map = Random_Algorithm(game_map=game_map)
    else:
        for tower in Game.List_Of_Towers:
            temp_map = Blocks_In_Range(temp_map, tower)
        num_of_tiles = 0
        tower = towers[random.randint(0, len(cl.towers) - 1)]
        while (tower.price > Player_Money):
            tower = towers[random.randint(0, len(cl.towers) - 1)]
            if Player_Money < cheapest.price:
                return game_map
        Player_Money = Player_Money - tower.price
        tower.row, tower.column = Best_Location(temp_map, tower)
        game_map[tower.row][tower.column] = tower
        Game.List_Of_Towers.append(tower)
    return game_map

def Expensive_Algorithm(game_map):
    global towers, cheapest
    while (Game.Player_Money >= cheapest.price):
        for tower_price in range(len(towers) - 1, 0, -1):
            if (Game.Player_Money >= towers[tower_price].price):
                tower = towers[tower_price]
                Game.Player_Money = Game.Player_Money - towers[tower_price].price
                tower.row, tower.column = Best_Location(game_map, tower)
                game_map[tower.row][tower.column] = tower
                Game.List_Of_Towers.append(tower)
                break
    return game_map

def Best_Location(game_map, tower: Tower):
    global check_SpreadAlgorithm
    best_location_row = 0
    best_location_column = 0
    num_of_tiles = 0
    biggest_num_of_tiles = 0
    for row in range(0, rows):
        for column in range(0, columns):
            if (game_map[row][column] == "empty"):
                if (check_SpreadAlgorithm):
                    num_of_tiles = Surrounding_tiles_SpreadAlgorithm(game_map, tower)
                    check_SpreadAlgorithm = False
                else:
                    num_of_tiles = Surrounding_tiles(game_map, tower, row, column)
            if num_of_tiles > biggest_num_of_tiles:
                biggest_num_of_tiles = num_of_tiles
                best_location_row = row
                best_location_column = column
    return best_location_row, best_location_column

def Surrounding_tiles_SpreadAlgorithm(game_map, tower: Tower):
    num_of_tiles = 0
    for row in range(max(0, tower.row - tower.attack_range), min(rows, tower.row + tower.attack_range + 1)):
        for column in range(max(0, tower.column - tower.attack_range), min(columns, tower.column + tower.attack_range + 1)):
            if ((game_map[row][column] in ["road", "spawner"] or isinstance(game_map[row][column], cl.Enemy))):
                num_of_tiles += 1
    return num_of_tiles

def Surrounding_tiles(game_map, tower: Tower, tower_row, tower_column):
    num_of_tiles = 0
    for row in range(max(0, tower_row - tower.attack_range), min(rows, tower_row + tower.attack_range + 1)):
        for column in range(max(0, tower_column - tower.attack_range), min(columns, tower_column + tower.attack_range + 1)):
            if (game_map[row][column] in ["road", "spawner"] or isinstance(game_map[row][column], cl.Enemy)):
                num_of_tiles += 1
    return num_of_tiles

def Create_Enemy(map_2d, enemy):
    global last_spawn_time
    if Game.num_of_rounds%4== 0:
        enemy_location_index = random.randint(0, num_spawners - 1)
        enemy.row = list_of_spawner_rows[enemy_location_index]
        enemy.column = list_of_spawner_columns[enemy_location_index]
        map_2d[enemy.row][enemy.column] = enemy
        enemy.OnSpawner = True
        enemy_health_increase_rate = 0.01
        a = enemy_health_increase_rate
        r = max(Game.num_of_rounds//40,1)
        enemy.health = enemy.initial_health * (1+a)**(r-1)
        print(enemy.health,"ushdunsnadicsdcsd")
        if (enemy.health > 11):
            print("BAD")
        Game.List_Of_Enemies.append(enemy)
    return map_2d


list_of_spawner_rows = []
list_of_spawner_columns = []
num_spawners = 0


def create_map(rows, columns, difficulty):
    global list_of_spawner_columns, list_of_spawner_rows, num_spawners
    map_2d = [["empty" for _ in range(columns)] for _ in range(rows)]
    num_spawners = 1
    valid_difficulties = ["easy", "medium", "hard"]

    while difficulty not in valid_difficulties:
        difficulty = input("Please type the difficulty again (easy, medium, hard): ").lower()

    if difficulty == "easy":
        map_2d[rows // 2][0] = "spawner"
    elif difficulty == "medium":
        num_spawners = 2
        column_distance = int(columns // 2 - 2)
    elif difficulty == "hard":
        num_spawners = 3
        column_distance = int(columns // 2 - 1)

    list_of_spawner_rows = []
    list_of_spawner_columns = []

    for _ in range(num_spawners):
        while True:
            if difficulty != "easy":
                row = random.randint(0, rows - 1)
                col = random.randint(0, column_distance)
                if map_2d[row][col] == "empty" and all(map_2d[row][i] != "spawner" for i in range(columns)):
                    map_2d[row][col] = "spawner"
                    break
            else:
                row = rows // 2
                col = 0
                break

        list_of_spawner_rows.append(row)
        list_of_spawner_columns.append(col)

    map_2d[rows // 2][columns - 1] = "base"

    for spawner in range(num_spawners):
        end_row = rows // 2
        end_column = columns - 1
        map_2d = Create_Path(map_2d, list_of_spawner_rows[spawner], list_of_spawner_columns[spawner], end_row,
                             end_column)

    return map_2d


def Create_Path(map_2d, spawner_row, spawner_column, end_block_row, end_block_column):
    road_row = spawner_row
    vertical_distance_from_base = end_block_row - spawner_row
    horizontal_distance = end_block_column - spawner_column
    change_direction_counter = 0
    square = spawner_column+1
    while ((road_row != end_block_row or square-change_direction_counter != end_block_column)):
        if is_within_bounds(road_row, square - change_direction_counter, len(map_2d), len(map_2d[0])):
            map_2d[road_row][square - change_direction_counter] = "road"

        if vertical_distance_from_base != 0:
            direction = random.randint(0, 1)  # 1 means vertical, 0 means horizontal
        else:
            direction = 0
        if square-change_direction_counter == end_block_column:
            direction = 1

        if direction == 1 and vertical_distance_from_base != 0:
            change_direction_counter += 1
            if vertical_distance_from_base > 0 and is_within_bounds(road_row + 1, square - change_direction_counter,len(map_2d), len(map_2d[0])):
                road_row += 1
                vertical_distance_from_base -= 1
            elif vertical_distance_from_base < 0 and is_within_bounds(road_row - 1, square - change_direction_counter,len(map_2d), len(map_2d[0])):
                road_row -= 1
                vertical_distance_from_base += 1
        square = square+1
        if (square == end_block_column):
            print(road_row, square, vertical_distance_from_base, change_direction_counter, spawner_row, spawner_column, "PRINTING")

    return map_2d

def is_within_bounds(row, column, rows, columns):
    return 0 <= row < rows and 0 <= column < columns
def count_adjacent_roads(game_map, row, column, rows, columns):
    adjacent_positions = [
        (row + 1, column),
        (row - 1, column),
        (row, column + 1),
        (row, column - 1)
    ]

    num_of_adjacent_roads = 0
    for r, c in adjacent_positions:
        if is_within_bounds(r, c, rows, columns) and game_map[r][c] in ["road", "base", "spawner"]:
            num_of_adjacent_roads += 1

    return num_of_adjacent_roads


def Fix_Path(game_map):
    invalid_paths = True
    while (Surrounding_tiles(game_map, tower=cl.ShotgunTower(0, 0), tower_row=rows // 2,tower_column=columns - 1) == 0) or invalid_paths:
        if Surrounding_tiles(game_map, tower=cl.ShotgunTower(0, 0), tower_row=rows // 2, tower_column=columns - 1) == 0:
            game_map = create_map(rows, columns, difficulty_level)

        invalid_paths = False
        for row in range(rows):
            for column in range(columns):
                if game_map[row][column] == "road":
                    num_of_adjacent_roads = count_adjacent_roads(game_map, row, column, rows, columns)
                    if num_of_adjacent_roads < 2:
                        invalid_paths = True
                        break  #Exit the for loop early if an invalid path is found
            if invalid_paths:
                break  #Exit the for loop early if an invalid path is found

        if invalid_paths:
            game_map = create_map(rows, columns, difficulty_level)

    return game_map


# Define the dimensions of the map
rows = Game.Rows
columns = Game.Columns

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


def Run_Game(game_map, Tower_Algorithm, Enemy_Algorithm):
     while True: #MIGHT HAVE TO PUT A FOR LOOP IN HERE TO FIX IN CASE THE LOOP GETS STUCKED
        num_of_enemies = len(Game.List_Of_Enemies)
        temp_num_of_enemies = len(Game.List_Of_Enemies)
        for Tower in range(0,len(Game.List_Of_Towers)):
            game_map = Game.List_Of_Towers[Tower].Check_Attack(game_map)
            num_of_enemies = len(Game.List_Of_Enemies)
        for enemy in range(0, len(Game.List_Of_Enemies)):
            game_map = Game.List_Of_Enemies[enemy].Move(game_map)
            if (Game.Player_HP <= 0):
                break
            if (len(Game.List_Of_Enemies) < num_of_enemies and len(Game.List_Of_Enemies) > 0):
                game_map = Game.List_Of_Enemies[enemy].Move(game_map)
                num_of_enemies = len(Game.List_Of_Enemies)
        game_map = Rounds(game_map,Tower_Algorithm=Tower_Algorithm,Enemy_Algorithm=Enemy_Algorithm)
        if (Game.Player_HP <= 0):
            print("YOU LOSE!")
            break

# Validate that each spawner has a path to the base
# while not validate_paths(game_map, 3):
# If validation fails, recreate the map until paths are valid
# game_map = create_map(rows, columns, difficulty_level)

def Rounds(game_map, Tower_Algorithm, Enemy_Algorithm):
    global Player_Money, Enemy_Money, Round_time, Enemies
    game_map = Enemy_Algorithm(game_map)
    game_map = Tower_Algorithm(game_map)
    if (Game.num_of_rounds % 40 == 0):
        Enemy_Money = Enemy_Money + 20*(Game.num_of_rounds/100)
        Player_Money = Player_Money + 20*(Game.num_of_rounds/100)
    Game.num_of_rounds = Game.num_of_rounds + 1
    return game_map

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


algorithms = {
    "Random_Algorithm": Random_Algorithm,
    "Expensive_Algorithm": Expensive_Algorithm,
    "SpreadPlacement_Algorithm": SpreadPlacement_Algorithm
}

for algorithm_name, algorithm in algorithms.items():
    for game in range(0, 100):
        total_enemies_killed = 0
        total_rounds_survived = 0
        total_time_survived = 0
        for avg in range(0, 10):
            # Reset Variables
            Game.num_of_rounds = 0
            Game.List_Of_Towers = []
            Game.List_Of_Enemies = []
            Player_Money = 50
            Game.enemies_killed = 0
            Enemy_Money = 10
            Game.Player_HP = 1
            list_of_spawner_columns = []
            list_of_spawner_rows = []

            # Create the map based on the chosen difficulty
            game_map = create_map(rows, columns, difficulty_level)
            game_map = Fix_Path(game_map)
            for row in game_map:
                print(row)
            temp_map = copy.deepcopy(game_map)
            start_time = time.time()

            start_time = time.time()
            Run_Game(game_map, Tower_Algorithm=algorithm, Enemy_Algorithm=Random_Enemy_Algorithm)  # Run the game with the algorithm
            # Save game stats to JSON
            end_time = time.time()
            game_duration = end_time - start_time
            total_time_survived += game_duration
            total_enemies_killed += Game.enemies_killed
            total_rounds_survived += Game.num_of_rounds
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
        filename = f"game_results_{algorithm_name}.json"
        with open(filename, "a") as f:
            json.dump(game_stats, f)
            f.write("\n")

    print("THE CODE RUN SUCCESFULLY")
