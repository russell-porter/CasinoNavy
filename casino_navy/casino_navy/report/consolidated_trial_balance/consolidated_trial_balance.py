# Copyright (c) 2023, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.trial_balance import trial_balance

from .utils import get_child_companies, get_accounts_name, get_company_abbr


MERGE_KEYS = {
	"closing_credit",
	"closing_debit",
	"credit",
	"debit",
	"opening_credit",
	"opening_debit",
}


ROW_TEMPLATE =  {
  "account": "",
  "account_name": "",
  "closing_credit": 0.0,
  "closing_debit": 0.0,
  "credit": 0.0,
  "currency": "",
  "debit": 0.0,
  "from_date": "",
  "has_value": False,
  "indent": 0,
  "opening_credit": 0.0,
  "opening_debit": 0.0,
  "parent_account": None,
  "warn_if_negative": False,
  "to_date": "",
 }

def execute(filters=None):
	trial_balance.validate_filters(filters)
	data = get_data(filters)
	columns = get_columns()

	return columns, data


def get_columns():
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Data",
			"options": "Account",
			"width": 300,
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
		{
			"fieldname": "opening_debit",
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "opening_credit",
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "closing_debit",
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "closing_credit",
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]


def get_data(filters):
	data = list()

	company = filters.get("company")
	for company in get_child_companies(company):
		filters.update({
			"company": company,
		})

		# let's now merge the data based on the keys
		for companied_row in trial_balance.get_data(filters):
			if not companied_row: # empty row
				continue

			try:
				row_account = companied_row["account"]
			except KeyError: # a row without account?
				continue     # not sure what to do here

			if row_account == "'Total'":
				continue # ignore Totals row

			# let's now merge the data based on the keys
			added_row = get_added_row(data, row_account, companied_row)

			if not added_row:
				frappe.throw("Something went wrong")

			for key, value in companied_row.items():
				if key not in MERGE_KEYS:
					continue
				
				added_row[key] += flt(value)

	return data


def get_added_row(data, account, incoming_row):
	"""Get the row based on the account's name from the out list
	and add it if it doesn't exists"""
	searched_account_name = get_accounts_name(account)

	for row in data:
		if not row: # we found an empty row
			continue

		found_account_name = get_accounts_name(
			row.get("account")
		)

		# we found a row with the same account name
		if found_account_name == searched_account_name:
			return row

	new_row = ROW_TEMPLATE.copy()

	new_row.update({
		"account": account,
		"account_name": searched_account_name,
	})

	for key, value in incoming_row.items():
		if key in MERGE_KEYS: # we want defvalues for these keys
			continue

		if key == "parent_account" and value:
			new_row[key] = get_accounts_name(value)
			continue

		new_row[key] = value # override the default value

	data.append(new_row)

	return new_row
