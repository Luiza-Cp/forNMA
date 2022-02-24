import pandas as pd
import matplotlib.pyplot as plt

NAME ='/media/luiza/DATA/Doutorado/53BP1/git.csv'

df = pd.read_csv(NAME)

df['Date'] = pd.to_datetime(df['Date'].values)
df = df.sort_values(by='Date')

df['LinesAddedCumulative'] = df['LinesAdded'].cumsum()
df['LinesDeletedCumulativeAbs'] = df['LinesDeleted'].cumsum().abs()
plt.rcParams['axes.facecolor'] = 'white'
plt.plot(df['Date'], df['LinesAddedCumulative'], label='Added')
plt.plot(df['Date'], df['LinesDeletedCumulativeAbs'], label='Deleted')
plt.legend()

plt.show()
