class IORedirector(object):
    def __init__(self, write_callback):
        self.write_callback = write_callback


class StdoutRedirector(IORedirector):
    def write(self, text):
        self.write_callback(text)

    def flush(self):
        pass
