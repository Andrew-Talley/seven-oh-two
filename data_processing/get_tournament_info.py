import re
from parse_date_line import parse_date_line

def get_tournament_info(file_iterator):
  info = {
    'tab_notes': list()
  }

  name_line = next(file_iterator)
  if name_line.startswith("AMERICAN"):
    name_line = next(file_iterator)
  info['name'] = re.match(r'(\d{4} )?(.+)( )?(Open|Regional)?', name_line).group(2)

  for line in file_iterator:
    lower_line = line.lower()
    if "division" in lower_line:
      info['division'] = re.match(r".+\sDivision", line).group(0)

    elif "hosted" in lower_line or "presented" in lower_line:
      line = re.sub(r"\s", " ", line)

      line = line.replace("Hosted by", "")
      line = line.replace("Presented by", "")

      groups = line.split(" in ")
      if len(groups) == 1:
        groups = line.split(" at the ")

      info['host'] = groups[0].strip()
      
      if len(groups) > 1:
        info['location'] = groups[1].strip()

    else:
      try:
        info['start_date'], info['end_date'] = parse_date_line(line)
      except:
        1 + 1 # no-op

    if "summary" in lower_line:
      return info

  raise EOFError()
