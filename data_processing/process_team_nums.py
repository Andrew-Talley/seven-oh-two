import pandas as pd
import os
import sys
import re

team_num_re = r'[0-9]{4}'

def process_team_nums(year):
    teams = []
    team_nums = open("team_numbers/text/" + year + ".txt")
    for line in team_nums:
        re_match = re.match(r'([0-9]{4})\s(.+)', line)
        if re_match:
            if not "TEAM NUMBERS" in re_match.group(2):
                team_name = re_match.group(2)
                team_name = re.sub(r' [0-9]+/[0-9]+/[0-9]+', '', team_name)
                team_name = re.sub(r'(\t|\\t)', ' ', team_name)
                team_name = team_name.strip()
                teams.append(
                    {'Team #': re_match.group(1),
                    'Team Name': team_name}
                )
    team_nums.close()

    tpr = open("team_numbers/tpr/" + year + ".txt")
    # for line in tpr:
    #     re_match = re.match(r'([0-9]{1,3}) (.+?) \D.+', line)
    #     if re_match:
    #         print(re_match.group(1))
    #         print(re_match.group(2))
    tpr.close()

    new_table = pd.DataFrame(teams, columns=['Team #', 'Team Name']).set_index('Team #')
    print(new_table.head())

    new_table.to_csv(f'team_numbers/csv/{year}.csv')

    return new_table


if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_team_nums(sys.argv[1])
    else:
        for year in range(2013, 2021):
            process_team_nums(str(year))