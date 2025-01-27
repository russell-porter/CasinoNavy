# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import Criterion
from frappe.model.document import Document

class ChargeType(Document):
	pass

@frappe.whitelist()
def get_charge_type_query(doctype, txt, searchfield, start, page_len, filters):
	CT = frappe.qb.DocType('Charge Type')
	MA = frappe.qb.DocType('Mode of Payment Account')

	conditions = []

	if filters.get('company'):
		conditions.append(MA.company == filters.get('company'))
	
	if filters.get('type'):
		conditions.append(CT.type == filters.get('type'))
	
	if txt:
		conditions.append(CT.name.like('%{0}%'.format(txt)))
	
	return frappe.qb.from_(CT).join(MA).on(
		(CT.name == MA.parent)&
		(MA.parenttype == 'Charge Type')
	).select(
		CT.name
	).where(
		Criterion.all(conditions)
	).run()