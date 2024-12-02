import frappe
from frappe import qb
from frappe.query_builder import Query

DI = qb.DocType('Data Import')
IL = qb.DocType('Data Import Log')

@frappe.whitelist()
def delete_all_data_imports(name):
    # We will delete in three steps
    # 1. Delete related documents
    # 2. Delete related logs
    # 3. Delete the data import itself

    doc = frappe.get_doc("Data Import", name)

    if doc.reference_doctype not in ("Transaction Ledger", "Balance Transfer"):
        frappe.throw("This option is only available for Transaction Ledger and Balance Transfer")

    REF = qb.DocType(doc.reference_doctype)
    
    references = Query.from_(IL).select(
        IL.docname
    ).where(
        (IL.data_import == doc.name)&
        (IL.success == 1)
    )
    frappe.publish_realtime(
        "delete_data_import",
        {
            "current": 1,
            "total": 3,
            "success": True,
            "mapping_name": doc.name,
        },
        doctype=doc.doctype,
        docname=doc.name
    )

    # Step 1
    if references:
        qb.from_(REF).delete().where(REF.name.isin(references)).run()
    
    frappe.publish_realtime("delete_data_import_refresh", {"mapping": doc.name})

    # Step 2
    qb.from_(IL).delete().where(IL.data_import == doc.name).run()
    
    frappe.publish_realtime("delete_data_import_complete", {"mapping": doc.name})

    # Step 3
    doc.delete()
