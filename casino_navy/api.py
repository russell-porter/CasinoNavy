import frappe
from frappe.utils import today
from datetime import datetime
from casino_navy.casino_navy.report.transactions_summary.transactions_summary import get_data
from frappe.exceptions import ValidationError


@frappe.whitelist()
def get_balance(company, supplier, date=None):
    """
    Get the balance for a specific supplier for a given company up to a specified date.

    :param company: Name of the company.
    :param supplier: Name of the supplier.
    :param date: Optional. The date up to which the balance is calculated. Defaults to today's date.
    :return: Balance data retrieved from the transactions summary.
    :raises ValidationError: If any of the input parameters are invalid.
    :raises frappe.DoesNotExistError: If the company or supplier does not exist in the system.
    """
    # Validate input parameters
    if not company or not supplier:
        raise ValidationError("Both 'company' and 'supplier' parameters are required.")
    
    try:
        # Validate date if provided
        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            date = today()
    except ValueError:
        raise ValidationError("Invalid date format. Please provide a valid date (YYYY-MM-DD).")

    # Check if the company and supplier exist
    if not frappe.db.exists("Company", company):
        raise frappe.DoesNotExistError(f"Company '{company}' does not exist.")
    if not frappe.db.exists("Supplier", supplier):
        raise frappe.DoesNotExistError(f"Supplier '{supplier}' does not exist.")
    
    # Prepare filters for the report
    filters = {
        "company": company,
        "supplier": supplier,
        "from_date": "2020-01-01",
        "to_date": date,
        "summary": 1
    }
    
    try:
        # Retrieve the balance data
        balance_data = get_data(filters)
    except Exception as e:
        frappe.log_error(message=str(e), title="Error in get_balance API")
        raise Exception from e

    return balance_data



@frappe.whitelist()
def add_transaction(data):
    """
    Add a new transaction to the Transaction Ledger.

    :param data: JSON string containing transaction details.
    :return: Success message or validation errors.
    """
    try:
        # Parse the input data
        transaction_data = frappe.parse_json(data)

        # Define the required fields
        required_fields = ["company", "transaction_type", "supplier", "date", "amount", "fee"]

        # Check if required fields are provided
        missing_fields = [field for field in required_fields if not transaction_data.get(field)]
        if missing_fields:
            frappe.throw(f"Missing required fields: {', '.join(missing_fields)}")
        
        date  = transaction_data["date"]
        
        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            date = today()

        # Prepare the document for insertion
        transaction = frappe.get_doc({
            "doctype": "Transaction Ledger",
            "company": transaction_data["company"],
            "transaction_type": transaction_data["transaction_type"],
            "supplier": transaction_data["supplier"],
            "date": date,
            "amount": transaction_data["amount"],
            "fee": transaction_data["fee"],
            "transaction_id": transaction_data.get("transaction_id"),  # Optional
            "third_party_reference": transaction_data.get("third_party_reference"),  # Optional
            "username": transaction_data.get("username"),  # Optional
            "description": transaction_data.get("description")  # Optional
        })

        # Insert the document into the database
        transaction.save()

        return {"status": "success", "message": "Transaction added successfully", "transaction": transaction.as_dict()}

    except Exception as e:
        frappe.log_error("Add Transaction Ledger API Error", frappe.get_traceback())
        return {"status": "error", "message": str(e)}
