# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import Query, Criterion, Case
from frappe.query_builder.custom import ConstantColumn
from frappe.utils import getdate, nowdate


def execute(filters=None):
    if not filters:
        filters = {}

    return get_columns(), get_entries(filters)


def get_columns():
    columns = [
        {
            "label": _("Payment Document Type"),
            "fieldname": "payment_document_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Payment Entry"),
            "fieldname": "payment_entry",
            "fieldtype": "Dynamic Link",
            "options": "payment_document_type",
            "width": 140,
        },
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Cheque/Reference No"), "fieldname": "cheque_no", "width": 120},
        {"label": _("Clearance Date"), "fieldname": "clearance_date", "fieldtype": "Date", "width": 120},
        {
            "label": _("Against Account"),
            "fieldname": "against",
            "fieldtype": "Link",
            "options": "Account",
            "width": 200,
        },
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
    ]

    return columns



def get_entries(filters):
    JV  = frappe.qb.DocType("Journal Entry")
    JVA  = frappe.qb.DocType("Journal Entry Account")
    PE = frappe.qb.DocType("Payment Entry")

    conditions = []

    bank_account = frappe.get_value("Bank Account", filters.get('account'))

    journal_entries = Query.from_(JV).join(JVA).on(
        JV.name == JVA.parent
    ).select(
        ConstantColumn("Journal Entry").as_("payment_document_type"),
        JV.name.as_("payment_entry"),
        JV.posting_date,
        JV.cheque_no,
        JV.clearance_date,
        JVA.against_account,
        (JVA.debit - JVA.credit).as_("amount"),
    ).where(
        (JV.docstatus == 1)&
        (JVA.account == bank_account)
    )

    payment_entries = Query.from_(PE).select(
        ConstantColumn("Payment Entry").as_("payment_document_type"),
        PE.name.as_("payment_entry"),
        PE.posting_date,
        PE.reference_no,
        PE.clearance_date,
        PE.party,
        Case()
        .when(PE.paid_from == bank_account, (PE.paid_amount * -1) - PE.total_taxes_and_charges)
        .else_(PE.received_amount).as_("amount")
    ).where(
        (PE.docstatus == 1)&
        (
            (PE.paid_from == bank_account) |
            (PE.paid_to  == bank_account)
        )
    )

    query = journal_entries + payment_entries

    if filters.get("from_date"):
        conditions.append(query.posting_date >= filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append(query.posting_date <= filters.get("to_date"))

    return frappe.qb.from_(query).select('*').where(
        Criterion.all(conditions)
    ).orderby(query.posting_date).run(debug=True)


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
