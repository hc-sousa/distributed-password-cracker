"""Protocol for multicast group - Computação Distribuida Final Assignment."""

import json
from datetime import datetime
from json.decoder import JSONDecodeError
from logging import exception
from socket import socket


class Message:
    """Message Type."""
    def __init__(self, command):
        self.command = command

class HelloMessage(Message):
    """Message to Anounce himself in the network."""
    def __init__(self, id: str = None, sock: socket = None):
        super().__init__("hello")
        self.id = id
        self.sock = sock
    def __repr__(self):
        return json.dumps(self.__dict__)

class WelcomeMessage(Message):
    """Message to welcome a worker and inform of his own address."""
    def __init__(self, id: str = None, guesses: list = None, sock: socket = None):
        super().__init__("welcome")
        self.id = id
        self.guesses = guesses
        self.sock = sock
    def __repr__(self):
        return json.dumps(self.__dict__)
    
class TryMessage(Message):
    """Message to try a password."""
    def __init__(self, password: str = None):
        super().__init__("try")
        self.password = password
    
    def __repr__(self):
        return json.dumps(self.__dict__)

class PeerTryMessage(Message):
    """Message to send try password from peer."""
    def __init__(self, password: str = None):
        super().__init__("peerTry")
        self.password = password
    
    def __repr__(self):
        return json.dumps(self.__dict__)

class GuessMessage(Message):
    """Message when server password is guessed."""
    def __init__(self, password):
        super().__init__("guess")
        self.server_pwd = password

    def __repr__(self):
        return json.dumps(self.__dict__)

class LeavingMessage(Message):
    """Message to anounce client is leaving."""
    def __init__(self, id: str = None, times: int = 1):
        super().__init__("leaving")
        self.id = id
        self.times = times

    def __repr__(self):
        return json.dumps(self.__dict__)

class HackProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def hello(cls, id: str, sock: socket) -> HelloMessage:
        """Creates a HelloMessage object."""
        return HelloMessage(id, sock)

    @classmethod
    def welcome(cls, id: str, guesses: list, sock: socket) -> WelcomeMessage:
        """Creates a WelcomeMessage object."""
        return WelcomeMessage(id, guesses, sock)

    @classmethod
    def guess(cls, guess: str) -> TryMessage:
        """Creates a TryMessage object."""
        return TryMessage(guess)

    @classmethod
    def peerguess(cls, guess: str) -> PeerTryMessage:
        """Creates a PeerTryMessage object."""
        return PeerTryMessage(guess)

    @classmethod
    def guessed(cls, server_pwd) -> GuessMessage:
        """Creates a GuessMessage object."""
        return GuessMessage(server_pwd)

    @classmethod
    def leave(cls, id: str, times: int = 0) -> LeavingMessage:
        """Creates a LeavingMessage object."""
        return LeavingMessage(id, times)

    @classmethod
    def get_msg(cls, msg: Message):
        """Get an Message object JSON string"""
        try:
            return repr(msg)
        except HackProtoBadFormat as e:
            return e.original_msg()

class HackProtoBadFormat(Exception):
    """Exception when source message is not HackProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")