# INV - Algorithmic Trading Bot for Binance Futures

**A rule-based trend-following bot for ETHUSDT perpetual futures, with a backtested strategy engine, a live Binance execution layer, and Telegram trade notifications.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Exchange](https://img.shields.io/badge/exchange-Binance%20Futures-yellow)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

> ⚠️ **This bot trades real derivatives with real capital.** It has no independent risk review beyond the author's own backtests. Nothing here is financial advice, and running it against a live account can result in the loss of the entire allocated balance. See [Risk and limitations](#risk-and-limitations) before using it with anything other than testnet funds.

---

## What it does

The bot trades Ethereum futures (originally on Binance, adaptable to other perpetual/futures venues) using a discretionary technical-analysis strategy made systematic: it looks for trend reversals at the edges of a volatility-based price channel, confirms them with the trend's slope, and manages the exit in stages rather than all at once. The same codebase runs in two modes:

- **Backtest / research mode** — the strategy runs against historical OHLCV data pulled from Alpha Vantage, so entry/exit logic can be tuned before any capital is at risk.
- **Live mode** — the same signal logic runs against real-time data streamed from Binance over WebSockets, and the bot places and closes orders on the account via signed REST calls.

A companion Telegram bot mirrors every open/close event so positions can be monitored without watching the exchange UI.

## Strategy logic

The strategy is a composite of four classical technical-analysis building blocks, evaluated on each candle:

| Component | What it measures | Role in the strategy |
|---|---|---|
| **Price channel** (upper/lower bounds around a moving average) | Where the current price sits relative to its recent volatility band | Entries are only considered near the channel edges: **LONG** candidates form near the lower bound, **SHORT** candidates near the upper bound |
| **Local minima / maxima** | Confirmed swing points (a price point that is lower/higher than both its neighbours *and* the prior swing point) | A confirmed local minimum is the trigger condition for a long setup; a local maximum, for a short setup |
| **Trend slope** | The angle of the price trend line at the swing point | A long requires slope below −20°, a short requires slope above +20°; anything flatter is treated as a range (flat) and skipped, to avoid trading chop |
| **Average True Range (ATR)**, Wilder's method | Recent volatility, via the exponential moving average of the true range | Used alongside the channel to size the stop distance |

An entry only fires when a confirmed swing point, the channel position, and the slope condition all agree — a simple form of multi-indicator confirmation meant to reduce false breakouts.

**Exit management** is staged rather than a single take-profit: a configurable ladder of price-move thresholds closes a portion of the position at each level (e.g. close 1 contract after a move of 20 points, another after 40, 2 more after 60, and so on), with a hard stop-loss at roughly 1% adverse move from the entry price. This scales out of winners incrementally instead of exiting the full position at one target.

## Repository layout

```
.
├── data_gathering.py   # pulls historical OHLCV candles (Alpha Vantage) for backtesting
├── strategy_test.py    # backtest engine: channel/slope/ATR signal logic run over historical data
├── strategy_main.py    # live trading loop: runs the same signal logic against real-time data
├── binance_api.py      # Binance REST/WebSocket client: market data, order placement, position queries
├── futures_sign.py     # HMAC-SHA256 request signing for Binance's signed (USER_DATA) endpoints
├── tg_bot_notif.py      # Telegram bot: pushes a message on every position open/close
├── cred.py             # exchange and data-provider credentials — see Credentials below
├── requirements.txt
├── LICENSE             # MIT
└── README.md
```

<!-- TODO: confirm this mapping against the current file contents — file names were renamed at some point after the accompanying writeup was drafted (e.g. sign.py → futures_sign.py, data_picking.py → data_gathering.py, bot_market_data.py appears to have been folded into binance_api.py), and strategy_main.py vs strategy_test.py's exact split (test-contour vs production-contour logic) should be checked against the actual code before publishing. -->

## How the pieces fit together

1. `data_gathering.py` fetches historical 5–30 minute OHLCV candles for the target symbol from Alpha Vantage and loads them into a pandas DataFrame (`timestamp, open, high, low, close, volume`).
2. `strategy_test.py` computes, per candle, the ATR, the trend slope, the channel bounds, and the local min/max flags, then simulates entries and exits against that history to evaluate the strategy before any live capital is used.
3. `futures_sign.py` implements Binance's signing scheme: it builds the query string, computes an HMAC-SHA256 signature over it using the account's API secret, and attaches it to every request that hits a `USER_DATA` (signed) endpoint — as required for order placement, balance queries, and position queries.
4. `binance_api.py` wraps the exchange interaction: opening a `ThreadedWebsocketManager` connection for real-time candle/account data, and issuing signed `POST` requests (e.g. `/fapi/v1/batchOrders`) to open and close positions.
5. `strategy_main.py` runs the live loop: it feeds real-time candles into the same signal logic validated in step 2, and calls into `binance_api.py` to act on signals.
6. `tg_bot_notif.py` listens for open/close events and sends a message to a configured Telegram chat, so trade activity can be monitored remotely.

## Data

| Purpose | Source | Notes |
|---|---|---|
| Historical candles for backtesting | [Alpha Vantage](https://www.alphavantage.co/) | Free tier available under student status (no documentation required to claim it, per Alpha Vantage's own signup flow at the time of writing) |
| Real-time candles and account data for live trading | Binance Futures API / WebSockets | Requires an API key and secret with futures trading permission |

## Credentials

The bot needs two sets of credentials: an Alpha Vantage API key (for backtesting data) and a Binance API key/secret pair with futures permissions (for live trading).

**Do not commit real credentials to this repository.** The accompanying project writeup shows keys written directly as variables inside the data-fetching and signing modules — that pattern is convenient for a local experiment but unsafe for anything checked into version control, public or private. Before running this yourself:

- Confirm `cred.py` (or wherever keys are read from) is listed in `.gitignore` and was never committed with real values. If a real key has already been pushed to this repository's history at any point, treat it as compromised — rotate it on Binance / Alpha Vantage even after deleting the file, since git history retains old commits.
- Prefer environment variables or a local `.env` file (excluded via `.gitignore`) over hardcoding keys in a tracked `.py` file.
- On Binance, scope the API key to **futures trading only**, disable withdrawal permissions, and restrict it to a fixed IP if the bot runs from a static address.

<!-- TODO: verify .gitignore currently excludes cred.py, and check whether any historical commit contains a real (not placeholder) API key or secret. -->

## Running it

```bash
git clone https://github.com/Kira-Knife/INV.git
cd INV
pip install -r requirements.txt
```

Backtest against historical data:
```bash
python strategy_test.py
```

Run live against Binance Futures (testnet first — see below):
```bash
python strategy_main.py
```

Binance exposes a separate testnet endpoint for exactly this purpose; point the client at it before pointing it at production:
- Production: `https://fapi.binance.com`
- Testnet: `https://testnet.binancefuture.com`

<!-- TODO: confirm strategy_main.py currently exposes a flag/config value to switch between these, or whether the endpoint is hardcoded and needs a manual edit. -->

## Deployment

The bot is designed to run continuously rather than on demand, since it evaluates each new candle as it closes. The originally planned production setup:

- A Ubuntu VM (Yandex Cloud Compute Cloud, or any always-on host)
- A ClickHouse or PostgreSQL instance for persisting candle data and trade history
- The bot and the Telegram notifier running as long-lived processes on the VM

<!-- TODO: confirm whether this cloud deployment was actually carried out, or whether it remains a planned/future step — the source documentation describes it as the intended next stage rather than a completed one. -->

## Risk and limitations

- **This is not investment advice, and the strategy has not been independently audited.** Backtested performance on historical ETHUSDT data does not guarantee similar results going forward, especially across different volatility regimes.
- The channel/slope/ATR logic is a rules-based heuristic, not a statistically fitted model — thresholds (the ±20° slope cutoff, the 1% stop, the profit-ladder levels) were chosen by the author rather than optimised against out-of-sample data.
- Two extensions were planned but not completed at the time of the accompanying writeup: an ARIMA forecasting layer and an LSTM price-prediction model, both intended to complement the rule-based signals rather than replace them.
<!-- TODO: confirm current status of the ARIMA/LSTM extensions — the source document marks both "in development" as of 2022. -->
- The bot depends on a live WebSocket connection and the exchange's API availability; it has no documented behaviour for reconnect handling, partial fills, or exchange downtime beyond what's described above.
- Tested primarily on ETHUSDT perpetual futures; using it for other pairs or asset classes would need the channel/slope thresholds re-tuned.

## References

Wilder, J. W. Jr. (1978). *New Concepts in Technical Trading Systems.* Trend Research.

## Author

**Polina Lanina** ([@Kira-Knife](https://github.com/Kira-Knife))

Built as a personal project in 2022. Licensed under MIT.
