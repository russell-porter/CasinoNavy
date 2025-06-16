// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["E-Wallet Summary"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1,
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_end(),
			"reqd": 1
		},
		{
			"fieldname": "presentation_currency",
			"label": __("Currency"),
			"fieldtype": "Select",
			"options": erpnext.get_presentation_currency_list()
		},
		{
			"fieldname": "bank_account",
			"label": __("Bank Account"),
			"fieldtype": "Link",
			"options": "Bank Account",
			"get_query": function() {
				return {
					filters: {
						"company": frappe.query_report.get_filter_value("company"),
						"is_company_account": 1,
					}
				};
			}
		},
		{
			"fieldname": "summary",
			"label": __("Summary"),
			"fieldtype": "Check",
			"default": 1,
			"on_change": function() {
				const summary = frappe.query_report.get_filter_value("summary");
				frappe.query_report.toggle_filter_display("bank_account", !!summary);
			}
		}
	],

	onload: function(report) {
		const summary = frappe.query_report.get_filter_value("summary");
		frappe.query_report.toggle_filter_display("bank_account", !!summary);
	}
};