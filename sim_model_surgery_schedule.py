import numpy as np
import simpy
import random
import copy
import streamlit as st
import pandas as pd

np.random.seed(0)

entitlement_select = st.slider("Select Knees Entitlement", 1, 15, 1)

SURG_TIME = 0.0
CONS_INV = [{'surg_type': 'primary knee', 'entitlement': 0, 'onHand': 0, 'openOrder': 0, 'orderQty': 0},
            {'surg_type': 'primary hip', 'entitlement': 5, 'onHand': 6, 'openOrder': 0, 'orderQty': 0}]

CONS_INV[0]['entitlement'] = entitlement_select + 1
CONS_INV[0]['onHand'] = entitlement_select + 1

O_R = [{'surg_type': 'primary knee', 'orderDay': [], 'orderQty': [], 'receiptDay': [], 'receiptQty': []},
       {'surg_type': 'primary hip', 'orderDay': [], 'orderQty': [], 'receiptDay': [], 'receiptQty': []}]

WAREHOUSE = [{'surg_type': 'primary knee', 'entitlement': 30, 'onHand': 300, 'openOrder': 0},
             {'surg_type': 'primary hip', 'entitlement': 30, 'onHand': 300, 'openOrder': 0}]
SCHED = []

LT = [2, 3, 4, 5]
LT_PROB = [0.45, 0.3, 0.2, 0.05]

TIME_HIST = []
INV_HIST = []
LT_HIST = []
temp = []


surg_on_a_day = [np.random.randint(1, 6), np.random.randint(1, 4)]

surg_type_ = ['primary knee', 'primary hip']
surg_type_weights = [0.6, 0.4]


def generate_samples():
    surgery_type = random.choices(surg_type_, weights=surg_type_weights, k=1)
    return surgery_type[0]


pid = 0
wk = 0
day_of_week = 1
day = 7*wk + day_of_week

while wk < 4:
    # append surgeon A schedule on day
    if day_of_week == 1 or day_of_week == 2 or day_of_week == 5:
        for i in range(surg_on_a_day[0]):
            SCHED.append({'patient_id': pid, 'surgeon': 'A', 'surg_day': day,
                         'surg_type': generate_samples(), 'stockout_prob': 0.})
            pid += 1
        # append surgeon B schedule on day
    if day_of_week == 2 or day_of_week == 3:
        for i in range(surg_on_a_day[1]):
            SCHED.append({'patient_id': pid, 'surgeon': 'B', 'surg_day': day,
                         'surg_type': generate_samples(), 'stockout_prob': 0.})
            pid += 1

    day_of_week += 1
    day = 7*wk + day_of_week
    if day_of_week == 8:
        day_of_week = 1
        wk += 1
        day = 7*wk + day_of_week


class Surgery:
    def __init__(self, env, schedule, inv):
        self.env = env
        self.schedule = copy.deepcopy(SCHED)
        self.cons = copy.deepcopy(CONS_INV)
        self.order_receipts = copy.deepcopy(O_R)
        self.warehouse = copy.deepcopy(WAREHOUSE)
        self.surgery = env.event()
        env.process(self.sEvent(self.env, self.schedule))

    def sEvent(self, env, schedule):
        for index, item in enumerate(schedule):
            if index == 0:
                yield env.timeout(self.schedule[0]['surg_day'])

            if item['surg_day'] == schedule[index-1]['surg_day']:
                day_change = False
            else:
                day_change = True

            if day_change == True and index != 0:
                yield env.timeout(item['surg_day'] - schedule[index-1]['surg_day'])

            if item['surg_type'] == 'primary knee':
                c_index = 0
            else:
                c_index = 1

            if self.cons[c_index]['onHand'] > 0:
                self.surgery.succeed()
                self.cons[c_index]['onHand'] -= 1

            self.surgery = self.env.event()
            env.process(self.replenishOrder(self.env, c_index, index))
            TIME_HIST.append(env.now)
            INV_HIST.append(copy.deepcopy(self.cons[c_index]))

    def replenishOrder(self, env, c, i):
        if self.cons[c]['onHand'] < self.cons[c]['entitlement']:
            orderQuantity = max(
                self.cons[c]['entitlement'] - self.cons[c]['onHand'] - self.cons[c]['openOrder'], 0)
            self.cons[c]['orderQty'] = orderQuantity
            self.cons[c]['openOrder'] += orderQuantity
            self.order_receipts[c]['orderDay'].append(env.now)
            self.order_receipts[c]['orderQty'].append(orderQuantity)

            lead_time = self.getLT()
            yield env.timeout(lead_time)
            LT_HIST.append(lead_time)
            self.order_receipts[c]['receiptDay'].append(env.now)
            self.order_receipts[c]['receiptQty'].append(orderQuantity)
            self.cons[c]['onHand'] += orderQuantity
            self.cons[c]['openOrder'] -= orderQuantity

    def getLT(self):
        lead_time = random.choices(LT, weights=LT_PROB, k=1)
        return lead_time[0]


env = simpy.Environment()
s = Surgery(env, SCHED, CONS_INV)
env.run()
for index, item in enumerate(INV_HIST):
    item['time'] = TIME_HIST[index]

df_orderlog = pd.DataFrame()
df = pd.DataFrame(INV_HIST)
df_sched = pd.DataFrame(s.schedule)

for i in range(len(s.order_receipts)):
    mydict = s.order_receipts[i]
    df_temp = pd.DataFrame(dict(list(mydict.items())[1:]))
    df_temp['surg_type'] = mydict['surg_type']
    df_orderlog = pd.concat([df_orderlog, df_temp])

# Streamlit Portion


option = st.selectbox(
    'Select Surgery Type',
    ('primary knee', 'primary hip'))

x = (df[df.surg_type == option]['onHand'])

st.write("""#My App - Jamadu Ka Gulla""")
st.line_chart(x)
