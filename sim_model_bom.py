# import packages

import simpy
import numpy as np
import matplotlib.pyplot as plt
import copy
import warnings
import openpyxl

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import pandas as pd

# set random seed
np.random.seed(0)

# declare bill of material object for a bike

BOM = [{'id': 0, 'item': 'wheel', 'uom': 2, 'ssl': 50, 'maxInv': 120, 'lt': 2},
       {'id': 1, 'item': 'brake', 'uom': 2, 'ssl': 50, 'maxInv': 120, 'lt': 2},
       {'id': 2, 'item': 'frame', 'uom': 1, 'ssl': 50, 'maxInv': 100, 'lt': 4},
       {'id': 3, 'item': 'seat', 'uom': 1, 'ssl': 20, 'maxInv': 50, 'lt': 1},
       {'id': 4, 'item': 'chain', 'uom': 1, 'ssl': 30, 'maxInv': 70, 'lt': 2},
       {'id': 5, 'item': 'handlebar', 'uom': 1, 'ssl': 30, 'maxInv': 70, 'lt': 2}]

# Maximum INventory level and Safety Stock parameters

INV = []
SAFETY = []

# Open Orders object

OPEN_ORDER = [{'id': 0, 'open_order': 0},
              {'id': 1, 'open_order': 0},
              {'id': 2, 'open_order': 0},
              {'id': 3, 'open_order': 0},
              {'id': 4, 'open_order': 0},
              {'id': 5, 'open_order': 0}]

# Variables to Record historical data and for reporting and visualization

OBS_TIME = []
INV_LEVEL = []
BIKES = []


# create INV parameter for invSim class with initial inventory values and key metrics to be tracked - item_inventory, open orders, backorders and bike demand from customers.

for item in BOM:
    INV.append({'id': item['id'], 'uom': item['uom'], 'lt': item['lt'], 'ssl': item['ssl'], 'maxInv': item['maxInv'],
                'item_inventory': item['maxInv'], 'open_order': 0, 'backOrder': 0, 'bike_demand': 0})


class invSim:
    # create class with Inventory and Open Order Variables
    def __init__(self, env, invMax, OO):
        self.env = env
        self.OO = OO
        self.item_inventory = copy.deepcopy(invMax[:])
        self.bike_demand = 0

        self.inventory_history = [copy.deepcopy(invMax[:])]
        self.time_history = [0]
        self.bike_history = [self.bikeAssembly(invMax)]
        self.bike_demand_history = [0]

        env.process(self.customer_event(self.env))

    def customer_event(self, env):

        while True:
            interarrival = np.random.exponential(1./5.)
            yield env.timeout(interarrival)
            self.bike_demand = np.random.randint(1, 4)

            for index, item in enumerate(self.item_inventory):
                item['bike_demand'] = self.bike_demand
                if self.bike_demand*item['uom'] <= item['item_inventory']:
                    item['item_inventory'] -= self.bike_demand*item['uom']
                else:
                    item['backOrder'] = self.bike_demand * \
                        item['uom'] - item['item_inventory']

            self.history(env, self.item_inventory)
            for index, item in enumerate(self.item_inventory):
                if item['item_inventory'] < item['ssl'] and self.OO[index]['open_order'] == 0:
                    env.process(self.handle_order(self.env, index))

    def handle_order(self, env, i):
        # handles the proces of placing orders to suppliers once inventory drops below safety stock
        self.OO[i]['open_order'] += self.item_inventory[i]['maxInv'] - \
            self.item_inventory[i]['item_inventory']
        self.item_inventory[i]['open_order'] = self.OO[i]['open_order']
        yield env.timeout(self.item_inventory[i]['lt'])
        self.item_inventory[i]['item_inventory'] += self.OO[i]['open_order']
        self.item_inventory[i]['open_order'] = 0
        self.item_inventory[i]['backOrder'] = 0
        self.OO[i]['open_order'] = 0

    def bikeAssembly(self, item_bom):
        # calculates how many bikes can be built with available component inventory
        item_bom_decompose = []
        for item in item_bom:
            item_bom_decompose.append(item['item_inventory'] // item['uom'])
        return min(item_bom_decompose)

    def history(self, env, i):
        self.time_history.append(env.now)
        self.inventory_history.append(copy.deepcopy(i))
        self.bikeInventory = self.bikeAssembly(i)
        self.bike_history.append(self.bikeInventory)
        self.bike_demand_history.append(copy.deepcopy(self.bike_demand))

    def observe(self, env):
        while True:
            OBS_TIME.append(env.now)
            INV_LEVEL.append(copy.deepcopy(self.item_inventory))
            BIKES.append(copy.deepcopy(self.bikeAssembly(self.item_inventory)))
            yield env.timeout(0.1)


def run(invMax, OO):
    meta = []
    env = simpy.Environment()
    inv = invSim(env, invMax, OO)
    env.process(inv.observe(env))
    env.run(until=30)

    for index, item in enumerate(INV_LEVEL):
        for subitem in item:
            subitem['time'] = OBS_TIME[index]
            subitem['bike_inventory'] = BIKES[index]

    df = pd.DataFrame()

    for index, item in enumerate(INV_LEVEL):
        for j in range(6):
            df_inv = pd.DataFrame(item[j], index=[(index*6)+(j)])
            df = pd.concat([df, df_inv])

    writer = pd.ExcelWriter('output.xlsx')
    # write dataframe to excel
    df.to_excel(writer)
    # save the excel
    writer.save()
    print('DataFrame is written successfully to Excel File.')

    plt.figure()
    plt.step(inv.time_history, inv.bike_history, where='post')
    plt.xlabel('Time')
    plt.ylabel('Inventory Level')


if __name__ == '__main__':
    (run(INV, OPEN_ORDER))
