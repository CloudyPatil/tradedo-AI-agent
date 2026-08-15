# E:\tradedo\app\backend\agent\manual_executor.py

"""
MANUAL TRADING EXECUTOR
Handles manual buy/sell/hold operations.
Separate portfolio from autonomous agent.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import Dict, Optional, List
from datetime import datetime

from database.db import (
    get_manual_state, update_manual_state,
    create_manual_order, get_manual_order, get_manual_orders,
    update_manual_order, cancel_manual_order,
    create_manual_trade, get_manual_trade, get_manual_trades,
    update_manual_trade, close_manual_trade,
)
from data_pipeline.price_provider import get_price_provider
from agent.sectors import get_sector

logger = logging.getLogger("tradedo.manual")


# ═══════════════════════════════════════════════════════════════
#   ORDER VALIDATION
# ═══════════════════════════════════════════════════════════════

def validate_order(order_data: Dict) -> Dict:
    """Validate order before placement."""
    errors = []
    
    # Required fields
    required = ["symbol", "order_type", "side", "quantity"]
    for field in required:
        if not order_data.get(field):
            errors.append(f"{field} is required")
    
    # Order type validation
    valid_types = ["MARKET", "LIMIT", "SL", "SL_MARKET"]
    if order_data.get("order_type") not in valid_types:
        errors.append(f"Invalid order_type. Must be one of: {valid_types}")
    
    # Side validation
    if order_data.get("side") not in ["BUY", "SELL"]:
        errors.append("side must be BUY or SELL")
    
    # Quantity validation
    qty = order_data.get("quantity", 0)
    if qty <= 0:
        errors.append("Quantity must be positive")
    
    # Price validation for limit orders
    if order_data.get("order_type") == "LIMIT" and not order_data.get("price"):
        errors.append("Price required for LIMIT order")
    
    # SL validation
    if order_data.get("order_type") in ["SL", "SL_MARKET"] and not order_data.get("trigger_price"):
        errors.append("Trigger price required for SL orders")
    
    # Bracket order validation
    if order_data.get("is_bracket"):
        if not order_data.get("stop_loss"):
            errors.append("Stop loss required for bracket order")
        if not order_data.get("target"):
            errors.append("Target required for bracket order")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


# ═══════════════════════════════════════════════════════════════
#   PLACE ORDER
# ═══════════════════════════════════════════════════════════════

def place_manual_order(order_data: Dict) -> Dict:
    """
    Place a manual order.
    Returns result with order_id or error.
    """
    logger.info(f"📝 Manual order: {order_data.get('side')} {order_data.get('quantity')} {order_data.get('symbol')}")
    
    # 1. Validate
    validation = validate_order(order_data)
    if not validation["valid"]:
        return {
            "success": False,
            "errors": validation["errors"],
        }
    
    # 2. Get current price
    provider = get_price_provider()
    price_result = provider.get_ltp(order_data["symbol"])
    
    if not price_result:
        return {
            "success": False,
            "errors": ["Could not fetch current price"],
        }
    
    current_price = price_result["last_price"]
    
    # 3. Determine execution price
    order_type = order_data["order_type"]
    execution_price = None
    execute_immediately = False
    
    if order_type == "MARKET":
        execution_price = current_price
        execute_immediately = True
    elif order_type == "LIMIT":
        limit_price = order_data["price"]
        # Check if limit already meets market
        if order_data["side"] == "BUY" and current_price <= limit_price:
            execution_price = current_price
            execute_immediately = True
        elif order_data["side"] == "SELL" and current_price >= limit_price:
            execution_price = current_price
            execute_immediately = True
        # else: order remains pending
    
    # 4. Check capital for BUY orders
    if order_data["side"] == "BUY" and execute_immediately:
        required_capital = execution_price * order_data["quantity"]
        state = get_manual_state()
        available = state["capital"] - state["current_exposure"]
        
        if required_capital > available:
            return {
                "success": False,
                "errors": [
                    f"Insufficient capital. Required: ₹{required_capital:.2f}, "
                    f"Available: ₹{available:.2f}"
                ],
            }
    
    # 5. Create order
    order_id = create_manual_order(order_data)
    logger.info(f"  → Order created: #{order_id}")
    
    # 6. Execute if market order or limit met
    if execute_immediately:
        return execute_order(order_id, execution_price)
    
    return {
        "success": True,
        "order_id": order_id,
        "status": "PENDING",
        "message": f"{order_type} order placed. Waiting for trigger price.",
    }


def execute_order(order_id: int, execution_price: float) -> Dict:
    """Execute an order (create trade)."""
    order = get_manual_order(order_id)
    if not order:
        return {"success": False, "errors": ["Order not found"]}
    
    if order["status"] != "PENDING":
        return {"success": False, "errors": [f"Order already {order['status']}"]}
    
    # Update order as filled
    update_manual_order(
        order_id,
        status="FILLED",
        filled_quantity=order["quantity"],
        avg_fill_price=execution_price,
        filled_at=datetime.now().isoformat(),
    )
    
    # For BUY: create new trade
    if order["side"] == "BUY":
        investment = execution_price * order["quantity"]
        
        trade_id = create_manual_trade({
            "symbol": order["symbol"],
            "direction": "LONG",
            "sector": get_sector(order["symbol"]),
            "entry_order_id": order_id,
            "entry_price": execution_price,
            "stop_loss": order.get("stop_loss"),
            "target": order.get("target"),
            "quantity": order["quantity"],
            "investment": investment,
            "notes": order.get("notes"),
        })
        
        # Update capital
        state = get_manual_state()
        update_manual_state(
            current_exposure=state["current_exposure"] + investment,
            open_positions=state["open_positions"] + 1,
            trades_today=state["trades_today"] + 1,
        )
        
        logger.info(f"  ✅ BUY executed: {order['quantity']} shares @ ₹{execution_price}")
        
        return {
            "success": True,
            "order_id": order_id,
            "trade_id": trade_id,
            "status": "FILLED",
            "execution_price": execution_price,
            "investment": investment,
            "message": f"BUY order filled at ₹{execution_price}",
        }
    
    # For SELL: close existing trade(s) FIFO
    else:
        return close_position_by_symbol(order["symbol"], order["quantity"], execution_price, order_id)


def close_position_by_symbol(symbol: str, quantity: int, exit_price: float, order_id: int) -> Dict:
    """Close open positions FIFO for a symbol."""
    # Get open trades for this symbol
    open_trades = [t for t in get_manual_trades("OPEN") if t["symbol"] == symbol]
    
    if not open_trades:
        return {
            "success": False,
            "errors": [f"No open positions for {symbol}"],
        }
    
    # Sort by entry_time (FIFO)
    open_trades.sort(key=lambda t: t["entry_time"])
    
    remaining_qty = quantity
    closed_trades = []
    total_pnl = 0
    total_released_capital = 0
    
    for trade in open_trades:
        if remaining_qty <= 0:
            break
        
        if remaining_qty >= trade["quantity"]:
            # Close entire trade
            pnl = close_manual_trade(trade["id"], exit_price, "MANUAL_SELL")
            total_pnl += pnl
            total_released_capital += trade["investment"]
            remaining_qty -= trade["quantity"]
            closed_trades.append(trade["id"])
        else:
            # Partial close - split the trade
            partial_qty = remaining_qty
            
            is_long = trade["direction"] == "LONG"
            entry = trade["entry_price"]
            
            if is_long:
                partial_pnl = round((exit_price - entry) * partial_qty, 2)
            else:
                partial_pnl = round((entry - exit_price) * partial_qty, 2)
            
            total_pnl += partial_pnl
            
            # Reduce trade quantity
            new_qty = trade["quantity"] - partial_qty
            new_investment = new_qty * entry
            released = trade["investment"] - new_investment
            total_released_capital += released
            
            update_manual_trade(
                trade["id"],
                quantity=new_qty,
                investment=new_investment,
            )
            
            remaining_qty = 0
    
    # Update capital
    state = get_manual_state()
    positions_closed = len(closed_trades)
    
    is_profit = total_pnl > 0
    wins_delta = 1 if is_profit else 0
    losses_delta = 1 if total_pnl < 0 else 0
    
    update_manual_state(
        capital=state["capital"] + total_pnl,
        current_exposure=state["current_exposure"] - total_released_capital,
        open_positions=max(0, state["open_positions"] - positions_closed),
        total_realized_pnl=state["total_realized_pnl"] + total_pnl,
        pnl_today=state["pnl_today"] + total_pnl,
        wins_today=state["wins_today"] + wins_delta,
        losses_today=state["losses_today"] + losses_delta,
    )
    
    logger.info(f"  ✅ SELL executed: {quantity} shares @ ₹{exit_price}, P&L: ₹{total_pnl}")
    
    return {
        "success": True,
        "order_id": order_id,
        "closed_trades": closed_trades,
        "status": "FILLED",
        "execution_price": exit_price,
        "total_pnl": total_pnl,
        "message": f"SELL order filled at ₹{exit_price}, P&L: ₹{total_pnl}",
    }


# ═══════════════════════════════════════════════════════════════
#   PENDING ORDER MONITORING
# ═══════════════════════════════════════════════════════════════

def check_pending_orders() -> Dict:
    """Check all pending orders and execute if conditions met."""
    pending = get_manual_orders(status="PENDING")
    if not pending:
        return {"checked": 0, "executed": 0}
    
    logger.info(f"🔍 Checking {len(pending)} pending orders...")
    
    provider = get_price_provider()
    executed = []
    
    for order in pending:
        # Get current price
        price_result = provider.get_ltp(order["symbol"])
        if not price_result:
            continue
        
        current_price = price_result["last_price"]
        should_execute = False
        exec_price = None
        
        # Check trigger based on order type
        order_type = order["order_type"]
        side = order["side"]
        
        if order_type == "LIMIT":
            limit_price = order["price"]
            if side == "BUY" and current_price <= limit_price:
                should_execute = True
                exec_price = current_price
            elif side == "SELL" and current_price >= limit_price:
                should_execute = True
                exec_price = current_price
        
        elif order_type == "SL":
            trigger = order["trigger_price"]
            limit = order["price"]
            
            if side == "BUY" and current_price >= trigger:
                if current_price <= limit:
                    should_execute = True
                    exec_price = current_price
            elif side == "SELL" and current_price <= trigger:
                if current_price >= limit:
                    should_execute = True
                    exec_price = current_price
        
        elif order_type == "SL_MARKET":
            trigger = order["trigger_price"]
            
            if side == "BUY" and current_price >= trigger:
                should_execute = True
                exec_price = current_price
            elif side == "SELL" and current_price <= trigger:
                should_execute = True
                exec_price = current_price
        
        if should_execute:
            result = execute_order(order["id"], exec_price)
            if result.get("success"):
                executed.append(order["id"])
    
    return {
        "checked": len(pending),
        "executed": len(executed),
        "executed_ids": executed,
    }


# ═══════════════════════════════════════════════════════════════
#   POSITION UPDATES (Live P&L)
# ═══════════════════════════════════════════════════════════════

def update_position_prices():
    """Update current prices and unrealized P&L for open positions."""
    open_trades = get_manual_trades("OPEN")
    if not open_trades:
        return {"updated": 0}
    
    provider = get_price_provider()
    symbols = list(set(t["symbol"] for t in open_trades))
    prices = provider.get_multiple_ltp(symbols)
    
    updated_count = 0
    total_unrealized = 0
    
    for trade in open_trades:
        symbol = trade["symbol"]
        if symbol not in prices:
            continue
        
        current_price = prices[symbol]["last_price"]
        
        # Calculate unrealized P&L
        is_long = trade["direction"] == "LONG"
        entry = trade["entry_price"]
        qty = trade["quantity"]
        
        if is_long:
            unrealized = round((current_price - entry) * qty, 2)
        else:
            unrealized = round((entry - current_price) * qty, 2)
        
        # Track highest/lowest
        highest = trade.get("highest_price") or entry
        lowest = trade.get("lowest_price") or entry
        
        updates = {
            "current_price": current_price,
            "unrealized_pnl": unrealized,
        }
        
        if current_price > highest:
            updates["highest_price"] = current_price
        if current_price < lowest:
            updates["lowest_price"] = current_price
        
        update_manual_trade(trade["id"], **updates)
        
        total_unrealized += unrealized
        updated_count += 1
    
    # Update total unrealized in state
    update_manual_state(total_unrealized_pnl=total_unrealized)
    
    return {"updated": updated_count, "total_unrealized_pnl": total_unrealized}


# ═══════════════════════════════════════════════════════════════
#   HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_manual_account_summary() -> Dict:
    """Get complete manual account summary."""
    state = get_manual_state()
    open_trades = get_manual_trades("OPEN")
    pending_orders = get_manual_orders("PENDING")
    
    total_investment = sum(t["investment"] for t in open_trades)
    total_unrealized = sum((t.get("unrealized_pnl") or 0) for t in open_trades)
    total_current = total_investment + total_unrealized
    
    return {
        "capital":          state.get("capital", 0),
        "starting_capital": state.get("starting_capital", 100000),
        "available":        state.get("capital", 0) - state.get("current_exposure", 0),
        "deployed":         state.get("current_exposure", 0),
        "total_realized_pnl": state.get("total_realized_pnl", 0),
        "total_unrealized_pnl": total_unrealized,
        "total_pnl":        state.get("total_realized_pnl", 0) + total_unrealized,
        "open_positions":   len(open_trades),
        "pending_orders":   len(pending_orders),
        "todays_stats": {
            "trades":       state.get("trades_today", 0),
            "wins":         state.get("wins_today", 0),
            "losses":       state.get("losses_today", 0),
            "pnl":          state.get("pnl_today", 0),
        },
    }


def reset_manual_capital(new_capital: float = 100000) -> Dict:
    """Reset manual account capital."""
    update_manual_state(
        capital=new_capital,
        starting_capital=new_capital,
        current_exposure=0,
        open_positions=0,
        total_realized_pnl=0,
        total_unrealized_pnl=0,
        trades_today=0,
        wins_today=0,
        losses_today=0,
        pnl_today=0,
    )
    logger.info(f"💰 Manual capital reset to ₹{new_capital:,}")
    return {"success": True, "capital": new_capital}


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("MANUAL EXECUTOR TEST")
    print("="*60)
    
    summary = get_manual_account_summary()
    print(f"\n💼 Account Summary:")
    for k, v in summary.items():
        print(f"   {k}: {v}")