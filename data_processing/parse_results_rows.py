import re
import itertools

def parse_results_rows(file_iterator):
  opponents_row = next(file_iterator)
  opponents = re.findall(r"\d{4}", opponents_row)[-4:]
  sides = re.findall(r"[PD∏ΠπΔ∆]", opponents_row)

  results_row = next(file_iterator)
  if results_row == "Washington & Jefferson\n":
    results_row.rstrip("\n")
    results_row += " " + next(file_iterator)
  try:
    relevant_section = re.search(r"([WLT]\s){4,}", results_row).group(0)
  except:
    print(results_row)
    raise
  num_results = len(re.findall(r"[WLT]", relevant_section))
  if num_results % 4 != 0:
    raise Exception(f"Improper number of results: {num_results} for line: \"{results_row}\" (matched section: \"{relevant_section}\")")
  ballots_per_round = num_results // 4

  pd_line = next(file_iterator)
  ballots = list()
  for _ in range(num_results):
    space_ind = pd_line.find(" ")
    try:
      ballots.append(int(pd_line[0:space_ind]))
    except ValueError:
      ballots.append(float(pd_line[0:space_ind]))

    pd_line = pd_line[space_ind+1:]

  def expand_arr(arr):
    return list(itertools.chain.from_iterable([i] * ballots_per_round for i in arr))

  round_nums = expand_arr(range(1, 5))
  opponents = expand_arr(opponents)
  sides = expand_arr(sides)

  return opponents, sides, ballots, round_nums
