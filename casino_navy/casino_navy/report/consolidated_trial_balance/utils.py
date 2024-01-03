# Copyright (c) 2023, Yefri Tavarez and Contributors
# For license information, please see license.txt

import functools

import frappe

from frappe.utils import nestedset

@functools.lru_cache(maxsize=1)
def get_child_companies(name):
	"""Get all child companies of a company"""
	doctype = "Company"
	order_by = "name Asc"
	ignore_permissions = True

	return nestedset.get_descendants_of(
		doctype,
		name,
		order_by=order_by,
		ignore_permissions=ignore_permissions
	)


@functools.lru_cache(maxsize=128)
def get_company_abbr(name):
	"""Get abbreviation of a company"""
	doctype = "Company"
	fieldname = "abbr"
	return frappe.db.get_value(doctype, name, fieldname)


@functools.lru_cache(maxsize=128)
def get_accounts_name(name):
	"""Get the account_name without abbreviations"""
	doctype = "Account"
	fieldname = "account_name"
	return frappe.db.get_value(doctype, name, fieldname)