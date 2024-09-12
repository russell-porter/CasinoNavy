frappe.listview_settings["Transaction Ledger"] = {
	add_fields: [
		"transaction_type",
	],
	get_indicator: function (doc) {
		const status_colors = {
			Deposit: "green",
			Withdrawal: "red",
		};
		return [__(doc.transaction_type), status_colors[doc.transaction_type], "transaction_type,=," + doc.transaction_type];
	},
}