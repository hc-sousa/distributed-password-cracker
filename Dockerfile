FROM python:3.8-slim-buster

WORKDIR /

COPY slave.py slave.py 

COPY src/slave.py src/slave.py

COPY src/protocol.py src/protocol.py

COPY server/const.py server/const.py

ENTRYPOINT [ "python3", "-u", "slave.py", "%s" ]

CMD [ "" ]
