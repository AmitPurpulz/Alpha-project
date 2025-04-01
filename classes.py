import random
import Game_Settings as G


class Enemy:
    """
    Base class representing an enemy in the game.
    """

    def __init__(self, name, health, speed, money_drop, base_damage, row, column, price):
        """
        Initialize an Enemy instance.

        Parameters:
            name (str): The enemy's name.
            health (int): The enemy's initial and current health.
            speed (float): The enemy's movement speed.
            money_drop (int): Money dropped when the enemy is defeated.
            base_damage (int): Damage dealt by the enemy to the player/base.
            row (int): Current row position.
            column (int): Current column position.
            price (int): The cost to spawn this enemy.
        """
        self.name = name
        self.health = health
        self.initial_health = health
        self.speed = speed
        self.money_drop = money_drop
        self.base_damage = base_damage
        self.row = row
        self.column = column
        self.OnSpawner = False
        self.price = price

    def Check_Road(self, map_2d):
        """
        Determine the next valid road tile for enemy movement.

        Parameters:
            map_2d (list): The 2D map layout.

        Returns:
            tuple: The (row, column) position of the next valid road tile.
        """
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
                if direction == "right" and ((move_right in ["road", "spawner", "base"])):
                    return row, column + 1
                if direction == "right" and (isinstance(move_right, Enemy)):
                    break
            except:
                pass
            try:
                move_up = map_2d[row - 1][column]
                if direction == "up" and (move_up in ["road", "spawner", "base"]):
                    return row - 1, column
                if (direction == "up" and isinstance(move_up, Enemy)):
                    break
            except:
                pass
            try:
                move_down = map_2d[row + 1][column]
                if direction == "down" and (move_down in ["road", "spawner", "base"]):
                    return row + 1, column
                if (direction == "down" and isinstance(move_down, Enemy)):
                    break
            except:
                pass
        return row, column

    def Move(self, map_2d: list):
        """
        Move the enemy on the map according to its speed and current position.

        Parameters:
            map_2d (list): The current game map.

        Returns:
            list: The updated game map.
        """
        if (self not in G.List_Of_Enemies):
            return map_2d
        if (self.row == G.Rows // 2 and self.column == G.Columns - 1):
            print("THIS IS ON BASE")
            map_2d = self.Destroy_Enemy(map_2d)
            map_2d[self.row][self.column] = "base"
            return map_2d
        if G.num_of_rounds % self.speed * 4 == 0:
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
            if map_2d[self.row][self.column] == "base":
                map_2d = self.Destroy_Enemy(map_2d)
                map_2d[self.row][self.column] = "base"
            else:
                map_2d[self.row][self.column] = self
        return map_2d

    def Destroy_Enemy(self, map_2d):
        """
        Remove the enemy from the map and update game map accordingly.

        Parameters:
            map_2d (list): The current game map.

        Returns:
            list: The updated game map.
        """
        if self.OnSpawner:
            map_2d[self.row][self.column] = "spawner"
        elif self.row == G.Rows // 2 and self.column == G.Columns - 1:
            map_2d[self.row][self.column] = "base"
        else:
            map_2d[self.row][self.column] = "road"
        G.List_Of_Enemies.pop(G.List_Of_Enemies.index(self))
        if (self.health > 0):
            G.Player_HP = G.Player_HP - self.base_damage
        else:
            G.enemies_killed = G.enemies_killed + 1
        return map_2d


class Tower:
    """
    Base class representing a tower that attacks enemies.
    """

    def __init__(self, name, damage, firerate, attack_range, attack_type, price, row, column):
        """
        Initialize a Tower instance.

        Parameters:
            name (str): The name of the tower.
            damage (float): The damage the tower inflicts.
            firerate (float): The firing rate of the tower.
            attack_range (int): The attack range of the tower.
            attack_type (str): The strategy for selecting which enemy to attack.
            price (float): The cost of the tower.
            row (int): The row position on the map.
            column (int): The column position on the map.
        """
        self.name = name
        self.damage = damage
        self.firerate = firerate
        self.attack_range = attack_range
        self.attack_type = attack_type
        self.price = price
        self.upgrade_1 = False
        self.upgrade_2 = False
        self.row = row
        self.column = column
        self.upgrade_1_cost = self.price * 0.5
        self.upgrade_2_cost = self.price

    def Attack_Enemy(self, enemy: Enemy, game_map):
        """
        Attack a specified enemy, reducing its health, and update the game map if the enemy is destroyed.

        Parameters:
            enemy (Enemy): The enemy to attack.
            game_map (list): The current game map.

        Returns:
            list: The updated game map.
        """
        enemy.health = enemy.health - self.damage
        if enemy.health <= 0:
            game_map = enemy.Destroy_Enemy(game_map)
            G.Player_Money = G.Player_Money + enemy.money_drop
        return game_map

    def Check_Attack(self, game_map):
        """
        Check for enemies within attack range and attack based on the tower's attack type.

        Parameters:
            game_map (list): The current game map.

        Returns:
            list: The updated game map.
        """
        if G.num_of_rounds % (self.firerate * 4) == 0:
            if (self.attack_type == "first"):
                for column in range(min(self.column + self.attack_range, G.Columns - 1),
                                    max(self.column - self.attack_range, 0), -1):
                    for row in range(min(self.row + self.attack_range, G.Rows - 1),
                                     max(self.row - self.attack_range, 0), -1):
                        if isinstance(game_map[row][column], Enemy) and game_map[row][column] in G.List_Of_Enemies:
                            game_map = self.Attack_Enemy(game_map[row][column], game_map)
                            return game_map
            elif (self.attack_type == "last"):
                for column in range(max(self.column - self.attack_range, 0),
                                    min(self.column + self.attack_range, G.Columns - 1)):
                    for row in range(max(self.row - self.attack_range, 0),
                                     min(self.row + self.attack_range, G.Rows - 1)):
                        if isinstance(game_map[row][column], Enemy) and game_map[row][column] in G.List_Of_Enemies:
                            game_map = self.Attack_Enemy(game_map[row][column], game_map)
                            return game_map
            else:
                Enemies_In_Range = []
                for column in range(min(self.column + self.attack_range, G.Columns - 1),
                                    max(self.column - self.attack_range, 0), -1):
                    for row in range(min(self.row + self.attack_range, G.Rows - 1),
                                     max(self.row - self.attack_range, 0), -1):
                        if isinstance(game_map[row][column], Enemy) and game_map[row][column] in G.List_Of_Enemies:
                            Enemies_In_Range.append(game_map[row][column])
                if (len(Enemies_In_Range) > 0):
                    strongest_enemy = 0
                    strongest_enemy_health = 0
                    weakest_enemy = 0
                    weakest_enemy_health = 10 ** 10
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
        """
        Upgrade the tower to improve its damage. If the first upgrade has not been applied, apply it;
        otherwise, if the second upgrade is available, apply that.
        """
        if (not self.upgrade_1):
            self.upgrade_1 = True
            self.damage = self.damage * 1.5
            G.Player_Money -= self.upgrade_1_cost
        elif (not self.upgrade_2):
            self.upgrade_2 = True
            self.damage = (self.damage / 1.5) * 2
            G.Player_Money -= self.upgrade_2_cost

    def Check_Surrounding_Enemies(self, game_map):
        """
        Count the number of enemy units within the tower's attack range.

        Parameters:
            game_map (list): The current game map.

        Returns:
            int: The number of enemies in range.
        """
        num_of_enemies = 0
        for column in range(max(self.column - self.attack_range, 0),
                            min(self.column + self.attack_range, G.Columns - 1)):
            for row in range(max(self.row - self.attack_range, 0), min(self.row + self.attack_range, G.Rows - 1)):
                if isinstance(game_map[row][column], Enemy):
                    num_of_enemies += 1
        return num_of_enemies


class NormalTower(Tower):
    """
    A tower with moderate damage, rate, and range.
    """

    def __init__(self, row, column):
        """
        Initialize a NormalTower at the specified position.
        """
        super().__init__(name="normal_tower", damage=3, firerate=1, attack_range=2, attack_type="first", price=10,
                         row=row, column=column)


class ShotgunTower(Tower):
    """
    A tower that deals high damage at close range.
    """

    def __init__(self, row, column):
        """
        Initialize a ShotgunTower at the specified position.
        """
        super().__init__(name="shotgun_tower", damage=6, firerate=2, attack_range=1, attack_type="first", price=20,
                         row=row, column=column)


class MachinegunTower(Tower):
    """
    A tower with rapid fire but lower damage.
    """

    def __init__(self, row, column):
        """
        Initialize a MachinegunTower at the specified position.
        """
        super().__init__(name="machinegun_tower", damage=1.5, firerate=0.5, attack_range=2, attack_type="first",
                         price=30, row=row, column=column)


class SniperTower(Tower):
    """
    A tower with high damage and long range but slower firing rate.
    """

    def __init__(self, row, column):
        """
        Initialize a SniperTower at the specified position.
        """
        super().__init__(name="sniper_tower", damage=8, firerate=4, attack_range=5, attack_type="first", price=40,
                         row=row, column=column)


class MinigunTower(Tower):
    """
    A tower with very fast firing rate and moderate damage.
    """

    def __init__(self, row, column):
        """
        Initialize a MinigunTower at the specified position.
        """
        super().__init__(name="minigun_tower", damage=1.5, firerate=0.25, attack_range=2, attack_type="first", price=50,
                         row=row, column=column)


towers_list = [NormalTower(0, 0), ShotgunTower(0, 0), MachinegunTower(0, 0), SniperTower(0, 0), MinigunTower(0, 0)]
towers = {
    'normal_tower': NormalTower(0, 0),
    'shotgun_tower': ShotgunTower(0, 0),
    'machinegun_tower': MachinegunTower(0, 0),
    'sniper_tower': SniperTower(0, 0),
    'minigun_tower': MinigunTower(0, 0),
}
towers_attack_types = ["first", "last", "strongest", "weakest"]


class NormalEnemy(Enemy):
    """
    An enemy with average health and damage.
    """

    def __init__(self, row, column):
        """
        Initialize a NormalEnemy at the specified position.
        """
        super().__init__("normal_enemy", 5, 1, 1, 1, row, column, price=5)


class FastEnemy(Enemy):
    """
    An enemy with lower health and faster speed.
    """

    def __init__(self, row, column):
        """
        Initialize a FastEnemy at the specified position.
        """
        super().__init__("fast_enemy", 3, 0.5, 2, 2, row, column, price=8)


class StrongEnemy(Enemy):
    """
    An enemy with higher health and damage.
    """

    def __init__(self, row, column):
        """
        Initialize a StrongEnemy at the specified position.
        """
        super().__init__("strong_enemy", 10, 1, 4, 3, row, column, price=12)


class BossEnemy(Enemy):
    """
    A powerful enemy with very high health and damage.
    """

    def __init__(self, row, column):
        """
        Initialize a BossEnemy at the specified position.
        """
        super().__init__("boss_enemy", 50, 2, 10, 10, row, column, price=50)


List_Of_Enemies_Instances = [NormalEnemy(0, 0), FastEnemy(0, 0), StrongEnemy(0, 0), BossEnemy(0, 0)]
List_Of_Enemies_Options = [NormalEnemy, FastEnemy, StrongEnemy, BossEnemy]
List_Of_Towers_Options = [NormalTower, ShotgunTower, MachinegunTower, SniperTower, MinigunTower]

if __name__ == "main":
    """
    If this module is run as the main program, print the attributes of each tower and enemy.
    """
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
