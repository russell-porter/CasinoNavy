# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext import get_company_currency
from erpnext.accounts.report.utils import convert_to_presentation_currency, get_currency


def execute(filters=None):
	if not filters:
		filters = {}

	if not filters.get("company"):
		frappe.throw(_("Company is required"))

	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required"))

	company_currency = get_company_currency(filters["company"])
	filters["company_currency"] = company_currency

	filters["currency"] = filters.get("presentation_currency") or company_currency

	if filters.get("summary"):
		filters["bank_accounts"] = frappe.get_all(
			"Bank Account",
			filters={"company": filters["company"], "is_company_account": 1},
			fields=["name", "account"]
		)
	else:
		if not filters.get("bank_account"):
			frappe.throw(_("Bank Account is required for detailed view"))

		account = frappe.db.get_value("Bank Account", filters["bank_account"], "account")
		if not account:
			frappe.throw(_("The selected Bank Account is not linked to a GL Account"))

		filters["account"] = account

	columns = get_columns(filters)
	data = get_summary_data(filters) if filters.get("summary") else get_detailed_data(filters)

	return columns, data, None, get_chart(data, filters)


def get_columns(filters):
	currency = filters.get("currency")

	if filters.get("summary"):
		return [
			{"label": _("E-Wallet (Bank Account)"), "fieldname": "e_wallet", "fieldtype": "Link", "options": "Bank Account", "width": 200},
			{"label": _("Opening Balance ({0})").format(currency), "fieldname": "opening_balance", "fieldtype": "Currency", "width": 180},
			{"label": _("Debit ({0})").format(currency), "fieldname": "debit", "fieldtype": "Currency", "width": 130},
			{"label": _("Credit ({0})").format(currency), "fieldname": "credit", "fieldtype": "Currency", "width": 130},
			{"label": _("Total in Period ({0})").format(currency), "fieldname": "period_total", "fieldtype": "Currency", "width": 180},
			{"label": _("Closing (Opening + Total) ({0})").format(currency), "fieldname": "closing_balance", "fieldtype": "Currency", "width": 230},
		]
	else:
		return [
			{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
			{"label": _("E-Wallet (Bank Account)"), "fieldname": "e_wallet", "fieldtype": "Link", "options": "Bank Account", "width": 200},
			{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
			{"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
			{"label": _("Debit ({0})").format(currency), "fieldname": "debit", "fieldtype": "Currency", "width": 130},
			{"label": _("Credit ({0})").format(currency), "fieldname": "credit", "fieldtype": "Currency", "width": 130},
			{"label": _("Balance ({0})").format(currency), "fieldname": "balance", "fieldtype": "Currency", "width": 130},
		]


def get_summary_data(filters):
	data = []
	gl_entries = []

	for bank in filters["bank_accounts"]:
		account = bank.account
		account_entries = frappe.db.sql("""
			SELECT
				posting_date, account, debit, credit,
				debit_in_account_currency, credit_in_account_currency,
				account_currency, voucher_type, voucher_no
			FROM `tabGL Entry`
			WHERE company = %(company)s AND account = %(account)s
				AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		""", {**filters, "account": account}, as_dict=1)

		for entry in account_entries:
			gl_entries.append(entry)
			entry["e_wallet"] = bank.name

	if filters.get("presentation_currency") and filters["presentation_currency"] != filters["company_currency"]:
		currency_map = get_currency(filters)
		for gle in gl_entries:
			gle.setdefault("debit_in_account_currency", gle.get("debit", 0))
			gle.setdefault("credit_in_account_currency", gle.get("credit", 0))
			gle.setdefault("account_currency", filters.get("company_currency"))
		gl_entries = convert_to_presentation_currency(gl_entries, currency_map)

	totals = {"debit": 0.0, "credit": 0.0, "period_total": 0.0, "closing_balance": 0.0}

	bank_accounts = {}
	for row in gl_entries:
		name = row["e_wallet"]
		if name not in bank_accounts:
			bank_accounts[name] = {
				"e_wallet": name,
				"debit": 0.0,
				"credit": 0.0,
				"period_total": 0.0,
				"closing_balance": 0.0,
				"account": row["account"]
			}

		bank_accounts[name]["debit"] += row["debit"] or 0
		bank_accounts[name]["credit"] += row["credit"] or 0

	for row in bank_accounts.values():
		opening = get_opening_balance(row["account"], filters)
		period_total = row["debit"] - row["credit"]
		closing = opening + period_total

		row["opening_balance"] = opening
		row["period_total"] = period_total
		row["closing_balance"] = closing

		totals["debit"] += row["debit"]
		totals["credit"] += row["credit"]
		totals["period_total"] += period_total
		totals["closing_balance"] += closing

		data.append(row)

	return data


def get_detailed_data(filters):
	account = filters["account"]
	bank_account = filters["bank_account"]

	gl_entries = frappe.db.sql("""
		SELECT 
			posting_date, voucher_type, voucher_no, debit, credit,
			debit_in_account_currency, credit_in_account_currency,
			account_currency
		FROM `tabGL Entry`
		WHERE company = %(company)s AND account = %(account)s
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY posting_date, creation
	""", filters, as_dict=1)

	if filters.get("presentation_currency") and filters["presentation_currency"] != filters["company_currency"]:
		for gle in gl_entries:
			gle["account_currency"] = filters["company_currency"]
		currency_map = get_currency(filters)
		gl_entries = convert_to_presentation_currency(gl_entries, currency_map)

	for row in gl_entries:
		row["e_wallet"] = bank_account
		row["balance"] = (row.get("debit") or 0) - (row.get("credit") or 0)

	return gl_entries


def get_opening_balance(account, filters):
	opening = frappe.db.sql("""
		SELECT SUM(debit - credit)
		FROM `tabGL Entry`
		WHERE company = 'X2 - JMS Investment Group N.V' AND account = '13005 - Papara - King - X2' AND posting_date < '2025-05-04'
	""", {**filters, "account": account})

	return opening[0][0] or 0.0

def get_chart(data, filters):
	if not filters.get("summary") or not data:
		return None

	labels = [d["e_wallet"] for d in data if d.get("e_wallet")]
	values = [d["closing_balance"] for d in data if d.get("closing_balance") is not None]

	# Optional: create a unique color for each wallet
	colors = [
		"#5e64ff", "#ff5858", "#7cd6fd", "#ffa3ef", "#ffcd56", "#5bc0de", "#4caf50", "#e91e63",
		"#9c27b0", "#03a9f4", "#009688", "#cddc39", "#ffc107", "#ff5722"
	]
	# Repeat or trim the color list to match the data length
	colors = (colors * ((len(values) // len(colors)) + 1))[:len(values)]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("Closing Balance"),
					"values": values
				}
			]
		},
		"type": "bar",
		"barOptions": {
			"distributed": 1  # This enables per-bar coloring
		},
		"colors": colors
	}