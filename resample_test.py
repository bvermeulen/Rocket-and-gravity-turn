from pprint import pprint
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

rocket_control_df = pd.read_excel('mintoc_gravity_turn.xlsx')
t = rocket_control_df['t']
u = rocket_control_df['u']

t_resampled = np.arange(0, 400+1, 1)
u_resampled = np.interp(t_resampled, t, u)
print(u_resampled)

fig, ax = plt.subplots()
ax.plot(t, u, 'o')
ax.plot(t_resampled, u_resampled, 'x')
plt.show()