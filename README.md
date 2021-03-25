# README

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