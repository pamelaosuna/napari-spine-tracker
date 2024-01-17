import numpy as np
import pandas as pd

if __name__ == '__main__':
    fp = "/Users/pamelaosuna/Documents/spines/data/bens_data/results/lr_0.001_warmup_None_momentum_0.6_L2_None_union/time_tracking/date040822_stack1_sub11_timetracked.csv"
    df = pd.read_csv(fp)

    # rename ids such that we use the smallest id possible
    # e.g. if we have ids 10, 45, 100, we want to rename them to 0, 1, 2
    curr_ids = df['id'].unique()
    new_ids = np.arange(len(curr_ids))
    id_map = dict(zip(curr_ids, new_ids))
    df['id'] = df['id'].map(id_map)

    df.to_csv(fp, index=False)