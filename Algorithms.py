import random
from Game import Player_Money, Rows, Columns, Enemy_Money
from classes import List_Of_Towers_Options, NormalTower, Tower, Enemy, NormalEnemy


def Random_Enemy_Algorithm(Enemy_Options: list, game_map):
    global Enemy_Money
    normal_enemy_instance = NormalEnemy(0,0)
    while (tower.price > Player_Money):
        tower = Tower_Options[random.randint(0, len(Tower_Options)-1)](0,0)
        if Player_Money < normal_tower_instance.price:
            break
    row, column = Best_Location(game_map, tower)

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
    for row in range(0, Rows):
        for column in range(0, Columns):
            if (game_map[row][column] == "empty"):
                num_of_tiles = Surrounding_tiles(game_map, tower, row, column)
            if num_of_tiles > biggest_num_of_tiles:
                biggest_num_of_tiles = num_of_tiles
                best_location_row = row
                best_location_column = column
    return best_location_row, best_location_column

def Surrounding_tiles(game_map, tower: Tower, tower_row, tower_column):
    num_of_tiles = 0
    for row in range(min(tower_row + tower.attack_range, Rows-1), max(tower_row - tower.attack_range, 0), -1):
        for column in range(min(tower_column + tower.attack_range, Columns-1),max(tower_column - tower.attack_range, 0), -1):
            if (game_map[row][column] == "road" or game_map[row][column] == "spawner"):
                num_of_tiles = num_of_tiles + 1
    return num_of_tiles
