from server import Server
from content import parse
from gui import Gui
from app import Program
import sys


if __name__ == "__main__":
    # load content
    if len(sys.argv) < 2:
        print("Please provide a YML config file!")
        sys.exit()
    
    cfg = parse(sys.argv[1])

    # set up and run server
    server = Server(cfg)

    # setup gui
    gui = Gui(cfg)

    # Set up and run program
    Program(cfg, gui, server).run()
