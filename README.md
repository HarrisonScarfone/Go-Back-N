# Go-Back-N

A client/server model implementing Go-Back-N transmission protocol. This is built to be a demo for a class project.

The event loop of `client.py` uses `epoll` and therefore needs to be run on a system that supports `epoll`.

In one terminal, run:
```python3
python3 server.py
```

Then in a second terminal, run:
```python3
python3 client.py
```

Watch the transmission of ten lower case names to a server, which then spits out the list of capitalized names.

> *Note*: The scripts are setup for protocol demonstration purposes and introduce errors at specified client buffer indices. As required by assignment specs, it introduces 2 errors per 10 frames - a timeout error and a ACK sequencing error.
