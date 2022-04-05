# Go-Back-N Implementation for ELEC4360

A client/server model implementing Go-Back-N transmission protocol. This is built to be a demo for a class project.

> *Potential Compatibility Issue*: **The event loop of `client.py` uses `epoll` and therefore needs to be run on a system that supports `epoll`.**

---
## Running the Demo
To run the demo, in one terminal, run:
```python3
python3 server.py
```

Then in a second terminal, run:
```python3
python3 client.py
```

In order to create text output files to view the terminal output easier, simply redirect the output to text files.
```
python3 server.py > server_output.txt
```
```
python3 client.py > client_output.txt
```

Watch the transmission of ten lower case names from `transmit.txt` to a server, which then spits out the list of capitalized names in `receive.txt`.

---

## Custom Packets
In order to make it a bit easier to visualize, the project encodes and decodes json based custom packets with their `fields` and `types` defined as `IntEnum` in `packet_fields.py` and `packet_types.py`.

---

> *Note*: The scripts are setup for protocol demonstration purposes and introduce errors at specified server buffer indices. As required by assignment specs, it introduces 2 errors per 10 frames - a timeout error and a ACK sequencing error.

> *Note*: It was easiest to do the error demonstration on either client or server side rather than a mix of both, and I chose server side since it wasn't specified.


