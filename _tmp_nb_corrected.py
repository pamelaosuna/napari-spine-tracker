import glob
import pandas as pd
import numpy as np

csv_dir = '/Users/pamelaosuna/Downloads/eval_ttrack/'

files = glob.glob(csv_dir + '*.csv')

n_ids = 0

for f in files:
    df = pd.read_csv(f)
    ids = df['id'].unique()
    n_ids += len(ids)

print(n_ids)