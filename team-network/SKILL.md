---
name: team-network
description: Run the team's network paths — the xray SOCKS proxy chain, the socat forwarder, curl transport with retry, and exit-IP checks — and diagnose dead proxies and geo-blocks the way Ada does for Bybit and the Matrix poller.
---

# Team Network

You run the team's network paths. The VM cannot do what a normal host
does — no `tun` interface, no Docker, no VPN client — so everything here
goes through userspace proxies and plain `curl`. Test the path before you
trust it, and report what the test actually returned.

## The proxy chain (Bybit demo)

- Start it with `~/workspace/proxy/start-bybit-proxy.sh`, stop it with
  `stop-bybit-proxy.sh`. The chain is: socat CONNECT forwarder on
  `127.0.0.1:12083` → xray VLESS/REALITY as a SOCKS proxy on
  `127.0.0.1:10808` → the egress proxy.
- The config lives at `~/workspace/proxy/xray/config-bybit.json`, mode
  600. Never repeat its values, never print them, never commit them.
- Verify the exit before any real call: check the exit IP and hit a
  public endpoint (Bybit `/v5/market/time` must return `retCode 0`).
  The verified exit is Milan, Italy — Bybit is geo-blocked from this
  VM's own egress, so a call that bypasses the proxy fails by design.
- Kill by pidfile (`socat.pid`, `xray/xray.pid`), then check no stray
  `socat`/`xray` process survives. A half-stopped chain is worse than a
  stopped one: the next start binds nothing and fails silently.

## curl, not urllib

- Every HTTP call from a poller or tool goes through `curl` with retry
  and backoff — never `urllib`. The VM's egress proxy drops long-polls
  mid-response under `urllib`; the curl transport (Matrix template v2+)
  fixed it.
- Set a max-time on every call and a hold shorter than it (Matrix sync:
  10 s hold inside curl's 45 s max-time). A call with no timeout hangs
  the poller and looks exactly like a dead hook.
- Treat a proxy failure as a value failure, not a code failure: Karen's
  Matrix poller died on dead proxy values (HTTP 407) and a template bug,
  not on her code. Check the proxy values first, then the code.

## Diagnose in order

- Is the chain up? Listeners on 12083 and 10808, exit IP as expected.
- Is the proxy value alive? A 407 means the credentials are dead — get
  fresh values, don't retry the same ones.
- Is the endpoint reachable through the proxy? One `curl` against the
  real endpoint, with the real proxy, before touching any tool code.
- Only then read the tool's own log. Most "hook is dead" reports on this
  team were the platform restarting the VM, not the hook: check whether
  the Telegram hook died at the same minute before blaming the code.

## Limits that stay limits

- No VPN tunnel on this VM: creating a `tun` interface fails with
  "Operation not permitted". Do not ask for VPN usernames or passwords —
  the userspace proxy chain is the working route.
- Never re-run an OAuth flow while a token refresh still works, and
  refresh tokens before expiry. A re-run while a refresh works is how
  sessions get invalidated.
- Nothing here buys, rents, or activates a paid service. A new host, a
  new proxy, or a paid tier needs Daniel's explicit yes first.
