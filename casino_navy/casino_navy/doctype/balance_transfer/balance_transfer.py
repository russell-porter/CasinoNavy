# Copyright (c) 2024, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document
from casino_navy.utils import get_exchange_rate

class BalanceTransfer(Document):

    def validate(self):
        self.fetch_accounts_and_rates()
        self.validate_bank_account()

    def on_submit(self):
        self.make_entries()

    def on_cancel(self):
        self.cancel_entry()

    def on_trash(self):
        self.delete_entry()

    def make_entries(self):
        """"
            We need to make two entries from and to the bank accounts
        """
        success = False
        from_jv = frappe.new_doc("Journal Entry")
        to_jv = frappe.new_doc("Journal Entry")
        defaults = {
            "voucher_type": "Bank Entry",
            "posting_date": self.date,
            "reference_type": self.doctype,
            "reference_name": self.name,
            "cheque_date": self.date,
            "multi_currency": 1,
        }

        from_jv.update(defaults)
        from_jv.update({
            "company": self.from_company,
            "cheque_no": f"Balance Transfer Out {self.name}",
        })
        to_jv.update(defaults)
        to_jv.update({
            "company": self.to_company,
            "cheque_no": f"Balance Transfer In {self.name}",
        })
        # Source of funds
        amount = abs(flt(self.amount)) + abs(flt(self.from_fee))
        base_amount = amount * self.from_bank_exchange_rate
        from_company = frappe.get_doc("Company", self.from_company)
        
        row = from_jv.append("accounts", {
            "account": self.from_bank_account,
            "account_currency": self.from_bank_currency,
            "exchange_rate": self.from_bank_exchange_rate,
            "credit_in_account_currency": amount,
            "credit": amount * self.from_bank_exchange_rate,
            "bank_account": self.from_bank,
            "cost_center": from_company.cost_center,
        })
        
        if self.from_fee:
            from_jv.append("accounts", {
                "account": self.from_fee_account,
                "account_currency": self.from_fee_currency,
                "exchange_rate": self.from_fee_exchange_rate,
                "debit_in_account_currency": self.from_fee * self.from_fee_exchange_rate,
                "debit": self.from_fee * self.from_fee_exchange_rate,
                "cost_center": from_company.cost_center,
            })
        
        from_jv.append("accounts", {
            "account": self.from_charge_account,
            "account_currency": self.from_charge_currency,
            "exchange_rate": self.from_charge_exchange_rate,
            "debit_in_account_currency": base_amount * self.from_charge_exchange_rate,
            "debit": base_amount,
            "cost_center": from_company.cost_center,
        })
        # Destination of funds
        amount = abs(flt(self.amount)) - abs(flt(self.to_fee))
        to_company = frappe.get_doc("Company", self.to_company)

        row = to_jv.append("accounts", {
            "account": self.to_bank_account,
            "account_currency": self.to_bank_currency,
            "exchange_rate": self.to_bank_exchange_rate,
            "debit_in_account_currency": amount,
            "debit": amount * self.to_bank_exchange_rate,
            "bank_account": self.to_bank,
            "cost_center": to_company.cost_center,
        })

        if self.to_fee:
            row = to_jv.append("accounts", {
                "account": self.to_fee_account,
                "account_currency": self.to_fee_currency,
                "exchange_rate": self.to_fee_exchange_rate,
                "debit_in_account_currency": self.to_fee * self.to_fee_exchange_rate,
                "debit": self.to_fee * self.to_fee_exchange_rate,
                "cost_center": to_company.cost_center,
            })

        row = to_jv.append("accounts", {
            "account": self.to_charge_account,
            "account_currency": self.to_charge_currency,
            "exchange_rate": self.to_charge_exchange_rate,
            "credit_in_account_currency": base_amount * self.to_charge_exchange_rate,
            "credit": base_amount,
            "cost_center": to_company.cost_center,
        })

        try:
            from_jv.save()
            from_jv.submit()
            to_jv.save()
            to_jv.submit()

            success = True
        except Exception as e:
            content = f" From Journal Entry: {from_jv.as_json()}\n\n{str(e)}\n\n{frappe.get_traceback()}"
            content += f" To Journal Entry: {to_jv.as_json()}"
            frappe.log_error("Balance Transfer Error", content)    
            
        if not success:
            frappe.throw(f"An error occurred while creating the journal entry for this transaction check the logs for more details")

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

    def fetch_accounts_and_rates(self):
        from_company_currency = frappe.get_value("Company", self.from_company, "default_currency")
        to_company_currency = frappe.get_value("Company", self.to_company, "default_currency")
        
        from_bank_details = self.get_bank_account_details(self.from_bank)
        self.from_bank_account = from_bank_details.bank_account
        self.from_bank_currency = from_bank_details.account_currency
        self.from_bank_exchange_rate = get_exchange_rate(
            self.from_bank_currency,
            from_company_currency,
            self.date,
        )

        to_bank_details = self.get_bank_account_details(self.to_bank)
        self.to_bank_account = to_bank_details.bank_account
        self.to_bank_currency = to_bank_details.account_currency
        self.to_bank_exchange_rate = get_exchange_rate(
            self.to_bank_currency,
            to_company_currency,
            self.date,
        )

        from_charge_details = get_charge_account_details(self.from_company, self.from_charge_type)
        self.from_charge_account = from_charge_details.default_account
        self.from_charge_currency = from_charge_details.account_currency
        self.from_charge_exchange_rate = get_exchange_rate(
            self.from_charge_currency,
            from_company_currency,
            self.date,
        )
        
        if self.from_fee_type:
            from_fee_details = get_charge_account_details(self.from_company, self.from_fee_type)
            self.from_fee_account = from_fee_details.default_account
            self.from_fee_currency = from_fee_details.account_currency
            self.from_fee_exchange_rate = get_exchange_rate(
                self.from_fee_currency,
                from_company_currency,
                self.date,
            )
        
        if self.to_fee_type:
            to_fee_details = get_charge_account_details(self.to_company, self.to_fee_type)
            self.to_fee_account = to_fee_details.default_account
            self.to_fee_currency = to_fee_details.account_currency
            self.to_fee_exchange_rate = get_exchange_rate(
                self.to_fee_currency,
                to_company_currency,
                self.date,
            )

        to_charge_details = get_charge_account_details(self.to_company, self.to_charge_type)
        self.to_charge_account = to_charge_details.default_account
        self.to_charge_currency = to_charge_details.account_currency
        self.to_charge_exchange_rate = get_exchange_rate(
            self.to_charge_currency,
            to_company_currency,
            self.date,
        )


    def get_bank_account_details(self, bank=None):
        BA = frappe.qb.DocType("Bank Account")
        A = frappe.qb.DocType("Account")
        result = frappe.qb.from_(BA).join(A).on(
            BA.account == A.name
        ).select(
            A.name.as_("bank_account"),
            A.account_currency
        ).where(
            (BA.name == bank if bank else self.bank)
        ).run(as_dict=True)
        
        if not result:
            frappe.throw(f"Bank Account '{self.bank}' does not have an account")
        
        return result[0]

    def validate_bank_account(self):
        # let's make sure the fee and the bank account currency are the same
        if self.from_fee and self.from_fee > 0:
            if self.from_fee_currency != self.from_bank_currency:
                frappe.throw(f"Fee currency '{self.from_fee_currency}' does not match bank account currency '{self.from_bank_currency}'")
        if self.to_fee and self.to_fee > 0:
            if self.to_fee_currency != self.to_bank_currency:
                frappe.throw(f"Fee currency '{self.to_fee_currency}' does not match bank account currency '{self.to_bank_currency}'")

def get_bank_account(bank):
    bank_account = frappe.get_value("Bank Account", bank, "account")
    if not bank_account:
        frappe.throw(f"Bank Account '{bank}' does not have an account")
    return bank_account
    

@frappe.whitelist()
def get_charge_account_details(company, charge_type):
    MOPA = frappe.qb.DocType("Mode of Payment Account")
    CT = frappe.qb.DocType("Charge Type")
    A = frappe.qb.DocType("Account")

    result  = frappe.qb.from_(MOPA).join(CT).on(
        MOPA.parent == CT.name
    ).join(A).on(
        MOPA.default_account == A.name
    ).select(
        MOPA.default_account,
        A.account_currency
    ).where(
        (MOPA.company == company)&
        (CT.name == charge_type)
    ).run(as_dict=True)

    if not result:
        frappe.throw(f"Charge Type '{charge_type}' does not have a default account for company '{company}'")
    
    return result[0]
