import pandas as pd

apiKey = 'YLOQ86WTNEW35QBI'

interval_var = '5min'
symbol = 'ETH'

path = 'https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol=' + symbol + '&market=USD&interval=' + interval_var + '&apikey=' + apiKey + '&datatype=csv&outputsize=full'

print(path)

df = pd.read_csv(path)
df = df[::-1].reset_index()
df = df.drop(['index'], axis=1)

print(df)
