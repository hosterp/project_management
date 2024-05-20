from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import exceptions
from openerp.exceptions import except_orm, ValidationError
import time


class Employeelnsurance(models.Model):
	_name = 'employee.insurance'
	# _rec_name = 'policy_id'

	name = fields.Char('Name', compute="_get_name", store=True)
	employee_id = fields.Many2one('hr.employee', string='Employees', required=True)
	gender = fields.Selection(related="employee_id.gender", string="Gender")
	# qualification = fields.Char('Qualification')
	# techinical_training = fields.Char('Techinical Training')
	# birthday = fields.Date('DOB')
	# age =fields.Char('Age')
	# work_phone = fields.Char('Phone No')
	birthday = fields.Date(related="employee_id.birthday", string="DOB")
	age =fields.Char(related="employee_id.age", string="Age")
	work_phone = fields.Char(related="employee_id.work_phone",string="Phone No")
	# address = fields.Text('Address')
	user_category = fields.Selection(related="employee_id.user_category", string='User Category',required=True)
	# designation = fields.Char('Designation')
	# sponsor = fields.Char('Sponsored By')
	# date = fields.Date(string='Date',default=datetime.today(),required=True,readonly=True)
	insurer_id = fields.Many2one('res.partner',string="Insurer")
	policy_id = fields.Many2one('policy.type', string='Type of Policy')
	is_company_policy = fields.Boolean(string='Is a company policy?')
	claim_duration = fields.Float(related="policy_id.duration", string='Claim Duration')
	premium_amount = fields.Float(string='Premium Amount')
	emp_paid_amt = fields.Float(string='Amount Paid By Employee')

	comp_contribution = fields.Float(string='Company Contribution')
	empol_contribution = fields.Float(string='Staff Contribution')
	no_of_person = fields.Integer('No of Persons')
	policy_no = fields.Char('Policy No')
	insured_code = fields.Char('Insured Code')
	commit_date = fields.Date('Commit Date')
	renew_date = fields.Date('Renewal Date')
	state = fields.Selection([('draft','draft'),
							('paid','Paid'),
							('closed','Collected')
							], default='draft')


	insurance_status = fields.Selection([('draft','Active'),
							('renew','Renewed'),
							('closed','Closed')
							], default='draft', string="Insurance Status")	

	@api.multi
	@api.depends('policy_id','policy_no','insured_code')
	def _get_name(self):
		for record in self:
			if record.policy_id.name and record.policy_no and record.insured_code:
				record.name = record.policy_id.name + '/' + record.insured_code + '/' + record.policy_no


	@api.multi
	def view_renewal(self):
		self.insurance_status = 'renew'
		new_commit_date = (datetime.strptime(self.renew_date,'%Y-%m-%d') + relativedelta(days=1)).strftime('%Y-%m-%d')
		new_renew_date = (datetime.strptime(self.renew_date,'%Y-%m-%d') + relativedelta(months=12)).strftime('%Y-%m-%d')
		print 'new_commit_date-----------', new_commit_date, new_renew_date
		self.env['employee.insurance'].create({'employee_id': self.employee_id.id,
											'policy_id': self.policy_id.id,
											'insurer_id': self.insurer_id.id,
											'is_company_policy': self.is_company_policy,
											'premium_amount': self.premium_amount,
											'empol_contribution': self.empol_contribution,
											'comp_contribution': self.comp_contribution,
											'no_of_person': self.no_of_person,
											'insured_code': self.insured_code,
											'commit_date': new_commit_date,
											'renew_date': new_renew_date,
											})

	@api.multi
	def view_close(self):
		self.insurance_status = 'closed'


class PolicyType(models.Model):
	_name = 'policy.type'

	name = fields.Char('Policy')
	duration = fields.Float('Duration')
	account_id = fields.Many2one('account.account', string="Account")


class EmployeeInsurancePayment(models.Model):
	_name = 'insurance.policy.payment'

	date = fields.Date('Date',default=fields.Date.today)
	payment_ids = fields.One2many('insurance.policy.payment.line','line_id')
	state = fields.Selection([('draft','Draft'),
							('send_approval','Send To Approval'),
							('approved','Approved'),
							('paid','Paid')], default="draft")
	policy_id = fields.Many2one('policy.type', string='Type of Policy')

	@api.multi
	def view_action_payment(self):
		amount = 0
		for record  in self.payment_ids:
			amount += record.amount
		res = {
			'name': 'Insurance Payment',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'policy.payment.wizard',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_payment_id': self.id,'default_payment_amount': amount},

		}

		return res

	@api.multi
	def view_action_send_approval(self):
		self.state = 'send_approval'

	@api.multi
	def view_action_approve(self):
		self.state = 'approved'



class EmployeeInsurancePaymentLine(models.Model):
	_name = 'insurance.policy.payment.line'

	line_id = fields.Many2one('insurance.policy.payment')
	emp_policy_id = fields.Many2one('employee.insurance', string="Policy")
	employee_id = fields.Many2one(related="emp_policy_id.employee_id", string='Employee')
	amount = fields.Float(related="emp_policy_id.premium_amount", string='Premium Amount')
	insured_code = fields.Char(related="emp_policy_id.insured_code", string='Insured No')
	commit_date = fields.Date(related="emp_policy_id.commit_date", string='Commit Date')
	renew_date = fields.Date(related="emp_policy_id.renew_date", string='Renewal Date')
	insurer_id = fields.Many2one('res.partner',related="emp_policy_id.insurer_id", string='Insurer')

	@api.onchange('emp_policy_id')
	def onchange_emp_policy_id(self):
		policy_ids = []
		policy_ids = [policy.id for policy in self.env['employee.insurance'].search([('policy_id','=',self.line_id.policy_id.id)])]
		return {
				'domain': {
					'emp_policy_id': [('id','in',policy_ids)]
				}
			}

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.emp_policy_id = self.env['employee.insurance'].search([('policy_id','=',self.line_id.policy_id.id),('employee_id','=',self.employee_id.id),('state','=','draft')], order="commit_date asc", limit=1).id

		record = self.env['employee.insurance'].search([('policy_id','=',self.line_id.policy_id.id),('state','=','draft')])
		ids = []
		for item in record:
			ids.append(item.employee_id.id)
		return {'domain': {'employee_id': [('id', 'in', ids)]}}

class EmployeeClaim(models.Model):
	_name = 'insurance.policy.claim'

	date = fields.Date('Date',default=fields.Date.today)
	emp_policy_id = fields.Many2one('employee.insurance', string="Policy")
	employee_id = fields.Many2one(related="emp_policy_id.employee_id", string='Employee')
	insurer_id = fields.Many2one('res.partner',related="emp_policy_id.insurer_id", string='Insurer')
	insured_code = fields.Char(related="emp_policy_id.insured_code", string='Insured No')
	commit_date = fields.Date(related="emp_policy_id.commit_date", string='Commit Date')
	renew_date = fields.Date(related="emp_policy_id.renew_date", string='Renewal Date')
	state = fields.Selection([('draft','draft'),
							('active','Active'),
							('claim_request','Claim Request'),
							('claim_release','Claim Release')
							], default='draft')
	amount_paid = fields.Float(string='Amount Paid To Employee', compute="_compute_paid_amount")
	requested_claim_amount = fields.Float(string='Requested Claim Amount')
	released_claim_amount = fields.Float(string='Released Claim Amount')
	claim_asset_account_id = fields.Many2one('account.account', string="Employee Claim Refund Account")
	company_expense_account_id = fields.Many2one('account.account', string="Company Expense Account Account")
	payment_ids = fields.One2many('claim.payment.wizard', 'claim_id', string="Payments To Employee")


	@api.multi
	@api.depends('payment_ids')
	def _compute_paid_amount(self):
		for record in self:
			amount = 0
			for rec in record.payment_ids:
				amount += rec.amount_paid
			record.amount_paid = amount

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.emp_policy_id = self.env['employee.insurance'].search([('employee_id','=',self.employee_id.id),('state','=','paid')], order="commit_date asc", limit=1).id

		record = self.env['employee.insurance'].search([('state','=','paid')])
		ids = []
		for item in record:
			ids.append(item.employee_id.id)
		return {'domain': {'employee_id': [('id', 'in', ids)]}}


	@api.multi
	def view_action_payment(self):
		# 

		res = {
			'name': 'Claim Amount Payment To Employee',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'claim.payment.wizard',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_claim_id': self.id,
						# 'default_amount_paid': self.amount_paid,
						'default_claim_asset_account_id': self.claim_asset_account_id.id,
						},

		}

		return res

	@api.multi
	def button_claim_request(self):
		self.state = 'claim_request'
		if self.requested_claim_amount == False:
			raise exceptions.ValidationError('Requested Claim Amount should not be zero.')


	@api.multi
	def button_claim_release(self):
		res = {
			'name': 'Claim Amount Release',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'claim.release.wizard',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_claim_id': self.id,
						# 'default_amount_paid': self.amount_paid,
						'default_claim_asset_account_id': self.claim_asset_account_id.id,
						},

		}

		return res


class EmployeeClaimPaymentWizard1(models.Model):
	_name = 'claim.payment.wizard'

	date = fields.Date('Date',default=fields.Date.today)
	claim_id = fields.Many2one('insurance.policy.claim')
	payment_mode = fields.Many2one('account.journal', string="Mode of Payment", domain=[('type','in',['cash','bank'])])
	claim_asset_account_id = fields.Many2one('account.account', string="Employee Claim Refund Account")
	amount_paid = fields.Float(string='Maximum Claim Amount')

	@api.multi
	def button_payment(self):
		self.claim_id.state = 'active'
		# self.claim_id.amount_paid = self.amount_paid
		# self.claim_id.claim_asset_account_id = self.claim_asset_account_id.id
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.payment_mode.id,
							'date': datetime.now(),
							})
		# print 'account---------------------', self.payment_mode.default_credit_account_id.id, self.payment_id.policy_id.account_id.id
		
		line_id = move_line.create({
								'account_id': self.payment_mode.default_credit_account_id.id,
								'name': 'Claim Amount',
								'credit': self.amount_paid,
								'debit': 0,
								'move_id': move_id.id,
								})
			
		line_id = move_line.create({
								'account_id': self.claim_asset_account_id.id,
								'name': 'Claim Amount',
								'credit': 0,
								'debit': self.amount_paid,
								'move_id': move_id.id,
								})
		move_id.button_validate()


class EmployeeClaimReleaseWizard(models.TransientModel):
	_name = 'claim.release.wizard'

	date = fields.Date('Date',default=fields.Date.today)
	claim_id = fields.Many2one('insurance.policy.claim')
	payment_mode = fields.Many2one('account.journal', string="Mode of Payment", domain=[('type','in',['cash','bank'])])
	released_claim_amount = fields.Float(string='Released Claim Amount')
	company_expense_account_id = fields.Many2one('account.account', string="Company Expense Account Account")

	@api.multi
	def button_release(self):
		self.claim_id.state = 'claim_release'
		self.claim_id.released_claim_amount = self.released_claim_amount
		self.claim_id.company_expense_account_id = self.company_expense_account_id.id
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.payment_mode.id,
							'date': datetime.now(),
							})
		# print 'account---------------------', self.payment_mode.default_credit_account_id.id, self.payment_id.policy_id.account_id.id
		
		line_id = move_line.create({
								'account_id': self.payment_mode.default_credit_account_id.id,
								'name': 'Released Claim Amount',
								'debit': self.released_claim_amount,
								'credit': 0,
								'move_id': move_id.id,
								})
			
		line_id = move_line.create({
								'account_id': self.claim_id.claim_asset_account_id.id,
								'name': 'Claim Amount',
								'credit': self.claim_id.amount_paid,
								'debit': 0,
								'move_id': move_id.id,
								})
		print 'z----------------------------------', self.released_claim_amount, self.claim_id.amount_paid
		if self.released_claim_amount < self.claim_id.amount_paid:
			print 'z1111-------------------', self.claim_id.amount_paid - self.released_claim_amount
			line_id = move_line.create({
									'account_id': self.company_expense_account_id.id,
									'name': 'Claim Amount',
									'credit': 0,
									'debit': self.claim_id.amount_paid - self.released_claim_amount,
									'move_id': move_id.id,
									})
		move_id.button_validate()


class EmployeeInsurancePaymentWizard(models.Model):
	_name = 'policy.payment.wizard'

	date = fields.Date('Date',default=fields.Date.today)
	payment_id = fields.Many2one('insurance.policy.payment')
	payment_mode = fields.Many2one('account.journal', string="Mode of Payment", domain=[('type','in',['cash','bank'])])
	payment_amount = fields.Float('Payment Amount')


	@api.multi
	def button_payment(self):
		self.payment_id.state = 'paid'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.payment_mode.id,
							'date': datetime.now(),
							})
		print 'account---------------------', self.payment_mode.default_credit_account_id.id, self.payment_id.policy_id.account_id.id
		
		line_id = move_line.create({
								'account_id': self.payment_mode.default_credit_account_id.id,
								'name': 'Insurance Amount',
								'credit': self.payment_amount,
								'debit': 0,
								'move_id': move_id.id,
								})
			
		line_id = move_line.create({
								'account_id': self.payment_id.policy_id.account_id.id,
								'name': 'Insurance Amount',
								'credit': 0,
								'debit': self.payment_amount,
								'move_id': move_id.id,
								})
		move_id.button_validate()

		for record in self.payment_id.payment_ids:
			if record.emp_policy_id.renew_date:

				# record.state = 'paid'
				record.emp_policy_id.write({'state':'paid'})

				# date = (datetime.strptime(record.emp_policy_id.renew_date,'%Y-%m-%d') + relativedelta(months=12)).strftime('%Y-%m-%d')
				# self.env['employee.insurance'].create({'employee_id': record.employee_id.id,
				# 									'policy_id': record.emp_policy_id.policy_id.id,
				# 									# 'policy_no': record.emp_policy_id.policy_no,
				# 									'is_company_policy': record.emp_policy_id.is_company_policy,
				# 									'premium_amount': record.emp_policy_id.premium_amount,
				# 									'empol_contribution': record.emp_policy_id.empol_contribution,
				# 									'comp_contribution': record.emp_policy_id.comp_contribution,
				# 									'no_of_person': record.emp_policy_id.no_of_person,
				# 									'insured_code': record.emp_policy_id.insured_code,
				# 									'commit_date': record.emp_policy_id.renew_date,
				# 									'renew_date': date,
				# 									})









class ManagementPolicy(models.Model):
	_name = 'management.policy'

	# name = fields.Char('Policy')
	name = fields.Char('Name', compute="_get_name")
	res_company_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Policy Holder')
	policy_type_id = fields.Many2one('management.policy.type', 'Policy Type')
	is_money_back_policy = fields.Boolean(related="policy_type_id.is_money_back_policy", string='Is a money back policy?')
	# insurance_company_id = fields.Many2one('insurance.company', 'Company Name')
	account_id = fields.Many2one('account.account', string="Account")
	policy_no = fields.Char('Policy No')
	commencement_date = fields.Date('Commencement Date')
	remittance_date = fields.Date('Last Remittance Date')
	maturity_date = fields.Date('Maturity Date')
	payment_mode = fields.Selection([('mly','Monthly'),
									('qly','Quarterly'),
									('hly','Half Yearly'),
									('yly','Yearly'),
									],'Payment Mode')
	sum_assured = fields.Float('Sum Assured')
	premium_amount = fields.Float('Premium Amount')
	remarks = fields.Text('Remarks')
	payment_ids = fields.One2many('management.policy.line','line_id')
	state = fields.Selection([('draft','Draft'),
							('active','Active'),
							('surrender','Surrender'),
							('matured','Matured'),
							('release','Released'),
							], default='draft')
	released_sum_assured = fields.Float("Released Sum Assurance")
	released_survival_benefit = fields.Float('Survival Benefit')
	released_amount = fields.Float('Total Released Amount')
	released_payment_mode = fields.Many2one('account.journal', string="Mode of Payment", domain=[('type','in',['cash','bank'])])
	survival_benefit_account_id = fields.Many2one('account.account', string="Survival Benefit Account")

	mn_ids = fields.One2many('management.policy.money_back','payment_id', domain=[('state','=','released')])

	@api.multi
	def _get_name(self):
		for record in self:
			if record.policy_type_id.name and record.policy_no:
				record.name = record.policy_type_id.name + '-' + record.policy_no


	@api.model
	def _cron_manag_policy_maturity_entries(self):
		print 'f3333333333333333333333ggggggggggggggggggggggggggggggggggggg', fields.Date.today()
		date_today = fields.Date.today()
		for day in self.env['management.policy'].search([('maturity_date','=',date_today)]):
			print 'day1------------------', day, day.state
			day.write({'state':'matured'})
			print 'day2------------------', day, day.state

	@api.multi
	def button_active(self):
		self.state = 'active'

	@api.multi
	def view_action_payment(self):
		# 

		res = {
			'name': 'Management Policy Release',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'management.policy.release.wizard',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_payment_id': self.id, 'default_sum_assured': self.sum_assured},

		}

		return res

	@api.multi
	def view_action_surrender(self):
		# 

		res = {
			'name': 'Management Policy Surrender',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'management.policy.release.wizard',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_payment_id': self.id},

		}

		return res

	@api.multi
	def view_action_mn(self):
		# 

		res = {
			'name': 'Management Policy Surrender',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'management.policy.money_back',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_payment_id': self.id},

		}

		return res




class ManagementPolicyMnWizard(models.Model):
	_name = 'management.policy.money_back'

	payment_id = fields.Many2one('management.policy')
	date = fields.Date('Date',default=fields.Date.today)
	payment_mode = fields.Many2one('account.journal', string="Mode of Payment", domain=[('type','in',['cash','bank'])])
	payment_amount = fields.Float('Released Amount')
	state = fields.Selection([('draft','Draft'),('released','Released')], default="draft")
	# survival_benefit_account_id = fields.Many2one('account.account', string="Survival Benefit Account")

	


	@api.multi
	def button_policy_money_back(self):
		self.state = 'released'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.payment_mode.id,
							'date': datetime.now(),
							})
		# print 'account---------------------', self.payment_mode.default_credit_account_id.id, self.payment_id.policy_type_id.account_id.id
		
		line_id = move_line.create({
								'account_id': self.payment_mode.default_credit_account_id.id,
								'name': 'Insurance Amount',
								'debit': self.payment_amount,
								'credit': 0,
								'move_id': move_id.id,
								})
			
		line_id = move_line.create({
								'account_id': self.payment_id.account_id.id,
								'name': 'Sum Assured',
								'debit': 0,
								'credit': self.payment_amount,
								'move_id': move_id.id,
								})
		
		move_id.button_validate()




class ManagementPolicyReleaseWizard(models.Model):
	_name = 'management.policy.release.wizard'

	date = fields.Date('Date',default=fields.Date.today)
	payment_amount = fields.Float('Released Amount')
	payment_id = fields.Many2one('management.policy')
	sum_assured = fields.Float('Sum Assured')
	survival_benefit = fields.Float('Survival Benefit')
	payment_mode = fields.Many2one('account.journal', string="Mode of Payment", domain=[('type','in',['cash','bank'])])
	survival_benefit_account_id = fields.Many2one('account.account', string="Survival Benefit Account")

	@api.onchange('payment_amount')
	def onchange_amount(self):
		amount = 0
		money_back_amt = 0
		for rec in self.payment_id.payment_ids:
			if rec.state == 'paid':
				amount += rec.premium_amount
		self.sum_assured = amount
		self.survival_benefit = self.payment_amount - amount

		# if self.payment_id.is_money_back_policy == True:
		# 	for vals in self.payment_id.mn_ids:
		# 		money_back_amt += vals.payment_amount
		# 	self.sum_assured = amount
		# 	self.survival_benefit = self.payment_amount - (amount - money_back_amt)
		# else:
		# 	self.sum_assured = amount
		# 	self.survival_benefit = self.payment_amount - amount


	@api.multi
	def button_policy_release(self):
		if self.payment_id.state == 'active':
			self.payment_id.state = 'surrender'
		if self.payment_id.state == 'matured':
			self.payment_id.state = 'release'
		self.payment_id.released_sum_assured = self.sum_assured
		self.payment_id.released_survival_benefit = self.survival_benefit
		self.payment_id.released_amount = self.payment_amount
		self.payment_id.released_payment_mode = self.payment_mode
		self.payment_id.survival_benefit_account_id = self.survival_benefit_account_id
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.payment_mode.id,
							'date': datetime.now(),
							})
		# print 'account---------------------', self.payment_mode.default_credit_account_id.id, self.payment_id.policy_type_id.account_id.id
		
		line_id = move_line.create({
								'account_id': self.payment_mode.default_credit_account_id.id,
								'name': 'Insurance Amount',
								'debit': self.payment_amount,
								'credit': 0,
								'move_id': move_id.id,
								})
			
		line_id = move_line.create({
								'account_id': self.payment_id.account_id.id,
								'name': 'Sum Assured',
								'debit': 0,
								'credit': self.sum_assured,
								'move_id': move_id.id,
								})
		if self.survival_benefit != False:
			line_id = move_line.create({
									'account_id': self.survival_benefit_account_id.id,
									'name': 'Survival Benefit',
									'debit': 0,
									'credit': self.survival_benefit,
									'move_id': move_id.id,
								})
		move_id.button_validate()

	


		

class ManagementPolicyLine(models.Model):
	_name = 'management.policy.line'

	line_id = fields.Many2one('management.policy', string="Policy No.")
	date = fields.Date('Payment Date')
	premium_amount = fields.Float('Premium Amount')
	payment_mode = fields.Many2one('account.journal', string="Mode of Payment", domain=[('type','in',['cash','bank'])])
	state = fields.Selection([('draft','draft'),
							('paid','Paid')
							], default='draft')	
	account_id = fields.Many2one('account.account', related="line_id.account_id", string="Account")
	res_company_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", related="line_id.res_company_id", string='Policy Holder')
	policy_type_id = fields.Many2one('management.policy.type', related="line_id.policy_type_id", string= 'Policy Type')
	policy_no = fields.Char( related="line_id.policy_no", string='Policy No')
	commencement_date = fields.Date( related="line_id.commencement_date", string='Commencement Date')
	remittance_date = fields.Date( related="line_id.remittance_date", string='Last Remittance Date')
	maturity_date = fields.Date( related="line_id.maturity_date", string='Maturity Date')
	payment_duration = fields.Selection([('mly','Monthly'),
									('qly','Quarterly'),
									('hly','Half Yearly'),
									('yly','Yearly'),
									], related="line_id.payment_mode", string='Payment Mode')
	sum_assured = fields.Float( related="line_id.sum_assured", string='Sum Assured')


	@api.multi
	def button_payment(self):
		self.state = 'paid'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.payment_mode.id,
							'date': datetime.now(),
							})
		line_id = move_line.create({
								'account_id': self.payment_mode.default_credit_account_id.id,
								'name': 'Insurance Amount',
								'credit': self.premium_amount,
								'debit': 0,
								'move_id': move_id.id,
								})
			
		line_id = move_line.create({
								'account_id': self.account_id.id,
								'name': 'Insurance Amount',
								'credit': 0,
								'debit': self.premium_amount,
								'move_id': move_id.id,
								})
		move_id.button_validate()





	@api.model
	def _cron_monthly_manag_policy_entries(self):
		print 'f11111111111111111111111gggggggggggggggggggggggg'
		for day in self.env['management.policy'].search([('payment_mode','=','mly'),('state','=','active')]):
			lines = self.env['management.policy.line'].search([('line_id','=', day.id)])
			if lines:
				date = self.env['management.policy.line'].search([('line_id','=', day.id)])[-1].date
			else:
				date = day.commencement_date

			day3 = time.strftime("%A", time.strptime(date, "%Y-%m-%d"))
			month =  datetime.strptime(date, "%Y-%m-%d").month

			date_start_dt = fields.Datetime.from_string(date)
			dt = date_start_dt + relativedelta(months=1)
			new_date = fields.Datetime.to_string(dt)
			
			print 'newdate11111111111111111111============================', new_date
			 
			self.env['management.policy.line'].create({'line_id':day.id,'date':new_date, 'premium_amount':day.premium_amount,'state':'draft'})


			
	@api.model
	def _cron_quarterly_manag_policy_entries(self):
		print 'f222222222222222222gggggggggggggggggggggggggggggggg'
		for day in self.env['management.policy'].search([('payment_mode','=','qly'),('state','=','active')]):
			lines = self.env['management.policy.line'].search([('line_id','=', day.id)])
			if lines:
				date = self.env['management.policy.line'].search([('line_id','=', day.id)])[-1].date
			else:
				date = day.commencement_date

			day3 = time.strftime("%A", time.strptime(date, "%Y-%m-%d"))
			month =  datetime.strptime(date, "%Y-%m-%d").month

			date_start_dt = fields.Datetime.from_string(date)
			dt = date_start_dt + relativedelta(months=3)
			new_date = fields.Datetime.to_string(dt)
			
			print 'newdate222222222222222222===============================', new_date

			 
			self.env['management.policy.line'].create({'line_id':day.id,'date':new_date, 'premium_amount':day.premium_amount,'state':'draft'})




	@api.model
	def _cron_half_yearly_manag_policy_entries(self):
		print 'f3333333333333333333333ggggggggggggggggggggggggggggggggggggg'
		for day in self.env['management.policy'].search([('payment_mode','=','hly'),('state','=','active')]):
			lines = self.env['management.policy.line'].search([('line_id','=', day.id)])
			if lines:
				date = self.env['management.policy.line'].search([('line_id','=', day.id)])[-1].date
			else:
				date = day.commencement_date

			day3 = time.strftime("%A", time.strptime(date, "%Y-%m-%d"))
			month =  datetime.strptime(date, "%Y-%m-%d").month

			date_start_dt = fields.Datetime.from_string(date)
			dt = date_start_dt + relativedelta(months=6)
			new_date = fields.Datetime.to_string(dt)
			
			print 'newdate333333333333333333333=====================', new_date


			self.env['management.policy.line'].create({'line_id':day.id,'date':new_date, 'premium_amount':day.premium_amount,'state':'draft'})



	@api.model
	def _cron_yearly_manag_policy_entries(self):
		print 'f44444444444444444444444yyyyyyyyyyyyyyyyyyyy'
		for day in self.env['management.policy'].search([('payment_mode','=','yly'),('state','=','active')]):
			lines = self.env['management.policy.line'].search([('line_id','=', day.id)])
			if lines:
				date = self.env['management.policy.line'].search([('line_id','=', day.id)])[-1].date
			else:
				date = day.commencement_date

			day3 = time.strftime("%A", time.strptime(date, "%Y-%m-%d"))
			month =  datetime.strptime(date, "%Y-%m-%d").month

			date_start_dt = fields.Datetime.from_string(date)
			dt = date_start_dt + relativedelta(months=12)
			new_date = fields.Datetime.to_string(dt)
			
			print 'newdate444444444444444444444[[[]]]]]]]]]]]', new_date
			 
			self.env['management.policy.line'].create({'line_id':day.id,'date':new_date, 'premium_amount':day.premium_amount,'state':'draft'})



class ManagementPolicyType(models.Model):
	_name = 'management.policy.type'

	name = fields.Char('Insurance Company')
	is_money_back_policy = fields.Boolean('Is a money back policy?', default=False)
