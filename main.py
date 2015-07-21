__author__ = 'Inha Joo and Vishnu Raveendran'

import multiprocessing
from client import Client
from gamec import GameCoordinator


gc = GameCoordinator()
client = Client(10, 'Test', gc)
