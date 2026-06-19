from app import App
from version import VERSION_MAJOR, VERSION_MINOR

if __name__ == '__main__':
    app = App(VERSION_MAJOR, VERSION_MINOR)
    app.start()
