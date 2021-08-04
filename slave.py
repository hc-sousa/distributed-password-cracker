import sys
from src.slave import Slave

if __name__ == "__main__":

    log = True if "-l" in sys.argv else False

    slave = Slave(log)

    data, allGuesses, slaveGuesses = slave.attack()

    print(f"There were {len(allGuesses)} different password guesses. The guesses were the following:\n{allGuesses}") if "-l" in sys.argv and allGuesses != None else None
    print(f"This Worker guessed the following:\n{slaveGuesses}") if "-l" in sys.argv and slaveGuesses != None else None
    print(data) if data != None else None

