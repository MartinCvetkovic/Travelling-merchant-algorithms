import math
import random

import pygame
import os
import config

from itertools import permutations
import heapq


class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, x, y, file_name, transparent_color=None, wid=config.SPRITE_SIZE, hei=config.SPRITE_SIZE):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (wid, hei))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Surface(BaseSprite):
    def __init__(self):
        super(Surface, self).__init__(0, 0, 'terrain.png', None, config.WIDTH, config.HEIGHT)


class Coin(BaseSprite):
    def __init__(self, x, y, ident):
        self.ident = ident
        super(Coin, self).__init__(x, y, 'coin.png', config.DARK_GREEN)

    def get_ident(self):
        return self.ident

    def position(self):
        return self.rect.x, self.rect.y

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class CollectedCoin(BaseSprite):
    def __init__(self, coin):
        self.ident = coin.ident
        super(CollectedCoin, self).__init__(coin.rect.x, coin.rect.y, 'collected_coin.png', config.DARK_GREEN)

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.RED)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Agent(BaseSprite):
    def __init__(self, x, y, file_name):
        super(Agent, self).__init__(x, y, file_name, config.DARK_GREEN)
        self.x = self.rect.x
        self.y = self.rect.y
        self.step = None
        self.travelling = False
        self.destinationX = 0
        self.destinationY = 0

    def set_destination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        self.step = [self.destinationX - self.x, self.destinationY - self.y]
        magnitude = math.sqrt(self.step[0] ** 2 + self.step[1] ** 2)
        self.step[0] /= magnitude
        self.step[1] /= magnitude
        self.step[0] *= config.TRAVEL_SPEED
        self.step[1] *= config.TRAVEL_SPEED
        self.travelling = True

    def move_one_step(self):
        if not self.travelling:
            return
        self.x += self.step[0]
        self.y += self.step[1]
        self.rect.x = self.x
        self.rect.y = self.y
        if abs(self.x - self.destinationX) < abs(self.step[0]) and abs(self.y - self.destinationY) < abs(self.step[1]):
            self.rect.x = self.destinationX
            self.rect.y = self.destinationY
            self.x = self.destinationX
            self.y = self.destinationY
            self.travelling = False

    def is_travelling(self):
        return self.travelling

    def place_to(self, position):
        self.x = self.destinationX = self.rect.x = position[0]
        self.y = self.destinationX = self.rect.y = position[1]

    # coin_distance - cost matrix
    # return value - list of coin identifiers (containing 0 as first and last element, as well)
    def get_agent_path(self, coin_distance):
        pass


class ExampleAgent(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [i for i in range(1, len(coin_distance))]
        random.shuffle(path)
        return [0] + path + [0]


class Aki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = []
        index = 0
        for counter in range(len(coin_distance)):
            path.append(index)
            row = coin_distance[index]
            next_value = None
            for next_index in range(len(row)):
                if next_index in path:
                    continue
                if next_value is None or row[next_index] < next_value:
                    next_value = row[next_index]
                    index = next_index
        return path + [0]


class Jocke(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        indexes = [i for i in range(1, len(coin_distance))]
        path = None
        min_price = None
        for permutation in permutations(indexes):
            price = 0
            prev_index = 0
            for index in permutation:
                price += coin_distance[prev_index][index]
                prev_index = index
            price += coin_distance[prev_index][0]
            if min_price is None or min_price > price:
                min_price = price
                path = list(permutation)
        return [0] + path + [0]


class Uki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        partial_paths = []
        heapq.heapify(partial_paths)
        best_path = {"cost": 0, "path": [0]}
        heapq.heappush(partial_paths, (best_path["cost"], -len(best_path["path"]), best_path["path"][-1], 0, best_path))
        cnt = 0
        while True:
            # partial_paths.sort(key=lambda path: (path["cost"], -len(path["path"]), path["path"][-1]))
            best_path = heapq.heappop(partial_paths)[4]
            if len(best_path["path"]) > 1 and best_path["path"][-1] == 0:
                return best_path["path"]
            has_new_node = False
            for index in range(len(coin_distance[best_path["path"][-1]])):
                if index in best_path["path"]:
                    continue
                has_new_node = True
                path = best_path["path"] + [index]
                cost = best_path["cost"] + coin_distance[best_path["path"][-1]][index]
                heapq.heappush(partial_paths, (cost, -len(path), path[-1], cnt, {
                    "path": path,
                    "cost": cost
                }))
            if has_new_node is False:
                path = best_path["path"] + [0]
                cost = best_path["cost"] + coin_distance[best_path["path"][-1]][0]
                heapq.heappush(partial_paths, (cost, -len(path), path[-1], cnt, {
                    "path": path,
                    "cost": cost
                }))
            cnt += 1


class Micko(Agent):
    identificators = []

    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    @staticmethod
    def merge_graph(parent, child, identificators):
        while identificators[parent] != parent:
            parent = identificators[parent]
        while identificators[child] != child:
            child = identificators[child]
        identificators[child] = parent

    @staticmethod
    def same_graph(i, j, identificators):
        while identificators[i] != i:
            i = identificators[i]
        while identificators[j] != j:
            j = identificators[j]
        return i == j

    @staticmethod
    def calculate_heuristic(coin_distance, indexes):
        heuristic = 0
        for cnt in range(len(indexes) - 1):
            min_cost = None
            parent = None
            child = None
            for i in range(len(coin_distance)):
                if i not in indexes:
                    continue
                for j in range(len(coin_distance[i])):
                    if j not in indexes or i == j:
                        continue
                    value = coin_distance[i][j]
                    if not Micko.same_graph(i, j, Micko.identificators.copy()) and (min_cost is None or min_cost > value):
                        min_cost = value
                        parent = i
                        child = j
            Micko.merge_graph(parent, child, Micko.identificators.copy())
            heuristic += min_cost
        return heuristic

    def get_agent_path(self, coin_distance):
        Micko.identificators = [i for i in range(len(coin_distance))]
        partial_paths = []
        heapq.heapify(partial_paths)
        best_path = {"cost": 0, "path": [0], "heuristic": Micko.calculate_heuristic(coin_distance, Micko.identificators.copy())}
        heapq.heappush(partial_paths, (best_path["cost"] + best_path["heuristic"], -len(best_path["path"]), best_path["path"][-1], 0, best_path))
        cnt = 0
        while True:
            # partial_paths.sort(key=lambda path: (path["cost"] + path["heuristic"], -len(path["path"]), path["path"][-1]))
            best_path = heapq.heappop(partial_paths)[4]
            if len(best_path["path"]) > 1 and best_path["path"][-1] == 0:
                return best_path["path"]
            heuristic = Micko.calculate_heuristic(coin_distance, [i for i in Micko.identificators if i not in best_path["path"]])
            has_new_node = False
            for index in range(len(coin_distance[best_path["path"][-1]])):
                if index in best_path["path"]:
                    continue
                has_new_node = True
                path = best_path["path"] + [index]
                cost = best_path["cost"] + coin_distance[best_path["path"][-1]][index]
                heapq.heappush(partial_paths, (cost + heuristic, -len(path), path[-1], cnt, {
                    "path": path,
                    "cost": cost,
                    "heuristic": heuristic
                }))
            if has_new_node is False:
                path = best_path["path"] + [0]
                cost = best_path["cost"] + coin_distance[best_path["path"][-1]][0]
                heapq.heappush(partial_paths, (cost + heuristic, -len(path), path[-1], cnt, {
                    "path": path,
                    "cost": cost,
                    "heuristic": 0
                }))
            cnt += 1
