import os
import re
import pandas as pd

table = pd.DataFrame()

for dir, subdirs, files in os.walk('round_results'):
  print(dir)
  if len(subdirs) == 0:
    for filename in files:
      if re.match(r'.+\.csv', filename):
        new_table = pd.read_csv(f"{dir}/{filename}")
        table = table.append(new_table, sort=False)

table.to_csv('head-data.csv')