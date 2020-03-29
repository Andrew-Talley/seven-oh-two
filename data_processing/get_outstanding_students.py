import re
import pandas as pd
from collections import deque, defaultdict

num = "(\\d{2}\\.?\\d?)"
sides = "([PDpd∏ΠπΔ∆&])"
separators = "[\\/,-]"
number_combo = f"{num}( ?{separators}? ?{num})?"
sides_combo = f"{sides} ?{separators}? ?{sides}?"
outstanding_student_reg = re.compile(f"{number_combo} {sides_combo} (.+)\\n?")

new_combo = f"{sides} ?{num}"

new_outstanding_reg = re.compile(f"{new_combo}{separators}?({new_combo})? (\\D+).+\\n")
def get_outstanding_students(file_iterator, year):
  all_schools = pd.read_csv(f"team_numbers/csv/{year}.csv")
  all_schools = set(school[:-1] if school[-2:-1] == " " else school for school in all_schools['Team Name'])
  all_schools = set(school.rstrip() for school in all_schools)

  students = list()
  school_nums = list()
  sides = list()
  ranks = list()
  roles = list()

  double_award = deque()

  current_role = "Witness"

  for line in file_iterator:
    if line[len(line) - 1] != "\n":
      line += "\n"
    line = line.replace("\t", " ")
    line = line.replace("U.", "University")
    line = line.replace("Univ.", "University")

    match = re.match(outstanding_student_reg, line)
    new_match = re.match(new_outstanding_reg, line)
    num_match = re.search(r"\d{4}", line)
    ranks_1 = ranks_2 = side_1 = side_2 = name = None
    if match:
      [ranks_1, _, ranks_2, side_1, side_2, name] = match.groups()
    elif new_match:
      [side_1, ranks_1, _, side_2, ranks_2, name] = new_match.groups()

    if match or new_match:
      for school in all_schools:
        name = name.replace(" " + school, "")

      students.append(name)
      ranks.append(ranks_1)
      sides.append(side_1)
      roles.append(current_role)
      if side_2:
        if not ranks_2:
          ranks_2 = ranks_1
        double_award.append(True)

        students.append(name)
        ranks.append(ranks_2)
        sides.append(side_2)
        roles.append(current_role)
      else:
        double_award.append(False)

    if num_match and "*" not in line:
      school_num = num_match.group(0)
      if int(school_num) < 2000:
        school_nums.append(school_num)
        try:
          if double_award.popleft():
            school_nums.append(school_num)
        except:
          print(double_award)
          print(students)
          print(len(students))
          print(school_nums)
          print(len(school_nums))
          raise

    elif "Attorneys" in line:
      current_role = "Attorney"

  award_data_iter = zip(school_nums, students, sides, ranks, roles)
  award_data = defaultdict(list)
  for school_num, student, side, rank, role in award_data_iter:
    award_data[school_num].append([student, role, rank, side])

  return award_data
