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
from agent.charges_calculator import ChargesCalculator
from agent.leverage_manager import LeverageManager

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
    Place a manual order with leverage and charges.
    """
    logger.info(f"📝 Manual order: {order_data.get('side')} {order_data.get('quantity')} {order_data.get('symbol')}")
    
    # 1. Validate
    validation = validate_order(order_data)
    if not validation["valid"]:
        return {"success": False, "errors": validation["errors"]}
    
    # 2. Get current price
    provider = get_price_provider()
    price_result = provider.get_ltp(order_data["symbol"])
    
    if not price_result:
        return {"success": False, "errors": ["Could not fetch current price"]}
    
    current_price = price_result["last_price"]
    
    # 3. Determine execution price
    order_type = order_data["order_type"]
    product_type = order_data.get("product_type", "INTRADAY").upper()
    execution_price = None
    execute_immediately = False
    
    if order_type == "MARKET":
        execution_price = current_price
        execute_immediately = True
    elif order_type == "LIMIT":
        limit_price = order_data["price"]
        if order_data["side"] == "BUY" and current_price <= limit_price:
            execution_price = current_price
            execute_immediately = True
        elif order_data["side"] == "SELL" and current_price >= limit_price:
            execution_price = current_price
            execute_immediately = True
    
    # 4. Check margin required (NOT full turnover!)
    if order_data["side"] == "BUY" and execute_immediately:
        state = get_manual_state()
        available = state["capital"] - state["current_exposure"]
        
        # Calculate margin required (with leverage)
        margin_info = LeverageManager.calculate_margin_required(
            symbol=order_data["symbol"],
            quantity=order_data["quantity"],
            price=execution_price,
            product_type=product_type,
        )
        
        margin_required = margin_info["margin_required"]
        
        # Also add estimated charges to required capital
        charges = ChargesCalculator.calculate_charges(
            symbol=order_data["symbol"],
            quantity=order_data["quantity"],
            price=execution_price,
            side="BUY",
            product_type=product_type,
        )
        
        total_required = margin_required + charges["total_charges"]
        
        if total_required > available:
            return {
                "success": False,
                "errors": [
                    f"Insufficient capital. Required: ₹{total_required:.2f} "
                    f"(Margin: ₹{margin_required:.2f} + Charges: ₹{charges['total_charges']:.2f}), "
                    f"Available: ₹{available:.2f}"
                ],
                "margin_info": margin_info,
                "charges_info": charges,
            }
    
    # 5. Create order
    order_id = create_manual_order(order_data)
    logger.info(f"  → Order created: #{order_id}")
    
    # 6. Execute if applicable
    if execute_immediately:
        return execute_order(order_id, execution_price)
    
    return {
        "success": True,
        "order_id": order_id,
        "status": "PENDING",
        "message": f"{order_type} order placed. Waiting for trigger price.",
    }


def execute_order(order_id: int, execution_price: float) -> Dict:
    """Execute an order with charges."""
    order = get_manual_order(order_id)
    if not order:
        return {"success": False, "errors": ["Order not found"]}
    
    if order["status"] != "PENDING":
        return {"success": False, "errors": [f"Order already {order['status']}"]}
    
    product_type = order.get("product_type", "INTRADAY").upper()
    
    # Calculate charges for this leg
    charges = ChargesCalculator.calculate_charges(
        symbol=order["symbol"],
        quantity=order["quantity"],
        price=execution_price,
        side=order["side"],
        product_type=product_type,
    )
    
    # Update order as filled
    update_manual_order(
        order_id,
        status="FILLED",
        filled_quantity=order["quantity"],
        avg_fill_price=execution_price,
        filled_at=datetime.now().isoformat(),
    )
    
    # For BUY: create trade with margin
    if order["side"] == "BUY":
        margin_info = LeverageManager.calculate_margin_required(
            symbol=order["symbol"],
            quantity=order["quantity"],
            price=execution_price,
            product_type=product_type,
        )
        
        # Investment = Margin (what actually locks capital) + Charges
        investment = margin_info["margin_required"] + charges["total_charges"]
        turnover = margin_info["turnover"]
        
        trade_id = create_manual_trade({
            "symbol": order["symbol"],
            "direction": "LONG",
            "sector": get_sector(order["symbol"]),
            "entry_order_id": order_id,
            "entry_price": execution_price,
            "stop_loss": order.get("stop_loss"),
            "target": order.get("target"),
            "quantity": order["quantity"],
            "investment": investment,  # Actual capital deployed (margin + charges)
            "notes": order.get("notes"),
        })
        
        # Update state
        state = get_manual_state()
        update_manual_state(
            capital=state["capital"] - charges["total_charges"],  # Deduct charges from capital
            current_exposure=state["current_exposure"] + margin_info["margin_required"],
            open_positions=state["open_positions"] + 1,
            trades_today=state["trades_today"] + 1,
        )
        
        logger.info(
            f"  ✅ BUY: {order['quantity']} shares @ ₹{execution_price} "
            f"(Turnover: ₹{turnover:,.2f}, Margin: ₹{margin_info['margin_required']:,.2f}, "
            f"Charges: ₹{charges['total_charges']:.2f})"
        )
        
        return {
            "success": True,
            "order_id": order_id,
            "trade_id": trade_id,
            "status": "FILLED",
            "execution_price": execution_price,
            "turnover": turnover,
            "margin_used": margin_info["margin_required"],
            "leverage": margin_info["leverage"],
            "charges": charges,
            "message": (
                f"BUY filled at ₹{execution_price}. "
                f"Margin: ₹{margin_info['margin_required']:.2f} "
                f"({margin_info['leverage']}x leverage), "
                f"Charges: ₹{charges['total_charges']:.2f}"
            ),
        }
    
    # For SELL: close positions
    else:
        return close_position_by_symbol(
            order["symbol"], order["quantity"], execution_price, order_id, charges
        )


def close_position_by_symbol(
    symbol: str, quantity: int, exit_price: float, order_id: int, exit_charges: Dict
) -> Dict:
    """Close open positions FIFO with charges."""
    open_trades = [t for t in get_manual_trades("OPEN") if t["symbol"] == symbol]
    
    if not open_trades:
        return {"success": False, "errors": [f"No open positions for {symbol}"]}
    
    open_trades.sort(key=lambda t: t["entry_time"])
    
    remaining_qty = quantity
    closed_trades = []
    total_gross_pnl = 0
    total_net_pnl = 0
    total_released_margin = 0
    
    for trade in open_trades:
        if remaining_qty <= 0:
            break
        
        product_type = "INTRADAY"  # Default
        
        # Get exit charges proportion
        qty_to_close = min(remaining_qty, trade["quantity"])
        
        # Proportional charges for partial close
        exit_charge_portion = (exit_charges["total_charges"] * qty_to_close) / quantity
        
        if remaining_qty >= trade["quantity"]:
            # Close entire trade
            entry_price = trade["entry_price"]
            
            # Calculate P&L
            gross_pnl = round((exit_price - entry_price) * trade["quantity"], 2)
            
            # Get entry charges (from investment)
            # investment already includes entry charges
            # entry_margin = investment - entry_charges
            
            # Calculate margin returned
            margin_info = LeverageManager.calculate_margin_required(
                symbol=trade["symbol"],
                quantity=trade["quantity"],
                price=entry_price,
                product_type=product_type,
            )
            margin_returned = margin_info["margin_required"]
            
            net_pnl = round(gross_pnl - exit_charge_portion, 2)
            
            total_gross_pnl += gross_pnl
            total_net_pnl += net_pnl
            total_released_margin += margin_returned
            
            close_manual_trade(trade["id"], exit_price, "MANUAL_SELL")
            
            # Update trade with net P&L
            update_manual_trade(trade["id"], realized_pnl=net_pnl)
            
            remaining_qty -= trade["quantity"]
            closed_trades.append(trade["id"])
        else:
            # Partial close (simplified)
            partial_qty = remaining_qty
            entry = trade["entry_price"]
            gross_pnl = round((exit_price - entry) * partial_qty, 2)
            net_pnl = round(gross_pnl - exit_charge_portion, 2)
            
            total_gross_pnl += gross_pnl
            total_net_pnl += net_pnl
            
            # Reduce trade
            new_qty = trade["quantity"] - partial_qty
            proportion = new_qty / trade["quantity"]
            new_investment = trade["investment"] * proportion
            released = trade["investment"] - new_investment
            total_released_margin += released
            
            update_manual_trade(
                trade["id"],
                quantity=new_qty,
                investment=new_investment,
            )
            
            remaining_qty = 0
    
    # Update state
    state = get_manual_state()
    positions_closed = len(closed_trades)
    
    is_profit = total_net_pnl > 0
    wins_delta = 1 if is_profit else 0
    losses_delta = 1 if total_net_pnl < 0 else 0
    
    update_manual_state(
        capital=state["capital"] + total_net_pnl,
        current_exposure=state["current_exposure"] - total_released_margin,
        open_positions=max(0, state["open_positions"] - positions_closed),
        total_realized_pnl=state["total_realized_pnl"] + total_net_pnl,
        pnl_today=state["pnl_today"] + total_net_pnl,
        wins_today=state["wins_today"] + wins_delta,
        losses_today=state["losses_today"] + losses_delta,
    )
    
    logger.info(
        f"  ✅ SELL: {quantity} @ ₹{exit_price} | "
        f"Gross P&L: ₹{total_gross_pnl}, Charges: ₹{exit_charges['total_charges']:.2f}, "
        f"Net P&L: ₹{total_net_pnl}"
    )
    
    return {
        "success": True,
        "order_id": order_id,
        "closed_trades": closed_trades,
        "status": "FILLED",
        "execution_price": exit_price,
        "gross_pnl": total_gross_pnl,
        "charges": exit_charges,
        "net_pnl": total_net_pnl,
        "message": (
            f"SELL filled. Gross P&L: ₹{total_gross_pnl:.2f}, "
            f"Charges: ₹{exit_charges['total_charges']:.2f}, "
            f"Net P&L: ₹{total_net_pnl:.2f}"
        ),
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

# ADD to manual_executor.py

def force_close_intraday_positions() -> Dict:
    """
    Force close all INTRADAY positions at 3:15 PM.
    Called by scheduler.
    """
    from datetime import datetime, time as dt_time
    
    now = datetime.now().time()
    close_time = dt_time(15, 15)   # 3:15 PM
    
    if now < close_time:
        return {"status": "not_time", "message": "Not yet 3:15 PM"}
    
    # Get all open trades
    open_trades = get_manual_trades("OPEN")
    
    # Filter to only INTRADAY (need to check order for product_type)
    intraday_trades = []
    for trade in open_trades:
        # Get order to check product type
        if trade.get("entry_order_id"):
            order = get_manual_order(trade["entry_order_id"])
            if order and order.get("product_type", "INTRADAY").upper() == "INTRADAY":
                intraday_trades.append(trade)
    
    if not intraday_trades:
        return {"status": "no_intraday", "closed": 0}
    
    logger.info(f"⏰ EOD: Force closing {len(intraday_trades)} intraday positions")
    
    provider = get_price_provider()
    closed = []
    total_pnl = 0
    
    for trade in intraday_trades:
        try:
            # Get current price
            price_result = provider.get_ltp(trade["symbol"])
            if not price_result:
                continue
            
            exit_price = price_result["last_price"]
            
            # Calculate exit charges
            from agent.charges_calculator import ChargesCalculator
            exit_charges = ChargesCalculator.calculate_charges(
                symbol=trade["symbol"],
                quantity=trade["quantity"],
                price=exit_price,
                side="SELL",
                product_type="INTRADAY",
            )
            
            # Close trade
            gross_pnl = (exit_price - trade["entry_price"]) * trade["quantity"]
            net_pnl = gross_pnl - exit_charges["total_charges"]
            
            close_manual_trade(trade["id"], exit_price, "EOD_AUTO_SQUARE_OFF")
            update_manual_trade(trade["id"], realized_pnl=round(net_pnl, 2))
            
            # Update state
            state = get_manual_state()
            update_manual_state(
                capital=state["capital"] + net_pnl,
                current_exposure=state["current_exposure"] - trade["investment"],
                open_positions=max(0, state["open_positions"] - 1),
                total_realized_pnl=state["total_realized_pnl"] + net_pnl,
                pnl_today=state["pnl_today"] + net_pnl,
                wins_today=state["wins_today"] + (1 if net_pnl > 0 else 0),
                losses_today=state["losses_today"] + (1 if net_pnl < 0 else 0),
            )
            
            total_pnl += net_pnl
            closed.append({
                "trade_id": trade["id"],
                "symbol": trade["symbol"],
                "pnl": round(net_pnl, 2),
            })
            
            logger.info(
                f"  ✅ Force closed: {trade['symbol']} | "
                f"Entry: ₹{trade['entry_price']}, Exit: ₹{exit_price}, "
                f"Net P&L: ₹{net_pnl:.2f}"
            )
        
        except Exception as e:
            logger.error(f"Failed to close {trade['symbol']}: {e}")
    
    return {
        "status": "completed",
        "closed": len(closed),
        "total_pnl": round(total_pnl, 2),
        "positions": closed,
    }


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