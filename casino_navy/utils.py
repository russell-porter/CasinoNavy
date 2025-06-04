import frappe
from erpnext.setup.utils import get_exchange_rate as get_conversion_rate

def get_exchange_rate(from_currency, to_currency, date=None, conversion_type="for_selling"):
    if from_currency == to_currency:
        return 1
    if not date:
        date = frappe.utils.today()
    if not frappe.db.exists("Currency", from_currency):
        frappe.throw(f"Currency {from_currency} not found")
    if not frappe.db.exists("Currency", to_currency):
        frappe.throw(f"Currency {to_currency} not found")
    exchange = get_conversion_rate(from_currency, to_currency, date, conversion_type)
    print(f"Exchange rate between {from_currency} and {to_currency} on {date}: {exchange}")
    return exchange


