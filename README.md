# Dark_OSINT
(Threat Intelligence) Development of dark web information notification and OSINT collection system

### Usage
---
```
$docker-compose up --build -d
```

kibana : http://localhost:5601

The script in docker would run at 09:00 & 21:00 (TZ : America/New_York)

If you want to run the script follow below
```
$docker-compose up --build -d
$docker exec -it tor /bin/bash
$python3 main.py
```
