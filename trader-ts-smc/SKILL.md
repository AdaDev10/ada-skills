---
name: trader-ts-smc
description: TS-SMC (Time-Scaled Smart Money) V1 — Daniel's own Smart Money method ("Smart Money Danny"). HTF liquidity zone (POI) + MTF CHoCH confirmation + Fib entries (0.5/0.618) + BOS trailing stop + progressive halving exits. Three time-scaled setups (daily, 4H, 1H structures), RR2 filter, fixed-dollar risk. Backtested on top-10 coins.
---

# TS-SMC (Time-Scaled Smart Money) V1

Daniel's own Smart Money method, taught by Daniel ("دنی" / Danny) 2026-11-15.
Rule-based If-Then system. Spot + Long/Short futures. Works on crypto.

## The six steps

### 1. Timeframe matrix (lock first)
Three time-scaled setups — same rules, different structure scale:
- **Setup 1 (daily structure):** HTF = 1D, MTF = 4H, LTF = 1H.
- **Setup 2 (4H structure):** HTF = 4H, MTF = 1H, LTF = 15m.
- **Setup 3 (risky, 1H structure):** HTF = 1H, MTF = 15m, LTF = 5m.
Setup 3 is the best performer in backtests (see below).

### 2. HTF POI + N_Approach
- Find a major HTF reversal point with strong past reactions.
- Zone = the strong high-volume candle that was the origin of the push
  (up for Long/Spot, down for Short), marked from highest wick to lowest
  wick. The zone must be unmitigated.
- When price touches the zone, go to MTF and count the candles of the last
  wave that brought price from the last major high/low before the zone to
  the touch → **N_Approach**.

### 3. CHoCH validation
- Zone invalid if an HTF candle closes fully behind the POI (whole scenario
  cancelled).
- Long: price must break the last internal Lower High upward.
  Short: break the last internal Higher Low downward.
- The break must be in MTF and the candle must **CLOSE beyond the level**.
  **CORRECTED by Daniel (2026-11-15): the full-body 70% rule is DROPPED —
  a candle just CLOSING beyond the level counts as CHoCH; wick crossing
  alone still does not count (only the close matters).**

### 4. Fib + execution (LTF)
- After the MTF CHoCH close, go to LTF, wait for the initial wave to finish
  (local high/low with ≥2 corrective candles against the new move), draw
  Fib retracement on the whole CHoCH wave.
- Fib 0.0 = origin inside the zone (lowest low recorded in buy / highest
  high in sell). Fib 1.0 = end of the wave formed after the CHoCH break.
- **R:R filter: if distance 0.5→TP1 < 2.0 × distance 0.5→0.0 (R:R < 2),
  cancel the trade.** (RR2 is the best filter in backtests; RR1.5 is close,
  RR1 is clearly worse — see Backtests.)
- **Entry:** 50% of volume as limit at 0.5 Fib, 50% at 0.618 Fib.
- **Initial SL:** exactly behind 0.0 Fib (+ 2 pips or 0.1% buffer).
- **Cancel condition:** if price continues without touching 0.5 and breaks
  1.0 (BOS before entry), delete the placed orders immediately.
- **Added rule (Daniel 2026-11-15):** if only the 0.5 entry filled and price
  never reached 0.618, but the chart went to TP1 or formed a BOS and SL
  moved to risk-free (breakeven), **CANCEL the pending 0.618 limit order**.

### 5. Dynamic trailing (LTF BOS)
- 1st BOS (= break of 1.0 Fib level) → move SL of the whole trade to
  average entry (risk-free).
- 2nd BOS and later → move SL to exactly behind the **origin candle**
  (below the low of the origin candle in buy / above the high in sell).
  Origin candle = the lowest/highest candle in the low/high of the
  correction of the last wave that pushed price and caused the previous BOS.
- Repeat for each new BOS. The trailing stop is the main profit engine.

### 6. Exits — TPs + two-thirds rule + halving
- TP1, TP2…TPn = nearest opposing HTF liquidity zones in the direction
  of movement.
- **Two-thirds momentum rule:** N_Return = MTF candles counted from entry
  activation until price reaches TP1. Max_Candles = Round(2/3 × N_Approach).
  - Scenario A (fast, N_Return ≤ Max_Candles): close 50% at TP1, keep the
    rest for TP2, trail SL; re-apply the two-thirds rule from TP1 to TP2.
  - Scenario B (slow/zigzag, N_Return > Max_Candles): close 100% of the
    remaining volume at the next target touched.
- **Halving rule (Daniel 2026-11-16, for RR2):** at EVERY TP level close
  50% of the currently open quantity — 50% at TP1, 25% of the original at
  TP2, 12.5% at TP3, and keep halving. The trailing stop still protects
  the runner; the trade ends at the stop or at max hold. In RR2 backtests
  halving beats the two-thirds rule (+91.05R vs +86.55R combined).

### Risk — fixed dollars per trade
- Risk per trade is a FIXED dollar number; position size = risk / stop
  distance, so a stopped-out trade loses exactly that amount.
- Backtests used $10 risk. **Low-risk live plan (Daniel 2026-11-16): $100
  capital, $2 risk per trade.** 50 consecutive losses × $2 = $100 = wiped
  out — but at ~46% win rate the probability of 50 straight losses is
  ~1e-14, effectively zero.

## Chart example (Daniel's ETH, 2026-11-16)
ETH/USDT 4h short — Zone ~2,780, Fib 0.5/0.618 at 2,572/2,612, entries
~2,530/2,600, trailing stops SL1–4, BOS marks. R:R was RR1 (not 2) and the
trade HIT TP (TP zone ~2,360–2,390). Daniel's reasoning: the rise was sharp
(small N_Approach → small Max_Candles) and the fall was very slow (large
N_Return > Max) → Scenario B → close 100% at the FIRST TP.

## Backtests (script: ~/workspace/trader-sm-backtest.py, $10 fixed risk)
- **R:R filter comparison (top 10, all setups):** RR1: 343 trades +16.80R;
  RR1.5: 252 trades +78.13R; **RR2: 224 trades +86.55R (best)**.
- **RR2 + halving (best config):** Setup 1 (2y): 86 trades +21.89R;
  Setup 2 (60d): 40 trades +20.47R; Setup 3 (60d): 100 trades +48.69R;
  **combined 226 trades +91.05R (+$910.50), win rate 40.0% (88/220)**.
- **Setup 3 is the best setup** (avg +0.45–0.50R/trade vs +0.22R Setup 1,
  +0.15–0.42R Setup 2). Best coins: SOL (+15.98R Setup 3), XRP, AVAX, TRX.
  ADA is positive only in Setup 3 (+5.19R); it loses in Setup 1 (−9.35R)
  and Setup 2 (−3.81R). DOGE is the only loser in Setup 3 (−4.35R) but
  the best in Setup 2 (+8.24R).
- **Win rate ~40% but profitable** — winners are much bigger than losers
  (trailing stop keeps big winners, losses capped ~1R, many losses are
  breakeven thanks to the risk-free rule). Classic trend-following profile.
  Best win rates: TRX Setup 3 85.7%, LINK Setup 2 71.4%, AVAX Setup 1 70%.
- **Low-risk plan, past 30 days ($2 risk, RR2 + halving):** Setup 1: 0
  trades (30 days is too short for a daily structure — needs 90d+ to find
  zones); Setup 2: 13 trades +2.72R (+$5.44); Setup 3: 59 trades +23.41R
  (+$46.82). Combined 72 trades +26.13R (+$52.26) on $100 capital →
  **$152.26 (+52.3% in one month)**. Long 30 trades +8.15R, Short 42
  trades +17.98R. Win rate 45.8% (33/72).
- Caveats: backtest ≠ live (no fees/slippage — fees matter at $2 risk);
  Setup 2/3 windows are only 60 days (Yahoo 5m/15m cap); Setup 1 30-day
  window gives zero zones. Demo-test first.

## Rules
- Crypto only, 4h is NOT the sweet spot here — Setup 3 (1H/15m/5m) is.
- RR2 filter + halving exits + fixed-dollar risk.
- Demo-test first (e.g. Bybit demo) with small risk before real money.
- Nothing trades without Daniel's explicit yes per order.
- Backtest script: ~/workspace/trader-sm-backtest.py
  (--setup 1|2|3, --min-rr, --exit-mode twothirds|halving, --risk-dollars).
  Summary: ~/workspace/trader-sm-backtest-summary-2026-11-15.md
