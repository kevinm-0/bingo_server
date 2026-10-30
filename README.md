# Jet Set Radio Future Bingo Server


The accompanying websocket server for the [Jet Set Radio Future Bingo Client](https://github.com/kevinm-0/bingo_client)

## Overview

Implemented features include persistent sychronous board state, auto square marking, persistent board state, game commital to a pocketbase database, pausing, team selection, keep alive websocket requests, board generation, "snipe" detection, and message handling. 

See it in action at https://bingo.kevcyg.net/

## Getting Started

Run main.py with python version greater than 3.11.6.

Ensure you have a .env file as follows in the same directory.

```
py_port = 1234
py_host = "127.0.0.1"
py_pocketbase_api_key = "example"
py_pocketbase_url = "https://example.com"
```

## Contributors

Developed entirely in large by me, with special contributions for board generators made by [BSBussell](https://github.com/BSBussell) and daft7. Thankyou very much!