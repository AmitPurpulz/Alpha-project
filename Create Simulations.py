import json
import random
import pickle
import classes
from trying import MapGenerator, Random_Enemy_Generator_Algorithm
import Game

rows = Game.Rows
columns = Game.Columns

def generate_simulations(num_simulations=10):
    simulations = []
    map_gen = MapGenerator()
    for _ in range(num_simulations):
        simulation = []

        game_map = map_gen.create_map(rows, columns, difficulty="hard")
        simulation.append(map_gen)
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