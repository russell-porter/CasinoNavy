// Copyright (c) 2024, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Balance Transfer', {
	refresh(frm) {
		$.map(["set_queries", "add_custom_buttons"], (field) => {
			frm.trigger(field);
		});
	},
	set_queries(frm) {
		frm.set_query("from_bank", function() {
			return {
				"filters": {
					"company": frm.doc.from_company,
					"is_company_account": 1
				}
			}
		});
		frm.set_query("to_bank", function() {
			return {
				"filters": {
					"company": frm.doc.to_company,
					"is_company_account": 1
				}
			}
		});
	
		set_query(frm, "from_fee_type", "Fee", frm.doc.from_company);
		set_query(frm, "to_fee_type", "Fee", frm.doc.to_company);
		set_query(frm, "from_charge_type", "Expense", frm.doc.from_company);
		set_query(frm, "to_charge_type", "Income", frm.doc.to_company);
		
	},
	add_custom_buttons(frm) {
		if (frm.doc.docstatus !=1 )
			return 
		
		frm.add_custom_button(__("View Ledger"), () => {
			frappe.route_options = {
				"reference_type": frm.doc.doctype,
				"reference_name": frm.doc.name,
			}
			frappe.set_route("List", "Journal Entry");
		});
	},
});

function set_query(frm, field, type, company) {
	const query = 'casino_navy.casino_navy.doctype.charge_type.charge_type.get_charge_type_query';
	const filters = { company, type };
	frm.set_query(field, function() {
		return { query, filters }
	});
}