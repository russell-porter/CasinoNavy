// Copyright (c) 2024, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Transaction Ledger', {
	refresh(frm){
		$.map(["set_queries", "add_custom_buttons"], (field) => {
			frm.trigger(field);
		});
		
	},
	validate(frm) {
		frappe.db.get_value("Supplier", frm.doc.supplier, "enforce_fees").then( ({message}) => {
			if(message.enforce_fees)
				frappe.show_alert({
					"message": __("The Fee was enforced by the system"),
					"indicator": "orange"
				})
		})
	},
	set_queries(frm) {
		frm.set_query("bank", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"is_company_account": 1
				}
			}
		});
		
		$.map(["fee_type", "charge_type"], (field) => {
			frm.set_query(field, function() {
				return {
					query: 'casino_navy.casino_navy.doctype.charge_type.charge_type.get_charge_type_query',
					filters: {
						company: frm.doc.company,
						type: field == "fee_type" ? "Fee" : frm.doc.transaction_type == "Deposit" ? "Income" : "Expense"
					}
				}
			});
		});
	},
	add_custom_buttons(frm) {
		if (frm.doc.docstatus !=1 )
			return 
		
		frm.add_custom_button(__("View Ledger"), () => {
			const method = "casino_navy.casino_navy.controllers.journal_entry.get_reference_entry";
			const {doctype, name} = frm.doc;
			const args = {doctype, name};
			frappe.call(method, args).then(({ message }) => {
				if (!message){
					frappe.msgprint("No records found!!")
					return;
				}	
				frappe.route_options = {
					"company": frm.doc.company,
					"from_date": frm.doc.date,
					"to_date": frm.doc.date,
					"voucher_no": message,
					"include_dimensions": 1,
					"include_default_book_entries": 1
				}
				frappe.set_route("query-report", "General Ledger");

			});
		});
	},
	transaction_type(frm) {
		frm.set_value("charge_type", "");
	},
});
