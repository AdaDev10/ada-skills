# Bybit Demo connector for trader-broker

Bybit is **not** a broker the skill supports natively (Alpaca and IBKR are).
`bybit.py` adds Bybit **Demo Trading only** as the execution layer, reusing
the same files and the same three gates as `ticket.py`:

1. `trader-risk` PASS for this exact order today (fingerprint match).
2. An explicit yes recorded in `trader/state/broker.json`
   (`ticket.py approve --index N --reply "yes"`).
3. Demo only. The base URL is `https://api-demo.bybit.com` and the code
   refuses any other host. No mainnet, no withdrawals, no transfers.

## What it trades

Bybit's real-share product (DirectStocks) has **no documented V5 order
endpoint**, so it is not traded here. What the V5 API does support for stock
exposure, verified live 2026-11-13:

- **xStocks (tokenized shares), category=spot, symbolType=xstocks** - this is
  what the connector trades: `TSLA` -> `TSLAXUSDT`, `AAPL` -> `AAPLXUSDT`,
  `NVDA` -> `NVDAXUSDT`. Spot, no leverage, fractional (min 0.001), price
  tracks the stock. Settlement in USDT.
- **Stock perpetuals, category=linear, symbolType=stock** (`TSLAUSDT`) -
  deliberately NOT supported: leveraged derivatives, a different risk model
  from the skill's share sizing.

A bracket order maps to one Bybit order with atomic TP/SL:
`takeProfit` + `stopLoss` + `tpslMode=Full` on the same `POST /v5/order/create`.
Bybit spot has no `day` time-in-force; the flat-by rule is enforced by
`trader-alerts` / `flatten`, not by the exchange, so the order uses GTC.

## Setup

1. On the Bybit website: switch to **Demo Trading**, profile -> **API** ->
   Create New Key (system-generated, Read + Trade only, **never** Withdraw).
   Demo keys only work on `api-demo.bybit.com`. Demo starts with 50,000 USDT
   simulated. Keys can only be created on the website, not in the app.
2. Export the keys in the shell before running (never paste them in chat):
   `export BYBIT_DEMO_API_KEY=... BYBIT_DEMO_API_SECRET=...`
3. Bybit is geo-blocked from a US IP. All calls go through the SOCKS proxy
   on `127.0.0.1:10808` (the Italy exit); start it first with
   `~/workspace/proxy/start-bybit-proxy.sh`, stop it with
   `stop-bybit-proxy.sh` when done.

## Use

    python3 bybit.py balance                 # demo wallet (read-only)
    python3 bybit.py show --index 1         # the Bybit JSON (no placement)
    python3 bybit.py place --index 1        # ONE approved order, gates enforced
    python3 bybit.py status                  # open orders on demo
    python3 bybit.py executions              # recent fills (+ the ticket.py fill line)
    python3 bybit.py cancel --order-id ID
    python3 bybit.py test                    # offline self-test (no network, no keys)

`place` also verifies the symbol is a live xStocks instrument before sending,
and records the placement with `ticket.py result --status placed`, so the
decision log stays in one place (`trader/state/broker.json`).

## Limits

- Demo only: a demo key cannot touch real funds, and demo orders keep 7 days.
- Not every v5 endpoint works on demo (Bybit's own note); the connector
  surfaces Bybit's own `retCode`/`retMsg` when an endpoint is unsupported.
- xStocks trade 24/7 on Bybit, unlike the underlying shares - the skill's
  market-hours rules (no entries before 09:45 / after 15:30, flat by 15:55)
  still apply as the operator's discipline, not as an exchange constraint.
- The skill's analysis still reads Yahoo Finance; Bybit prices are the
  execution prices. Cross-check the two before placing.
