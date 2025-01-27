# Copyright (c) 2024, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document

class BalanceTransfer(Document):
    def validate(self):
        self.fetch_accounts()
        self.validate_bank_account()

    def on_submit(self):
        from_data = frappe._dict({
            "company": self.from_company,
            "bank": self.from_bank,
            "fee_type": self.from_fee_type,
            "fee": self.from_fee,
            "amount": self.amount,
            "charge_type": self.from_charge_type,
            "transaction_type": "Withdraw",
        })
        to_data = frappe._dict({
            "company": self.to_company,
            "bank": self.to_bank,
            "fee_type": self.to_fee_type,
            "fee": self.to_fee,
            "amount": self.amount,
            "charge_type": self.to_charge_type,
            "transaction_type": "Deposit",
        })

        self.make_entry(from_data)
        self.make_entry(to_data)

    def on_cancel(self):
        self.cancel_entry()

    def on_trash(self):
        self.delete_entry()

    def make_entry(self, data):
        """"
            We need to make two entries from and to the bank accounts
        """
        jv = frappe.new_doc("Journal Entry")
        jv.update({
            "voucher_type": "Bank Entry",
            "posting_date": self.date,
            "cheque_no": f"Transaction Ledeger {self.name}",
            "reference_type": self.doctype,
            "reference_name": self.name,
            "cheque_date": self.date,
        })

        company = frappe.get_doc("Company", data.company)

        default_income_account = company.default_income_account
        default_cost_center = company.cost_center

        if not default_income_account:
            frappe.throw(f"Please set a default income account for the company {data.company}")

        # Amount
        if data.transaction_type == "Deposit":
            amount = abs(flt(data.amount)) - abs(flt(data.fee))
            jv.append("accounts", {
                "account": get_bank_account(data.bank),
                "debit_in_account_currency": amount,
                "debit": amount,
                "bank_account": data.bank,
                "cost_center": default_cost_center,
            })

            if data.fee:
                jv.append("accounts", {
                    "account": get_charge_account(data.company, data.fee_type),
                    "debit_in_account_currency": data.fee,
                    "debit": data.fee,
                    "cost_center": default_cost_center,
                })

            jv.append("accounts", {
                "account": get_charge_account(data.company, data.charge_type),
                "credit_in_account_currency": data.amount,
                "credit": data.amount,
                "cost_center": default_cost_center,
            })
        elif data.transaction_type == "Withdraw":
            amount = abs(flt(data.amount)) + abs(flt(data.fee))
            jv.append("accounts", {
                "account": get_bank_account(data.bank),
                "credit_in_account_currency": amount,
                "credit": amount,
                "bank_account": data.bank,
                "cost_center": default_cost_center,
            })
            if data.fee:
                jv.append("accounts", {
                    "account": get_charge_account(data.company, data.fee_type),
                    "debit_in_account_currency": data.fee,
                    "debit": data.fee,
                    "cost_center": default_cost_center,
                })
            jv.append("accounts", {
                "account": get_charge_account(data.company, data.charge_type),
                "debit_in_account_currency": data.amount,
                "debit": data.amount,
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
        self.from_bank_account = get_bank_account(self.from_bank)
        self.to_bank_account = get_bank_account(self.to_bank)
        self.from_fee_account = get_charge_account(self.from_company, self.from_fee_type)
        self.to_fee_account = get_charge_account(self.to_company, self.to_fee_type)

    def validate_bank_account(self):
        pass

def get_bank_account(bank):
    bank_account = frappe.get_value("Bank Account", bank, "account")
    if not bank_account:
        frappe.throw(f"Bank Account '{bank}' does not have an account")
    return bank_account

def get_charge_account(company, charge_type):
    MOPA = frappe.qb.DocType("Mode of Payment Account")
    CT = frappe.qb.DocType("Charge Type")

    result  = frappe.qb.from_(MOPA).join(CT).on(
        MOPA.parent == CT.name
    ).select(MOPA.default_account).where(
        (MOPA.company == company)&
        (CT.name == charge_type)
    ).run()

    return result[0][0] if result else None
