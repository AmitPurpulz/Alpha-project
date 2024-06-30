# THIS CODE IS TO MAKE A RANDOM MAP HOWEVER IT MAKES AN EXCESSIVE AMOUNT OF ROADS (AND IS IN COMPLETE)
import random
import numpy as np
import matplotlib.pyplot as plt
import classes as cl
import plotly as pl

def create_map(rows, columns, difficulty):
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

    # Place the "Base" in the middle row at the last column
    map_2d[rows // 2][columns - 1] = "Base"

    for spawner in range(0, num_spawners):
        # if (spawner == 0):
        map_2d =  Create_Path(map_2d, list_of_spawner_rows[spawner], list_of_spawner_columns[spawner])
        '''
        else:
            map_2d = Remaining_paths(map_2d,list_of_spawner_rows[spawner],list_of_spawner_columns[spawner])

        temp = []
        change_direction_counter =0
        if list_of_spawner_rows[spawner] == rows//2:
            for square in range(list_of_spawner_columns[spawner]+1,columns-1):
                map_2d[list_of_spawner_rows[spawner]][square] = "road"
        else:
            road_row = list_of_spawner_rows[spawner]
            vertical_distance_from_base = rows//2-list_of_spawner_rows[spawner]

            for square in range(list_of_spawner_columns[spawner]+1,columns):
                if (vertical_distance_from_base != 0 ):
                    direction = random.randint(0,1) #1 indicates that the next road will be up or down and 0 means it will go to the right
                else:
                    direction = 0

                if (direction == 1):
                    change_direction_counter+=1 #how many time a road was placed up or down
                    if (vertical_distance_from_base > 0 and map_2d[road_row+1][square-change_direction_counter] != "spawner"):
                        road_row += 1
                        map_2d[road_row][square-change_direction_counter] = "road"
                        vertical_distance_from_base-=1

                    elif(vertical_distance_from_base < 0 and map_2d[road_row-1][square-change_direction_counter] != spawner):
                        road_row -= 1
                        map_2d[road_row][square-change_direction_counter] = "road"
                        vertical_distance_from_base += 1

                else:
                    if (map_2d[road_row][square-change_direction_counter] != "spawner"):
                        map_2d[road_row][square-change_direction_counter] = "road"
                temp.append(direction)
                temp.append((road_row,square))
        print(temp)
        '''

    return map_2d


def Place_Road(map_2d, row, column):
    vertical_distance_from_base = rows // 2 - row
    direction = random.randint(0, 1)
    if (direction == 0):
        column += 1
        map_2d[row][column] = "road"
    else:
        if (vertical_distance_from_base > 0):
            row -= 1
            map_2d[row][column] = "road"
        elif (vertical_distance_from_base < 0):
            row += 1
            map_2d[row][column] = "road"
        else:
            column += 1
            map_2d[row][column] = "road"

    return map_2d, row, column


def Create_Path(map_2d, spawner_row, spawner_column):
    temp = []
    change_direction_counter = 0
    if spawner_row == rows // 2:
        for square in range(spawner_column + 1, columns - 1):
            map_2d[spawner_row][square] = "road"
    else:
        road_row = spawner_row
        vertical_distance_from_base = rows // 2 - spawner_row

        for square in range(spawner_column + 1, columns + (vertical_distance_from_base - 1)):
            if (vertical_distance_from_base != 0):
                direction = random.randint(0,
                                           1)  # 1 indicates that the next road will be up or down and 0 means it will go to the right
            else:
                direction = 0

            if (direction == 1):
                change_direction_counter += 1  # how many time a road was placed up or down
                if (vertical_distance_from_base > 0 and map_2d[road_row + 1][
                    square - change_direction_counter] != "spawner"):
                    road_row += 1
                    map_2d[road_row][square - change_direction_counter] = "road"
                    vertical_distance_from_base -= 1

                elif (vertical_distance_from_base < 0 and map_2d[road_row - 1][
                    square - change_direction_counter] != "spawner"):
                    road_row -= 1
                    map_2d[road_row][square - change_direction_counter] = "road"
                    vertical_distance_from_base += 1

            else:
                if (map_2d[road_row][square - change_direction_counter] != "spawner"):
                    map_2d[road_row][square - change_direction_counter] = "road"
            temp.append(direction)
            temp.append((road_row, square))
    return map_2d


def Remaining_paths(map_2d, spawner_row, spawner_column):
    check_connected = True
    current_row = spawner_row
    current_column = spawner_column
    if Surrounding_Roads(map_2d, spawner_row, spawner_column) >= 1:
        return map_2d  # No need to proceed if there are enough surrounding roads
    else:
        while check_connected:
            current_row, current_column = Place_Road(map_2d, current_row, current_column)[1:]
            map_2d = Place_Road(map_2d, current_row, current_column)[0]
            if Surrounding_Roads(map_2d, current_row, current_column) >= 2:
                check_connected = False
    return map_2d


def Surrounding_Roads(map_2d, tile_row, tile_column):
    important_tiles = 0
    try:
        for row in range(max(0, tile_row - 1), min(len(map_2d), tile_row + 2)):
            print("Row:", row)  # Print row value
            for column in range(max(0, tile_column - 1), min(len(map_2d[0]), tile_column + 2)):
                if row == tile_row and column == tile_column:
                    continue  # Skip the current tile
                if map_2d[row][column] == "road":
                    important_tiles += 1
    except IndexError:
        pass  # Ignore IndexError caused by out-of-bounds access
    return important_tiles

    '''
    important_tiles = 0
    try:
        for row in range(tile_row-1, tile_row+2):
            if (row != tile_row):
                if map_2d[row][tile_column] == "road":
                    important_tiles+=1

            else:
                for column in range(tile_column-1, tile_column+2, 2):
                    if (map_2d[row][column] == "road"):
                        important_tiles+=1
    except:
        try:
            for row in range(tile_row, tile_row+2):
                if (row != tile_row):
                    if (map_2d[row][tile_column] == "road"):
                        important_tiles += 1
                else:
                    for column in range(tile_column-1, tile_column+2, 2):
                        if (map_2d[row][column] == "road"):
                            important_tiles+=1
        except:
            for row in range(tile_row-1, tile_row + 1):
                if (row != tile_row):
                    if map_2d[row][tile_column] == "road":
                        important_tiles += 1
                else:
                    for column in range(tile_column - 1, tile_column + 2, 2):
                        if map_2d[row][column] == "road":
                            important_tiles += 1

    return important_tiles
    '''


def Surrounding_tiles(map, tile_row, tile_column):
    important_tiles = 0
    try:
        for row in range(tile_row - 1, tile_row + 2):
            if (row != tile_row):
                if map[row][tile_column] == "road" or "spawner" or "base":
                    important_tiles += 1

            else:
                for column in range(tile_column - 1, tile_column + 2, 2):
                    if map[row][column] == "road" or "spawner" or "base":
                        important_tiles += 1
    except:
        try:
            for row in range(tile_row, tile_row + 2):
                if (row != tile_row):
                    if map[row][tile_column] == "road" or "spawner" or "base":
                        important_tiles += 1
                else:
                    for column in range(tile_column - 1, tile_column + 2, 2):
                        if map[row][column] == "road" or "spawner" or "base":
                            important_tiles += 1
        except:
            for row in range(tile_row - 1, tile_row + 1):
                if (row != tile_row):
                    if map[row][tile_column] == "road" or "spawner" or "base":
                        important_tiles += 1
                else:
                    for column in range(tile_column - 1, tile_column + 2, 2):
                        if map[row][column] == "road" or "spawner" or "base":
                            important_tiles += 1
    return important_tiles


def Path_cleaner(map):  # this function will delete any unecesary roads in order to make the map look better

    for row in range(0, len(map)):
        for column in range(0, row):
            if map[row][column] == "road":
                if Surrounding_tiles(map, row, column) == 3:
                    map[row][column] = "empty"
    return map


# Define the dimensions of the map
rows = 10
columns = 10

# Set the difficulty level ('easy', 'medium', or 'hard')
difficulty_level = input("write the difficulty you want")

# Create the map based on the chosen difficulty
game_map = create_map(rows, columns, difficulty_level)

# Validate that each spawner has a path to the Base
# while not validate_paths(game_map, 3):
# If validation fails, recreate the map until paths are valid
# game_map = create_map(rows, columns, difficulty_level)


# CONVERTING TO VISUAL

game_map_COPY = game_map
def Convert_map_to_visual_map(matrix):
    game_map2 = [["empty" for _ in range(columns)] for _ in range(rows)]
    for _ in range(len(matrix)):
        for i in range(len(matrix[_])):
            game_map2[_][i] = matrix[_][i]
    print("YIPPIE")
    for row in range(len(game_map2)):
        for space in range(len(game_map2[row])): ######IT SHOULD BE len(game_map[row])
            if game_map2[row][space] == "spawner":
                game_map2[row][space] = 1
            elif game_map2[row][space] == "empty":
                game_map2[row][space] = 0
            elif game_map2[row][space] == "Base":
                game_map2[row][space] = 3
            elif game_map2[row][space] == "road":
                game_map2[row][space] = 2
            elif type(game_map2[row][space]) == cl.Enemy:
                game_map2[row][space] = 5
            elif type(game_map2[row][space]) == cl.unit:
                game_map2[row][space] = 8
    return game_map2

bad = cl.Enemy("evil", 10, 10, 10, 10, 5, 5)
game_map[5][5] = bad

visual_map = Convert_map_to_visual_map(game_map)
# Print the visual_map_array

# Display the visual map using matplotlib
plt.ion() #turns on interactive mode

while True:
    plt.imshow(visual_map, cmap='viridis', interpolation='nearest')
    plt.show()
    plt.pause(5)
    plt.close()
    game_map = bad.Move(game_map)
    visual_map = Convert_map_to_visual_map(game_map)

