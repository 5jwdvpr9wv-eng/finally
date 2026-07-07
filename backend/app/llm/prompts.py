"""System prompt and chat message construction for the LLM."""

from __future__ import annotations

from app.db.models import ChatMessage

from .models import PortfolioContext

SYSTEM_PROMPT = """You are FinAlly, an AI trading assistant embedded in a simulated trading \
terminal. The user trades with virtual money only — there are no real financial \
consequences.

Your job:
- Analyze portfolio composition, risk concentration, and P&L when asked or relevant.
- Suggest trades with clear, data-driven reasoning.
- Execute trades when the user asks for one or agrees to a suggestion.
- Manage the watchlist proactively (add tickers the user is interested in, remove ones \
they no longer want tracked).
- Be concise. Prefer numbers and specifics over hedging or filler.

Trades and watchlist changes you return are auto-executed immediately with no further \
confirmation from the user, so only include a trade or watchlist change if the user has \
actually asked for it or clearly agreed to it — do not include ones you are merely \
proposing for consideration.

Trade rules: `ticker` is the stock symbol, `side` is "buy" or "sell", `quantity` is a \
positive number (fractional shares are allowed). Trades still go through normal \
validation (sufficient cash for buys, sufficient shares for sells) — if one fails, you \
will be told so you can inform the user.

Watchlist rules: `action` is "add" or "remove".

Always respond with the message you want to show the user plus any trades or watchlist \
changes to execute."""


def format_portfolio_context(portfolio_context: PortfolioContext) -> str:
    """Render portfolio state as plain text for the system prompt."""
    lines = [
        "Current portfolio:",
        f"- Cash: ${portfolio_context.cash:,.2f}",
        f"- Total portfolio value: ${portfolio_context.total_value:,.2f}",
    ]

    if portfolio_context.positions:
        lines.append("- Positions:")
        for pos in portfolio_context.positions:
            lines.append(
                f"  - {pos.ticker}: {pos.quantity:g} shares @ avg cost "
                f"${pos.avg_cost:,.2f}, current price ${pos.current_price:,.2f}, "
                f"unrealized P&L ${pos.unrealized_pnl:,.2f} "
                f"({pos.unrealized_pnl_percent:+.2f}%)"
            )
    else:
        lines.append("- Positions: none")

    if portfolio_context.watchlist:
        lines.append("- Watchlist (live prices):")
        for item in portfolio_context.watchlist:
            price = f"${item.price:,.2f}" if item.price is not None else "unavailable"
            lines.append(f"  - {item.ticker}: {price}")
    else:
        lines.append("- Watchlist: empty")

    return "\n".join(lines)


def build_messages(
    portfolio_context: PortfolioContext,
    history: list[ChatMessage],
    user_message: str,
) -> list[dict]:
    """Build the full message list for the LLM: system + context, history, new message."""
    system_content = f"{SYSTEM_PROMPT}\n\n{format_portfolio_context(portfolio_context)}"
    messages = [{"role": "system", "content": system_content}]

    for msg in history[-20:]:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})
    return messages
