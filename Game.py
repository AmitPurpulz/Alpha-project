import time

Player_HP = 100
Player_Money = 20
Enemy_Money = 0
List_Of_Enemies = []
List_Of_Towers = []
last_spawn_time = 0
Round = 1


Rows = 10
Columns = 10

def Create_Enemy(map_2d, enemy):
    global List_Of_Enemies, last_spawn_time
    if (time.time() - last_spawn_time >= 2):
        last_spawn_time = time.time()
        map_2d[enemy.row][enemy.column] = enemy
        enemy.OnSpawner = True
        List_Of_Enemies.append(enemy)
    return map_2d, List_Of_Enemies

def Place_Tower(game_map, soldier_list):
    Towers = []
    print(soldier_list)
    Tower_chosen = int(input("here is the list of soliders, choose the number of the soldier you want to place, make sure you have the money for it"))
    if soldier_list[Tower_chosen] in soldier_list:
        Tower = soldier_list[Tower_chosen]
        Tower_instance = Tower(Tower.damage, Tower.firerate, Tower.range, Tower.price)
        place_location_row = int(input("write down the row you would like to put a unit in"))
        place_location_column = int(input("write down the column you would like to put a unit in"))
        game_map[place_location_row][place_location_column] = "Tower"
    else:
        print("there was an error when choosing a tower, make sure to spell it correctly next time")

    Towers.append((Tower_instance,place_location_row,place_location_column))

