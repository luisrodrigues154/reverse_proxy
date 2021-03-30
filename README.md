# README


# Layer 7 reverse proxy

Structure:
- Reverse_proxy listening on 127.0.0.1:1414
- A cache with an invalidator when used 4 times
- http.server used for communication

To run the reverse proxy you'll need the requirements present in the **requirements.txt** file (it is just the requests module). Also it uses python 3 (tested with 3.9.2)

``` 
pip install -r requirements.txt
```

Then you can run as so
```
> python reverse_proxy_L7.py

[SETUP] Initializing Cache
[SERVER] Listening on ('127.0.0.1', 1414)
```

And you can issue requests as following
```
> curl -X GET 127.0.0.1:1414 -H "Host: address"
```

# Layer 3 reverse proxy  

To run the reverse proxy you need any linux OS with python 3 (i used python 3.9.2) <br>
**Note:** not sure about windows, since sockets behave differently, but it might work since it is running over python 

Structure
- Reverse_proxy listening on 127.0.0.1:1414
- 4 python http.server's are spawn in the por range 8080-8084
- A cache with an invalidator when used 4 times
- A load balancer (that does not load balance)
  - generates a random integer number between 0-n_servers
  - return the address in that index
- Sockets used to communicate with clients and servers
 

## How to run
```
cmd: pwd 
$ (...)/RP_ENV
cmd: source bin/activate
cmd: ./reverse_proxy
```

To issue requests i tested a browser (firefox) and cURL
```
curl -X GET http://localhost:1414
```