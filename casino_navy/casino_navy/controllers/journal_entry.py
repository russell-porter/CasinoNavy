import frappe

@frappe.whitelist()
def get_reference_entry(doctype, name):
    """
        Get the reference journal entry of a document

        :param doctype: The document type
        :param name: The document name
        :return: The name of the reference journal entry
    """

    filters = {
        "reference_type": doctype,
        "reference_name": name
    }
    if name := frappe.db.exists("Journal Entry", filters):
        return name

    return None
