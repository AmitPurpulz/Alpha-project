import copy
import random
import sys
import time
import Game_Settings as G
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
        Distance_From_Base_Vertical = self.row - G.Rows // 2
        while True:
            Distance_From_Base_Vertical = self.row - G.Rows // 2
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
        #this is a temporary fix to the problem where the base gets deleted by a enemy who is in the same location as the base but doesnt get erased for some reason
        if (self.row == G.Rows//2 and self.column == G.Columns-1):
            print("THIS IS ON BASE")
            map_2d = self.Destroy_Enemy(map_2d)
            map_2d[self.row][self.column] = "base"
            return map_2d
        #end of the temporary fix
        if G.num_of_rounds % self.speed*4 == 0:
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
        elif self.row == G.Rows//2 and self.column == G.Columns-1:
            map_2d[self.row][self.column] = "base"
        else:
            map_2d[self.row][self.column] = "road"
        G.List_Of_Enemies.pop(G.List_Of_Enemies.index(self))
        if (self.health > 0):
            G.Player_HP = G.Player_HP - self.base_damage
        else:
            G.enemies_killed = G.enemies_killed+1
        return map_2d

class Tower:
    def __init__(self, damage, firerate, attack_range, attack_type, price, row, column):
        self.damage = damage
        self.firerate = firerate
        self.attack_range = attack_range
        self.attack_type = attack_type
        self.price = price
        self.upgrade_1 = False
        self.upgrade_2 = False
        self.row = row
        self.column = column
        self.upgrade_1_cost = self.price*0.5
        self.upgrade_2_cost = self.price*1.5
    def Place_Tower(self, tower, row, column, map_2d):
        game_map = map_2d
        game_map[row][column] = tower
        return game_map

    def Attack_Enemy(self, enemy: Enemy, map_2d):
        game_map = map_2d
        enemy.health = enemy.health - self.damage
        if enemy.health <= 0:
            game_map = enemy.Destroy_Enemy(map_2d)
            G.Player_Money = G.Player_Money + enemy.money_drop
        return game_map

    def Check_Attack(self, map_2d):
        game_map = map_2d
        if G.num_of_rounds % (self.firerate*4) == 0:
            if (self.attack_type == "first"):
                for column in range(min(self.column + self.attack_range, G.Columns - 1),max(self.column - self.attack_range, 0), -1):
                    for row in range(min(self.row + self.attack_range, G.Rows - 1), max(self.row - self.attack_range, 0),-1):
                        if isinstance(map_2d[row][column], Enemy) and map_2d[row][column] in G.List_Of_Enemies:
                            game_map = self.Attack_Enemy(map_2d[row][column], map_2d)
                            return game_map
            elif (self.attack_type == "last"):
                for column in range(max(self.column - self.attack_range, 0),min(self.column + self.attack_range, G.Columns - 1)):
                    for row in range(max(self.row - self.attack_range, 0),min(self.row + self.attack_range, G.Rows - 1)):
                        if isinstance(map_2d[row][column], Enemy) and map_2d[row][column] in G.List_Of_Enemies:
                            game_map = self.Attack_Enemy(map_2d[row][column], map_2d)
                            return game_map
            else:
                Enemies_In_Range = []
                for column in range(min(self.column + self.attack_range, G.Columns - 1),max(self.column - self.attack_range, 0), -1):
                    for row in range(min(self.row + self.attack_range, G.Rows - 1), max(self.row - self.attack_range, 0),-1):
                        if isinstance(map_2d[row][column], Enemy) and map_2d[row][column] in G.List_Of_Enemies:
                            Enemies_In_Range.append(map_2d[row][column])
                if (len(Enemies_In_Range) > 0):
                    strongest_enemy = 0
                    strongest_enemy_health = 0
                    weakest_enemy = 0
                    weakest_enemy_health = sys.maxsize
                    for enemy in Enemies_In_Range:
                        if enemy.health > strongest_enemy_health:
                            strongest_enemy = enemy
                            strongest_enemy_health = enemy.health
                        if enemy.health < weakest_enemy_health:
                            weakest_enemy = enemy
                            weakest_enemy_health = enemy.health
                    if (self.attack_type == "strongest"):
                        game_map = self.Attack_Enemy(strongest_enemy, game_map)
                    elif (self.attack_type == "weakest"):
                        game_map = self.Attack_Enemy(weakest_enemy, game_map)
        return game_map

    def Upgrade_Tower(self):
        if (not self.upgrade_1):
            self.upgrade_1 = True
            self.damage = self.damage*1.5
            G.Player_Money -= self.upgrade_1_cost
        elif (not self.upgrade_2):
            self.upgrade_2 = True
            self.damage = (self.damage/1.5)*2
            G.Player_Money -= self.upgrade_2_cost

class NormalTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=1, firerate=1, attack_range=2, attack_type="first" ,price=10, row=row, column=column)

class ShotgunTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=3, firerate=2, attack_range=1, attack_type="first", price=20, row=row, column=column)

class MachinegunTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=1, firerate=0.5, attack_range=2, attack_type="first", price=30, row=row, column=column)

class SniperTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=5, firerate=4, attack_range=4, attack_type="first", price=40, row=row, column=column)

class MinigunTower(Tower):
    def __init__(self, row, column):
        super().__init__(damage=1, firerate=0.25, attack_range=2, attack_type="first", price=50, row=row, column=column)

# Example towers
towers_list = [NormalTower(0, 0), ShotgunTower(0, 0), MachinegunTower(0, 0), SniperTower(0, 0), MinigunTower(0, 0)]
towers = {
    'normal_tower': NormalTower(0, 0),
    'shotgun_tower': ShotgunTower(0, 0),
    'machinegun_tower': MachinegunTower(0, 0),
    'sniper_tower': SniperTower(0, 0),
    'minigun_tower': MinigunTower(0, 0),
}


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

List_Of_Enemies_Options = [NormalEnemy(0,0), FastEnemy(0,0), StrongEnemy(0,0), BossEnemy(0,0)]
List_Of_Towers_Options = [NormalTower, ShotgunTower, MachinegunTower, SniperTower, MinigunTower]

if __name__ == "main":
    for tower_name, tower_instance in towers.items():
        print(f"{tower_name}:")
        for attribute, value in vars(tower_instance).items():
            print(f"    {attribute}: {value}")
        print()

    normal_enemy_instance = NormalEnemy(5, 5)
    print(vars(normal_enemy_instance))

    fast_enemy_instance = FastEnemy(5, 5)
    print(vars(fast_enemy_instance))

    strong_enemy_instance = StrongEnemy(5, 5)
    print(vars(strong_enemy_instance))

    boss_enemy_instance = BossEnemy(5, 5)
    print(vars(boss_enemy_instance))
