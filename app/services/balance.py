"""
Balance engine.

Calculates net balances for users within a group based on expenses and splits.
Uses a greedy algorithm to simplify debts (suggested settlements).
Note: When settlements are implemented in Phase 8, this engine will be updated
to include them in the net balance calculation.
"""

import uuid
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.user import User
from app.models.group import Group
from app.models.settlement import Settlement
from app.schemas.balance import UserBalanceSummary, Debt, GroupBalanceReport


async def get_group_balances(db: AsyncSession, group_id: uuid.UUID) -> GroupBalanceReport:
    """
    Calculate the net balances for all users in a group and generate suggested settlements.
    
    Net Balance = (Amount Paid for Group) - (Share of Group Expenses)
    """
    # 1. Calculate how much each user has paid in this group
    paid_query = select(
        Expense.payer_id, 
        func.sum(Expense.amount).label("total_paid")
    ).where(Expense.group_id == group_id).group_by(Expense.payer_id)
    
    paid_result = await db.execute(paid_query)
    paid_amounts = {row.payer_id: Decimal(str(row.total_paid)) for row in paid_result.all()}

    # 2. Calculate how much each user owes (their share) in this group
    share_query = select(
        ExpenseSplit.user_id,
        func.sum(ExpenseSplit.share_amount).label("total_share")
    ).join(Expense).where(Expense.group_id == group_id).group_by(ExpenseSplit.user_id)
    
    share_result = await db.execute(share_query)
    share_amounts = {row.user_id: Decimal(str(row.total_share)) for row in share_result.all()}

    # 3. Calculate settlements paid by each user in this group
    settlements_paid_query = select(
        Settlement.payer_id,
        func.sum(Settlement.amount).label("total_settlements_paid")
    ).where(Settlement.group_id == group_id).group_by(Settlement.payer_id)
    
    sp_result = await db.execute(settlements_paid_query)
    settlements_paid_amounts = {row.payer_id: Decimal(str(row.total_settlements_paid)) for row in sp_result.all()}

    # 4. Calculate settlements received by each user in this group
    settlements_received_query = select(
        Settlement.receiver_id,
        func.sum(Settlement.amount).label("total_settlements_received")
    ).where(Settlement.group_id == group_id).group_by(Settlement.receiver_id)
    
    sr_result = await db.execute(settlements_received_query)
    settlements_received_amounts = {row.receiver_id: Decimal(str(row.total_settlements_received)) for row in sr_result.all()}

    # 5. Get all involved users
    involved_user_ids = set(paid_amounts.keys()).union(
        set(share_amounts.keys()), 
        set(settlements_paid_amounts.keys()), 
        set(settlements_received_amounts.keys())
    )
    if not involved_user_ids:
        return GroupBalanceReport(group_id=group_id, balances=[], suggested_settlements=[])
        
    users_query = select(User).where(User.id.in_(involved_user_ids))
    users_result = await db.execute(users_query)
    users_map = {user.id: user for user in users_result.scalars().all()}

    # 6. Calculate Net Balances
    balances = []
    net_balances_decimal = {}
    
    for user_id in involved_user_ids:
        paid = paid_amounts.get(user_id, Decimal('0'))
        share = share_amounts.get(user_id, Decimal('0'))
        sp = settlements_paid_amounts.get(user_id, Decimal('0'))
        sr = settlements_received_amounts.get(user_id, Decimal('0'))
        
        # Net Balance = Paid - Share + Settlements Paid - Settlements Received
        net = paid - share + sp - sr
        
        net_balances_decimal[user_id] = net
        balances.append(
            UserBalanceSummary(
                user=users_map[user_id],
                net_balance=float(net)
            )
        )

    # 7. Calculate Suggested Settlements (Greedy Debt Simplification)
    debtors = []   # Users who owe money (net < 0)
    creditors = [] # Users who are owed money (net > 0)
    
    for user_id, net in net_balances_decimal.items():
        if net < 0:
            debtors.append({"user_id": user_id, "amount": abs(net)})
        elif net > 0:
            creditors.append({"user_id": user_id, "amount": net})
            
    # Sort by amount descending to minimize transactions
    debtors.sort(key=lambda x: x["amount"], reverse=True)
    creditors.sort(key=lambda x: x["amount"], reverse=True)
    
    suggested_settlements = []
    i, j = 0, 0
    
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        settle_amount = min(debtor["amount"], creditor["amount"])
        
        # Avoid zero-amount settlements (floating point artifacts)
        if settle_amount > Decimal('0.00'):
            suggested_settlements.append(
                Debt(
                    from_user=users_map[debtor["user_id"]],
                    to_user=users_map[creditor["user_id"]],
                    amount=float(settle_amount)
                )
            )
            
        debtor["amount"] -= settle_amount
        creditor["amount"] -= settle_amount
        
        if debtor["amount"] == 0:
            i += 1
        if creditor["amount"] == 0:
            j += 1

    return GroupBalanceReport(
        group_id=group_id,
        balances=balances,
        suggested_settlements=suggested_settlements
    )


async def get_user_overall_balance(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Calculate a single user's total net balance across all groups."""
    
    paid_query = select(func.sum(Expense.amount)).where(Expense.payer_id == user_id)
    paid_result = await db.execute(paid_query)
    total_paid = Decimal(str(paid_result.scalar() or 0))
    
    share_query = select(func.sum(ExpenseSplit.share_amount)).where(ExpenseSplit.user_id == user_id)
    share_result = await db.execute(share_query)
    total_share = Decimal(str(share_result.scalar() or 0))
    
    sp_query = select(func.sum(Settlement.amount)).where(Settlement.payer_id == user_id)
    sp_result = await db.execute(sp_query)
    total_sp = Decimal(str(sp_result.scalar() or 0))
    
    sr_query = select(func.sum(Settlement.amount)).where(Settlement.receiver_id == user_id)
    sr_result = await db.execute(sr_query)
    total_sr = Decimal(str(sr_result.scalar() or 0))
    
    net_balance = total_paid - total_share + total_sp - total_sr
    
    return {
        "user_id": user_id,
        "total_paid": float(total_paid),
        "total_owed": float(total_share),
        "net_balance": float(net_balance)
    }
