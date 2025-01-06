#!/usr/bin/env bash

if [ $# -ne 2 ]; then
    echo "[-] Usage: $0 <team_id> <flag>"
    exit 1
fi

curl -X POST http://localhost:9090/submit_flags \
    -H "Content-Type: application/json" \
    -d "{
        "team_id": $1,
        "flags": ["$2"]
    }"