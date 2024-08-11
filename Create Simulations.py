import json
import random
import pickle
import time

import classes
from trying import Game_Map, Random_Enemy_Generator_Algorithm
import Game_Settings as G

rows = G.Rows
columns = G.Columns

def generate_simulations(num_simulations=1000):
    simulations = []
    map_gen = Game_Map()
    for _ in range(num_simulations):
        if (_ % 100 == 0 and _ != 0):
            G.difficulty_level += 1
        random.seed(time.time() + random.randint(0, 1000))
        map_gen = Game_Map()
        simulation = []
        game_map = map_gen.map_2d
        simulation.append(map_gen.to_dict())
        list_of_enemies = Random_Enemy_Generator_Algorithm(game_map)
        simulation.append(list_of_enemies)
        simulations.append(simulation)
    return simulations


# Generate the JSON data
data = generate_simulations()

# Write the JSON data to a file
with open('simulations.json', 'w') as f:
    json.dump(data, f)
'''
with open('simulations2.pkl', 'wb') as f:
    pickle.dump(data, f)
'''