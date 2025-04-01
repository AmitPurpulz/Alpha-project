import copy
import json
import random
import time

from Main import Game_Map, Random_Enemy_Generator_Algorithm
import Game_Settings as G

rows = copy.deepcopy(G.Rows)
columns = copy.deepcopy(G.Columns)


def generate_simulations(num_simulations=5, max_spawners=5):
    """
    Generate simulation data (Enemy list, Enemy spawn order, spawners locations,  etc.)
    for the default map configuration using the original G.Rows and G.Columns.

    The function makes maps with different amount of spawners based on the "difficulty level"
    and cycles the difficulty level (the number of spawners) every (num_simulations/5)
    simulations. For each simulation, a new game map is generated, a random enemy order is produced, and the
    map settings are stored as a dictionary.

    Parameters:
        num_simulations (int, optional): The number of simulations to generate. Default set to 5.
        max_spawners (int, optional): The maximum number of spawners allowed in one map. Default set to 5.

    Returns:
        list: A list of simulation data; each simulation is a list containing the game map dictionary.
    """
    simulations = []
    G.Rows = rows
    G.Columns = columns
    G.difficulty_level = 1
    for i in range(num_simulations):
        if i % max_spawners != 0 and i != 0:
            G.difficulty_level += 1
        else:
            G.difficulty_level = 1
        random.seed(time.time() + random.randint(0, 1000))
        map_gen = Game_Map()
        simulation = []
        game_map = map_gen.map_2d
        list_of_enemies = Random_Enemy_Generator_Algorithm(game_map)
        map_gen.Enemy_Order = list_of_enemies
        map_gen.Enemy_Order_Copy = copy.copy(list_of_enemies)
        simulation.append(map_gen.to_dict())
        simulations.append(simulation)
    return simulations

if __name__ == "__main__":
    data = generate_simulations()
    with open('simulations.json', 'w') as f:
        json.dump(data, f)
    print("The code ran succesfully")
