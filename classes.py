import random
import time

import Game

class Enemy:
    def __init__(self, name, health, speed, money_drop, base_damage, row, column):
        self.name = name
        self.health = health
        self.initial_health = health  # Added initial_health attribute
        self.speed = speed
        self.money_drop = money_drop
        self.base_damage = base_damage
        self.row = row
        self.column = column
        self.OnSpawner = False

    def Check_Road(self, map_2d):
        row = int(self.row)
        column = int(self.column)
        if (isinstance(map_2d[row][column], Enemy) or map_2d[row][column] == "spawner"):
            pass
        Distance_From_Base_Vertical = self.row - Game.Rows // 2
        while True:
            Distance_From_Base_Vertical = self.row - Game.Rows // 2
            choices = ["right"]
            if Distance_From_Base_Vertical > 0:
                choices.append("up")
            elif Distance_From_Base_Vertical < 0:
                choices.append("down")
            direction = random.choice(choices)
            try:
                move_right = map_2d[row][column + 1]
                if (direction == "right" and isinstance(move_right, Enemy)):
                    if (len(choices) > 1):
                        direction = random.choice(choices)
                    else:
                        break
                if direction == "right" and ((move_right in ["road","spawner","base"])):
                    return row, column + 1
                if direction == "right" and (isinstance(move_right, Enemy)):
                    break
            except:
                pass
            try:
                move_up = map_2d[row - 1][column]
                if direction == "up" and (move_up in ["road","spawner","base"] ):
                    return row - 1, column
                if (direction == "up" and isinstance(move_up, Enemy)):
                    break
            except:
                pass
            try:
                move_down = map_2d[row + 1][column]
                if direction == "down" and (move_down in ["road","spawner","base"]):
                    return row + 1, column
                if (direction == "down" and isinstance(move_down, Enemy)):
                    break
            except:
                pass
        return row, column

    def Move(self, map_2d: list):
        if Game.num_of_rounds % self.speed*4 == 0:
            row = self.row
            column = self.column
            if self.OnSpawner:
                map_2d[row][column] = "spawner"
                self.OnSpawner = False
            else:
                map_2d[row][column] = "road"
            new_position = self.Check_Road(map_2d)
            self.row, self.column = new_position
            if map_2d[self.row][self.column] == "spawner":
                self.OnSpawner = True
            else:
                pass
            if map_2d[self.row][self.column] == "base":
                map_2d = self.Destroy_Enemy(map_2d)
                map_2d[self.row][self.column] = "base"
            else:
                map_2d[self.row][self.column] = self
        return map_2d

    def Destroy_Enemy(self, map_2d):
        if self.OnSpawner:
            map_2d[self.row][self.column] = "spawner"
        else:
            map_2d[self.row][self.column] = "road"
        Game.List_Of_Enemies.pop(Game.List_Of_Enemies.index(self))
        if (self.health > 0):
            Game.Player_HP = Game.Player_HP - self.base_damage
        else:
            Game.enemies_killed = Game.enemies_killed+1
        print("DEADHDISFSD")
        return map_2d

class Tower:
    def __init__(self, damage, firerate, attack_range, price, row, column):
        self.damage = damage
        self.firerate = firerate
        self.attack_range = attack_range
        self.price = price
        self.upgrade_cost_1 = price * 0.75
        self.upgrade_cost_2 = price * 1.5
        self.row = row
        self.column = column

    def Place_Tower(self, tower, row, column, map_2d):
        game_map = map_2d
        game_map[row][column] = tower
        return game_map

    def Attack_Enemy(self, enemy: Enemy, map_2d):
        game_map = map_2d
        enemy.health = enemy.health - self.damage
        if enemy.health <= 0:
            game_map = enemy.Destroy_Enemy(map_2d)
            Game.Player_Money = Game.Player_Money+enemy.money_drop
        return game_map

    def Check_Attack(self, map_2d):
        game_map = map_2d
        if Game.num_of_rounds % (self.firerate*4) == 0:
            for row in range(min(self.row + self.attack_range, Game.Rows-1), max(self.row - self.attack_range,0), -1):
                for column in range(min(self.column + self.attack_range, Game.Columns-1), max(self.column - self.attack_range, 0), -1):
                    if isinstance(map_2d[row][column], Enemy):
                        game_map = self.Attack_Enemy(map_2d[row][column], map_2d)
                        return game_map

        return game_map

class NormalTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=1, firerate=1, attack_range=2, price=10, row=row, column=column)

class ShotgunTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=3, firerate=2, attack_range=1, price=20, row=row, column=column)

class MachinegunTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=1, firerate=0.5, attack_range=2, price=30, row=row, column=column)

class SniperTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=5, firerate=4, attack_range=4, price=40, row=row, column=column)

class MinigunTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=1, firerate=0.25, attack_range=2, price=50, row=row, column=column)

# Example towers
towers_list = [NormalTower(0, 0), ShotgunTower(0, 0), MachinegunTower(0, 0), SniperTower(0, 0), MinigunTower(0, 0)]
towers = {
    'normal_tower': NormalTower(0, 0),
    'shotgun_tower': ShotgunTower(0, 0),
    'machinegun_tower': MachinegunTower(0, 0),
    'sniper_tower': SniperTower(0, 0),
    'minigun_tower': MinigunTower(0, 0),
}

for tower_name, tower_instance in towers.items():
    print(f"{tower_name}:")
    for attribute, value in vars(tower_instance).items():
        print(f"    {attribute}: {value}")
    print()

class NormalEnemy(Enemy):
    def __init__(self, row, column):
        super().__init__("normal_enemy", 3, 1, 1, 1, row, column)

class FastEnemy(Enemy):
    def __init__(self, row, column):
        super().__init__("fast_enemy", 2, 0.5, 2, 2, row, column)

class StrongEnemy(Enemy):
    def __init__(self, row, column):
        super().__init__("strong_enemy", 5, 1, 4, 3, row, column)

class BossEnemy(Enemy):
    def __init__(self, row, column):
        super().__init__("boss_enemy", 10, 2, 10, 5, row, column)

List_Of_Enemies_Options = [NormalEnemy, FastEnemy, StrongEnemy, BossEnemy]
List_Of_Towers_Options = [NormalTower, ShotgunTower, MachinegunTower, SniperTower, MinigunTower]
# Example usage
normal_enemy_instance = NormalEnemy(5, 5)
print(vars(normal_enemy_instance))

fast_enemy_instance = FastEnemy(5, 5)
print(vars(fast_enemy_instance))

strong_enemy_instance = StrongEnemy(5, 5)
print(vars(strong_enemy_instance))

boss_enemy_instance = BossEnemy(5, 5)
print(vars(boss_enemy_instance))
