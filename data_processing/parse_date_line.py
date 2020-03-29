import re

def get_date_string(month, date, year):
  date = "%02d" % (int(date))
  return f"{month} {date}, {year}"

def parse_date_line(line):
  date_parse = re.match(r'(\w+)\s(\d+)\s?-\s?([A-Za-z]+)?\s?(\d+),\s(\d{4})', line)
  start_month, start_day = date_parse.group(1), date_parse.group(2)
  end_month, end_day = date_parse.group(3), date_parse.group(4)
  if end_month == None:
    end_month = start_month
  year = date_parse.group(5)

  start_date = get_date_string(start_month, start_day, year)
  end_date = get_date_string(end_month, end_day, year)

  return start_date, end_date
