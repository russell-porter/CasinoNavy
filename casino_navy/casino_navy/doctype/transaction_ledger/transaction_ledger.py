# Copyright (c) 2024, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TransactionLedger(Document):
	def validate(self):
		self.set_default_fee()

	def set_default_fee(self):
		supplier = frappe.get_doc("Supplier", self.supplier)
		if not supplier.enforce_fees:
			return
		else:
			fee = supplier.default_deposit_fee if self.transaction_type == "Deposit" else supplier.default_withdraw_fee
			self.fee = self.amount * fee / 100.00