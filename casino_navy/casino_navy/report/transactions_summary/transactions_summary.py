# Copyright (c) 2024, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import qb
from frappe.query_builder import Case, Criterion, Query, functions as fn

T = qb.DocType('Transaction Ledger')

def execute(filters=None):
	return get_columns(filters), get_data(filters)

def get_columns(filters):
	columns = []
	if filters.get('summary'):
		columns = [
			{
				'fieldname': 'supplier',
				'label': 'Supplier',
				'fieldtype': 'Link',
				'options': 'Supplier',
				'width': 200
			},
			{
				'fieldname': 'deposit',
				'label': 'Deposit',
				'fieldtype': 'Currency',
				'width': 140
			},
			{
				'fieldname': 'deposit_fee',
				'label': 'Deposit Fee',
				'fieldtype': 'Currency',
				'width': 140
			},
			{
				'fieldname': 'withdrawal',
				'label': 'Withdrawal',
				'fieldtype': 'Currency',
				'width': 140
			},
			{
				'fieldname': 'withdrawal_fee',
				'label': 'Withdrawal Fee',
				'fieldtype': 'Currency',
				'width': 140
			},
			{
				'fieldname': 'balance',
				'label': 'Balance',
				'fieldtype': 'Currency',
				'width': 140
			}
			
		]

	else:
		columns = [
			{
				'fieldname': 'supplier',
				'label': 'Supplier',
				'fieldtype': 'Link',
				'options': 'Supplier',
				'width': 180
			},
			{
				'fieldname': 'date',
				'label': 'Date',
				'fieldtype': 'Date',
				'width': 100
			},
			{
				'fieldname': 'transaction_type',
				'label': 'Transaction Type',
				'fieldtype': 'Data',
				'width': 150
			},
			{
				'fieldname': 'deposit',
				'label': 'Deposit',
				'fieldtype': 'Currency',
				'width': 140
			},
			{
				'fieldname': 'deposit_fee',
				'label': 'Deposit Fee',
				'fieldtype': 'Currency',
				'width': 130
			},
			{
				'fieldname': 'withdrawal',
				'label': 'Withdrawal',
				'fieldtype': 'Currency',
				'width': 130
			},
			{
				'fieldname': 'withdrawal_fee',
				'label': 'Withdrawal Fee',
				'fieldtype': 'Currency',
				'width': 130
			},			
		]

	return columns

def get_data(filters):
	conditions = []
	
	if filters.get('from_date'):
		conditions.append(T.date >= filters.get('from_date'))
	if filters.get('to_date'):
		conditions.append(T.date <= filters.get('to_date'))
	if filters.get('supplier'):
		conditions.append(T.supplier == filters.get('supplier'))

	if filters.get('summary'):
		return qb.from_(T).select(
			T.supplier,
			fn.Sum(Case().when(T.transaction_type == 'Deposit', T.amount).else_(0)).as_('deposit'),
			fn.Sum(Case().when(T.transaction_type == 'Deposit', T.fee).else_(0)).as_('deposit_fee'),
			fn.Sum(Case().when(T.transaction_type == 'Withdrawal', T.amount).else_(0)).as_('withdrawal'),
			fn.Sum(Case().when(T.transaction_type == 'Withdrawal', T.fee).else_(0)).as_('withdrawal_fee'),
			fn.Sum(Case().when(T.transaction_type == 'Deposit', T.amount).else_(-T.amount) ).as_('balance'),
		).where(Criterion.all(conditions)).groupby(T.supplier).orderby(T.supplier).run(as_dict=True)
	else:
		return qb.from_(T).select(
			T.supplier,
			T.date,
			T.transaction_type,
			Case().when(T.transaction_type == 'Deposit', T.amount).else_(0).as_('deposit'),
			Case().when(T.transaction_type == 'Deposit', T.fee).else_(0).as_('deposit_fee'),
			Case().when(T.transaction_type == 'Withdrawal', T.amount).else_(0).as_('withdrawal'),
			Case().when(T.transaction_type == 'Withdrawal', T.fee).else_(0).as_('withdrawal_fee'),
		).where(Criterion.all(conditions)).orderby(T.date).run(as_dict=True)