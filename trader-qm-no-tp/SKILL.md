---
name: trader-qm-no-tp
description: Daniel's Quasimodo (QM) trading system — the QM reversal pattern with Daniel's "No TP" money management (trailing stop in 1R steps, fixed dollar risk), backtested on crypto 4h. Use when the user says "QM with No TP", "Daniel's QM system", "run the QM system", or asks for the backtested QM method with trailing stop. Do not use for the bare pattern alone — that is trader-qm.
---

# trader-qm-no-tp — Daniel's QM System (No TP)

## Overview

This is the complete trading system Daniel taught Ada on 2026-11-15: the
Quasimodo reversal pattern **plus** Daniel's money management — no fixed
target, only a trailing stop, and a fixed dollar risk per trade. The pattern
alone is not enough: plain QM on BTC 4h was only +1.76R; with Daniel's
money management it reached +11.68R. The money management is what makes
the system profitable.

Full pattern detail lives in `trader-qm`. This skill is the system: pattern
+ entry + No-TP management + where it was proven to work.

## The pattern (summary — see trader-qm for full detail)

Four swing points, in time order:

- **P1** — left shoulder: first low in a downtrend / first high in an uptrend.
- **P2** — retracement: a temporary high / low.
- **P3** — the "head": breaks P1 to sweep liquidity (Hunt/Sweep), making a
  Lower Low (LL) or Higher High (HH).
- **P4** — strong opposite move breaking P2 = Break of Structure (BOS/Choch).

**Bearish QM** (uptrend): H_1 → L_1 → H_2 > H_1 → sharp drop breaks L_1,
making L_2 < L_1. Confirmed iff H_2 > H_1 AND L_2 < L_1.

**Bullish QM** (downtrend): L_1 → H_1 → L_2 < L_1 → strong rise breaks H_1,
making H_2 > H_1. Confirmed iff L_2 < L_1 AND H_2 > H_1.

## Entry and stop

After confirmation, **never enter immediately**. Place a limit order:

- **Entry (QML):** exactly at the left-shoulder level (H_1 bearish, L_1
  bullish). For precision, use the last counter-trend candle before the main
  drop/rise in the left-shoulder area (Order Block) as the entry zone.
- **Stop loss:** bearish — slightly above the head (H_2 + Buffer); bullish —
  slightly below the head (L_2 − Buffer). Buffer used in backtests: 0.2%.
- **First touch only:** the QML level is valid the first time price returns
  to it. If already touched, delete the order.

## Money management — Daniel's "No TP" rule (the core of this system)

No fixed target. The full position stays open until the trailing stop is hit:

- **At 1R profit:** move the stop to the entry price (risk-free).
- **At 2R:** move the stop to the 1R level.
- **At 3R:** move the stop to the 2R level. At NR, the stop sits at (N−1)R.
- **Fixed dollar risk:** the loss on any stopped-out trade is a fixed dollar
  amount (backtests used $10). Position size = risk_dollars / stop distance,
  so a stop-out loses exactly that amount. Dollar P&L = R × risk_dollars.
- **Why it works:** the trailing stop lets the few big winners run while
  losers are capped at 1R. Win rate is low (~18–28%) but winners are much
  larger than losers.

An earlier variant (close half at 1R, stop to entry, TP 2R) gave
essentially the same result on BTC 4h (+11.57R vs +11.68R for No-TP), so
the trailing-stop version is the canonical rule.

## Where it works — backtested findings (2026-11-15)

Backtests: `~/workspace/trader-qm-backtest.py` (yfinance), No-TP rule,
$10 fixed risk, 2 years of data (15m only 60 days — Yahoo's cap).
Backtests exclude fees/slippage and are history, not predictions. Full
numbers: `~/workspace/trader-qm-backtest-summary-2026-11-15.md`.

### 4h is the sweet spot

Top 10 coins by market cap, 4h, 2 years, No-TP — **all 10 profitable**:
307 trades, **+$1,569.90 total, avg +$5.11/trade**.

| Coin | Trades | Total | Avg / trade | Max R |
|---|---|---|---|---|
| ADA | 25 | +$265.00 | **+$10.60** | 10.94R |
| DOGE | 29 | +$282.40 | **+$9.74** | 23.08R |
| LINK | 36 | +$279.00 | **+$7.75** | 9.74R |
| SOL | 37 | +$183.50 | **+$4.96** | 6.98R |
| AVAX | 30 | +$135.00 | +$4.50 | 12.72R |
| TRX | 18 | +$76.70 | +$4.26 | 3.62R |
| ETH | 39 | +$128.90 | +$3.31 | 7.30R |
| XRP | 29 | +$90.50 | +$3.12 | 9.65R |
| BTC | 39 | +$116.80 | +$2.99 | 5.98R |
| BNB | 25 | +$12.10 | +$0.48 | 6.40R |

**Best combination: 4h, No-TP, on ADA, LINK, SOL, DOGE.**

### Other timeframes (same four coins, avg $/trade)

| Coin | 15m (60d) | 1h | 4h | 8h | 12h |
|---|---|---|---|---|---|
| ADA | −$2.00 | +$2.89 | **+$10.60** | +$15.38 | −$0.04 |
| LINK | +$0.19 | +$2.27 | **+$7.75** | +$3.55 | +$0.91 |
| SOL | −$2.86 | +$0.60 | **+$4.96** | $0.00 | −$0.50 |
| DOGE | −$1.02 | +$0.73 | **+$9.74** | +$3.28 | −$0.72 |

- **15m loses** on everything (BTC −$75.40, ETH −$8.50, SOL −$117.40
  over 60 days). Too noisy.
- **1h is profitable but weak** (ADA +$2.89/trade on 139 trades).
- **8h** (built from 1h candles — Yahoo has no native 8h/12h): ADA best
  per trade (+$15.38) but on only 16 trades; SOL breakeven. Sample too
  small to trust.
- **12h is ~breakeven** on 5–11 trades per coin — not reliable.
- **Daily pays more per trade but trades too rarely** (BTC 6 trades in
  2 years, +$50.00, avg +$8.33; SOL 4 trades, +$30.00).

### Honest caveats

- Win rate is low (~18–28%). The edge is winners much bigger than losers.
- DOGE's total is lifted by a single 23R trade; without it DOGE is less
  impressive.
- Live Yahoo data drifts slightly between runs (e.g. LINK 4h +$7.75 then
  +$8.03); treat small differences as window shift, not error.
- **QM loses on TSLA stock** (1h −6.54R/−5.78R, daily −3.00R). This
  system was proven on crypto, not on stocks.
- Backtest ≠ live: no fees, no slippage, and past results do not predict
  the future. Demo-test first (e.g. the Bybit demo) with small risk before
  real money.

## Filters (avoid traps)

1. **FVG/Imbalance:** the BOS move (P3→P4) must have large, strong candles
   with a price gap (FVG). If the break happens with weak/ranging candles,
   the pattern is invalid.
2. **Risk:Reward:** if the entry-to-stop distance makes the reward:risk to
   TP1 less than 1:2, cancel the trade.
3. **First Touch:** the QML level is valid only the first time price returns
   to it. If already touched, delete the order.

## Rules

- Never enter on confirmation alone — always wait for price to return to the
  QML level (limit order).
- Long and short both allowed (unlike the ORB skill, which is long-only).
- 4h crypto only, until a new backtest proves another market/timeframe.
  15m is excluded — it loses. TSLA/stocks are excluded — QM loses there.
- A signal is information, not an order, and not a promise. Nothing here
  promises winning trades or money.
- Paper trading by default. Nothing places an order except trader-broker,
  and only with Daniel's explicit yes per order.
- No options, margin, short selling or leverage unless the config allows it
  and Daniel confirms.
- Demo-test first: the system is backtested, not live-proven. Small risk
  until the live loop proves itself.
