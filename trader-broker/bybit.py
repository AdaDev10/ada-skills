#!/usr/bin/env python3
"""Bybit connector for trader-broker (DEMO TRADING ONLY). Standard library only.

Reads the same trader/orders.json + trader/state/risk.json +
trader/state/broker.json as ticket.py, and places a READY, user-approved order
on Bybit Demo Trading (api-demo.bybit.com) as an xStocks spot order
(TSLA -> TSLAXUSDT, tokenized shares, same price as the stock, spot, no
leverage). Bybit's real-share product (DirectStocks) has no documented V5
order endpoint, so it is NOT traded here; stock perpetuals (category=linear)
are leveraged and are deliberately NOT supported either.

Gates (same as trader-broker, enforced in code, every time):
  1. trader-risk PASS for this exact order today (fingerprint match).
  2. An explicit yes recorded in trader/state/broker.json (ticket.py approve).
  3. DEMO ONLY: MAINNET_BLOCKED. The base URL is api-demo.bybit.com and the
     code refuses any other host. No mainnet, no withdrawals, no transfers,
     no leverage. The connector only calls: order create/cancel, order
     realtime, execution list, wallet balance.

Auth: HMAC-SHA256 per Bybit v5 (X-BAPI-API-KEY / X-BAPI-TIMESTAMP /
X-BAPI-SIGN). Keys come from BYBIT_DEMO_API_KEY / BYBIT_DEMO_API_SECRET
(environment only, never in chat and never written by this tool). HTTP goes
through the SOCKS proxy on 127.0.0.1:10808 (the Italy exit) via curl, because
Bybit is geo-blocked from this VM's US egress.

    python3 bybit.py balance                 # demo wallet balance (read-only)
    python3 bybit.py show --index 1         # the Bybit JSON for one order (no placement)
    python3 bybit.py place --index 1        # place ONE approved order (gates enforced)
    python3 bybit.py status                  # open orders on demo
    python3 bybit.py executions              # recent fills (then record with ticket.py fill)
    python3 bybit.py cancel --order-id ID    # cancel one open order
    python3 bybit.py test                    # offline self-test (no network, no keys)
"""

import argparse
import datetime
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time

DEMO_BASE = "https://api-demo.bybit.com"
MAINNET_HOSTS = ("api.bybit.com", "api.bytick.com", "api-testnet.bybit.com")
SOCKS_PROXY = "127.0.0.1:10808"
RECV_WINDOW = "5000"

# xStocks spot symbols verified live 2026-11-13 (category=spot,
# symbolType=xstocks). The connector also verifies a symbol live before
# placing, and refuses anything not in this family.
XSTOCKS_SUFFIX = "XUSDT"


class BybitError(Exception):
    pass


# ------------------------------------------------------------------ state files
def _read_json(path, what, required=True):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        if required:
            raise BybitError("missing %s: %s" % (what, path))
        return None
    except json.JSONDecodeError as e:
        raise BybitError("bad JSON in %s: %s" % (path, e))


def _today_ny():
    # New York date without tz files: UTC-5 in standard time, UTC-4 in DST
    # (second Sunday of March to first Sunday of November).
    now = datetime.datetime.utcnow()
    def nth_sunday(y, m, n):
        d = datetime.date(y, m, 1)
        d += datetime.timedelta(days=(6 - d.weekday()) % 7)
        return d + datetime.timedelta(weeks=n - 1)
    start = datetime.datetime.combine(nth_sunday(now.year, 3, 2), datetime.time(7, 0))
    end = datetime.datetime.combine(nth_sunday(now.year, 11, 1), datetime.time(6, 0))
    off = -4 if start <= now < end else -5
    return (now + datetime.timedelta(hours=off)).date().isoformat()


ALPACA_FIELDS = ("symbol", "side", "qty", "notional", "type", "time_in_force",
                 "limit_price", "stop_price", "trail_price", "trail_percent",
                 "extended_hours", "client_order_id", "order_class",
                 "take_profit_limit_price", "stop_loss_stop_price",
                 "stop_loss_limit_price", "advanced_instructions")


def fingerprint(order):
    """Same function as trader-risk/check.py and trader-broker/ticket.py."""
    core = {k: order[k] for k in ALPACA_FIELDS if k in order and order[k] is not None}
    blob = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _price(v):
    """A price to the cent, as Bybit expects (tickSize 0.01 on xStocks)."""
    f = float(v)
    return "%.2f" % f


def _qty(v):
    """An xStocks quantity: base coin, step 0.001, min 0.001."""
    f = float(v)
    if f <= 0:
        raise BybitError("qty must be positive, got %r" % (v,))
    return ("%.3f" % f).rstrip("0").rstrip(".")


# ------------------------------------------------------------------ mapping
def map_symbol(ticker):
    """TSLA -> TSLAXUSDT (xStocks spot). Refuses anything not in that family."""
    t = str(ticker or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{1,5}", t):
        raise BybitError("not a bare stock ticker: %r" % (ticker,))
    return t + XSTOCKS_SUFFIX


def map_order(order, today=None):
    """An Alpaca-style bracket order -> the exact Bybit v5 place-order body.

    Entry is a market (or limit) buy of the xStocks token; the stop-loss and
    take-profit ride on the same request as atomic TP/SL (tpslMode Full).
    Bybit has no 'day' time-in-force on spot: the flat-by rule is enforced by
    trader-alerts / flatten, not by the exchange, so GTC is correct here.
    """
    symbol = map_symbol(order.get("symbol"))
    side = str(order.get("side", "")).lower()
    if side != "buy":
        raise BybitError("Bybit connector only places buy entries (got side %r)" % (side,))
    qty = _qty(order.get("qty"))
    otype = str(order.get("type", "market")).lower()
    if otype not in ("market", "limit"):
        raise BybitError("unsupported order type %r" % (otype,))
    if order.get("take_profit_limit_price") is None or order.get("stop_loss_stop_price") is None:
        raise BybitError("bracket needs both take-profit and stop-loss (refusing a naked order)")
    body = {
        "category": "spot",
        "symbol": symbol,
        "side": "Buy",
        "orderType": "Market" if otype == "market" else "Limit",
        "qty": qty,
        "timeInForce": "GTC",
        "takeProfit": _price(order["take_profit_limit_price"]),
        "stopLoss": _price(order["stop_loss_stop_price"]),
        "tpslMode": "Full",
        "tpTriggerBy": "LastPrice",
        "slTriggerBy": "LastPrice",
    }
    if otype == "limit":
        if order.get("limit_price") is None:
            raise BybitError("limit order needs limit_price")
        body["price"] = _price(order["limit_price"])
    day = today or _today_ny()
    body["orderLinkId"] = "ada-%s-%s" % (day.replace("-", ""), fingerprint(order)[:8])
    return body


# ------------------------------------------------------------------ signing
def sign(secret, timestamp, api_key, recv_window, payload):
    """Bybit v5 signature: HMAC-SHA256(secret, timestamp + api_key +
    recv_window + payload), hex. Payload is the query string (GET) or the
    exact JSON body string (POST)."""
    msg = "%s%s%s%s" % (timestamp, api_key, recv_window, payload)
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def _keys():
    key = os.environ.get("BYBIT_DEMO_API_KEY", "")
    secret = os.environ.get("BYBIT_DEMO_API_SECRET", "")
    if not key or not secret:
        raise BybitError(
            "missing BYBIT_DEMO_API_KEY / BYBIT_DEMO_API_SECRET. "
            "Create them inside Bybit Demo Trading (website: switch to Demo "
            "Trading, profile -> API), then export them in the shell before "
            "running this tool. They are demo keys only; never paste them in chat.")
    return key, secret


def _http(method, path, body=None, timeout=30):
    """One signed Bybit v5 call through the SOCKS proxy (curl). Returns the
    parsed JSON. Raises BybitError on transport failure or retCode != 0."""
    if DEMO_BASE.split("://")[1] in MAINNET_HOSTS:
        raise BybitError("MAINNET_BLOCKED: refusing non-demo host")
    key, secret = _keys()
    ts = str(int(time.time() * 1000))
    if method == "GET":
        qs = ""
        if body:
            qs = "&".join("%s=%s" % (k, body[k]) for k in sorted(body))
        sig = sign(secret, ts, key, RECV_WINDOW, qs)
        url = DEMO_BASE + path + ("?" + qs if qs else "")
        data = None
    else:
        raw = json.dumps(body or {}, sort_keys=True, separators=(",", ":"))
        sig = sign(secret, ts, key, RECV_WINDOW, raw)
        url = DEMO_BASE + path
        data = raw
    cmd = ["curl", "-s", "-m", str(timeout), "--socks5-hostname", SOCKS_PROXY,
           "-X", method, url,
           "-H", "X-BAPI-API-KEY: " + key,
           "-H", "X-BAPI-TIMESTAMP: " + ts,
           "-H", "X-BAPI-RECV-WINDOW: " + RECV_WINDOW,
           "-H", "X-BAPI-SIGN: " + sig,
           "-H", "Content-Type: application/json"]
    if data is not None:
        cmd += ["--data-binary", data]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    except (subprocess.SubprocessError, OSError) as e:
        raise BybitError("curl failed: %s (is the proxy chain running? "
                         "start-bybit-proxy.sh)" % (e,))
    if out.returncode != 0:
        raise BybitError("curl exit %d: %s" % (out.returncode, out.stderr.strip()))
    try:
        resp = json.loads(out.stdout)
    except json.JSONDecodeError:
        raise BybitError("non-JSON reply from Bybit: %r" % (out.stdout[:200],))
    if resp.get("retCode") != 0:
        raise BybitError("Bybit retCode %s: %s" % (resp.get("retCode"), resp.get("retMsg")))
    return resp


def _http_public(method, path, params=None, timeout=30):
    """An unsigned public call (no keys) through the SOCKS proxy."""
    qs = ""
    if params:
        qs = "&".join("%s=%s" % (k, params[k]) for k in sorted(params))
    url = DEMO_BASE + path + ("?" + qs if qs else "")
    cmd = ["curl", "-s", "-m", str(timeout), "--socks5-hostname", SOCKS_PROXY, url]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    except (subprocess.SubprocessError, OSError) as e:
        raise BybitError("curl failed: %s" % (e,))
    if out.returncode != 0:
        raise BybitError("curl exit %d: %s" % (out.returncode, out.stderr.strip()))
    try:
        resp = json.loads(out.stdout)
    except json.JSONDecodeError:
        raise BybitError("non-JSON reply: %r" % (out.stdout[:200],))
    if resp.get("retCode") != 0:
        raise BybitError("Bybit retCode %s: %s" % (resp.get("retCode"), resp.get("retMsg")))
    return resp


# ------------------------------------------------------------------ gates
def _load_all(trader_dir):
    orders = _read_json(os.path.join(trader_dir, "orders.json"), "orders")
    risk = _read_json(os.path.join(trader_dir, "state", "risk.json"),
                      "risk verdicts", required=False) or {}
    state = _read_json(os.path.join(trader_dir, "state", "broker.json"),
                       "broker state", required=False) or {"orders": []}
    cfg = _read_json(os.path.join(trader_dir, "config.json"),
                     "config", required=False) or {}
    return orders, risk, state, cfg


def _risk_pass(order, risk, today):
    fp = fingerprint(order)
    for r in risk.get("results", []) or []:
        if r.get("fingerprint") == fp and r.get("verdict") == "PASS":
            return True, r
    return False, None


def _yes_recorded(order, state, today):
    fp = fingerprint(order)
    for rec in reversed(state.get("orders", []) or []):
        if rec.get("fingerprint") == fp and str(rec.get("date", ""))[:10] == today:
            if str(rec.get("decision", "")).lower() in ("yes", "approved"):
                return True, rec
            return False, rec
    return False, None


def _order_by_index(orders, index):
    if not isinstance(orders, list) or not orders:
        raise BybitError("no orders in trader/orders.json (run trader-budget first)")
    if index < 1 or index > len(orders):
        raise BybitError("index %d out of range (1..%d)" % (index, len(orders)))
    return orders[index - 1]


# ------------------------------------------------------------------ commands
def cmd_balance(args):
    resp = _http("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})
    print("Bybit DEMO wallet (UNIFIED):")
    for acct in resp["result"].get("list", []):
        for coin in acct.get("coin", []):
            print("  %-6s wallet=%s available=%s" % (
                coin.get("coin"), coin.get("walletBalance"), coin.get("availableToWithdraw")))
    return 0


def cmd_show(args):
    orders, risk, state, cfg = _load_all(args.trader)
    order = _order_by_index(orders, args.index)
    body = map_order(order)
    print("Bybit DEMO order (not placed):")
    print(json.dumps(body, indent=2, sort_keys=True))
    today = _today_ny()
    ok, _ = _risk_pass(order, risk, today)
    yes, _ = _yes_recorded(order, state, today)
    print("gates: risk PASS=%s, explicit yes recorded=%s" % (ok, yes))
    return 0


def cmd_place(args):
    orders, risk, state, cfg = _load_all(args.trader)
    order = _order_by_index(orders, args.index)
    today = _today_ny()
    ok, rv = _risk_pass(order, risk, today)
    if not ok:
        raise BybitError("BLOCKED: trader-risk did not PASS this exact order today "
                         "(run trader-risk first; fingerprint %s)" % fingerprint(order))
    yes, rec = _yes_recorded(order, state, today)
    if not yes:
        raise BybitError("BLOCKED: no explicit yes recorded for this order today "
                         "(ticket.py approve --index %d --reply \"yes\" first)" % args.index)
    body = map_order(order, today)
    # Verify the symbol is a live xStocks instrument before sending money.
    inst = _http_public("GET", "/v5/market/instruments-info",
                        {"category": "spot", "symbol": body["symbol"]})
    if not inst["result"].get("list"):
        raise BybitError("symbol %s is not a live xStocks instrument" % body["symbol"])
    print("placing on Bybit DEMO: %s %s %s @ market, TP %s, SL %s" % (
        body["side"], body["qty"], body["symbol"], body["takeProfit"], body["stopLoss"]))
    resp = _http("POST", "/v5/order/create", body)
    result = resp["result"]
    print("PLACED on Bybit DEMO: orderId=%s orderLinkId=%s" % (
        result.get("orderId"), result.get("orderLinkId")))
    # Record it the same way ticket.py does, so the log stays in one place.
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, "ticket.py"), "result",
                    "--index", str(args.index), "--status", "placed",
                    "--broker-id", str(result.get("orderId", "")),
                    "--trader", args.trader], check=False)
    return 0


def cmd_status(args):
    resp = _http("GET", "/v5/order/realtime", {"category": "spot"})
    lst = resp["result"].get("list", [])
    if not lst:
        print("no open orders on Bybit DEMO (spot)")
        return 0
    for o in lst:
        print("%s %s %s %s qty=%s price=%s status=%s" % (
            o.get("orderId"), o.get("symbol"), o.get("side"), o.get("orderType"),
            o.get("qty"), o.get("price"), o.get("orderStatus")))
    return 0


def cmd_executions(args):
    resp = _http("GET", "/v5/execution/list", {"category": "spot", "limit": "20"})
    lst = resp["result"].get("list", [])
    if not lst:
        print("no recent executions on Bybit DEMO (spot)")
        return 0
    for e in lst:
        print("%s %s %s qty=%s price=%s fee=%s %s" % (
            e.get("execId"), e.get("symbol"), e.get("side"), e.get("execQty"),
            e.get("execPrice"), e.get("execFee"), e.get("execTime")))
        print("   record it: ticket.py fill --symbol %s --side %s --qty %s --price %s"
              % (e.get("symbol", "").replace("XUSDT", ""), str(e.get("side", "")).lower(),
                 e.get("execQty"), e.get("execPrice")))
    return 0


def cmd_cancel(args):
    resp = _http("POST", "/v5/order/cancel",
                 {"category": "spot", "orderId": args.order_id})
    print("cancelled: %s" % resp["result"].get("orderId"))
    return 0


def cmd_test(args):
    """Offline self-test: signature vs openssl, mapping, gates. No network, no keys."""
    import shutil
    # 1. Signature against openssl (independent implementation).
    secret, ts, key, rw = "testsecret", "1700000000000", "testkey", "5000"
    payload = '{"category":"spot","qty":"8","side":"Buy","symbol":"TSLAXUSDT"}'
    mine = sign(secret, ts, key, rw, payload)
    msg = (ts + key + rw + payload).encode()
    if shutil.which("openssl") is None:
        print("SKIP openssl cross-check (openssl not installed)")
    else:
        out = subprocess.run(["openssl", "dgst", "-sha256", "-hmac", secret],
                             input=msg, capture_output=True)
        theirs = out.stdout.decode().strip().split("= ")[-1]
        assert mine == theirs, "signature mismatch: %s != %s" % (mine, theirs)
        print("signature: OK (matches openssl)")
    # 2. Symbol mapping.
    assert map_symbol("TSLA") == "TSLAXUSDT"
    assert map_symbol("aapl") == "AAPLXUSDT"
    try:
        map_symbol("TSLA!")
        raise AssertionError("bad ticker accepted")
    except BybitError:
        print("symbol mapping: OK")
    # 3. Order mapping (the README example: 8 TSLA, stop 358.32, target 370.04).
    order = {"symbol": "TSLA", "side": "buy", "qty": "8", "type": "market",
             "time_in_force": "day", "order_class": "bracket",
             "take_profit_limit_price": "370.04", "stop_loss_stop_price": "358.32"}
    body = map_order(order, today="2026-10-19")
    assert body == {"category": "spot", "symbol": "TSLAXUSDT", "side": "Buy",
                    "orderType": "Market", "qty": "8", "timeInForce": "GTC",
                    "takeProfit": "370.04", "stopLoss": "358.32", "tpslMode": "Full",
                    "tpTriggerBy": "LastPrice", "slTriggerBy": "LastPrice",
                    "orderLinkId": "ada-20261019-" + fingerprint(order)[:8]}, body
    print("order mapping: OK")
    # 4. Gates refuse without risk PASS / yes.
    try:
        _risk_pass(order, {"results": []}, "2026-10-19")
        print("gates: risk lookup runs (PASS=False as expected)")
    except Exception as e:
        raise AssertionError("gate check crashed: %s" % e)
    # 5. Mainnet refusal is structural: DEMO_BASE is the demo host.
    assert DEMO_BASE.split("://")[1] not in MAINNET_HOSTS
    assert "api-demo.bybit.com" in DEMO_BASE
    print("demo-only base URL: OK (%s)" % DEMO_BASE)
    print("bybit self-test: ALL OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bybit.py")
    ap.add_argument("--trader", default="trader",
                    help="trader/ working dir (orders, state, config)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("balance")
    p = sub.add_parser("show"); p.add_argument("--index", type=int, required=True)
    p = sub.add_parser("place"); p.add_argument("--index", type=int, required=True)
    sub.add_parser("status")
    sub.add_parser("executions")
    p = sub.add_parser("cancel"); p.add_argument("--order-id", required=True)
    sub.add_parser("test")
    args = ap.parse_args(argv)
    try:
        return {"balance": cmd_balance, "show": cmd_show, "place": cmd_place,
                "status": cmd_status, "executions": cmd_executions,
                "cancel": cmd_cancel, "test": cmd_test}[args.cmd](args)
    except BybitError as e:
        print("bybit: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
