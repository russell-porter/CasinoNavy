// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Charge Type', {
	refresh(frm) {
		frm.trigger('set_queries');
	},
	set_queries(frm) {
		// Let's set show onl accounts that belongs to the company on the table accounts 
		frm.set_query("default_account", "accounts", function(doc, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					is_group: 0
				}
			};
		});
	}
});