# Central Database Manager

# Test

```sh
python3 api_server.py
python3 web_server.py
open http://localhost:5001
```

## Add teams
```
curl -X POST http://127.0.0.1:5000/team -H "Content-Type: application/json" -d '{"name":"Team1"}'
curl -X POST http://127.0.0.1:5000/team -H "Content-Type: application/json" -d '{"name":"Team2"}'
```

## Add services
```
curl -X POST http://127.0.0.1:5000/service -H "Content-Type: application/json" -d '{"name":"Service1"}'
curl -X POST http://127.0.0.1:5000/service -H "Content-Type: application/json" -d '{"name":"Service2"}'
curl -X POST http://127.0.0.1:5000/service -H "Content-Type: application/json" -d '{"name":"Service3"}'
```

## Update service statuses
```
curl -X POST http://127.0.0.1:5000/status -H "Content-Type: application/json" -d '{"team_id":1,"service_id":1,"status":"up"}'
curl -X POST http://127.0.0.1:5000/status -H "Content-Type: application/json" -d '{"team_id":1,"service_id":2,"status":"down"}'
curl -X POST http://127.0.0.1:5000/status -H "Content-Type: application/json" -d '{"team_id":1,"service_id":3,"status":"up"}'
curl -X POST http://127.0.0.1:5000/status -H "Content-Type: application/json" -d '{"team_id":2,"service_id":1,"status":"up"}'
curl -X POST http://127.0.0.1:5000/status -H "Content-Type: application/json" -d '{"team_id":2,"service_id":2,"status":"up"}'
```

## Update scores
```
curl -X POST http://127.0.0.1:5000/score -H "Content-Type: application/json" -d '{"team_id":1,"points":300,"reason":"Flag captures"}'
curl -X POST http://127.0.0.1:5000/score -H "Content-Type: application/json" -d '{"team_id":2,"points":250,"reason":"Flag captures"}'
```