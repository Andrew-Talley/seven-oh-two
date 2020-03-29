import numpy as np
import pandas as pd
import os
import re
import functools
import itertools
import json
import traceback
from collections import deque, defaultdict

from Tournament_Iterator import Tournament_Iterator
from parse_results_rows import parse_results_rows
from get_outstanding_students import get_outstanding_students
from get_tournament_info import get_tournament_info
from parse_date_line import parse_date_line

import numpy as np

def get_tournament_txt_file(year, level, location):
  return open(f"text_data/{year}/{level}/{location}.txt")

record_reg = r'(\d{1,2}) ?- (\d{1,2}) - ?(\d{1,2})'

def expand_team_data(data, final_len):
  factor = round(final_len / len(data))
  return [itertools.chain.from_iterable([item] * factor for item in data)]

def parse_record_row(line):
  sides = list()
  opponents = list()

  for _ in range(4):
    sides.append(line[0:1])
    opponents.append(line[5:9])

    line = line[10:]

  return (sides, opponents)


def duplicate(arr):
  return [item for item in arr for _ in [0, 1]]

school_record = r'Team\sSchool\sRecord'

def get_amta_reps(file_iterator):
  amta_reps = list()

  for rep in file_iterator:
    if re.match(school_record, rep) or re.match(r"\d+", rep):
      return amta_reps
    elif "AMTA" in rep:
      continue
    else:
      amta_reps.append(rep.rstrip("\n"))


def get_tab_notes(file_iterator):
  notes = list()

  for note in file_iterator:
    if str.startswith(note, 'AMTA') or re.match(school_record, note):
      file_iterator.prepend(note)
      return notes
    else:
      notes.append(note.rstrip("\n"))


def get_series_of_teams(file_iterator):
  teams = list()

  for team in file_iterator:
    team_num = re.match(r'\d{1,2}?\D{2}?\s?(\d{4}).+', team)
    if team_num == None:
      file_iterator.prepend(team)
      return teams
    else:
      teams.append(team_num.group(1))

  raise EOFError()

def get_spamta(file_iterator):
  spamta_winners = list()
  spamta_ranks = 0

  honorable_mentions = list()
  honorable_mention_ranks = 0

  for line in file_iterator:
    winner_match = re.search(r'(\d{2})\s(\d{4})', line)
    team_num = ranks = None
    if winner_match != None:
      team_num, ranks = winner_match.group(2), winner_match.group(1)
    else:
      old_winner_match = re.search(r'(\d{4}).+(\d{2})', line)
      if old_winner_match != None:
        team_num, ranks = old_winner_match.group(1), old_winner_match.group(2)

    if team_num != None:
      if "Honorable Mention" in line:
        honorable_mentions.append(team_num)
        honorable_mention_ranks = ranks
      else:
        spamta_winners.append(team_num)
        spamta_ranks = ranks
    else:
      file_iterator.prepend(line)
      return (spamta_winners, spamta_ranks), (honorable_mentions, honorable_mention_ranks)

def get_bid_tournament(file_iterator):
  next(file_iterator) # Ignore this line, it has no useful data
  description_line = next(file_iterator)
  match = re.match(r'(.+-.+, \d{4}), (.+)', description_line)

  if not match:
    return None, None, None
  start_date, end_date = parse_date_line(match.group(1))
  location = match.group(2)
  return start_date, end_date, location

def create_table(data_list, columns=None):
  assert(len(columns) == len(data_list))
  transformed_arr = [[el for el in zip(*team_data)] for team_data in zip(*data_list)]
  flattened_arr = itertools.chain.from_iterable(transformed_arr)

  table = pd.DataFrame(flattened_arr, columns=columns)
  return table

def tournament_text_to_results(year, level, location):
  print(f"{year}/{level}/{location}")

  team_nums = set()
  opponent_lists = list()
  side_lists = list()
  pd_lists = list()
  round_lists = list()

  teams_with_bids = list()
  teams_with_honorable_mentions = list()

  spamta_winners = list()
  spamta_ranks = 0
  spamta_honorables = list()
  spamta_honorable_ranks = 0

  award_data = None

  tournament_file = Tournament_Iterator(get_tournament_txt_file(year, level, location))
  tournament_info = get_tournament_info(tournament_file)
  tournament_info['level'] = level
  tournament_info['year'] = year

  def check_for_tab_note(line):
    if "coin flip" in line:
      tournament_info['tab_notes'].append(line.rstrip('\n'))
      return True

    return False
  tournament_file.add_handler(check_for_tab_note)

  for line in tournament_file:
    if str.startswith(line, "Tabulation"):
      tournament_info['tab_notes'].extend(get_tab_notes(tournament_file))  # First, get the tab notes
      tournament_info['amta_reps'] = get_amta_reps(tournament_file) # Then, amta reps
      teams_with_bids = get_series_of_teams(tournament_file) # Then parse final results
      next_line = next(tournament_file)
      if next_line.startswith("Honorable"):
        teams_with_honorable_mentions = get_series_of_teams(tournament_file)
      else:
        tournament_file.prepend(next_line)

    elif str.startswith(line, "Awarded to the team that"):
      result = get_spamta(tournament_file)
      (spamta_winners, spamta_ranks), (spamta_honorables, spamta_honorable_ranks) = result

    elif "bids to" in line.lower():
      tournament_file.prepend(line)
      tournament_info['bid_start_date'], tournament_info['bid_end_date'], tournament_info['bid_location'] = get_bid_tournament(tournament_file)

    elif "Witness" in line:
      tournament_file.prepend(line)
      award_data = get_outstanding_students(tournament_file, year)


    elif re.search(record_reg, line):
        tournament_file.prepend(line)
        opponents, sides, ballots, round_nums = parse_results_rows(tournament_file)
        for opponent in opponents:
          team_nums.add(opponent)

        opponent_lists.append(opponents)
        side_lists.append(sides)
        pd_lists.append(ballots)
        round_lists.append(round_nums)

  team_nums = sorted(list(team_nums))
  elements = [round_lists, opponent_lists, side_lists, pd_lists]
  table = create_table(elements, columns=['RoundNum', 'OppNum', 'Side', 'PD'])

  ballots_per_team = len(table) // len(team_nums)
  team_num_col = list(itertools.chain.from_iterable([num] * ballots_per_team for num in team_nums))
  table['TeamNum'] = team_num_col

  table['Ballot_Result'] = ['Win' if float(pd) > 0 else 'Tie' if float(pd) == 0 else 'Loss' for pd in table['PD']]

  def sum_results(value):
    data = [sum(pd == value for pd in table['Ballot_Result'][table['TeamNum'] == team_num]) for team_num in table['TeamNum']]
    return data

  table['TotalWins'] = sum_results('Win')
  table['TotalTies'] = sum_results('Tie')
  table['TotalLosses'] = sum_results('Loss')
  table['TotalBallots'] = table['TotalWins'] + (table['TotalTies'] * .5)

  opponents = [set(opp for opp in opponents) for opponents in opponent_lists]

  cs = [sum(table[table['OppNum'] == opp]['TotalBallots'].iloc[0] for opp in opp_list) for opp_list in opponents]
  cs_df = pd.DataFrame(cs, columns=['TotalCS'], index=team_nums)
  table = table.merge(cs_df, left_on='TeamNum', right_index=True)

  ocs = [sum(table[table['OppNum'] == opp]['TotalCS'].iloc[0] for opp in opp_list) for opp_list in opponents]
  ocs_df = pd.DataFrame(ocs, columns=['TotalOCS'], index=team_nums)
  table = table.merge(ocs_df, left_on='TeamNum', right_index=True)

  pd_total = [sum(table[table['TeamNum'] == team]['PD']) for team in team_nums]
  pd_df = pd.DataFrame(pd_total, columns=['TotalPD'], index=team_nums)
  table = table.merge(pd_df, left_on='TeamNum', right_index=True)  

  results = cs_df.merge(ocs_df, left_index=True, right_index=True).merge(pd_df, left_index=True, right_index=True)
  ballots = pd.DataFrame([table[table['OppNum'] == team]['TotalBallots'].iloc[0] for team in team_nums], columns=['Ballots'], index=team_nums)
  results = ballots.merge(results, left_index=True, right_index=True)
  results = results.sort_values(['Ballots', 'TotalCS', 'TotalOCS', 'TotalPD'], ascending=False)
  results['Rank'] = list(range(1, len(results) + 1))
  results = results['Rank']
  table = table.merge(results, left_on='TeamNum', right_index=True)

  all_schools = pd.read_csv(f"team_numbers/csv/{year}.csv", index_col="Team #")['Team Name']
  def nums_to_names(team_num_list):
    return [all_schools[int(team_num)] if int(team_num) in all_schools.index else "Bye Bust Team" for team_num in table['TeamNum']]

  table['TeamName'] = nums_to_names(table['TeamNum'])
  table['OppName'] = nums_to_names(table['OppNum'])

  table['EarnedBid'] = [team in teams_with_bids for team in table['TeamNum']]
  table['EarnedHonorableMention'] = [team in teams_with_honorable_mentions for team in table['TeamNum']]
  table['WonSPAMTA'] = [team in spamta_winners for team in table['TeamNum']]
  table['SPAMTAHonorableMention'] = [team in spamta_honorables for team in table['TeamNum']]
  table['SPAMTARanks'] = [spamta_ranks if spamta else spamta_honorable_ranks if honorable else None 
                            for (_, (spamta, honorable)) in table[['WonSPAMTA', 'SPAMTAHonorableMention']].iterrows()]

  award_df = pd.DataFrame.from_dict(award_data, orient="index")
  # print(award_data)
  outstanding_columns = [award_df[col] for col in iter(award_df.columns)]
  outstanding_team_rows = [
    [column[team_num] if team_num in award_df.index else None for column in outstanding_columns] 
      for team_num in team_nums]
  outstanding_team_rows = [
    [[None, None, None, None] if el == None else el for el in col]
    for col in outstanding_team_rows
  ]
  outstanding_team_rows = [
    list(itertools.chain.from_iterable(team_row)) for team_row in outstanding_team_rows
  ]

  outstanding_col_names = [[f"Student{i}", f"Role{i}", f"Ranks{i}", f"Side{i}"] for i in range(0, len(award_df.columns))]
  outstanding_col_names = list(itertools.chain.from_iterable(outstanding_col_names))

  final_award_df = pd.DataFrame(outstanding_team_rows, columns=outstanding_col_names, index=team_nums)
  table = table.merge(final_award_df, left_on='TeamNum', right_index=True)

  output_dir_path = f"round_results/{year}/{level}"
  if not os.path.exists(output_dir_path):
    os.makedirs(output_dir_path)

  for amta_rep, i in zip(tournament_info['amta_reps'], itertools.count()):
    tournament_info[f'amta_rep_{i}'] = amta_rep
  tournament_info.pop('amta_reps')

  for note, i in zip(tournament_info['tab_notes'], itertools.count()):
    tournament_info[f'tab_note_{i}'] = note
  tournament_info.pop('tab_notes')

  tourn_info_cols = [key for key in tournament_info]
  tourn_info_data = [tournament_info.values()] * len(table)
  tourn_table = pd.DataFrame(tourn_info_data, columns=tourn_info_cols)
  table = pd.concat([table, tourn_table], axis=1)

  table.to_csv(f"{output_dir_path}/{location}.csv", index=False)

  with open(f'round_results/{year}/{level}/{location}.json', 'w') as fp:
    json.dump(tournament_info, fp)

  return tournament_info['name']


if __name__ == "__main__":
  # tournament_text_to_results(2020, "invitationals", "crimson_classic")
  names = []
  for dir, subdirs, files in os.walk('text_data/2020'):
    if len(subdirs) == 0:
      dir_data = re.match(r'.+/(.+)/(.+)', dir)
      (year, level) = (dir_data.group(1), dir_data.group(2))

      for filename in files:
        location = filename[:-4]
        try:
          tourn_name = tournament_text_to_results(year, level, location)
          names.append([location, tourn_name])
        except KeyboardInterrupt:
          exit(0)
        except Exception as e:
          print(f"{location} {level}, {year} errored:")
          traceback.print_exc()
          continue

  names_df = pd.DataFrame(names, columns=['SysName', 'TournName']).sort_values('TournName')
  names_df.to_csv('round_results/2020/names.csv')