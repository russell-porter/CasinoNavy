// Copyright (c) 2024, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Transaction Ledger', {
	validate(frm) {
		frappe.db.get_value("Supplier", frm.doc.supplier, "enforce_fees").then( ({message}) => {
			if(message.enforce_fees)
				frappe.show_alert({
					"message": __("The Fee was enforced by the system"),
					"indicator": "orange"
				})
		})
	}
});
