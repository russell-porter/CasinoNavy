# Copyright (c) 2024, Lewin Villar and contributors
# For license information, please see license.txt

from frappe import qb
from frappe.query_builder import Case, Criterion, Query, functions as fn
from frappe.query_builder.custom import ConstantColumn

T = qb.DocType('Transaction Ledger')
BT = qb.DocType('Balance Transfer')

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
				'fieldname': 'withdraw',
				'label': 'Withdraw',
				'fieldtype': 'Currency',
				'width': 140
			},
			{
				'fieldname': 'withdraw_fee',
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
				'fieldname': 'withdraw',
				'label': 'Withdraw',
				'fieldtype': 'Currency',
				'width': 130
			},
			{
				'fieldname': 'withdraw_fee',
				'label': 'Withdraw Fee',
				'fieldtype': 'Currency',
				'width': 130
			}
		]

	return columns

def get_data(filters):
	conditions = []
	trax_in_conditions = []
	trax_out_conditions = []
	
	if filters.get('from_date'):
		conditions.append(T.date >= filters.get('from_date'))
		trax_in_conditions.append(BT.date >= filters.get('from_date'))
		trax_out_conditions.append(BT.date >= filters.get('from_date'))
	if filters.get('to_date'):
		conditions.append(T.date <= filters.get('to_date'))
		trax_in_conditions.append(BT.date <= filters.get('to_date'))
		trax_out_conditions.append(BT.date <= filters.get('to_date'))
	if filters.get('supplier'):
		conditions.append(T.supplier == filters.get('supplier'))
		trax_in_conditions.append(BT.to_supplier == filters.get('supplier'))
		trax_out_conditions.append(BT.from_supplier == filters.get('supplier'))
	if filters.get('company'):
		conditions.append(T.company == filters.get('company'))
		trax_in_conditions.append(BT.to_company == filters.get('company'))
		trax_out_conditions.append(BT.from_company == filters.get('company'))

	if filters.get('summary'):
		# Deposits and Withdrawals
		dep_with = Query.from_(T).select(
			T.supplier,
			(Case().when(T.transaction_type == 'Deposit', T.amount).else_(0)).as_('deposit'),
			(Case().when(T.transaction_type == 'Deposit', T.fee).else_(0)).as_('deposit_fee'),
			(Case().when(T.transaction_type == 'Withdraw', T.amount).else_(0)).as_('withdraw'),
			(Case().when(T.transaction_type == 'Withdraw', T.fee).else_(0)).as_('withdraw_fee'),
			(Case().when(T.transaction_type == 'Deposit', T.amount).else_(-T.amount) ).as_('balance'),
		).where(Criterion.all(conditions)).orderby(T.supplier)
		# Transfers In
		transfers_in = Query.from_(BT).select(
			BT.to_supplier.as_('supplier'),
			(BT.amount).as_('deposit'),
			(BT.to_fee).as_('deposit_fee'),
			(BT.docstatus).as_('withdraw'),
			(BT.docstatus).as_('withdraw_fee'),
			(BT.amount).as_('balance')
		).where(Criterion.all(trax_in_conditions))
		# Transfers Out
		transfers_out = Query.from_(BT).select(
			BT.from_supplier.as_('supplier'),
			(BT.docstatus).as_('deposit'),
			(BT.docstatus).as_('deposit_fee'),
			(BT.amount).as_('withdraw'),
			(BT.from_fee).as_('withdraw_fee'),
			(-BT.amount).as_('balance')
		).where(Criterion.all(trax_out_conditions))

		query = dep_with + transfers_in + transfers_out

		return qb.from_(query).select(
			query.supplier,
			fn.Sum(query.deposit).as_('deposit'),
			fn.Sum(query.deposit_fee).as_('deposit_fee'),
			fn.Sum(query.withdraw).as_('withdraw'),
			fn.Sum(query.withdraw_fee).as_('withdraw_fee'),
			fn.Sum(query.balance).as_('balance')
		).groupby(query.supplier).run(as_dict=True)
	else:
		dep_with = Query.from_(T).select(
			T.supplier,
			T.date,
			T.transaction_type,
			Case().when(T.transaction_type == 'Deposit', T.amount).else_(0).as_('deposit'),
			Case().when(T.transaction_type == 'Deposit', T.fee).else_(0).as_('deposit_fee'),
			Case().when(T.transaction_type == 'Withdraw', T.amount).else_(0).as_('withdraw'),
			Case().when(T.transaction_type == 'Withdraw', T.fee).else_(0).as_('withdraw_fee'),
		).where(Criterion.all(conditions))

		transfers_in = Query.from_(BT).select(
			BT.to_supplier.as_('supplier'),
			BT.date,
			ConstantColumn('Transfer In').as_('transaction_type'),
			BT.amount.as_('deposit'),
			BT.to_fee.as_('deposit_fee'),
			BT.docstatus.as_('withdraw'),
			BT.docstatus.as_('withdraw_fee'),
		).where(Criterion.all(trax_in_conditions))

		transfers_out = Query.from_(BT).select(
			BT.from_supplier.as_('supplier'),
			BT.date,
			ConstantColumn('Transfer Out').as_('transaction_type'),
			BT.docstatus.as_('deposit'),
			BT.docstatus.as_('deposit_fee'),
			(BT.amount).as_('withdraw'),
			BT.from_fee.as_('withdraw_fee'),
		).where(Criterion.all(trax_out_conditions))

		query = dep_with + transfers_in + transfers_out

		return qb.from_(query).select(
			query.supplier,
			query.date,
			query.transaction_type,
			query.deposit.as_('deposit'),
			query.deposit_fee.as_('deposit_fee'),
			query.withdraw.as_('withdraw'),
			query.withdraw_fee.as_('withdraw_fee'),
		).orderby(query.date).run(as_dict=True)