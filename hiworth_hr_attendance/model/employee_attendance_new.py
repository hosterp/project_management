from openerp import models, fields, api, _
from datetime import datetime, timedelta
from openerp.osv import osv


class AttendanceEntryWizard(models.TransientModel):
	_name = 'attendance.entry.wizard'


	@api.model
	def default_get(self, default_fields):
		vals = super(AttendanceEntryWizard, self).default_get(default_fields)
		line_ids2 = []
		for line in self.env.context.get('active_ids'):
			values = {
				'employee_id': line,
				'attendance': 'full'
			}
			line_ids2.append((0, False, values ))
			vals['line_ids'] = line_ids2
		return vals

	date = fields.Date('Date From',default=fields.Datetime.now())
	date_to = fields.Date('Date To',default=fields.Datetime.now())
	line_ids = fields.One2many('attendance.entry.wizard.line', 'wizard_id', 'Employees')
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)

	@api.multi
	def do_mass_update(self):
		for rec in self:
			attendance = self.env['hiworth.hr.attendance']
			date =  datetime.strptime(rec.date,"%Y-%m-%d")
			differ = datetime.strptime(rec.date_to,"%Y-%m-%d") - datetime.strptime(rec.date,"%Y-%m-%d")
			count = 0
			for count in range((differ.days+1)):
				for lines in rec.line_ids:
					print "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",date
					
					entry = self.env['hiworth.hr.attendance'].search([('name','=',lines.employee_id.id),('date','=',date)])
					print 'entry--------------------------', entry
					if entry:
						raise osv.except_osv(_('Warning!'), _("Already entered attendance for employee '%s on %s'") % (lines.employee_id.name,date.strftime("%d-%m-%Y")))
	
					else:
						values = {'date': date,
							  'name': lines.employee_id.id,
							  'user_id': rec.user_id.id,
							  'attendance': lines.attendance}
						attendance.create(values)
				date = date + timedelta(days=1)
					




				




class AttendanceEntryWizardLine(models.TransientModel):
	_name = 'attendance.entry.wizard.line'

	employee_id = fields.Many2one('hr.employee', string='Employees', domain=[('cost_type','=','permanent')])
	attendance = fields.Selection([('full', 'Full Present'),
								('half','Half Present'),
								('absent','Absent'),
								   ('leave','Approved Leave'),
								   ('day','Day&Night'),
								   ('compens', 'Compensation')
								], default='full', string='Attendance')
	wizard_id = fields.Many2one('attendance.entry.wizard', string='Wizard')




class PayslipCashPaymentWizard(models.Model):
	_name = 'employee.payslip.cash.wizard'

	@api.model
	def _default_journal(self):
		return self.env['account.journal'].search([('name','=','Cash')], limit=1)

	@api.model
	def _default_account(self):
		return self.env['account.account'].search([('name','=','Cash')], limit=1)


	@api.model
	def default_get(self, default_fields):
		vals = super(PayslipCashPaymentWizard, self).default_get(default_fields)
		line_ids2 = []
		list = []
		print 'contxt-------------------------------', self.env.context.get('active_ids')
		for ids in self.env.context.get('active_ids'):
			list.append(ids)
		payslips = self.env['hr.payslip'].search([('id','in', list)])
		for line in payslips:
			amount = 0
			payment_amount = 0
			if line.state != 'done':
				raise osv.except_osv(_('Error!'),_("You are trying to create the payment of payslips which is not in confirmed state."))
			for ln in line.line_ids:
				if ln.rule_id.related_type == 'net':
					amount = ln.total
			print 'line--------------------------------', line.id
			cash_amt = 0
			bank_amt = 0
			cash = self.env['employee.payslip.cash.wizard.line'].search([('payslip_id','=', line.id)])
			print 'cash-----', cash
			if cash:
				for cash_entry in cash:
					cash_amt += cash_entry.payment_amount
			bank = self.env['employee.payslip.bank.wizard.line'].search([('payslip_id','=', line.id)])
			if bank:
				for bank_entry in bank:
					bank_amt += bank_entry.payment_amount
			payment_amount = amount - (cash_amt + bank_amt)
			print 'cash------------------------------', amount, cash_amt, bank_amt
			values = {
				'employee_id': line.employee_id.id,
				'payslip_id': line.id,
				'payment_amount': payment_amount
			}
			line_ids2.append((0, False, values ))
			vals['line_ids'] = line_ids2
		return vals


	@api.multi
	def do_confirm_payment(self):
		self.state = 'confirmed'
		amount = 0
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		values = {
				'journal_id': self.journal_id.id,
				'date': self.date,
				}
		move_id = move.create(values)

		for rec in self.line_ids:
			if rec.employee_id.petty_cash_account.id == False:
				raise osv.except_osv(_('Error!'),_("There is no petty cash account for employee") + ' ' + rec.employee_id.name)

			values2 = {
					'account_id': rec.employee_id.petty_cash_account.id,
					'name': 'Paid To' + ' ' + rec.employee_id.name,
					'debit': rec.payment_amount,
					'credit': 0,
					'move_id': move_id.id,
					}

			line_id = move_line.create(values2)
			amount += rec.payment_amount
			cash_amt = 0
			bank_amt = 0
			cash = self.env['employee.payslip.cash.wizard.line'].search([('payslip_id','=', rec.payslip_id.id)])
			if cash:
				for cash_entry in cash:
					cash_amt += cash_entry.payment_amount
			bank = self.env['employee.payslip.bank.wizard.line'].search([('payslip_id','=', rec.payslip_id.id)])
			if bank:
				for bank_entry in bank:
					bank_amt += bank_entry.payment_amount
			rule = self.env['hr.salary.rule'].search([('related_type','=','net')])

			# payslip_line = self.env['hr.payslip.line'].search([('slip_id','=', rec.payslip_id.id)])
			# print 'slip------------------------------------', payslip_line
			
			# payslip_line = self.env['hr.payslip.line'].search([('rule_id','=',rule.id)])
			# print 'rul------------------------------------', payslip_line

			payslip_line = self.env['hr.payslip.line'].search([('slip_id','=', rec.payslip_id.id),('rule_id','=',rule.id)])
			# print 'new------------------------------------', payslip_line, payslip_line.total, cash_amt, bank_amt
			if payslip_line.total == cash_amt + bank_amt:
				payslip_line.slip_id.state = 'paid'



			for rule in rec.payslip_id.line_ids:
				if rule.rule_id.related_type == 'insurance':
					# print 'vvv666-------------------------', rule.insurance_id.emp_paid_amt, rule.total,rule.insurance_id.empol_contribution
					rule.insurance_id.emp_paid_amt = rule.insurance_id.emp_paid_amt + rule.total
					if rule.insurance_id.emp_paid_amt == rule.insurance_id.empol_contribution:
						rule.insurance_id.state = 'closed'


				if rule.rule_id.related_type == 'welfare':
					current_total = rule.total
					welfares = self.env['employee.welfare.fund'].search([('state','=','active'),('employee_id','=', rec.employee_id.id)])
					for welf_id in welfares:
						if current_total >= (welf_id.amount - welf_id.repay_amount):
							current_total = current_total - (welf_id.amount - welf_id.repay_amount)
							welf_id.repay_amount = welf_id.repay_amount + (welf_id.amount - welf_id.repay_amount)
						else:
							welf_id.repay_amount = welf_id.repay_amount + current_total
							current_total = 0

						if welf_id.amount == welf_id.repay_amount:
							welf_id.state = 'closed'



		if amount != 0:
			values = {
				'account_id': self.account_id.id,
				'name': 'Salary Payment',
				'debit': 0,
				'credit': amount,
				'move_id': move_id.id,
				}
			line_id = move_line.create(values)
		move_id.button_validate()


	date = fields.Date('Date',default=fields.Datetime.now())
	line_ids = fields.One2many('employee.payslip.cash.wizard.line', 'wizard_id', 'Employees')
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
	account_id = fields.Many2one('account.account',string='Account', default=_default_account)
	journal_id = fields.Many2one('account.journal',string='Journal', domain="[('type','in',['cash','bank'])]", default=_default_journal)
	state = fields.Selection([
							('draft','Draft'),
							('confirmed','Confirmed')
							], default="draft", string="Status")



class PayslipCashPaymentWizardLine(models.Model):
	_name = 'employee.payslip.cash.wizard.line'

	employee_id = fields.Many2one('hr.employee', string='Employees', domain=[('cost_type','=','permanent')])
	wizard_id = fields.Many2one('employee.payslip.cash.wizard', string='Wizard')
	payment_amount = fields.Float('Payment Amount')
	payslip_id = fields.Many2one('hr.payslip', 'Payslip')
	state = fields.Selection(related="wizard_id.state")



class PayslipBankPaymentWizard(models.Model):
	_name = 'employee.payslip.bank.wizard'


	@api.model
	def default_get(self, default_fields):
		vals = super(PayslipBankPaymentWizard, self).default_get(default_fields)
		line_ids2 = []
		list = []
		print 'contxt-------------------------------', self.env.context.get('active_ids')
		for ids in self.env.context.get('active_ids'):
			list.append(ids)
		payslips = self.env['hr.payslip'].search([('id','in', list)])
		for line in payslips:
			amount = 0
			payment_amount = 0
			if line.state != 'done':
				raise osv.except_osv(_('Error!'),_("You are trying to create the payment of payslips which is not in confirmed state."))
			for ln in line.line_ids:
				if ln.rule_id.related_type == 'net':
					amount = ln.total
			print 'line--------------------------------', line.id
			cash_amt = 0
			bank_amt = 0
			cash = self.env['employee.payslip.cash.wizard.line'].search([('payslip_id','=', line.id)])
			if cash:
				for cash_entry in cash:
					cash_amt += cash_entry.payment_amount
			bank = self.env['employee.payslip.bank.wizard.line'].search([('payslip_id','=', line.id)])
			if bank:
				for bank_entry in bank:
					bank_amt += bank_entry.payment_amount
			payment_amount = amount - (cash_amt + bank_amt)
			values = {
				'employee_id': line.employee_id.id,
				'payslip_id': line.id,
				'payment_amount': payment_amount
			}
			line_ids2.append((0, False, values ))
			vals['line_ids'] = line_ids2
		return vals


	@api.multi
	def do_confirm_payment(self):
		self.state = 'confirmed'
		amount = 0
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		list = []
		for rec in self.line_ids:

			if rec.bank_id.id not in list:
				list.append(rec.bank_id.id)

		for bank in list:
			bank_record = self.env['res.partner.bank'].search([('id','=',bank)])
			print '0--------------------', bank_record.id
			print '1--------------------', bank_record.journal_id.name
			print '2--------------------', bank_record.journal_id.id, bank_record.journal_id.default_credit_account_id.id
			amount = 0
			values = {
				# 'journal_id': rec.bank.journal_id.id,
				'journal_id': bank_record.journal_id.id,
				'date': self.date,
				}
			move_id = move.create(values)

			record = self.env['employee.payslip.bank.wizard.line'].search([('wizard_id','=', self.id),('bank_id','=',bank)])
			for rec in record:
				print 'rec11-----------------------------------', rec.payment_amount
				amount += rec.payment_amount
				cash_amt = 0
				bank_amt = 0
				print 'rec------------------', rec.employee_id.petty_cash_account.id
				if rec.employee_id.petty_cash_account.id == False:
					raise osv.except_osv(_('Error!'),_("There is no petty cash account for employee") + ' ' + rec.employee_id.name)
					

				values2 = {
					'account_id': rec.employee_id.petty_cash_account.id,
					'name': 'Paid To' + ' ' + rec.employee_id.name,
					'debit': rec.payment_amount,
					'credit': 0,
					'move_id': move_id.id,
					}

				line_id = move_line.create(values2)
				# cash = self.env['employee.payslip.cash.wizard.line'].search([('payslip_id','=', line.id)]).payment_amount
				# bank = self.env['employee.payslip.bank.wizard.line'].search([('payslip_id','=', line.id)]).payment_amount
				# payslip_line = self.env['hr.payslip.line'].search([('line_id','=', rec.payslip_id.id)])
				# if payslip_line.total == cash + bank:
				# 	payslip_line.state = 'paid'
				cash = self.env['employee.payslip.cash.wizard.line'].search([('payslip_id','=', rec.payslip_id.id)])
				if cash:
					for cash_entry in cash:
						cash_amt += cash_entry.payment_amount
				bank = self.env['employee.payslip.bank.wizard.line'].search([('payslip_id','=', rec.payslip_id.id)])
				if bank:
					for bank_entry in bank:
						bank_amt += bank_entry.payment_amount
				rule = self.env['hr.salary.rule'].search([('related_type','=','net')], limit=1)
				payslip_line = self.env['hr.payslip.line'].search([('slip_id','=', rec.payslip_id.id),('rule_id','=',rule.id)])
				print 'new------------------------------------', payslip_line, payslip_line.total, cash_amt, bank_amt
				if payslip_line.total == cash_amt + bank_amt:
					payslip_line.slip_id.state = 'paid'


				for rule in rec.payslip_id.line_ids:
					if rule.rule_id.related_type == 'insurance':
						print 'vvv666-------------------------', rule.rule_id.name, rule.insurance_id.emp_paid_amt, rule.total,rule.insurance_id.empol_contribution
						rule.insurance_id.emp_paid_amt = rule.insurance_id.emp_paid_amt + rule.total
						if rule.insurance_id.emp_paid_amt == rule.insurance_id.empol_contribution:
							rule.insurance_id.state = 'closed'

			if amount != 0:
				values = {
					'account_id':bank_record.journal_id.default_credit_account_id.id,
					'name': 'Salary Payment',
					'debit': 0,
					'credit': amount,
					'move_id': move_id.id,
					}
				line_id = move_line.create(values)
				print 'ssssssssssssssssssssssssssssssssssssss'
			move_id.button_validate()


		

	date = fields.Date('Date',default=fields.Datetime.now())
	line_ids = fields.One2many('employee.payslip.bank.wizard.line', 'wizard_id', 'Employees')
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
	state = fields.Selection([('draft','Draft'),('confirmed','Confirmed')], default="draft", string="Status")



class PayslipBankPaymentWizardLine(models.Model):
	_name = 'employee.payslip.bank.wizard.line'

	employee_id = fields.Many2one('hr.employee', string='Employees', domain=[('cost_type','=','permanent')])
	wizard_id = fields.Many2one('employee.payslip.bank.wizard', string='Wizard')
	bank_id = fields.Many2one('res.partner.bank', string='Bank')
	payment_amount = fields.Float('Payment Amount')
	payslip_id = fields.Many2one('hr.payslip', 'Payslip')
	state = fields.Selection(related="wizard_id.state")
