#import packages

import simpy
import numpy as np

#set random seed
np.random.seed(0)

class invSim:
    def __init__(self, env, ssl, invMax):
        self.env = env
        self.ssl = ssl        
        self.invMax = invMax
        self.inventory = invMax
        self.open_order = 0  
        self.time_history = [0]
        self.inventory_history = [invMax]
        self.order_history = [0]
        self.ssl_history = [self.ssl]
        
        #ssl = safety stock level
        #invMax = Max inventory policy
        #inventory = inventory on hand. initial value is invMax
        #open_order = open orders to supplier. initial value is zero. only gets triggered when inventory drops below safety stock
        #history variables are lists to record values at each env.now
        
        
        
        print(f'{self.inventory} at time {env.now: .2f}')
        self.env.process(self.customer_event(self.env))
        
    def customer_event(self, env):
        while True:   
            #set customer interarrival. 5 customers per day
            self.interarrival = np.random.exponential(1./5.)            
            yield self.env.timeout(self.interarrival)  
            #set demand per customer, 1-5 units per customer ordered.
            self.demand = np.random.randint(1,5)
            
            if self.demand <= self.inventory:
                self.inventory -= self.demand                
                print(f'{self.inventory} at time {env.now: .2f}') 
            else:
                self.inventory = 0 
                print(f'{self.inventory} at time {env.now: .2f}')
            self.time_history.append(self.env.now)
            self.inventory_history.append(self.inventory)
            self.ssl_history.append(self.ssl)
                
            if self.inventory < self.ssl and self.open_order == 0:
                self.env.process(self.handle_order(self.env))
            else:
                self.order_history.append(self.open_order)
                
                
                
    def handle_order(self, env):
                self.open_order += self.invMax - self.inventory
                self.order_history.append(self.open_order)
                print(f'{self.open_order} placed at time {env.now}')
                yield self.env.timeout(2)
                print(f'{self.open_order} received at time {env.now}')
                self.inventory += self.open_order                
                self.open_order = 0                
   
import matplotlib.pyplot as plt

   
def run(ssl:float, invMax:float):
    env = simpy.Environment()
    inv = invSim(env, ssl, invMax)
    inv.env.run(30)
    #calculate % of time product was backordered
    x = np.array(inv.inventory_history)
    print(f'{x[x==0].size / x.size: .1%}')

    plt.figure()
    plt.step(inv.time_history, inv.inventory_history, where='post')
    plt.plot(inv.time_history, inv.order_history )
    plt.plot(inv.time_history, inv.ssl_history)
    plt.xlabel('Time')
    plt.ylabel('Inventory Level')

if __name__ == '__main__':
    (run(50,80))
