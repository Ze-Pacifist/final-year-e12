#!/bin/bash

if [ -z "$ROOT_PASSWORD" ]; then
  echo "No ROOT_PASSWORD set, using default 'root'"
  ROOT_PASSWORD="root"
fi

# Set the root password
echo "root:$ROOT_PASSWORD" | chpasswd

/usr/bin/supervisord
