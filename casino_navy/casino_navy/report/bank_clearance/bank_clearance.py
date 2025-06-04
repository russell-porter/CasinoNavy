# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import Query, Criterion, Case, functions as fn
from frappe.query_builder.custom import ConstantColumn
from frappe.utils import getdate, nowdate


def execute(filters=None):
    if not filters:
        filters = {}

    return get_columns(filters), get_entries(filters)


def get_columns(filters):
    if filters.get("summary"):
        columns = [
            {
                "label": _("Bank"),
                "fieldname": "bank",
                "fieldtype": "Data",
                "width": 230,
            },
            {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 280},
        ]
    
    else:
        columns = [
            # {
            #     "label": _("Payment Document Type"),
            #     "fieldname": "payment_document_type",
            #     "fieldtype": "Data",
            #     "width": 130,
            # },
            {
                "label": _("Payment Entry"),
                "fieldname": "payment_entry",
                "fieldtype": "Dynamic Link",
                "options": "payment_document_type",
                "width": 140,
            },
            {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
            {"label": _("Cheque/Reference No"), "fieldname": "cheque_no", "width": 250},
            {
                "label": _("Against Account"),
                "fieldname": "against_account",
                "fieldtype": "Link",
                "options": "Account",
                "width": 220,
            },
            {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 200},
        ]

    return columns


def get_entries(filters):
    JV  = frappe.qb.DocType("Journal Entry")
    JVA  = frappe.qb.DocType("Journal Entry Account")
    BA = frappe.qb.DocType("Bank Account")
    PE = frappe.qb.DocType("Payment Entry")

    conditions = [
        JV.docstatus == 1,
        BA.is_company_account == 1,
        # JVA.account == bank_account,
        # BA.account == bank_account,
    ]

    if filters.get("from_date"):
        conditions.append(JV.posting_date >= filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append(JV.posting_date <= filters.get("to_date"))
    
    if filters.get('bank_account'):
        conditions.append(BA.name == filters.get('bank_account'))

    query =  Query.from_(JV).join(JVA).on(
        JV.name == JVA.parent
    ).join(BA).on(
        (JVA.account == BA.account)&
        (JV.company == BA.company)
    ).select(
        ConstantColumn("Journal Entry").as_("payment_document_type"),
        BA.name.as_("bank"),
        JV.name.as_("payment_entry"),
        JV.posting_date,
        JV.cheque_no,
        JV.clearance_date,
        JVA.against_account,
        (JVA.debit - JVA.credit).as_("amount"),
    ).where( Criterion.all(conditions))
    
    if filters.get("summary"):
        return frappe.qb.from_(query).select(
            query.bank,
            fn.Sum(query.amount).as_("amount")
        ).groupby(query.bank).run(as_dict=True)
    else:
        return frappe.qb.from_(query).select('*').orderby(query.posting_date).run(as_dict=True)



@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_account_list(doctype, txt, searchfield, start, page_len, filters):
    BA = frappe.qb.DocType("Bank Account")
    A = frappe.qb.DocType("Account")

    conditions = [
        A.account_type == 'Bank',
        A.is_group == 0
    ]

    if filters.get("company"):
        conditions.append(BA.company == filters.get("company"))

    if txt:
        conditions.append(BA.name.like(f"%{txt}%"))

    return frappe.qb.from_(BA).join(A).on(
        BA.account == A.name
    ).select(
        BA.name
    ).where( Criterion.all(conditions) ).run(debug=True)
