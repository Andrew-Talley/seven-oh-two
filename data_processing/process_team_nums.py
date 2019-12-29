import pandas as pd
import os
import sys
import re

team_num_re = r'[0-9]{4}'

def process_team_nums(year):
    teams = []
    team_nums = open("team_numbers/text/" + year + ".txt")
    for line in team_nums:
        re_match = re.match(r'([0-9]{4}) (.+)', line)
        if re_match:
            teams.append(
                {'Team #': re_match.group(1),
                'Team Name': re.sub(r' [0-9]+/[0-9]+/[0-9]+', '', re_match.group(2))}
            )

    tpr = open("team_numbers/tpr/" + year + ".txt")
    for line in tpr:
        re_match = re.match(r'([0-9]{1,3}) (.+?) \D.+', line)
        if re_match:
            print(re_match.group(1))
            print(re_match.group(2))

    new_table = pd.DataFrame(teams, columns=['Team #', 'Team Name']).set_index('Team #')


if __name__ == "__main__":
    assert (len(sys.argv) > 1), "No year inputted"
    print (sys.argv)
    process_team_nums(sys.argv[1])