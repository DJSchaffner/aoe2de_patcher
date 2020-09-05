import utils

class IORedirector(object):
  def __init__(self, text_widget):
    # Store the widget
    self.text_widget = text_widget

class StdoutRedirector(IORedirector):
  def write(self, text):
    utils.log(self.text_widget, text)

  def flush(self):
    pass 