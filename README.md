# final-year-e12
Beta 0.0

## How To
- First run the vpn container to generate the client configs: `docker-compose up vpn`
- Run `vpn/update_server_config.sh` inside the container
- Stop the vpn container
- Then run the entire platform: `docker-compose up`