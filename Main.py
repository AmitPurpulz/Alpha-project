import copy
import math
import os
import random
import Game_Settings as G
import classes as cl
from classes import NormalEnemy, Tower, Enemy
import json
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import time
import collections
import pickle


class Game_Map:
    """
    Represents the game map.

    Manages creation of the 2D game map with spawners, roads, and base.
    Also provides methods to check and count tiles.
    """

    def __init__(self):
        """Initialize the Game_Map, set up spawner lists, create the map, and determine spawner order."""
        self.list_of_spawner_rows = []
        self.list_of_spawner_columns = []
        self.num_spawners = 0
        self.map_2d = self.create_map(rows=G.Rows, columns=G.Columns, difficulty=G.difficulty_level)
        self.Enemy_Order = []
        self.Enemy_Order_Copy = []
        self.Spawner_Order = self.Create_Spawner_Order()

    def to_dict(self):
        """Return the Game_Map instance attributes as a dictionary."""
        return self.__dict__

    def create_map(self, rows, columns, difficulty):
        """
        Create the 2D map grid.

        Parameters:
            rows (int): Number of rows.
            columns (int): Number of columns.
            difficulty (int): Difficulty level which affects the number of spawners and their allowed locations.

        Returns:
            list: A 2D matrix representing the map.
        """
        self.map_2d = [["empty" for _ in range(columns)] for _ in range(rows)]
        self.num_spawners = difficulty
        if self.num_spawners < 1:
            self.num_spawners = 1
        if self.num_spawners == 1:
            column_distance = int(columns // 2 - (columns // 2 - 2))
        elif difficulty < 5:
            column_distance = int(columns // 2 - (columns // 2 - 3))
        else:
            column_distance = int(columns // 2 - (columns // 2 - 4))

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
            self.map_2d = self.Create_Path(self.list_of_spawner_rows[spawner],
                                           self.list_of_spawner_columns[spawner],
                                           end_row, end_column)
        self.map_2d[rows // 2][columns - 1] = "base"
        return self.map_2d

    def Create_Path(self, spawner_row, spawner_column, end_block_row, end_block_column):
        """
        Create a road path from a spawner to the base.

        Parameters:
            spawner_row (int): The starting row of the spawner.
            spawner_column (int): The starting column of the spawner.
            end_block_row (int): The destination row (base).
            end_block_column (int): The destination column (base).

        Returns:
            list: Updated map with the road path created.
        """
        road_row = spawner_row
        vertical_distance_from_base = end_block_row - spawner_row
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
                if vertical_distance_from_base > 0 and self.is_within_bounds(road_row + 1,
                                                                             square - change_direction_counter):
                    road_row += 1
                    vertical_distance_from_base -= 1
                elif vertical_distance_from_base < 0 and self.is_within_bounds(road_row - 1,
                                                                               square - change_direction_counter):
                    road_row -= 1
                    vertical_distance_from_base += 1
            square = square + 1
        return self.map_2d

    def is_within_bounds(self, row, column):
        """
        Check if a coordinate is within the game map boundaries.

        Parameters:
            row (int): Row index.
            column (int): Column index.

        Returns:
            bool: True if within bounds, False otherwise.
        """
        return 0 <= row < len(self.map_2d) and 0 <= column < len(self.map_2d[0])

    def Num_Of_Spawners_Available(self):
        """
        Count the number of spawner tiles on the map.

        Returns:
            int: The number of spawner tiles.
        """
        num_of_spawner_tiles = 0
        for row in self.map_2d:
            for tile in row:
                if tile == "spawner":
                    num_of_spawner_tiles += 1
        return num_of_spawner_tiles

    def count_surrounding_tiles(self, tower: Tower, tower_row, tower_column):
        """
        Count how many nearby enemies/tiles (within tower attack range) are valid for attack.

        Parameters:
            tower (Tower): The tower object.
            tower_row (int): The tower's row position.
            tower_column (int): The tower's column position.

        Returns:
            int: The count of valid surrounding enemies/tiles.
        """
        num_of_tiles = 0
        for row in range(max(0, tower_row - tower.attack_range), min(G.Rows, tower_row + tower.attack_range + 1)):
            for column in range(max(0, tower_column - tower.attack_range),
                                min(G.Columns, tower_column + tower.attack_range + 1)):
                if (self.map_2d[row][column] in ["road", "spawner"] or isinstance(self.map_2d[row][column], cl.Enemy)):
                    num_of_tiles += 1
        return num_of_tiles

    def Check_num_of_Tiles(self, tile_type):
        """
        Count the number of tiles of a given type on the map.

        Parameters:
            tile_type: The type of tile to count (can be a string like "road" or a class type like Enemy).

        Returns:
            int: The count of tiles matching the specified type.
        """
        num_of_tiles = 0
        for row in self.map_2d:
            for tile in row:
                if tile == tile_type:
                    num_of_tiles += 1
                if (tile_type == cl.Enemy or tile_type == cl.Tower):
                    if isinstance(tile, tile_type):
                        num_of_tiles += 1
        return num_of_tiles

    def Check_Adjecent_To_Spawner(self, row, column):
        """
        Check if a given tile is adjacent to any spawner.

        Parameters:
            row (int): Row of the tile.
            column (int): Column of the tile.

        Returns:
            bool: True if adjacent to a spawner, False otherwise.
        """
        for spawner in range(0, self.num_spawners):
            for r in range(max(0, self.list_of_spawner_rows[spawner] - 1),
                           min(G.Rows, self.list_of_spawner_rows[spawner] + 1)):
                for c in range(max(0, self.list_of_spawner_columns[spawner] - 1),
                               min(G.Rows, self.list_of_spawner_columns[spawner] + 1)):
                    if (r == row and c == column):
                        return True

    def Check_Adjecent_To_Base(self, row, column):
        """
        Check if a given tile is adjacent to the base.

        Parameters:
            row (int): Row of the tile.
            column (int): Column of the tile.

        Returns:
            bool: True if adjacent to the base, False otherwise.
        """
        for r in range(G.Rows // 2 - 1, G.Rows // 2 + 2):
            for c in range(G.Columns - 2, G.Columns):
                if (r == row and c == column):
                    return True

    def Create_Spawner_Order(self):
        """
        Create a predetermined order of spawner indices for enemy spawning.

        Returns:
            list: A list containing random spawner indices.
        """
        List_Of_Spawn_Order = []
        for enemy in range(0, 1000):
            List_Of_Spawn_Order.append(random.randint(0, self.num_spawners - 1))
        return List_Of_Spawn_Order


class Tower_Algorithm:
    """
    Creates an algorithm to decide where to place or upgrade towers.

    The algorithm takes into account strategies regarding location, money, tower type, upgrade, and attack style.
    """

    def __init__(self, Location_Strategy: str, Money_Strategy: float, Tower_Strategy: [cl.Tower],
                 Upgrade_Strategy: int, Tower_Attack_Strategy: [str], Name):
        """
        Initialize the Tower_Algorithm with given strategy parameters.

        Parameters:
            Location_Strategy (str): How to choose tower placement ("Spread", "Base", "Spawner", "Tiles").
            Money_Strategy (float): Fraction of money to spend (0.0–1.0).
            Tower_Strategy (list): List of tower types to prioritize.
            Upgrade_Strategy (int): Maximum upgrade level for towers (0, 1 or 2).
            Tower_Attack_Strategy (list): Attack targeting preferences for the towers ("first", "last", "weakest", "strongest").
            Name: The name of the algorithm.
        """
        self.Location_Strategy = Location_Strategy
        self.Money_Strategy = Money_Strategy
        self.Tower_Strategy = Tower_Strategy
        self.Upgrade_Strategy = Upgrade_Strategy
        self.Tower_Attack_Strategy = Tower_Attack_Strategy
        self.Name = Name

    def choose_tower_location(self, game_map: Game_Map, tower: cl.Tower):
        """
        Choose the best location to place a tower based on the location strategy.

        Parameters:
            game_map (Game_Map): The current game map.
            tower (Tower): The tower to be placed.

        Returns:
            tuple: (row, column) for the best location.
        """
        temp_map = copy.deepcopy(game_map.map_2d)
        if self.Location_Strategy == "Spread":
            for tower in G.List_Of_Towers:
                temp_map = self.check_blocks_in_range(temp_map, tower)
            if not ("spawner" in temp_map or "road" in temp_map):
                temp_map = game_map.map_2d
        best_location_row = 0
        best_location_column = 0
        num_of_tiles = 0
        biggest_num_of_tiles = 0
        list_of_empty_tiles = []
        for row in range(0, G.Rows):
            for column in range(0, G.Columns):
                if temp_map[row][column] == "empty":
                    list_of_empty_tiles.append((row, column))
                    if self.Location_Strategy == "Base":
                        if game_map.Check_Adjecent_To_Base(row, column):
                            return row, column
                    elif self.Location_Strategy == "Spawner":
                        if game_map.Check_Adjecent_To_Spawner(row, column):
                            return row, column
                    else:  # For "Tiles" or "Spread"
                        num_of_tiles = game_map.count_surrounding_tiles(tower, row, column)
                        if num_of_tiles > biggest_num_of_tiles:
                            biggest_num_of_tiles = num_of_tiles
                            best_location_row = row
                            best_location_column = column

        if best_location_row == 0 and best_location_column == 0 and game_map.map_2d[best_location_row][
            best_location_column] != "empty":
            row, column = list_of_empty_tiles[random.randint(0, len(list_of_empty_tiles) - 1)]
            return row, column
        return best_location_row, best_location_column

    def Place_Tower(self, game_map: Game_Map, Min_Money: float):
        """
        Place a tower on the map if enough money is available and a valid location exists.

        Parameters:
            game_map (Game_Map): The current game map.
            Min_Money (float): Minimum amount of money that must remain after placement.

        Returns:
            list: The updated 2D map after attempting to place the tower.
        """
        cheapest_tower = cl.MinigunTower(0, 0)
        for tower in self.Tower_Strategy:
            if tower.price < cheapest_tower.price:
                cheapest_tower = tower
        if game_map.Check_num_of_Tiles("empty") == 0:
            return game_map.map_2d
        if G.Player_Money < cheapest_tower.price:
            return game_map.map_2d
        if G.Player_Money - cheapest_tower.price < Min_Money:
            return game_map.map_2d
        if len(self.Tower_Strategy) > 0:
            Tower_Options = copy.deepcopy(self.Tower_Strategy)
        else:
            Tower_Options = copy.deepcopy(cl.towers_list)
        tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
        while G.Player_Money < tower.price or G.Player_Money - tower.price < Min_Money:
            tower = Tower_Options[random.randint(0, len(Tower_Options) - 1)]
        row, column = self.choose_tower_location(game_map, tower)
        tower.row = row
        tower.column = column
        if len(self.Tower_Attack_Strategy) > 0:
            Attack_Type_Options = self.Tower_Attack_Strategy
        else:
            Attack_Type_Options = cl.towers_attack_types
        tower.attack_type = Attack_Type_Options[random.randint(0, len(Attack_Type_Options) - 1)]
        game_map.map_2d[tower.row][tower.column] = tower
        G.List_Of_Towers.append(tower)
        G.Player_Money -= tower.price
        return game_map.map_2d

    def Do_Turn(self, game_map: Game_Map):
        """
        Execute a turn of the algorithm, either placing a tower or upgrading based on the algorithm's strategy.

        Parameters:
            game_map (Game_Map): The current game map.
        """
        total_money = G.Player_Money
        Normal_Tower_Instance = cl.NormalTower(0, 0)
        cheapest_tower_price = 1000
        if len(self.Tower_Strategy) == 0:
            self.Tower_Strategy = copy.deepcopy(cl.towers_list)
        for tower in self.Tower_Strategy:
            if tower.price < cheapest_tower_price:
                cheapest_tower_price = tower.price
                cheapest_tower = tower
        Min_Money = total_money * (1 - self.Money_Strategy)
        while (G.Player_Money > Min_Money and G.Player_Money >= cheapest_tower_price and
               game_map.Check_num_of_Tiles("empty") > 0):
            Upgrades_Available = False
            if (G.Player_Money - cheapest_tower_price < Min_Money and
                    G.Player_Money - cheapest_tower.upgrade_1_cost < Min_Money):
                return game_map

            temp_list_of_towers = copy.deepcopy(G.List_Of_Towers)
            Upgrades_Available_1 = False
            Upgrades_Available_2 = False
            for t in temp_list_of_towers:
                if not t.upgrade_1:
                    Upgrades_Available1 = True
                if not t.upgrade_2 and t.upgrade_1:
                    Upgrades_Available_2 = True

            if self.Upgrade_Strategy == 1 and not Upgrades_Available_1:
                game_map.map_2d = self.Place_Tower(game_map, Min_Money)
            elif self.Upgrade_Strategy == 0 and G.Player_Money >= Normal_Tower_Instance.price and G.Player_Money - cheapest_tower_price >= Min_Money:
                game_map.map_2d = self.Place_Tower(game_map, Min_Money)
            elif self.Upgrade_Strategy == 1:
                if G.Player_Money - cheapest_tower.upgrade_1_cost < Min_Money:
                    return game_map
                else:
                    tower = G.List_Of_Towers[random.randint(0, len(G.List_Of_Towers) - 1)]
                    while (G.Player_Money - tower.upgrade_1_cost < Min_Money or tower.upgrade_1):
                        tower = G.List_Of_Towers[random.randint(0, len(G.List_Of_Towers) - 1)]
                    tower.Upgrade_Tower()
            elif self.Upgrade_Strategy == 2:
                if not Upgrades_Available_2 and not Upgrades_Available_1:
                    game_map.map_2d = self.Place_Tower(game_map, Min_Money)
                elif not Upgrades_Available_2 and Upgrades_Available_1:
                    while (G.Player_Money - tower.upgrade_1_cost < Min_Money or tower.upgrade_1):
                        tower = G.List_Of_Towers[random.randint(0, len(G.List_Of_Towers) - 1)]
                    tower.Upgrade_Tower()
                else:
                    tower = G.List_Of_Towers[random.randint(0, len(G.List_Of_Towers) - 1)]
                    while (G.Player_Money - tower.upgrade_2_cost < Min_Money or tower.upgrade_2 or not tower.upgrade_1):
                        tower = G.List_Of_Towers[random.randint(0, len(G.List_Of_Towers) - 1)]
                    tower.Upgrade_Tower()

            if (
                    not Upgrades_Available_1 and not Upgrades_Available_2 and G.Player_Money >= Normal_Tower_Instance.price):
                if G.Player_Money - cheapest_tower_price < Min_Money:
                    break
                else:
                    game_map.map_2d = self.Place_Tower(game_map, Min_Money)

    def check_blocks_in_range(self, temp_map, tower):
        """
        Mark blocks in the map that are within the attack range of the specified tower.

        Parameters:
            temp_map (list): A temporary copy of the map.
            tower (Tower): The tower to check against.

        Returns:
            list: The updated temporary map with marked tiles.
        """
        for row in range(max(tower.row - tower.attack_range, 0), min(tower.row + tower.attack_range + 1, G.Rows)):
            for column in range(max(tower.column - tower.attack_range, 0),
                                min(tower.column + tower.attack_range + 1, G.Columns)):
                if temp_map[row][column] in ["road", "spawner"] or isinstance(temp_map[row][column], cl.Enemy):
                    temp_map[row][column] = "marked"
        return temp_map


class Game:
    """
    Manages the overall game loop and execution.

    Coordinates tower actions, enemy movements, rounds, and integrates optional RL agent control.
    """

    def __init__(self, Game_map: Game_Map, Tower_Algorithm: Tower_Algorithm,
                 Enemy_Algorithm, use_rl_agent=False, rl_agent=None):
        """
        Initialize the Game with a map, tower and enemy algorithms, and optionally an RL agent.

        Parameters:
            Game_map (Game_Map): The game map object.
            Tower_Algorithm (Tower_Algorithm): The algorithm used for tower decisions.
            Enemy_Algorithm: The algorithm for enemy spawning and movement.
            use_rl_agent (bool): Flag indicating if an RL agent is used.
            rl_agent: The RL agent object (if any).
        """
        self.Game_map = Game_map
        self.Tower_Algorithm = Tower_Algorithm
        self.Enemy_Algorithm = Enemy_Algorithm
        self.use_rl_agent = use_rl_agent
        self.rl_agent = rl_agent
        self.rl_agent: DQLAgent
        self.state = None
        self.previous_state = None
        self.current_reward = None
        self.current_action = None
        self.previous_action = None
        self.previous_enemies_killed = 0

    def Run_Game(self):
        """
        Run the main game loop until the player runs out of health.

        Handles enemy movement, tower attacks, RL agent actions (if used), and round updates.
        """
        while True:
            Remake_Enemy_list(self.Game_map)
            for Tower in range(0, len(G.List_Of_Towers)):
                self.Game_map.map_2d = G.List_Of_Towers[Tower].Check_Attack(self.Game_map.map_2d)
            num_of_enemies = len(G.List_Of_Enemies)
            for enemy in range(0, len(G.List_Of_Enemies)):
                if enemy < len(G.List_Of_Enemies):
                    self.Game_map.map_2d = G.List_Of_Enemies[enemy].Move(self.Game_map.map_2d)
                if G.Player_HP <= 0:
                    break
                if (len(G.List_Of_Enemies) < num_of_enemies and len(G.List_Of_Enemies) > 0 and enemy < len(
                        G.List_Of_Enemies)):
                    self.Game_map.map_2d = G.List_Of_Enemies[enemy].Move(self.Game_map.map_2d)
                    num_of_enemies = len(G.List_Of_Enemies)

            if self.previous_state is not None:
                self.state = self.collect_state()
                self.rl_agent.remember(self.previous_state, self.current_action, self.current_reward, self.state,
                                       G.Player_HP > 0)

            if G.Player_HP > 0:
                self.Rounds()
            else:
                break

    def Rounds(self):
        """
        Update the game state each round.

        Handles RL agent actions (if an agent exists), enemy actions, tower placements/upgrades,
        money updates, and round count increments.
        """
        initial_enemies_killed = G.enemies_killed

        if G.num_of_rounds % 4 == 0:
            if self.use_rl_agent and self.rl_agent:
                self.previous_action = self.current_action
                reward = 0
                current_state = self.collect_state()
                action_tuple = self.rl_agent.act(current_state)
                action, tower_type, tower_attack_type, location = action_tuple
                self.current_action = action_tuple
                prev_money = G.Player_Money

                reward += self.check_duplicate_actions()
                reward += self.execute_action(action, tower_type, tower_attack_type, location)
                self.current_reward = reward
                self.previous_state = current_state

            self.Game_map.map_2d = self.Enemy_Algorithm(self.Game_map)

            if self.use_rl_agent and self.rl_agent and G.num_of_rounds % 100 == 0 and G.num_of_rounds != 0:
                self.rl_agent.replay(self.rl_agent.batch_size)
        if G.num_of_rounds % 40 == 0:
            if not self.use_rl_agent:
                self.Tower_Algorithm.Do_Turn(self.Game_map)
            G.Enemy_Money = G.Enemy_Money + 10 * float(G.num_of_rounds / 100)
            G.Player_Money = G.Player_Money + 50 + (G.num_of_rounds / 10)
        G.num_of_rounds += 1


    def execute_action(self, action, tower_type=None, tower_attack_type=None, location=None):
        """
        Execute an action of the Rl agent (place tower, upgrade tower, or skip turn)
        and calls a function to calculate the reward for the action and returns the reward.

        Parameters:
            action: The action to execute.
            tower_type: (Optional) The type of tower involved.
            tower_attack_type: (Optional) The attack type for the tower.
            location: (Optional) The location for the action.

        Returns:
            int: The reward from executing the action.
        """
        reward = 0
        if action == 'place_tower' or action == 0:
            if tower_type is not None and location is not None:
                tower = tower_type(0, 0)
                tower.attack_type = tower_attack_type
                tower.row, tower.column = location
            else:
                tower = random.choice(cl.List_Of_Towers_Options)(0, 0)
                tower.attack_type = random.choice(cl.towers_attack_types)
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                tower.row, tower.column = row, column
            if G.Player_Money >= tower.price:
                if self.Game_map.map_2d[tower.row][tower.column] == "empty":
                    self.Game_map.map_2d[tower.row][tower.column] = tower
                    G.List_Of_Towers.append(tower)
                    reward += self.calculate_reward(action, tower, (tower.row, tower.column))
                    G.Player_Money -= tower.price
                else:
                    reward += self.calculate_reward(action, tower, (tower.row, tower.column))
            else:
                reward += self.calculate_reward(action, tower, (tower.row, tower.column))
        elif action == 'upgrade_tower' or action == 1:
            if location:
                row, col = location
            else:
                row = random.randint(0, G.Rows - 1)
                col = random.randint(0, G.Columns - 1)
                tower_type = random.choice(cl.List_Of_Towers_Options)
            if isinstance(self.Game_map.map_2d[row][col], tower_type):
                tower = self.Game_map.map_2d[row][col]
                upgrade_cost = None
                if tower.upgrade_2:
                    upgrade_cost = None
                elif tower.upgrade_1:
                    upgrade_cost = tower.upgrade_2_cost
                else:
                    upgrade_cost = tower.upgrade_1_cost
                if upgrade_cost:
                    if G.Player_Money >= upgrade_cost:
                        tower.Upgrade_Tower()
                        reward += self.calculate_reward(action, tower, location, True)
                    else:
                        reward += self.calculate_reward(action, tower, location)
                else:
                    reward += self.calculate_reward(action, tower, location)
            else:
                reward += self.calculate_reward(action)
        elif action == 'skip_turn' or action == 2:
            reward += self.calculate_reward(action)
        return reward

    def calculate_reward(self, action, tower=None, tower_location=None, upgrade_tower=False):
        """
        Calculates the reward based on the performed action and the current state of the game.

        The reward is calculated based on things such as, how many towers have already been placed,
        the current danger level (how many enemies and how close they are to base, etc.

        Parameters:
            action: The action taken.
            tower: (Optional) The tower involved.
            tower_location: (Optional) The location of the tower.
            upgrade_tower (bool): Whether an upgrade was successful.

        Returns:
            int: The calculated reward.
        """
        action_dict = {0: "place_tower", 1: "upgrade_tower", 2: "skip_turn"}
        reward = 0
        if isinstance(action, int):
            action = action_dict[action]
        if action == "place_tower":
            if (self.Game_map.map_2d[tower.row][tower.column] != tower and
                    self.Game_map.map_2d[tower.row][tower.column] != "empty"):
                reward -= 150
            elif self.Game_map.map_2d[tower.row][tower.column] == "empty" and G.Player_Money < tower.price:
                reward -= 100
            elif self.Game_map.count_surrounding_tiles(tower, tower.row, tower.column) == 0:
                reward -= 100
            else:
                if len(G.List_Of_Towers) == 1:
                    reward += 100
                reward += 50
                reward += 5 * self.Game_map.count_surrounding_tiles(tower, tower.row, tower.column)
                reward += 10 * tower.Check_Surrounding_Enemies(self.Game_map.map_2d)
        elif action == "upgrade_tower":
            if not tower:
                reward -= 100
            else:
                if upgrade_tower:
                    reward += 100
                    reward += 5 * self.Game_map.count_surrounding_tiles(tower, tower.row, tower.column)
                    reward += 10 * tower.Check_Surrounding_Enemies(self.Game_map.map_2d)
                else:
                    reward -= 50
        elif action == "skip_turn":
            if self.Game_map.Check_num_of_Tiles("empty") != 0:
                if G.Player_Money > cl.MinigunTower(0, 0).price:
                    reward -= 200
            for tower in cl.towers_list[:-1]:
                if G.Player_Money < tower.price:
                    reward += 10
            reward += self.calculate_risk_level()
        return reward

    def check_duplicate_actions(self):
        """
        Check for duplicate consecutive actions and adjust the reward accordingly.

        This function is used to encourage the RL agent to not take the same action too many times consecutively.

        Returns:
            int: The reward adjustment based on duplicate actions.
        """
        reward = 0
        if self.previous_action:
            action, tower, tower_attack_type, location = self.current_action
            if self.current_action[0] == self.previous_action[0]:
                if self.current_action[0] == "place_tower":
                    if tower == self.previous_action[1] and location == self.previous_action[-1]:
                        tower_price = tower(0, 0).price
                        if isinstance(self.Game_map.map_2d[location[0]][location[1]], tower):
                            reward -= 100
                        elif G.Player_Money >= tower_price:
                            reward += 50
                        elif G.Player_Money < tower_price:
                            reward -= 50
                elif self.current_action[0] == "upgrade_tower":
                    if tower == self.previous_action[1] and location == self.previous_action[-1]:
                        tower = self.Game_map.map_2d[location[0]][location[1]]
                        if isinstance(tower, cl.Tower):
                            if tower.upgrade_2:
                                reward -= 50
                            if not tower.upgrade_1:
                                if G.Player_Money >= tower.upgrade_1_cost:
                                    reward += 50
                                else:
                                    reward -= 50
        return reward

    def calculate_risk_level(self):
        """
        Calculate the current risk level from enemy presence relative to player health.

        Returns:
            float: The risk-based reward (positive for low risk, negative for high risk).
        """
        risk_level = 0.0
        max_possible_distance = (G.Rows / 2 + G.Columns - 1)
        for enemy in G.List_Of_Enemies:
            enemy_distance_from_base = abs(G.Rows / 2 - enemy.row) + abs(G.Columns - enemy.column - 1)
            distance_factor = max(0.1, max_possible_distance / enemy_distance_from_base)
            enemy_risk = ((enemy.base_damage * enemy.health * distance_factor)) / G.Player_HP
            risk_level += enemy_risk
        risk_level = min(risk_level, 500)
        if risk_level < 50:
            reward = (50 - risk_level)
        elif risk_level < 200:
            reward = (50 - risk_level) / 2
        else:
            reward = -risk_level / 2
        if G.List_Of_Enemies == 0:
            reward = 50
        return reward



    def collect_state(self):
        """
        Collect the current state of the game.

        Returns:
            list: A deep copy of the current map, towers, enemies, player HP, and player money.
        """
        state = [copy.deepcopy(self.Game_map.map_2d),
                 copy.deepcopy(G.List_Of_Towers),
                 copy.deepcopy(G.List_Of_Enemies),
                 copy.copy(G.Player_HP),
                 copy.copy(G.Player_Money)]
        return state


class All_Money_Algorithm(Tower_Algorithm):
    """
    A simple Tower_Algorithm that uses all available money for tower placement.
    """

    def __init__(self):
        super().__init__(Location_Strategy="Tiles", Money_Strategy=1,
                         Tower_Strategy=copy.deepcopy(cl.towers_list),
                         Upgrade_Strategy=0, Tower_Attack_Strategy=[],
                         Name="All_Money_Algorithm")


class Spread_Algorithm(Tower_Algorithm):
    """
    A simple Tower_Algorithm that prefers spreading towers across the map.
    """

    def __init__(self):
        super().__init__(Location_Strategy="Spread", Money_Strategy=0.5,
                         Tower_Strategy=copy.deepcopy(cl.towers_list),
                         Upgrade_Strategy=0, Tower_Attack_Strategy=[],
                         Name="Spread_Algorithm")


class Upgrade_Algorithm(Tower_Algorithm):
    """
    A simple Tower_Algorithm that prefers upgrading existing towers.
    """

    def __init__(self):
        super().__init__(Location_Strategy="Tiles", Money_Strategy=0.5,
                         Tower_Strategy=copy.deepcopy(cl.towers_list),
                         Upgrade_Strategy=2, Tower_Attack_Strategy=[],
                         Name="Upgrade_Algorithm")


class Local_Search_Algorithm:
    """
    A local Search Algorithm to find the best Tower_Algorithm
    """

    def __init__(self, game_map_template, enemy_algorithm, iterations=100):
        """
        Initialize the Local_Search_Algorithm.

        Parameters:
            game_map_template: The base map used for evaluation.
            enemy_algorithm: The enemy algorithm function.
            iterations (int): Number of search iterations.
        """
        self.game_map_template = game_map_template
        self.enemy_algorithm = enemy_algorithm
        self.iterations = iterations
        self.best_algorithm = None
        self.best_performance = None

    def evaluate_algorithm(self, algorithm):
        """
        Evaluate a given algorithm by running a game simulation.

        Parameters:
            algorithm: The tower algorithm to evaluate.

        Returns:
            dict: Game stats including enemies killed, rounds survived, and duration.
        """
        Reset_Game_Settings()
        game_map = copy.deepcopy(self.game_map_template)
        game_map.Enemy_Order = copy.copy(game_map.Enemy_Order_Copy)
        game = Game(game_map, algorithm, self.enemy_algorithm)
        start_time = time.time()
        game.Run_Game()
        end_time = time.time()
        game_duration = end_time - start_time
        game_stats = {
            "enemies_killed": G.enemies_killed,
            "rounds": G.num_of_rounds,
            "duration_seconds": game_duration
        }
        return game_stats

    def modify_algorithm(self, algorithm):
        """
        Modify the algorithm by randomly changing one attribute.

        Parameters:
            algorithm: The tower algorithm to modify.

        Returns:
            The modified algorithm.
        """
        modify_random_attribute(algorithm)
        return algorithm

    def run(self):
        """
        Runs the simulation for the amount of iterations,
        and uses the local search optimization process to find the best Tower_Algorithm,
        for each iteration, a modified version of the current best algorithm is evaluated.

        Returns:
            tuple: (best_algorithm, average_rounds_survived, best_rounds)
        """
        total_rounds = 0
        current_algorithm = Create_Random_Tower_Algorithm("Local_Search_Algorithm")
        self.best_algorithm = copy.deepcopy(current_algorithm)
        self.best_performance = self.evaluate_algorithm(self.best_algorithm)
        all_rounds_survived = []
        for iteration in range(self.iterations):
            new_algorithm = self.modify_algorithm(copy.deepcopy(current_algorithm))
            new_performance = self.evaluate_algorithm(new_algorithm)
            total_rounds += new_performance["rounds"]
            all_rounds_survived.append(new_performance["rounds"])
            if new_performance["rounds"] > self.best_performance["rounds"]:
                self.best_algorithm = copy.deepcopy(new_algorithm)
                self.best_performance = new_performance
                current_algorithm = copy.deepcopy(new_algorithm)
        return self.best_algorithm, float(total_rounds / self.iterations), self.best_performance["rounds"]


class Genetic_Tower_Algorithm(Tower_Algorithm):
    """
    A Genetic Algorithm to find the best Tower_Algorithm.
    """

    def __init__(self, population_size, generations, mutation_rate, game_map, enemy_algorithm):
        """
        Initialize the Genetic_Tower_Algorithm.

        Parameters:
            population_size (int): Number of strategies in the population.
            generations (int): Number of generations to evolve.
            mutation_rate (float): Probability of mutation.
            game_map: The game map used for evaluation.
            enemy_algorithm: The enemy algorithm function.
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.game_map = game_map
        self.enemy_algorithm = enemy_algorithm
        self.population = self.initialize_population()
        self.Best_Performance = 0
        self.Best_Algorithm = None

    def initialize_population(self):
        """
        Initialize a population of random tower algorithms.

        Returns:
            list: The list of generated algorithms.
        """
        population = []
        for i in range(self.population_size):
            algorithm = Create_Random_Tower_Algorithm("Genetic_Algorithm")
            population.append(algorithm)
        return population

    def evaluate_population(self):
        """
        Evaluate the performance of the current population.

        Returns:
            list: Sorted performance data (highest to lowest from left to right).
        """
        global game_number
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
            game_stats = {
                "algorithm": algorithm,
                "enemies_killed": G.enemies_killed,
                "rounds": G.num_of_rounds,
                "duration_seconds": game_duration
            }
            performance_data.append(game_stats)
        performance_data.sort(key=lambda x: x["rounds"], reverse=True)
        return performance_data

    def select_best_algorithms(self, performance_data, top_n=2):
        """
        Select the best performing algorithms.

        Parameters:
            performance_data (list): List of performance dictionaries.
            top_n (int): Number of top algorithms to select.

        Returns:
            list: The best algorithms.
        """
        best_algorithms = [data["algorithm"] for data in performance_data[:top_n]]
        return best_algorithms

    def mutate_algorithm(self, algorithm):
        """Apply mutation to a given algorithm."""
        modify_random_attribute(algorithm)

    def crossover_algorithms(self, parent1, parent2):
        """
        Create a child algorithm by combining attributes from two parents.

        Parameters:
            parent1: The first parent algorithm.
            parent2: The second parent algorithm.

        Returns:
            Tower_Algorithm: The child algorithm.
        """
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
        """
        Evolve the current population using selection, mutation, and crossover.

        Parameters:
            performance_data (list): The evaluated performance data.
        """
        best_algorithms = self.select_best_algorithms(performance_data)
        new_population = []
        parent1, parent2 = random.sample(best_algorithms, 2)
        for _ in range(self.population_size):
            if random.random() < self.mutation_rate:
                algorithm = random.choice(best_algorithms)
                self.mutate_algorithm(algorithm)
            else:
                algorithm = self.crossover_algorithms(parent1, parent2)
            new_population.append(algorithm)
        self.population = new_population

    def run(self):
        """
        Run the genetic algorithm over several generations to find the best Tower_Algorithm.

        Returns:
            tuple: (best_algorithm, average_rounds_survived, best_rounds)
        """
        total_rounds = 0
        all_rounds_survived = []
        for generation in range(self.generations):
            performance_data = self.evaluate_population()
            for item in performance_data:
                total_rounds += item["rounds"]
                all_rounds_survived.append(item["rounds"])
                if item["rounds"] > self.Best_Performance:
                    self.Best_Performance = item["rounds"]
                    self.Best_Algorithm = copy.deepcopy(item["algorithm"])
            self.evolve_population(performance_data)
        return self.Best_Algorithm, float(
            total_rounds / (self.generations * self.population_size)), self.Best_Performance


class Simulated_Annealing_Algorithm:
    """
    A Simulated Annealing Algorithm to find the best Tower_Algorithm.
    """

    def __init__(self, game_map_template: Game_Map, enemy_algorithm,
                 initial_temperature: float, cooling_rate: float, iterations: int):
        """
        Initialize the simulated annealing algorithm.

        Parameters:
            game_map_template (Game_Map): The map template for evaluation.
            enemy_algorithm: The enemy algorithm function.
            initial_temperature (float): Starting temperature.
            cooling_rate (float): Rate at which the temperature decreases.
            iterations (int): Number of iterations to run.
        """
        self.game_map_template = game_map_template
        self.enemy_algorithm = enemy_algorithm
        self.current_algorithm = Create_Random_Tower_Algorithm("Simulated_Annealing_Algorithm")
        self.current_performance = None
        self.best_algorithm = self.current_algorithm
        self.current_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.iterations = iterations

    def acceptance_probability(self, current_performance, new_performance):
        """
        Calculate the probability of a Tower_Algorithm being accepted based on the current/best performance,
        and the new performance of the Tower_Algorithm being evaluated.

        Parameters:
            current_performance (dict): Performance of the current/best algorithm.
            new_performance (dict): Performance of the new algorithm.

        Returns:
            float: Acceptance probability.
        """
        current_score = current_performance["rounds"]
        new_score = new_performance["rounds"]
        if new_score >= current_score:
            if new_performance["enemies_killed"] >= current_performance["enemies_killed"]:
                return 1.0
            else:
                return math.exp((new_performance["enemies_killed"] - current_performance[
                    "enemies_killed"]) / self.current_temperature)
        return math.exp((new_score - current_score) / self.current_temperature)

    def evaluate_algorithm(self, algorithm: Tower_Algorithm):
        """
        Evaluate an algorithm by running a game simulation.

        Parameters:
            algorithm (Tower_Algorithm): The algorithm to evaluate.

        Returns:
            dict: Performance (enemies killed, rounds, duration).
        """
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
            "rounds": rounds_survived,
            "duration_seconds": game_duration
        }
        return performance_score

    def run(self):
        """
        Runs the simulation for the amount of iterations,
        and uses the Simulated Annealing optimization process to find the best Tower_Algorithm,
        for each iteration, a modified version of the current best algorithm is evaluated.

        Returns:
            tuple: (best_algorithm, average_rounds_survived, best_rounds)
        """
        total_rounds = 0
        best_performance = self.evaluate_algorithm(self.best_algorithm)
        all_rounds_survived = []
        for i in range(self.iterations):
            new_algorithm = copy.deepcopy(self.current_algorithm)
            modify_random_attribute(new_algorithm)
            if not self.current_performance:
                self.current_performance = self.evaluate_algorithm(self.current_algorithm)
            new_performance = self.evaluate_algorithm(new_algorithm)
            current_score = self.current_performance["rounds"]
            new_score = new_performance["rounds"]
            total_rounds += new_score
            all_rounds_survived.append(new_score)
            acceptance_probability = self.acceptance_probability(self.current_performance, new_performance)
            if acceptance_probability >= random.random():
                self.current_algorithm = new_algorithm
                self.current_performance = new_performance
                self.best_algorithm = copy.deepcopy(new_algorithm)
                best_performance = self.current_performance
            self.current_temperature *= self.cooling_rate
            self.current_temperature = max(self.current_temperature, 0.0001)
        return self.best_algorithm, float(total_rounds / self.iterations), best_performance["rounds"]


class DQLAgent:
    """
    Deep Q-Learning (DQL) Agent using PyTorch for decision making.
    """

    def __init__(self, state_size,gamma=0.95, epsilon=1, epsilon_decay=0.995, epsilon_min=0.01,learning_rate=0.001,batch_size=64):
        """
        Initialize the Deep Q-Learning (DQL) agent with specified parameters.

        Parameters:
            state_size (int): The dimensionality of the state representation.
            gamma (float, optional): Discount factor for future rewards. Default set to 0.95
            epsilon (float, optional): Initial exploration rate. Default set to 1
            epsilon_decay (float, optional): Multiplicative factor to decay the exploration rate after each training step. Default set to 0.995.
            epsilon_min (float, optional): Minimum allowable exploration rate. Default set to 0.01.
            learning_rate (float, optional): Learning rate for the optimizer. Default set to 0.001.
            batch_size (int, optional): Number of experiences sampled during each training replay. Default set to 64.

        Attributes:
            memory (collections.deque): A deque storing past experiences with a maximum length of 50,000.
            model (torch.nn.Module): The neural network model that approximates the Q-value function.
            optimizer (torch.optim.Optimizer): Adam optimizer configured with the given learning rate and weight decay.
            best_performance (dict): Tracks the best performance with keys 'enemies_killed' and 'rounds_survived'.
            loss_history (list): Stores the loss values recorded during training.
        """
        self.memory = collections.deque(maxlen=50000)
        self.state_size = state_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.model = self._build_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=1e-5)
        self.best_performance = {"enemies_killed": 0, "rounds_survived": 0}
        self.loss_history = []

    def _build_model(self):
        """
        Build the neural network model (with 2 hidden layers).
        Calculates the output size based on the total amount of different possible actions.

        Returns:
            nn.Module: The PyTorch neural network model.
        """
        total_tower_types = len(cl.List_Of_Towers_Options)
        map_size = G.Rows * G.Columns
        tower_attack_types = 4
        place_tower_options_size = (map_size * total_tower_types * tower_attack_types)
        upgrade_tower_options_size = (map_size * total_tower_types)
        total_action_space_size = place_tower_options_size + upgrade_tower_options_size + 1
        model = nn.Sequential(
            nn.Linear(self.state_size, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, total_action_space_size)
        )
        return model

    def remember(self, state, action, reward, next_state, done):
        """
        Store an experience in memory.

        Parameters:
            state: Current state.
            action: Action taken.
            reward (float): Reward received.
            next_state: Next state.
            done (bool): Whether the episode is finished.
        """
        encoded_state = self.encode_state(state)
        encoded_next_state = self.encode_state(next_state)
        self.memory.append((encoded_state, action, float(reward / 300), encoded_next_state, done))

    def act(self, state):
        """
        Chooses an action either randomly based on the epsilon value (Exploration) or
        Choose an action based on the current state and the memory of the agent (Exploitation).

        Parameters:
            state: The current state.

        Returns:
            tuple: The chosen action.
        """
        encoded_state = self.encode_state(state)
        state_tensor = torch.FloatTensor(encoded_state).unsqueeze(0)
        if random.random() <= self.epsilon:
            action = random.choice(["place_tower", "upgrade_tower", "skip_turn"])
            if action == "place_tower":
                tower_type = random.choice(cl.List_Of_Towers_Options)
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                tower_attack_type = random.choice(cl.towers_attack_types)
                return (action, tower_type, tower_attack_type, (row, column))
            elif action == "upgrade_tower":
                tower_type = random.choice(cl.List_Of_Towers_Options)
                row = random.randint(0, G.Rows - 1)
                column = random.randint(0, G.Columns - 1)
                return (action, tower_type, None, (row, column))
            else:
                return (action, None, None, None)
        else:
            q_values = self.model(state_tensor)
            action_index = torch.argmax(q_values[0]).item()
            action = self.decode_action(action_index)
        return action

    def replay(self, batch_size):
        """
        Perform experience replay to train the network.

        Parameters:
            batch_size (int): Number of experiences to sample.
        """
        action_map = {"place_tower": 0, "upgrade_tower": 1, "skip_turn": 2}
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        minibatch_predicted_q_values = []
        minibatch_target_q_values = []
        for state, (action, tower_type, tower_attack_type, location), reward, next_state, done in minibatch:
            action_index = self.encode_action(action, tower_type, tower_attack_type, location)
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)
            q_values = self.model(state_tensor)
            q_value_for_action = q_values.flatten()[action_index]
            target_q_value = reward
            if not done:
                next_q_values = self.model(next_state_tensor).max(1)[0].item()
                target_q_value += self.gamma * next_q_values
            minibatch_predicted_q_values.append(q_value_for_action)
            minibatch_target_q_values.append(target_q_value)
        minibatch_predicted_q_values = torch.stack(minibatch_predicted_q_values)
        minibatch_target_q_values = torch.tensor(minibatch_target_q_values, requires_grad=False, dtype=torch.float32)
        loss = F.mse_loss(minibatch_predicted_q_values, minibatch_target_q_values)
        self.loss_history.append(loss.item())
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def update_performance(self, enemies_killed, rounds_survived):
        """
        Update the best performance metrics if the current round is better.

        Parameters:
            enemies_killed (int): Number of enemies killed.
            rounds_survived (int): Number of rounds survived.
        """
        if rounds_survived > self.best_performance["rounds_survived"]:
            self.best_performance["rounds_survived"] = rounds_survived
            self.best_performance["enemies_killed"] = enemies_killed

    def save(self, model_path, memory_path):
        """
        Save the model parameters and memory to files.

        Parameters:
            model_path (str): File path for the model.
            memory_path (str): File path for the memory.
        """
        torch.save(self.model.state_dict(), model_path)
        with open(memory_path, 'wb') as f:
            pickle.dump(self.memory, f)
        print("The model and memory were saved successfully")

    def load(self, model_path, memory_path):
        """
        Load the model parameters and memory from files.

        Parameters:
            model_path (str): File path for the model.
            memory_path (str): File path for the memory.
        """
        self.model.load_state_dict(torch.load(model_path))
        try:
            with open(memory_path, 'rb') as f:
                self.memory = pickle.load(f)
            print("Memory load was successful")
        except FileNotFoundError:
            print("Memory file not found")
            self.memory = collections.deque(maxlen=50000)

    def encode_action(self, action, tower_type, tower_attack_type, location):
        """
        Encode an action into a unique index for the Q-network.

        Parameters:
            action: The action type.
            tower_type: The type of tower.
            tower_attack_type: The tower's attack type.
            location: The (row, column) location.

        Returns:
            int: The encoded action index.
        """
        action_dict = {"place_tower": 0, "upgrade_tower": 1, "skip_turn": 2}
        if isinstance(action, str):
            action_type_index = action_dict[action]
        else:
            action_type_index = action
        if action == "place_tower":
            tower_type_index = cl.List_Of_Towers_Options.index(tower_type)
            tower_attack_type_index = cl.towers_attack_types.index(tower_attack_type)
            location_index = location[0] * G.Columns + location[1]
            total_tower_types = len(cl.List_Of_Towers_Options)
            total_attack_types = len(cl.towers_attack_types)
            map_size = G.Rows * G.Columns
            index = tower_type_index * total_attack_types * map_size + tower_attack_type_index * map_size + location_index
        elif action == "upgrade_tower":
            tower_type_index = cl.List_Of_Towers_Options.index(tower_type)
            location_index = location[0] * G.Columns + location[1]
            total_tower_types = len(cl.List_Of_Towers_Options)
            total_attack_types = len(cl.towers_attack_types)
            map_size = G.Rows * G.Columns
            index = (total_attack_types * total_tower_types * map_size) + (tower_type_index * map_size + location_index)
        else:
            total_tower_types = len(cl.List_Of_Towers_Options)
            total_attack_types = len(cl.towers_attack_types)
            map_size = G.Rows * G.Columns
            index = (total_attack_types * total_tower_types * map_size) + (total_tower_types * map_size)
        return index

    def decode_action(self, index):
        """
        Decode an action index back into its components.

        Parameters:
            index (int): The encoded action index.

        Returns:
            tuple: (action, tower_type, tower_attack_type, location)
        """
        action_dict = {0: "place_tower", 1: "upgrade_tower", 2: "skip_turn"}
        total_tower_types = len(cl.List_Of_Towers_Options)
        tower_attack_types = 4
        map_size = G.Rows * G.Columns
        place_tower_options_size = (map_size * total_tower_types * tower_attack_types)
        upgrade_tower_options_size = (map_size * total_tower_types)
        total_actions = place_tower_options_size + upgrade_tower_options_size + 1
        if index >= place_tower_options_size:
            if index == total_actions - 1:
                action = "skip_turn"
            else:
                action = "upgrade_tower"
        else:
            action = "place_tower"
        if action == "place_tower":
            tower_type_index = int(index / (map_size * tower_attack_types))
            tower_attack_type_index = int(index / map_size) - (tower_type_index * tower_attack_types)
            location_index = index - (
                        (tower_type_index * (map_size * tower_attack_types)) + (tower_attack_type_index * map_size))
            row = location_index // G.Columns
            column = location_index % G.Columns
            location = (row, column)
            tower_type = cl.List_Of_Towers_Options[tower_type_index]
            tower_attack_type = cl.towers_attack_types[tower_attack_type_index]
            return (action, tower_type, tower_attack_type, location)
        elif action == "upgrade_tower":
            index = index - place_tower_options_size
            tower_type_index = int(index / map_size)
            location_index = index - (tower_type_index * map_size)
            row = location_index // G.Columns
            column = location_index % G.Columns
            location = (row, column)
            tower_type = cl.List_Of_Towers_Options[tower_type_index]
            return (action, tower_type, None, location)
        else:
            return (action, None, None, None)

    def encode_state(self, state):
        """
        Encode the full game state into a flat list of numbers for input into the network.

        Parameters:
            state (list): The game state (map, towers, enemies, player HP, player money).

        Returns:
            list: The encoded state.
        """
        game_map = state[0]
        towers_list = state[1]
        enemies_list = state[2]
        Player_HP = state[3]
        Player_Money = state[4]
        encoded_map = [G.tile_to_value[tile] for row in game_map for tile in row if isinstance(tile, str)]
        expected_map_size = G.Max_Map_Size
        encoded_map += [0] * (expected_map_size - len(encoded_map))
        encoded_towers = []
        encoded_enemies = []
        for tower in towers_list:
            tower_type = cl.List_Of_Towers_Options.index(type(tower))
            if tower.upgrade_2:
                tower_level = 2
            elif tower.upgrade_1:
                tower_level = 1
            else:
                tower_level = 0
            tower_attack_type = cl.towers_attack_types.index(tower.attack_type)
            encoded_towers.append(
                (tower_type + 1, tower.row + 1, tower.column + 1, tower_level + 1, tower_attack_type + 1))
        for enemy in enemies_list:
            enemy_type = cl.List_Of_Enemies_Options.index(type(enemy))
            encoded_enemies.append((enemy_type + 1, enemy.row + 1, enemy.column + 1, enemy.health))
        encoded_towers, encoded_enemies = self.pad_encode_state(encoded_towers, encoded_enemies, G.Max_Towers,
                                                                G.Max_Enemies)
        flattened_towers = [attribute for attributes in encoded_towers for attribute in attributes]
        flattened_enemies = [attribute for attributes in encoded_enemies for attribute in attributes]
        encoded_state = encoded_map + flattened_towers + flattened_enemies + [Player_HP] + [Player_Money]
        return encoded_state

    def pad_encode_state(self, encoded_towers, encoded_enemies, max_towers, max_enemies):
        """
        Pad the encoded towers and enemies to ensure a fixed state size.

        Parameters:
            encoded_towers (list): Encoded tower information.
            encoded_enemies (list): Encoded enemy information.
            max_towers (int): Maximum number of towers.
            max_enemies (int): Maximum number of enemies.

        Returns:
            tuple: (padded_towers, padded_enemies)
        """
        padded_towers = encoded_towers + [(0, 0, 0, 0, 0)] * (max_towers - len(encoded_towers))
        padded_towers = padded_towers[:max_towers]
        padded_enemies = encoded_enemies + [(0, 0, 0, 0)] * (max_enemies - len(encoded_enemies))
        padded_enemies = padded_enemies[:max_enemies]
        return padded_towers, padded_enemies

    def decode_state(self, state):
        """
        Decode an encoded state back into its original components.

        Parameters:
            state: The encoded state.

        Returns:
            list: The decoded state (map, towers, enemies, player HP, player money).
        """
        encoded_map = state[0]
        encoded_towers = state[1]
        encoded_enemies = state[2]
        decoded_map = [["" for _ in range(G.Columns)] for _ in range(G.Rows)]
        decoded_towers = []
        decoded_enemies = []
        for encoded_tower in encoded_towers:
            if encoded_tower[0] != 0:
                tower_row = encoded_tower[1] - 1
                tower_column = encoded_tower[2] - 1
                tower_level = encoded_tower[3] - 1
                tower_attack_type = encoded_tower[4] - 1
                tower = cl.List_Of_Towers_Options[encoded_tower[0] - 1](tower_row, tower_column)
                tower.attack_type = cl.towers_attack_types[tower_attack_type]
                temp_Player_Money = G.Player_Money
                if tower_level == 1:
                    tower.Upgrade_Tower()
                elif tower_level == 2:
                    tower.Upgrade_Tower()
                    tower.Upgrade_Tower()
                G.Player_Money = temp_Player_Money
                decoded_towers.append(tower)
                decoded_map[tower.row][tower.column] = tower
        for encoded_enemy in encoded_enemies:
            if encoded_enemy[0] != 0:
                enemy_row = encoded_enemy[1] - 1
                enemy_column = encoded_enemy[2] - 1
                enemy_health = encoded_enemy[3]
                enemy = cl.List_Of_Enemies_Options[encoded_enemy[0] - 1](enemy_row, enemy_column)
                enemy.health = enemy_health
                decoded_enemies.append(enemy)
                decoded_map[enemy.row][enemy.column] = enemy
        tile_index = 0
        for row in range(len(decoded_map)):
            for column in range(len(decoded_map[row])):
                tile = decoded_map[row][column]
                if tile == "":
                    decoded_map[row][column] = encoded_map[tile_index]
                    tile_index += 1
        player_hp = state[3]
        player_money = state[4]
        decoded_state = [decoded_map, decoded_towers, decoded_enemies, player_hp, player_money]
        return decoded_state


def run_agent(episodes, Game_map: Game_Map, agent: DQLAgent):
    """
    Runs the RL agent for a number of episodes/simulations.
    Trains the agent if the epsilon is set to a high value (Exploration process)
    Or simply runs the agent if epsilon set to a low value (Exploitation process).

    Parameters:
        episodes (int): Number of episodes/simulations.
        Game_map (Game_Map): The game map to use for all episodes.
        agent (DQLAgent): The RL agent.

    Returns:
        tuple: (agent, best_performance, average_rounds_survived)
    """
    training_Game_map = Game_map
    total_rounds_survived = 0
    all_rounds_survived = []
    for episode in range(episodes):
        episode_game_map = copy.deepcopy(training_Game_map)
        game = Game(episode_game_map, None, Enemy_Algorithm_function, use_rl_agent=True, rl_agent=agent)
        Reset_Game_Settings()
        G.Rows = len(episode_game_map.map_2d)
        G.Columns = len(episode_game_map.map_2d[0])
        game.Run_Game()
        total_rounds_survived += G.num_of_rounds
        all_rounds_survived.append(G.num_of_rounds)
        agent.replay(agent.batch_size)
        print(f"episode: {episode}, enemies killed: {G.enemies_killed}, num_of_rounds: {G.num_of_rounds}")
        agent.update_performance(G.enemies_killed, G.num_of_rounds)
    return agent, agent.best_performance, float(total_rounds_survived / episodes)


def save_performance(best_performance, filename='rl_algorithm_results.json'):
    """
    Save the best performance results to a JSON file.

    Parameters:
        best_performance: Performance data to save.
        filename (str): Filename to write to.
    """
    with open(filename, 'a') as f:
        json.dump(best_performance, f)
        f.write("\n")
    print(f"Best performance saved to {filename}", "best performance: ", best_performance)


def Enemy_Algorithm_function(Game_map: Game_Map):
    """
    The Main and only enemy algorithm
    Spawn enemies on the map according to available enemy money, spawn order and spawner availability.

    Parameters:
        Game_map (Game_Map): The game map.

    Returns:
        list: The updated map.
    """
    normal_enemy_instance = NormalEnemy(0, 0)
    i = 0
    enemy = 0
    if G.num_of_rounds >= 10:
        while normal_enemy_instance.price < G.Enemy_Money and Game_map.Num_Of_Spawners_Available() > 0:
            Enemies = copy.deepcopy(cl.List_Of_Enemies_Instances)
            if i == len(Game_map.Enemy_Order):
                break
            enemy_name = Game_map.Enemy_Order[i]
            for e in Enemies:
                if enemy_name == e.name:
                    enemy = e
                    break
            if enemy.price > G.Enemy_Money:
                i += 1
            else:
                Game_map = Create_Enemy(Game_map, enemy)
                G.Enemy_Money -= enemy.price
                Game_map.Enemy_Order.pop(i)
    return Game_map.map_2d


def Remake_Enemy_list(Game_map: Game_Map):
    """
    Reset the enemy and spawner orders if they are empty (in case the algorithm is very good and defeats all enemies)

    Parameters:
        Game_map (Game_Map): The current game map.
    """
    if len(Game_map.Enemy_Order) == 0:
        Game_map.Enemy_Order = copy.copy(Game_map.Enemy_Order_Copy)
        print("All enemies defeated, Resetting enemy list")
    if len(Game_map.Spawner_Order) == 0:
        Game_map.Spawner_Order = Game_map.Create_Spawner_Order()


def Create_Enemy(Game_map: Game_Map, enemy):
    """
    Place an enemy on the map at a spawner location.

    Parameters:
        Game_map (Game_Map): The current game map.
        enemy: The enemy instance to place.

    Returns:
        list: The updated map.
    """
    enemy_location_index = Game_map.Spawner_Order[0]
    Game_map.Spawner_Order.pop(0)
    enemy.row = Game_map.list_of_spawner_rows[enemy_location_index]
    enemy.column = Game_map.list_of_spawner_columns[enemy_location_index]
    while Game_map.map_2d[enemy.row][enemy.column] != "spawner":
        enemy_location_index = random.randint(0, Game_map.num_spawners - 1)
        enemy.row = Game_map.list_of_spawner_rows[enemy_location_index]
        enemy.column = Game_map.list_of_spawner_columns[enemy_location_index]
    Game_map.map_2d[enemy.row][enemy.column] = enemy
    G.List_Of_Enemies.append(enemy)
    enemy.OnSpawner = True
    enemy_health_increase_rate = 0.01
    r = G.num_of_rounds // 100
    enemy.health = round(enemy.initial_health * (1.2) ** (r))
    return Game_map


def Reset_Game_Settings():
    """
    Reset the game settings to their initial values.
    """
    G.num_of_rounds = 0
    G.List_Of_Towers = []
    G.List_Of_Enemies = []
    G.Player_Money = G.Perm_Player_Money
    G.enemies_killed = 0
    G.Enemy_Money = G.Perm_Enemy_Money
    G.Player_HP = G.Perm_Player_HP


def Create_Random_Tower_Algorithm(name):
    """
    Create a random Tower_Algorithm with random strategy attributes.

    Parameters:
        name: The name for the algorithm.

    Returns:
        Tower_Algorithm: The randomly generated tower algorithm.
    """
    Location_Strategy = random.choice(["Spread", "Base", "Spawner", "Tiles"])
    Money_Strategy = float(random.randint(1, 100)) / 100
    Tower_Strategy = random.sample(copy.deepcopy(cl.towers_list), random.randint(1, len(cl.towers_list)))
    Upgrade_Strategy = random.randint(0, 2)
    strategies = ["first", "last", "weakest", "strongest"]
    Tower_Attack_Strategy = random.sample(strategies, random.randint(1, len(strategies)))
    Name = name
    random_algorithm = Tower_Algorithm(
        Location_Strategy=Location_Strategy,
        Money_Strategy=Money_Strategy,
        Tower_Strategy=Tower_Strategy,
        Upgrade_Strategy=Upgrade_Strategy,
        Tower_Attack_Strategy=Tower_Attack_Strategy,
        Name=Name
    )
    return random_algorithm

def Random_Enemy_Generator_Algorithm():
    """
    Generate a predetermined list of enemy names for simulation consistency.

    Returns:
        list: A list of enemy names.
    """
    Predetermined_List_Of_Enemies = [] #in order to truly check the effectiveness of each algorithm we must make sure that every time we run the algorithms we use the same map and enemies. Thats why at the start of every "simulation" we will make a predetermined random list of enemies
    Enemy_Options = cl.List_Of_Enemies_Instances
    for rounds in range(0,1000):
        enemy_instance = Enemy_Options[random.randint(0, len(Enemy_Options) - 1)]
        enemy_name = enemy_instance.name
        Predetermined_List_Of_Enemies.append(enemy_name)
    return Predetermined_List_Of_Enemies

def modify_random_attribute(algorithm: Tower_Algorithm):
    """
    Modify one random attribute of a tower algorithm.

    Parameters:
        algorithm (Tower_Algorithm): The algorithm to modify.
    """
    attributes = ['Location_Strategy', 'Money_Strategy', 'Tower_Strategy', 'Upgrade_Strategy', 'Tower_Attack_Strategy']
    chosen_attribute = random.choice(attributes)
    if chosen_attribute == 'Location_Strategy':
        strategies = ["Spread", "Base", "Spawner", "Tiles"]
        available_strategies = list(set(strategies) - {algorithm.Location_Strategy})
        algorithm.Location_Strategy = random.choice(available_strategies)
    elif chosen_attribute == 'Money_Strategy':
        money_change = float(random.randint(-10, 10) / 100)
        new_money_strategy = algorithm.Money_Strategy + money_change
        new_money_strategy = max(0.01, new_money_strategy)
        new_money_strategy = min(1, new_money_strategy)
        algorithm.Money_Strategy = new_money_strategy
    elif chosen_attribute == 'Upgrade_Strategy':
        new_upgrade_strategy = algorithm.Upgrade_Strategy
        while new_upgrade_strategy == algorithm.Upgrade_Strategy:
            new_upgrade_strategy = random.choice([0, 1, 2])
        algorithm.Upgrade_Strategy = new_upgrade_strategy
    elif chosen_attribute == 'Tower_Strategy':
        max_towers_list = 100
        tower_types = copy.deepcopy(cl.towers_list)
        action = random.choice(['add', 'remove'])
        if (action == 'add' and len(algorithm.Tower_Strategy) < max_towers_list) or (
                action == 'remove' and len(algorithm.Tower_Strategy) <= 1):
            available_towers = tower_types
            algorithm.Tower_Strategy.append(random.choice(available_towers))
        else:
            algorithm.Tower_Strategy.remove(random.choice(algorithm.Tower_Strategy))
    elif chosen_attribute == 'Tower_Attack_Strategy':
        strategies = ["first", "last", "strongest", "weakest"]
        action = random.choice(['add', 'remove'])
        max_strategies_list = 100
        if (action == 'add' and len(algorithm.Tower_Attack_Strategy) < max_strategies_list) or (
                action == 'remove' and len(algorithm.Tower_Attack_Strategy) <= 1):
            available_strategies = strategies
            algorithm.Tower_Attack_Strategy.append(random.choice(available_strategies))
        else:
            algorithm.Tower_Attack_Strategy.remove(random.choice(algorithm.Tower_Attack_Strategy))


def serialize_algorithm(algorithm):
    """
    Convert an algorithm to a JSON-serializable dictionary.

    Parameters:
        algorithm: The algorithm to serialize.

    Returns:
        dict: The serialized algorithm.
    """
    algorithm_dict = algorithm.__dict__.copy()
    for key, value in algorithm_dict.items():
        if isinstance(value, list):
            algorithm_dict[key] = [v.__class__.__name__ if not isinstance(v, str) else v for v in value]
    return algorithm_dict


def MapSettingsGenerator(simulations_file):
    """
    Generator to yield map settings from a simulations file containing all map settings.

    Parameters:
        simulations_file (str): The file containing all simulation data.

    Yields:
        list: Map attributes for each simulation.
    """
    with open(simulations_file, 'r') as f:
        simulations = json.load(f)
    for simulation in range(0, len(simulations[0])):
        map_gen = copy.deepcopy(simulations[0][simulation][0])
        map_gen_attributes = list(map_gen.values())
        yield map_gen_attributes



def Set_Game_Settings(Player_money, Player_health, Enemy_Money=10):
    """
    Set permanent game settings.

    Parameters:
        Player_money (int): The starting money for the player.
        Player_health (int): The starting health for the player.
        Enemy_Money (int): The starting money for the enemy (default 10).
    """
    G.Perm_Player_Money = Player_money
    G.Perm_Player_HP = Player_health
    G.Perm_Enemy_Money = Enemy_Money




def Run_Basic_Strategies(algorithms): #to run the most basic strategy in case needed
    """
        Run a simulation for the basic strategies from a list of Tower_Algorithm

        For each algorithm, it loads simulation settings from a JSON file, resets game variables,
        runs multiple games, and writes average game statistics (for example, average rounds survived and enemies killed)
        to a results file.
        """

    for algorithm in algorithms:
        Map_Settings_Generator = MapSettingsGenerator("simulations.json")
        Game_map = Game_Map()
        Actual_Game = Game(Game_map, algorithm, Enemy_Algorithm_function)
        game_number = 0 #an index used to choose which simulation from the list of simulations
        for game in range(0, 100):
            total_enemies_killed = 0
            total_rounds_survived = 0
            total_time_survived = 0
            for avg in range(0, 5):
                # Reset Variables
                Reset_Game_Settings()

                map_gen_attributes = next(Map_Settings_Generator)
                list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Enemy_Options, Enemy_Options_Copy, Spawner_Order  = map_gen_attributes

                Game_map.map_2d = game_map
                Game_map.Enemy_Order = Enemy_Options
                Game_map.Enemy_Order_Copy = Enemy_Options_Copy
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

def Average_Results(algorithm : Tower_Algorithm, game_map: Game_Map, iterations=100):
    """
       Run multiple simulations using a given algorithm and return average results.
       This function is used to get the average results of the best Tower_Aglorithm that one of the optimization algorithms found.

       Parameters:
           algorithm (Tower_Algorithm): The algorithm to evaluate.
           game_map (Game_Map): The base game map.
           iterations (int): Number of simulations to run.

       Returns:
           tuple: Average rounds survived and average enemies killed over the iterations.
       """
    total_enemies_killed = 0
    total_rounds_survived = 0
    all_rounds_survived = []
    for i in range(iterations):
        Reset_Game_Settings()
        game = Game(copy.deepcopy(game_map),algorithm,Enemy_Algorithm_function)
        game.Run_Game()
        total_rounds_survived += G.num_of_rounds
        total_enemies_killed += G.enemies_killed
        all_rounds_survived.append(G.num_of_rounds)

    return (float(total_rounds_survived/iterations), float(total_enemies_killed/iterations))

def Run_Algorithms(simulations = 5, health_categories = 11, starting_player_money = 100):
    """
        Runs all 3 optimization algorithms for a number of simulations with different starting player health and money

        For each simulation, a different map is chosen and each algorithm process runs on the same map for different starting healths.
        The function writes the results (including average performance and best performance) to JSON files and prints the best algorithm configuration.

        Parameters:
            simulations (int): the amount of different maps/simulations. Default set to 5.
            health_categories (int): the amount of different starting health for each simulation. Default set to 11 (player starting health: 1, 10, 20... 100)
            starting_player_money (int): the amount of money the player starts with each game. Default set to 100.
        """
    saving_style = "a"
    Map_Settings_Generator = MapSettingsGenerator("simulations.json")
    All_simulation_game_attributes = []
    for sim in range(simulations):  # The number of games/simulations
        All_simulation_game_attributes.append(next(Map_Settings_Generator))

    for health_category in range(0, health_categories):
        Set_Game_Settings(starting_player_money,
                          max(1,10 * health_category))  # this way we can run all the different maps on different game settings
        for game_number in range(0, simulations):
            simulation_game_attibutes = copy.copy(All_simulation_game_attributes[game_number])

            simulation_game_map = Game_Map()
            Reset_Game_Settings()
            list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Enemy_Options, Enemy_Options_Copy, Spawner_Order = simulation_game_attibutes

            simulation_game_map.map_2d = game_map
            simulation_game_map.Enemy_Order = Enemy_Options
            simulation_game_map.Enemy_Order_Copy = Enemy_Options_Copy
            G.Rows = len(simulation_game_map.map_2d)
            G.Columns = len(simulation_game_map.map_2d[0])
            simulation_game_map.list_of_spawner_rows = list_of_spawner_rows
            simulation_game_map.list_of_spawner_columns = list_of_spawner_columns
            simulation_game_map.num_spawners = num_spawners
            simulation_game_map.Spawner_Order = Spawner_Order


            Reset_Game_Settings()
            ga = Genetic_Tower_Algorithm(
                population_size=10,
                generations=10,
                mutation_rate=0.05,
                game_map=copy.deepcopy(simulation_game_map),
                enemy_algorithm=Enemy_Algorithm_function
            )

            best_algorithm, total_average_performance, best_performance = ga.run()
            print("Best algorithm found:", best_algorithm.__dict__)
            print("total average performance:", total_average_performance)
            with open(f"GA_results{game_number+1}.json", saving_style) as f:
                results = Average_Results(best_algorithm,copy.deepcopy(simulation_game_map))
                json.dump({f"game_num:{game_number+1},health:{health_category+1}: best_algorithm: ": serialize_algorithm(best_algorithm),
                "average_performance": results, "total_average_performance": total_average_performance, "best_performance: " : best_performance}, f)
                f.write("\n")

            Reset_Game_Settings()
            simulated_annealing = Simulated_Annealing_Algorithm(
                game_map_template=copy.deepcopy(simulation_game_map),
                enemy_algorithm=Enemy_Algorithm_function,
                initial_temperature=1,
                cooling_rate=0.965,
                iterations=100
            )
            best_algorithm, total_average_performance, best_performance = simulated_annealing.run()
            print("Best algorithm found:", best_algorithm.__dict__)
            print("total average performance:", total_average_performance)

            with open(f"SA_results{game_number+1}.json", saving_style) as f:
                results = Average_Results(best_algorithm,copy.deepcopy(simulation_game_map))
                json.dump(
                    {f"game_num:{game_number+1},health:{health_category+1}: best_algorithm: ": serialize_algorithm(best_algorithm), "average_performance": results,
                     "total_average_performance": total_average_performance, "best_performance: " : best_performance},
                    f)
                f.write("\n")

            Reset_Game_Settings()
            local_search = Local_Search_Algorithm(
                game_map_template=copy.deepcopy(simulation_game_map),
                enemy_algorithm=Enemy_Algorithm_function,
                iterations=100
            )

            best_algorithm, total_average_performance, best_performance = local_search.run()
            print("Best algorithm found:", best_algorithm.__dict__)
            print("total average performance:", total_average_performance)
            with open(f"LS_results{game_number+1}.json", saving_style) as f:
                results = Average_Results(best_algorithm,copy.deepcopy(simulation_game_map))
                json.dump(
                    {f"game_num:{game_number+1},health:{health_category+1}: best_algorithm: ": serialize_algorithm(best_algorithm), "average_performance": results, "total_average_performance": total_average_performance, "best_performance: " : best_performance},
                    f)
                f.write("\n")

def Run_RLA(simulations = 5, health_categories = 11, starting_player_money = 100, Rl_agent_epsilon = 0.1):
    """
        Run the RL Agent simulation.

        Loads or initializes a DQL agent, sets up game parameters, trains the agent over a number of episodes,
        saves the performance results and saves the trained model.

        Parameters:
            simulations (int): the amount of different maps/simulations. Default set to 5.
            health_categories (int): the amount of different starting health for each simulation. Default set to 11 (player starting health: 1, 10, 20... 100)
            starting_player_money (int): the amount of money the player starts with each game. Default set to 100.
            Rl_agent_epsilon (int): the starting epsilon of the agent. Default set to 0.1 (in order to make the agent start from exploitation process).
        """
    All_simulation_game_attributes = []
    Map_Settings_Generator = MapSettingsGenerator("simulations.json")
    for sim in range(simulations):
        All_simulation_game_attributes.append(next(Map_Settings_Generator))

    for health_category in range(0, health_categories):
        for game_number in range(0, simulations):
            Game_map = Game_Map()
            map_gen_attributes = copy.copy(All_simulation_game_attributes[game_number])
            list_of_spawner_rows, list_of_spawner_columns, num_spawners, game_map, Enemy_Options, Enemy_Options_Copy, Spawner_Order = map_gen_attributes

            Game_map.map_2d = game_map
            Game_map.Enemy_Order = Enemy_Options
            Game_map.Enemy_Order_Copy = Enemy_Options_Copy
            G.Rows = len(Game_map.map_2d)
            G.Columns = len(Game_map.map_2d[0])
            Game_map.list_of_spawner_rows = list_of_spawner_rows
            Game_map.list_of_spawner_columns = list_of_spawner_columns
            Game_map.num_spawners = num_spawners
            Game_map.Spawner_Order = Spawner_Order

            Max_map_size = G.Max_Map_Size
            Max_Towers = G.Max_Towers
            Max_Enemies = G.Max_Enemies

            Set_Game_Settings(starting_player_money, max(1,10*health_category))
            Reset_Game_Settings()


            Towers_state_attributes = 5 #the number of attributes of the tower we represent in the state (type, row, column, level/how many upgrades and attack type)
            Enemies_state_attributes = 4 #the number of attributes of the enemy we represent in the state (type, row, column, health)

            state_size = Max_map_size + (Max_Towers*Towers_state_attributes) + (Max_Enemies*Enemies_state_attributes) + len([G.Player_HP,G.Player_Money]) #the maximum size of the state

            agent = DQLAgent(state_size)
            if os.path.exists(path="Main_RLA_DQL_model.pth"):
                agent.load("Main_RLA_DQL_model.pth","Main_RLA_DQL_memory.pkl")
            agent.epsilon = Rl_agent_epsilon
            trained_agent, best_performance, average_performance = run_agent(200, copy.deepcopy(Game_map), agent)
            with open(f"RL_results{game_number+1}.json", 'a') as f:
                json.dump(
                    {f"game_num:{game_number+1},health:{health_category+1}: best_performance: ": best_performance, "average_performance: ": average_performance},f)
                f.write("\n")
                print({f"game_num:{game_number+1},health:{health_category+1}: best_performance: ": best_performance})

            # Saving the trained model
            trained_agent.save("Main_RLA_DQL_model.pth","Main_RLA_DQL_memory.pkl")


Upgrade_Algorithm_instance = Upgrade_Algorithm()
All_Money_Algorithm_instance = All_Money_Algorithm()
Spread_Algorithm_instance = Spread_Algorithm()
algorithms = [All_Money_Algorithm_instance, Spread_Algorithm_instance, Upgrade_Algorithm_instance]

if __name__ == "__main__":
    Which_Simulation = input("write what simulation you want to run ").lower()
    if (Which_Simulation == "strategies"):
        Run_Basic_Strategies(algorithms)
    elif (Which_Simulation == "algorithms"):
       Run_Algorithms()
    elif (Which_Simulation == "rla"):
        Run_RLA()
    elif ("reset"):
        Algorithms = ["simulated_annealing_results", "genetic_algorithm_results", "local_search_results","simulated_annealing_algorithm_all_results", "genetic_algorithm_all_results","local_search_algorithm_all_results","rl_algorithm_results"]
        for algorithm in Algorithms:
            with open(f"D:/Alpha-project/{algorithm}.json", 'w') as f:
                f.write("")
                f.close()
    print("THE CODE RAN SUCCESFULLY")