from collections import deque 

class Tournament_Iterator(object):
  def __init__(self, iter):
    self.iter = iter
    self.queued_items = deque()
    self.event_handlers = []

  def __iter__(self):
    return self

  def __next__(self):
    nextItem = None

    if self.queued_items:
      nextItem = self.queued_items.popleft()
    else:
      nextItem = next(self.iter)

    for handler in self.event_handlers:
      if handler(nextItem):
        return next(self) # Allow handlers to skip over a line they've chosen to handle
    if nextItem.startswith("Page"):
      return next(self) # Skip over page headings

    return nextItem

  def prepend(self, item):
    self.queued_items.append(item)

  def add_handler(self, event_handler):
    self.event_handlers.append(event_handler)