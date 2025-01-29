// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank Clearance"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")?
				locals[":Company"][frappe.defaults.get_user_default("Company")]["default_bank_account"]: "",
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"width": "80"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_end()
		},
		{
			"fieldname":"bank_account",
			"label": __("Bank Account"),
			"fieldtype": "Link",
			"options": "Bank Account",
			"reqd": 1,
			"get_query": function() {
				return {
					"query": "casino_navy.casino_navy.report.bank_clearance.bank_clearance.get_account_list",
					"filters": {
						"company":  frappe.query_report.get_filter_value("company")
					}
				}
			}
		},
	]
}

