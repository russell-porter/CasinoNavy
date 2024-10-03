import frappe

def execute():
    TL = frappe.qb.DocType('Transaction Ledger')

    frappe.qb.update(TL).set(
        TL.transaction_type, 'Withdraw'
    ).where(
        TL.transaction_type == 'Withdrawal'
    ).run() 