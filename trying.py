# THIS CODE IS TO MAKE A RANDOM MAP HOWEVER IT MAKES AN EXCESSIVE AMOUNT OF ROADS (AND IS IN COMPLETE)
import random
import numpy as np
import matplotlib.pyplot as plt
import pickle
import Game
from Game import Enemy_Money, Player_Money, last_spawn_time, List_Of_Enemies, List_Of_Towers
import classes as cl
from classes import NormalTower, NormalEnemy, Tower, Enemy
import plotly as pl
import json
import time
from matplotlib.colors import ListedColormap


#THIS IS THE ALGORITHMS FILE I HAVE A CIRCULAR IMPORT ISSUE SO I TEMPORARLY MOVE THE ALGORITHMS FILE HERE
def Random_Enemy_Algorithm(Enemy_Options: list, game_map):
    global Enemy_Money
    normal_enemy_instance = NormalEnemy(0,0)
    enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options)-1)](0,0)
    enemy_instance: cl.Enemy
    while (enemy_instance.money_drop > Enemy_Money):
        enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options)-1)](0,0)
        if Enemy_Money < normal_enemy_instance.money_drop:
            return game_map
    Enemy_Money = Enemy_Money - enemy_instance.money_drop
    game_map, Game.List_Of_Enemies = Create_Enemy(game_map, enemy_instance)
    print(enemy_instance.name)
    return game_map

def Random_Algorithm(Tower_Options: list, game_map):
    global Player_Money
    normal_tower_instance = NormalTower(0,0)
    tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)](0, 0)
    while (tower.price > Player_Money):
        tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)](0, 0)
        if Player_Money < normal_tower_instance.price:
            return game_map
    Player_Money = Player_Money - tower.price
    row, column = Best_Location(game_map, tower)
    tower.row = row
    tower.column = column
    game_map[tower.row][tower.column] = tower
    List_Of_Towers.append(tower)
    print(tower)
    return game_map


def Expensive_Algorithm(Money, Tower_Options, game_map):
    cheapest = NormalTower.price
    while (Money >= cheapest):
        for tower in range(0, len(Tower_Options)):
            if (Tower_Options[tower].price <= Money):
                Money = Money - Tower_Options[tower].price

def Best_Location(game_map, tower: Tower):
    best_location_row = 0
    best_location_column = 0
    num_of_tiles = 0
    biggest_num_of_tiles = 0
    for row in range(0, rows):
        for column in range(0, columns):
            if (game_map[row][column] == "empty"):
                num_of_tiles = Surrounding_tiles(game_map, tower, row, column)
            if num_of_tiles > biggest_num_of_tiles:
                biggest_num_of_tiles = num_of_tiles
                best_location_row = row
                best_location_column = column
    return best_location_row, best_location_column

def Surrounding_tiles(game_map, tower: Tower, tower_row, tower_column):
    num_of_tiles = 0
    for row in range(min(tower_row + tower.attack_range, rows-1), max(tower_row - tower.attack_range, 0), -1):
        for column in range(min(tower_column + tower.attack_range, columns-1),max(tower_column - tower.attack_range, 0), -1):
            if (game_map[row][column] == "road" or game_map[row][column] == "spawner"):
                num_of_tiles = num_of_tiles + 1
    return num_of_tiles

def Create_Enemy(map_2d, enemy):
    global List_Of_Enemies, last_spawn_time
    if time.time() - last_spawn_time >= 2:
        last_spawn_time = time.time()
        enemy_location_index = random.randint(0, num_spawners - 1)
        enemy.row = list_of_spawner_rows[enemy_location_index]
        enemy.column = list_of_spawner_columns[enemy_location_index]
        map_2d[enemy.row][enemy.column] = enemy
        enemy.OnSpawner = True
        List_Of_Enemies.append(enemy)
    return map_2d, List_Of_Enemies



list_of_spawner_rows = []
list_of_spawner_columns = []
num_spawners = 0
def create_map(rows, columns, difficulty):
    global list_of_spawner_columns, list_of_spawner_rows, num_spawners
    # Create a 2D map using nested lists

    map_2d = [["empty" for _ in range(columns)] for _ in range(rows)]
    num_spawners = 1
    while (difficulty != "easy" and difficulty != "hard" and difficulty != "medium"):
        difficulty = input(
            "there seems to be an error, please type the difficulty chosen again. Make sure it is written in lowercase letter."
            "please write the difficulty you want:")

    if difficulty == "easy":
        # Place one spawner in the middle row at the first column
        map_2d[rows // 2][0] = "spawner"
    elif difficulty == "medium":
        # Determine the number of spawners based on difficulty
        num_spawners = 2
        column_distance = int(columns // 2 - 2)
    elif difficulty == "hard":
        num_spawners = 3
        column_distance = int(columns // 2 - 1)
    # Place spawners in random locations without touching each other
    list_of_spawner_rows = []
    list_of_spawner_columns = []
    for _ in range(0, num_spawners):
        while True:
            if (difficulty != "easy"):
                # Randomly choose a row and column within the specified range
                row = random.randint(0, rows - 1)
                col = random.randint(0, int(column_distance))

                # Check if the chosen location is empty and not in the same row as other spawners
                if map_2d[row][col] == "empty" and all(map_2d[row][i] != "spawner" for i in range(0, columns)):
                    map_2d[row][col] = "spawner"
                    break
            elif (difficulty == "easy"):
                row = rows // 2
                col = 0
                break

        list_of_spawner_rows.append(row)
        list_of_spawner_columns.append(col)

    # Place the "base" in the middle row at the last column
    map_2d[rows // 2][columns - 1] = "base"

    for spawner in range(0, num_spawners):
        # if (spawner == 0):
        if spawner == 0:
            end_row = rows//2
            end_column = columns-1
            map_2d = Create_Path(map_2d, list_of_spawner_rows[spawner], list_of_spawner_columns[spawner],end_row, end_column)
        else:
            end_row = rows//2
            end_column = random.randint(list_of_spawner_columns[spawner], columns-1)
            while (map_2d[end_row][end_column] == 'empty'):
                end_column = random.randint(list_of_spawner_columns[spawner], columns - 1)
            map_2d = Create_Path(map_2d, list_of_spawner_rows[spawner], list_of_spawner_columns[spawner], end_row, end_column)
    return map_2d

def Create_Path(map_2d, spawner_row, spawner_column, end_block_row, end_block_column):
    temp = []
    change_direction_counter = 0
    if spawner_row == rows // 2:
        for square in range(spawner_column + 1, columns - 1):
            map_2d[spawner_row][square] = "road"
    else:
        road_row = spawner_row
        vertical_distance_from_base = end_block_row - spawner_row
        for square in range(spawner_column + 1, end_block_column + abs(vertical_distance_from_base)):
            if (vertical_distance_from_base != 0):
                direction = random.randint(0,1)  # 1 indicates that the next road will be up or down and 0 means it will go to the right
            else:
                direction = 0

            if (map_2d[road_row][square-change_direction_counter] == "road"):
               break
            if (square-change_direction_counter >= end_block_column):
                direction = 1
            if direction == 1:
                change_direction_counter += 1  # how many times a road was placed up or down
                if (vertical_distance_from_base > 0 and map_2d[road_row + 1][ square - change_direction_counter] != "spawner"):
                    road_row += 1
                    map_2d[road_row][square - change_direction_counter] = "road"
                    vertical_distance_from_base -= 1

                elif (vertical_distance_from_base < 0 and map_2d[road_row - 1][square - change_direction_counter] != "spawner"):
                    road_row -= 1
                    map_2d[road_row][square - change_direction_counter] = "road"
                    vertical_distance_from_base += 1

            else:
                 if (map_2d[road_row][square - change_direction_counter] != "spawner"):
                    map_2d[road_row][square - change_direction_counter] = "road"
            temp.append(direction)
            temp.append((road_row, square))
    return map_2d

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
difficulty_level = input("write the difficulty you want")

# Create the map based on the chosen difficulty
game_map = create_map(rows, columns, difficulty_level)

# Validate that each spawner has a path to the base
# while not validate_paths(game_map, 3):
# If validation fails, recreate the map until paths are valid
# game_map = create_map(rows, columns, difficulty_level)

def Rounds(game_map):
    global Player_Money, Enemy_Money, Round_time
    game_map = Random_Enemy_Algorithm(cl.List_Of_Enemies_Options, game_map)
    game_map = Random_Algorithm(cl.List_Of_Towers_Options, game_map)
    if (time.time() >= Round_time+10):
        Player_Money = Player_Money + 20
        Enemy_Money = Enemy_Money + 20
        Round_time = time.time()
    return game_map





# CONVERTING TO VISUAL

game_map_COPY = game_map
def Convert_map_to_visual_map(matrix):
    game_map2 = [["empty" for _ in range(columns)] for _ in range(rows)]
    for _ in range(len(matrix)):
        for i in range(len(matrix[_])):
            game_map2[_][i] = matrix[_][i]
    for row in range(len(game_map2)):
        for space in range(len(game_map2[row])): ######IT SHOULD BE len(game_map[row])
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
            elif isinstance((game_map2[row][space]),cl.Tower):
                game_map2[row][space] = 8
    return game_map2


visual_map = Convert_map_to_visual_map(game_map)
# Print the visual_map_array
colors = ['#ffffff', '#ff0000', '#ffa500', '#ffff00', '#008000',
          '#00ffff', '#0000ff', '#800080', '#ff00ff', '#000000']
cmap = ListedColormap(colors)
plt.gca().set_facecolor('#d3d3d3')
# Display the visual map using matplotlib
plt.ion() #turns on interactive mode

matrix = plt.imshow(visual_map, cmap=cmap, interpolation='nearest', vmin=1, vmax =10)
plt.colorbar(ticks=range(1, 11))


Round_time = time.time()
while True:
    matrix.set_data(visual_map)
    plt.draw()
    plt.pause(0.25)
    num_of_enemies = len(Game.List_Of_Enemies)
    temp_num_of_enemies = len(Game.List_Of_Enemies)
    for Tower in Game.List_Of_Towers:
        game_map = Tower.Check_Attack(game_map)
        num_of_enemies = len(Game.List_Of_Enemies)
    for enemy in range(0,len(Game.List_Of_Enemies)):
        if (temp_num_of_enemies != num_of_enemies):
            if (enemy == num_of_enemies):
                break
        game_map = Game.List_Of_Enemies[enemy].Move(game_map)
        if (len(Game.List_Of_Enemies) < num_of_enemies and len(Game.List_Of_Enemies) > 0):
            game_map = Game.List_Of_Enemies[enemy].Move(game_map)
            num_of_enemies = len(Game.List_Of_Enemies)
    if (len(List_Of_Enemies) > 0):
        print(List_Of_Enemies[0].health)
    visual_map = Convert_map_to_visual_map(game_map)
    game_map = Rounds(game_map)
    if (Game.Player_HP <= 0):
        print("YOU LOSE!")
        break


