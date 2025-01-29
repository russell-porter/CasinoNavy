# Copyright (c) 2024, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document

class TransactionLedger(Document):
	def validate(self):
		self.fetch_accounts()
		self.validate_bank_account()
		self.validate_types()
		
		# self.set_default_fee()

	def on_submit(self):
		self.make_entry()
	
	def on_cancel(self):
		self.cancel_entry()
	
	def on_trash(self):
		self.delete_entry()
	
	def make_entry(self):
		jv = frappe.new_doc("Journal Entry")
		jv.update({
			"company": self.company,
			"voucher_type": "Bank Entry",
			"posting_date": self.date,
			"cheque_no": f"Transaction Ledeger {self.name}",
			"reference_type": self.doctype,
			"reference_name": self.name,
			"cheque_date": self.date,
			"multi_currency": 1,
		})

		company = frappe.get_doc("Company", self.company)
		
		default_income_account = company.default_income_account
		default_cost_center = company.cost_center

		if not default_income_account:
			frappe.throw(f"Please set a default income account for the company {self.company}")
		
		# Amount
		if self.transaction_type == "Deposit":
			amount = abs(flt(self.amount)) - abs(flt(self.fee))
			row = jv.append("accounts", {
				"account": self.get_bank_account(),
				"debit_in_account_currency": amount,
				"debit": amount,
				"bank_account": self.bank,
				"cost_center": default_cost_center,
			})
			
			if self.fee:
				row = jv.append("accounts", {
					"account": self.get_charge_account(self.fee_type),
					"debit_in_account_currency": self.fee,
					"debit": self.fee,
					"cost_center": default_cost_center,
				})

			row = jv.append("accounts", {
				"account": self.get_charge_account(self.charge_type),
				"credit_in_account_currency": self.amount,
				"credit": self.amount,
				"cost_center": default_cost_center,
			})	
		elif self.transaction_type == "Withdraw":
			amount = abs(flt(self.amount)) + abs(flt(self.fee))
			row = jv.append("accounts", {
				"account": self.get_bank_account(),
				"credit_in_account_currency": amount,
				"credit": amount,
				"bank_account": self.bank,
				"cost_center": default_cost_center,
			})
			if self.fee:
				row = jv.append("accounts", {
					"account": self.get_charge_account(self.fee_type),
					"debit_in_account_currency": self.fee,
					"debit": self.fee,
					"cost_center": default_cost_center,
				})
			row = jv.append("accounts", {
				"account": self.get_charge_account(self.charge_type),
				"debit_in_account_currency": self.amount,
				"debit": self.amount,
				"cost_center": default_cost_center,
			})

		jv.save()
		jv.submit()
		return jv.name

	def cancel_entry(self):
		filters = {
			"reference_type": self.doctype,
			"reference_name": self.name,
			"docstatus": 1
		}
		if name:= frappe.db.exists("Journal Entry", filters):
			jv = frappe.get_doc("Journal Entry", name)
			jv.cancel()
	
	def delete_entry(self):
		filters = {
			"reference_type": self.doctype,
			"reference_name": self.name,
			"docstatus": ["in", [0, 2]]
		}
		if name:= frappe.db.exists("Journal Entry", filters):
			jv = frappe.get_doc("Journal Entry", name)
			jv.delete()
		
	def fetch_accounts(self):
		self.bank_account = self.get_bank_account()
		self.fee_account = self.get_charge_account(self.fee_type)
		self.charge_account = self.get_charge_account(self.charge_type)

	def get_bank_account(self):
		bank_account = frappe.get_value("Bank Account", self.bank, "account")
		if not bank_account:
			frappe.throw(f"Bank Account '{self.bank}' does not have an account")
		return bank_account

	def set_default_fee(self):
		supplier = frappe.get_doc("Supplier", self.supplier)
		if not supplier.enforce_fees:
			return
		else:
			fee = supplier.default_deposit_fee if self.transaction_type == "Deposit" else supplier.default_withdraw_fee
			self.fee = self.amount * fee / 100.00
	
	def validate_bank_account(self):
		bank_account_company = frappe.get_value("Bank Account", self.bank, "company")
		if bank_account_company != self.company:
			frappe.throw(f"Bank Account '{self.bank}' does not belong to Company '{self.company}'")
	
	def validate_types(self):
		if not self.charge_type:
			return

		charge  = frappe.get_doc("Charge Type", self.charge_type)
		if self.transaction_type == "Deposit" and charge.type != "Income":
			frappe.throw(f"Charge Type '{self.charge_type}' is not an income type")
		elif self.transaction_type == "Withdraw" and charge.type != "Expense":
			frappe.throw(f"Charge Type '{self.charge_type}' is not an expense type")
		
			
			
	def get_charge_account(self, charge_type):
		MOPA = frappe.qb.DocType("Mode of Payment Account")
		CT = frappe.qb.DocType("Charge Type")

		result  = frappe.qb.from_(MOPA).join(CT).on(
			MOPA.parent == CT.name
		).select(MOPA.default_account).where(
			(MOPA.company == self.company)&
			(CT.name == charge_type)
		).run()

		return result[0][0] if result else None
