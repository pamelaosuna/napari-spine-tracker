import os, glob
import pandas as pd

csv_dir = "/Users/pamelaosuna/Downloads/eval_ttrack/"
out_dir = "/Users/pamelaosuna/Downloads/eval_ttrack/separated/"
files = glob.glob(csv_dir + '*.csv')

for f in files:
    df = pd.read_csv(f)
    df_tp1 = df[df['filename'].str.contains('_tp1_')]
    df_tp2 = df[df['filename'].str.contains('_tp2_')]

    out_name_tp1 = os.path.basename(f).replace('_stack', '_tp1' + '_stack')
    out_name_tp2 = os.path.basename(f).replace('_stack', '_tp2' + '_stack')

    df_tp1.to_csv(out_dir + out_name_tp1, index=False)
    df_tp2.to_csv(out_dir + out_name_tp2, index=False)
                                               