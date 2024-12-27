#!/usr/bin/env bash

curl -X POST "http://localhost:8080/submit_flags" --header "Content-Type: application/json" --data '{"team_id": "2", "flags": ["flag{0ffee8005a3c4fd525298402645de0289b6c012c5c21a84fc22091662f094d7c}"]}'