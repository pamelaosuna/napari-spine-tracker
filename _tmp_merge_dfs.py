import os
import pandas as pd

csv_dir_f1 = "/Users/pamelaosuna/Downloads/csvs/"
csv_dir_f2 = csv_dir_f1
# csv_dir_f2 = "/Users/pamelaosuna/Downloads/csvs/tp2-corrected_tp1-nextsession/"
out_dir = "/Users/pamelaosuna/Downloads/eval_ttrack/"

f1 = "aidv857_date220316_tp1_stack0_sub12_default_aug_False_epoch_19_theta_0.5_delta_0.5_Test.csv"
f2 = "aidv857_date220316_tp2_stack0_sub12_default_aug_False_epoch_19_theta_0.5_delta_0.5_Test.csv"
out_name = 'aidv857_date220316_stack0_sub12.csv'

df1 = pd.read_csv(csv_dir_f1 + f1)
df2 = pd.read_csv(csv_dir_f2 + f2)

df_merged = pd.concat([df1, df2], ignore_index=True)
if not os.path.exists(out_dir + out_name):
    df_merged.to_csv(out_dir + out_name, index=False)
else:
    print(f"File already exists")