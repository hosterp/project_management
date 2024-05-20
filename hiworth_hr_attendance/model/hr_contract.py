from openerp import models, fields, api, _
from datetime import datetime, date, timedelta
from openerp.osv import osv
from dateutil.relativedelta import relativedelta
from datetime import *


class ContractSalaryRule(models.Model):
	_name = 'contract.salary.rule'

	rule_id = fields.Many2one('hr.salary.rule', 'Rule')
	account_id = fields.Many2one('account.account', 'Related Account')
	contract_id = fields.Many2one('hr.contract', 'Contract')
	amount = fields.Float('Amount')
	percentage = fields.Float('Percentage')
	related_type = fields.Selection('Rule Process Type', related='rule_id.related_type')
	rule_type = fields.Selection([
								('fixed','Fixed'),
								('percent','Percentage'),
								# ('manual','Manual'),
								], 'Type')
	is_related = fields.Boolean('Is related to any daily activities', default=False)
	# related_type = fields.Selection([('canteen','canteen')], 'Related Process')
	per_day_amount = fields.Float('Per Day Amount')
	employer_amt_paid_by = fields.Selection([('employer','Paid by employer'),
		                               ('govt','Paid by government')
		                               ], default="employer", string="Employer Percent")

	@api.onchange('related_type','rule_id')
	def onchange_per_day_amount(self):
		if self.related_type == 'canteen':

			self.is_related = True
			self.per_day_amount = self.env['general.hr.configuration'].search([],limit=1).canteen_amount

	# @api.model
	# def create(self, vals):
	# 	print 'vals======================', vals
	# 	if vals.get('related_type') == 'canteen':
	# 		rule = self.env['contract.salary.rule'].search([('contract_id','=',vals.get('contract_id')),('related_type','=','canteen')])
	# 		if rule:
	# 			raise osv.except_osv(('Error'), ('Already Exist a rule with type "Canteen".'));
	# 	return super(ContractSalaryRule, self).create(vals)

	# @api.model
	# def create(self, vals):
	# 	print 'vals======================', vals
	# 	if vals.get('related_type') == 'canteen':
	# 		rule = self.env['contract.salary.rule'].search([('contract_id','=',self.contract_id.id),('related_type','=','canteen')])
	# 		if rule:
	# 			raise osv.except_osv(('Error'), ('Already Exist a rule with type "Canteen".'));
	# 	return super(ContractSalaryRule, self).create(vals)

	# @api.onchange('rule_type')
	# def onchange_amount(self):
	# 	if self.rule_type == 'lop':
	# 		self.amount = amount
	# 		days_count = 0
	# 		start_date = 01/05/2017
	# 		end_date = 30/05/2017
	# 		while (start_date < end_date):
	# 			day = dateutil.parser.parse(start_date).date().weekday()
	# 			if day != 1:
	# 				days_count += 1
	# 			start_date = start_date  + datetime.timedelta(days=1)
	# 			print 'days_count------------', days_count
			# lop = 
				
class HrContract(models.Model):
	_inherit = 'hr.contract'

	@api.onchange('struct_id')
	def onchange_struct_id(self):
		line_ids = []
		self.rule_lines = False
		if self.struct_id:
			for rule in self.struct_id.rule_ids:
				if rule.related_type == 'canteen':
					values = {
						'rule_id': rule.id,
						'name': rule.name,
						'is_related': True,
						'per_day_amount': self.env['general.hr.configuration'].search([],limit=1).canteen_amount,
					}
				else:
					values = {
						'rule_id': rule.id,
						'name': rule.name,
					}
				line_ids.append((0, 0, values ))
			self.rule_lines = line_ids


	@api.depends('employee_id')
	def _onchange_employee(self):
		ids = []
		for employee in self.env['hr.employee'].search([('cost_type','=','permanent')]):
		    ids.append(employee.id)
		return {'domain': {'employee_id': [('id', 'in', ids)]}}


	state = fields.Selection([('draft','Draft'),
							  ('active','Active'),
							  ('deactive','Deactive')], 'State', default='draft',)
	rule_lines = fields.One2many('contract.salary.rule', 'contract_id', 'Salary Rule')



	@api.multi
	def action_active(self):
		for rec in self:
			rec.state = 'active'
			canteen = self.env['contract.salary.rule'].search([('related_type','=','canteen'),('contract_id','=', self.id)])
			if canteen:
				rec.employee_id.canteen = True
			esi = self.env['contract.salary.rule'].search([('related_type','=','esi'),('contract_id','=', self.id)])
			if esi:
				rec.employee_id.esi = True
			pf = self.env['contract.salary.rule'].search([('related_type','=','pf'),('contract_id','=', self.id)])
			if pf:
				rec.employee_id.pf = True

		
	@api.multi
	def action_deactive(self):
		for rec in self:
			if not rec.date_end:
				raise osv.except_osv(('Error'), ('Please enter the end date of contract.'));
			rec.state = 'deactive'
			rec.employee_id.canteen = False
			rec.employee_id.esi = False
			rec.employee_id.pf = False


	@api.model
	def create(self, vals):
		if vals.get('employee_id') or 'employee_id' in vals:
			contract = self.env['hr.contract'].search([('employee_id','=', vals.get('employee_id')),('state','=','active')])
			if len(contract) != 0:
				raise osv.except_osv(('Error'), ('There is already exist a active contract for this employee.'));

		return super(HrContract, self).create(vals)

	


class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	related_type = fields.Selection([('basic','Basic'),
									('canteen','canteen'),
									('attendance','Attendance'),
									('net','Net'),
									('esi','ESI'),
									('pf','PF'),
									('insurance','Insurance'),
									('welfare','Welfare Fund'),
									], 'Related Process')
	rule_nature = fields.Selection([('deduction','Deduction'),
									('allowance','Allowance'),
									], 'Nature Of Rule')
	emloyee_ratio = fields.Float('Employee Contribution %')
	emloyer_ratio = fields.Float('Employer Contribution %')
	ratio = fields.Float('Percentage %')
	salary_limit = fields.Float('ESI Salary Limit')
	pf_sealing_limit = fields.Float('PF Sealing Limit')
	policy_id = fields.Many2one('policy.type', string='Type of Policy')

	employer_epf_ratio = fields.Float('Employer EPF %')
	eps_ratio = fields.Float('EPS %')
	edli_ratio = fields.Float('EDLI %')
	# emp_percent_limit = fields.Float('Employer Percent Limit')
	



	@api.model
	def create(self, vals):
		if vals.get('related_type'):
			rule_obj = self.env['hr.salary.rule'].search([('related_type','=',vals.get('related_type')),('related_type','!=','insurance'),('company_id','=',vals.get('company_id'))])
			if len(rule_obj) > 0:
				raise osv.except_osv(_('Warning!'), _("There is already a Salary Rule with the same Related Type"))

		return super(HrSalaryRule, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('related_type'):
			rule_obj = self.env['hr.salary.rule'].search([('id','!=', self.id),('related_type','=',vals.get('related_type')),('related_type','!=','insurance'),('company_id','=',self.company_id.id)])
			print 'self---------------------', self.id, self.related_type, rule_obj
			if len(rule_obj) > 0:
				raise osv.except_osv(_('Warning!'), _("There is already a Salary Rule with the same Related Type"))

		return super(HrSalaryRule, self).write(vals)


class CanteenDaily(models.Model):
	_name = 'canteen.daily'
	_order = "date desc"



	date = fields.Date('Date')
	employee_id = fields.Many2one('hr.employee', 'Employee')
	amount = fields.Float('Amount')
	user_id = fields.Many2one('res.users', 'User')


class CanteenEntryWizard(models.TransientModel):
	_name = 'canteen.entry.wizard'


	@api.model
	def default_get(self, default_fields):
		vals = super(CanteenEntryWizard, self).default_get(default_fields)
		line_ids2 = []
		for line in self.env.context.get('active_ids'):
			contract = self.env['hr.contract'].search([('employee_id','=',line),('state','=','active')])
			
			rule = self.env['hr.salary.rule'].search([('related_type','=','canteen')], limit=1)
			salary_rule = self.env['contract.salary.rule'].search([('rule_id','=',rule.id),('contract_id','=',contract.id)])
			print 'v--------------------------------', contract, contract.name, rule, rule.name, salary_rule
			# amount = self.env['employee.deduction.line'].search([('employee_id','=',line),('related_type','=','canteen')], limit=1).amount
			values = {
				'employee_id': line,
				'amount': salary_rule.per_day_amount if salary_rule.per_day_amount != 0 else 0

			}
			line_ids2.append((0, False, values ))
			vals['line_ids'] = line_ids2
		return vals

	date = fields.Date('Date',default=fields.Datetime.now())
	line_ids = fields.One2many('canteen.entry.wizard.line', 'wizard_id', 'Employees')
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)

	@api.multi
	def do_mass_update(self):
		for rec in self:
			canteen = self.env['canteen.daily']
			# canteen_account = self.env['general.hr.configuration'].search([], limit=1).canteen_account
			# if not canteen_account:
			# 	raise osv.except_osv(_('Warning!'), _("Please configure canteen Income account"))

			# move_line = self.env['account.move.line']
			# move = self.env['account.move']
			# journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
			# if not journal:
			# 	raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
			# if len(journal) > 1:
			# 	raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
			
			# values = {
			# 		'journal_id': journal.id,
			# 		'date': self.date,
			# 		}
			# move_id = move.create(values)
			

			# amount = 0
			# name = ""
			for lines in rec.line_ids:
				entry = self.env['canteen.daily'].search([('employee_id','=',lines.employee_id.id),('date','=',rec.date)])
				if len(entry) != 0:
					raise osv.except_osv(_('Warning!'), _("Already entered canteen attendance for Employee '%s'") % (lines.employee_id.name,))

				values = {'date': rec.date,
						  'employee_id': lines.employee_id.id,
						  'user_id': rec.user_id.id,
						  'amount': lines.amount}
				canteen.create(values)

			# 	contract = self.env['hr.contract'].search([('employee_id','=',lines.employee_id.id),('state','=','active')])
			# 	if not contract:
			# 		raise osv.except_osv(_('Warning!'), _("No Active contract is created for '%s'") % (lines.employee_id.name,))
			# 	salary_rule = self.env['contract.salary.rule'].search([('related_type','=','canteen'),('contract_id','=',contract.id)])
				
			# 	if not salary_rule:
			# 		raise osv.except_osv(_('Warning!'), _("No salary rule is defined for type 'canteen' in '%s''s contract") % (lines.employee_id.name,))
			# 	# account = self.env['contract.salary.rule'].search([('contract_id','=',contract.id),('rule_id','=',salary_rule.id)]).account_id
			# 	# print 'test===================',salary_rule
			# 	if not salary_rule.account_id:
			# 		raise osv.except_osv(_('Warning!'), _("No account linked for canteen entry to '%s'") % (lines.employee_id.name,))
			# 	values2 = {
			# 		'account_id': salary_rule.account_id.id,
			# 		'name': 'Canteen Expense',
			# 		'debit': lines.amount,
			# 		'credit': 0,
			# 		'move_id': move_id.id,
			# 		}
			# 	line_id = move_line.create(values2)
			# 	amount += lines.amount
			# 	name += lines.employee_id.name+', '

			# values3 = {
			# 		'account_id': canteen_account.id,
			# 		'name': 'Canteen Collection from ' + name,
			# 		'debit': 0,
			# 		'credit': amount,
			# 		'move_id': move_id.id,
			# 		}
			# line_id = move_line.create(values3)


				




class CanteenEntryWizardLine(models.TransientModel):
	_name = 'canteen.entry.wizard.line'

	employee_id = fields.Many2one('hr.employee', string='Employees', domain=[('cost_type','=','permanent')])
	amount = fields.Float('Amount')
	wizard_id = fields.Many2one('canteen.entry.wizard', string='Wizard')




class HrESIPayment(models.Model):
	_name = 'hr.esi.payment'

	date = fields.Date('Date', default=fields.Date.today)
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
	journal_id = fields.Many2one('account.journal',string='Journal', domain="[('type','in',['cash','bank'])]")
	state = fields.Selection([('draft','Draft'),('paid','Paid')], default="draft")
	month = fields.Selection([('January','January'),
								('February','February'),
								('March','March'),
								('April','April'),
								('May','May'),
								('June','June'),
								('July','July'),
								('August','August'),
								('September','September'),
								('October','October'),
								('November','November'),
								('December','December')], 'Month')
	line_ids = fields.One2many('esi.payment.line','line_id')
	employer_amount = fields.Float('Employer Contribution to ESI', compute="_compute_amount_total", store=True)
	employee_amount = fields.Float('Employee Contribution to ESI', compute="_compute_amount_total", store=True)
	amount_total = fields.Float('Total amount payable ESI', compute="_compute_amount_total", store=True)
	year = fields.Selection([(num, str(num)) for num in range(1900, 2080 )], 'Year', default=(datetime.now().year))


	@api.multi
	@api.depends('line_ids')
	def _compute_amount_total(self):
		for record in self:
			employer_amount = 0
			employee_amount = 0
			for rec in record.line_ids:
				employee_amount += rec.employee_amount
				employer_amount += rec.employer_amount
			record.employee_amount = employee_amount
			record.employer_amount = employer_amount
			record.amount_total = employer_amount + employee_amount

	@api.onchange('month')
	def onchange_esi(self):
		list = []
		self.line_ids = list

		if self.month:
			date = '1 '+self.month+' '+str(datetime.now().year)
			date_from = datetime.strptime(date, '%d %B %Y')
			date_to = date_from + relativedelta(day=31)
			date_from = date_from.date()
			date_to = date_to.date()

			for record in self.env['hr.employee'].search([('esi','=',True)]):
				contract = self.env['hr.contract'].search([('employee_id','=', record.id),('state','=','active')], limit=1)
				lop_amount = 0
				lop_days = 0

				for leave_type in record.leave_ids:
					taken = 0.0
					days = 0
					holiday = self.env['hr.holidays'].search([('date_from','<=', date_from),('date_to','>=', date_from),('type','=','remove'),('leave_id','=',leave_type.leave_id.id),('employee_id','=', record.id),('state','=','validate')])
					for hol_id in holiday:
						if hol_id.attendance == 'full':
							taken += hol_id.nos
						elif hol_id.attendance == 'half':
							taken += float(hol_id.nos)/2
						else:
							pass

					holiday1 = self.env['hr.holidays'].search([('date_from','<=', date_to),('date_to','>=', date_to),('type','=','remove'),('leave_id','=',leave_type.leave_id.id),('employee_id','=', record.id),('state','=','validate')])
					for hol_id1 in holiday1:
						if hol_id1.attendance == 'full':
							taken += hol_id1.nos
						elif hol_id1.attendance == 'half':
							taken += float(hol_id1.nos)/2
						else:
							pass
					# print 'taken-------------------------', taken, lop_days
					status = self.env['month.leave.status'].search([('leave_id','=', leave_type.leave_id.id),('month_id','=',date_from.month),('status_id','=', record.id)], limit=1)
					if status.allowed < taken:
						days = taken - status.allowed
					lop_days = lop_days + days
				# print 'lop_days----------------------------', lop_days

				days = {'mon':0,'tue':1,'wed':2,'thu':3,'fri':4,'sat':5,'sun':6}

				delta_day = timedelta(days=1)
				dt = date_from
				while dt <= date_to:
					if dt.weekday() == days['sun']:
						week_start = dt - relativedelta(days=6)
						week_end = dt
						# print 'weekk------------------------------------', week_start, week_end
						full = self.env['hiworth.hr.attendance'].search([('attendance','=','full'),('name','=', record.id),('date','>',week_start),('date','<',week_end)])
						half = self.env['hiworth.hr.attendance'].search([('attendance','=','half'),('name','=', record.id),('date','>',week_start),('date','<',week_end)])
						print 'len(full) + len(half)-----------------', full, half, len(full) + len(half)
						# print 'chck22---------------------------------', lop_days
						if (len(full) + (len(half)/2)) < 3:
							lop_days = lop_days + 1
						# print 'chck11---------------------------------', lop_days
					dt += delta_day

				   
				lop_amount = contract.wage/((abs((date_to - date_from).days)) + 1)
				wages_due = contract.wage - (lop_amount * lop_days)
				rule = self.env['hr.salary.rule'].search([('related_type','=','esi')], limit=1)
				employee_amount = wages_due * rule.emloyee_ratio/100
				employer_amount = wages_due * rule.emloyer_ratio/100

				values = {
					'employee_id': record.id,
					'attendance': ((abs((date_to - date_from).days)) + 1) - lop_days,
					'basic': contract.wage,
					'wages_due': wages_due,
					'employee_amount': employee_amount,
					'employer_amount': employer_amount,

				}
				list.append((0, False, values))
				self.line_ids = list



	@api.multi
	def button_payment(self):
		print 'z-----------------------------------------------------------'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		for rec in self:
			
			if self.env['general.hr.configuration'].search([],limit=1).esi_account.id == False:
				raise osv.except_osv(('Error'), ('Please configure a general account for ESI'));

			values = {
					'journal_id': self.journal_id.id,
					# 'date': rec.date,
					}
			move_id = move.create(values)

			values = {
					'account_id': self.env['general.hr.configuration'].search([],limit=1).esi_account.id,
					'name': 'ESI Payment',
					'debit': self.amount_total,
					'credit': 0,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values)
			
			values2 = {
					'account_id': self.journal_id.default_credit_account_id.id,
					'name': 'ESI Payment',
					'debit': 0,
					'credit': self.amount_total,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values2)
			move_id.button_validate()
			self.state = 'paid'


class ESIPaymentLine(models.Model):
	_name = 'esi.payment.line'

	line_id = fields.Many2one('hr.esi.payment')
	employee_id = fields.Many2one('hr.employee', 'Employee Name')
	attendance = fields.Float('Attendance')
	basic = fields.Float('Basic Pay')
	wages_due = fields.Float('Wages Due')
	employee_amount = fields.Float('Employee Amount')
	employer_amount = fields.Float('Employer Amount')



class PFPayment(models.Model):
	_name = 'pf.payment'

	date = fields.Date('Date', default=fields.Date.today)
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
	journal_id = fields.Many2one('account.journal',string='Journal', domain="[('type','in',['cash','bank'])]")
	state = fields.Selection([('draft','Draft'),('paid','Paid')], default="draft")
	month = fields.Selection([('January','January'),
								('February','February'),
								('March','March'),
								('April','April'),
								('May','May'),
								('June','June'),
								('July','July'),
								('August','August'),
								('September','September'),
								('October','October'),
								('November','November'),
								('December','December')], 'Month')
	year = fields.Selection([(num, str(num)) for num in range(1900, 2080 )], 'Year', default=(datetime.now().year))
	line_ids = fields.One2many('pf.payment.line','line_id')
	employer_amount = fields.Float('Employer Contribution to EPF', compute="_compute_amount_total", store=True)
	employee_amount = fields.Float('Employee Contribution to EPF', compute="_compute_amount_total", store=True)
	eps_amount = fields.Float('Employer Contribution to EPS', compute="_compute_amount_total", store=True)
	edli_amount = fields.Float('Empolyer Contribution to EDLI', compute="_compute_amount_total", store=True)
	amount_total = fields.Float('Total amount payable PF', compute="_compute_amount_total", store=True)
	admin_amount = fields.Float('Administrative Charges', compute="_compute_amount_total", store=True)

	
	@api.multi
	@api.depends('line_ids')
	def _compute_amount_total(self):
		for record in self:
			employer_amount = 0
			employee_amount = 0
			eps_amount = 0
			edli_amount = 0
			pf_wages = 0
			admin_percent = 0
			total_employer_amt = 0
			new_epf = 0
			new_eps = 0
			for rec in record.line_ids:
				employee_amount += rec.employee_epf
				edli_amount += rec.edli
				pf_wages += rec.pf_wages
				employer_amount += rec.employer_epf
				eps_amount += rec.employer_eps
				if rec.employer_amt_paid_by == 'employer':
			 		new_epf += rec.employer_epf
			 		new_eps += rec.employer_eps

			record.employee_amount = employee_amount
			record.employer_amount = employer_amount
			record.eps_amount = eps_amount
			record.edli_amount = edli_amount
			general = self.env['general.hr.configuration'].search([], limit=1)
			for line in general.pf_extra_ids:
				admin_percent += line.percent
			record.admin_amount = pf_wages * admin_percent

			total_employer_amt = new_epf + new_eps
			record.amount_total = total_employer_amt + employee_amount + edli_amount + (pf_wages * admin_percent)





	@api.multi
	def button_payment(self):
		print 'z-----------------------------------------------------------'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		for rec in self:
			
			if self.env['general.hr.configuration'].search([],limit=1).epf_account.id == False:
				raise osv.except_osv(('Error'), ('Please configure a general account for EPF'));

			values = {
					'journal_id': self.journal_id.id,
					# 'date': rec.date,
					}
			move_id = move.create(values)

			values = {
					'account_id': self.env['general.hr.configuration'].search([],limit=1).epf_account.id,
					'name': 'EPF Payment',
					'debit': self.amount_total,
					'credit': 0,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values)

			
			values2 = {
					'account_id': self.journal_id.default_credit_account_id.id,
					'name': 'PF Payment',
					'debit': 0,
					'credit': self.amount_total,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values2)
			move_id.button_validate()
			self.state = 'paid'




	@api.onchange('month')
	def onchange_pf(self):
		list = []
		print 'self.line_ids11111111-------------------', self.line_ids
		self.line_ids = list
		print 'self.line_ids22222222-------------------', self.line_ids

		if self.month:
			date = '1 '+self.month+' '+str(datetime.now().year)
			print 'date_from1111111111--------------------------------', date
			date_from = datetime.strptime(date, '%d %B %Y')
			date_to = date_from + relativedelta(day=31)
			date_from = date_from.date()
			date_to = date_to.date()
			print 'date_from--------------------------------', date_from.month

			for record in self.env['hr.employee'].search([('pf','=',True)]):
				contract = self.env['hr.contract'].search([('employee_id','=', record.id),('state','=','active')], limit=1)
				contract_line = self.env['contract.salary.rule'].search([('contract_id','=', contract.id),('related_type','=','pf')], limit=1)
				print 'contract_line.employer_amt_paid_by-------------------', contract_line, contract_line.employer_amt_paid_by
				lop_amount = 0
				lop_days = 0

				for leave_type in record.leave_ids:
					taken = 0.0
					days = 0
					holiday = self.env['hr.holidays'].search([('date_from','<=', date_from),('date_to','>=', date_from),('type','=','remove'),('leave_id','=',leave_type.leave_id.id),('employee_id','=', record.id),('state','=','validate')])
					for hol_id in holiday:
						if hol_id.attendance == 'full':
							taken += hol_id.nos
						elif hol_id.attendance == 'half':
							taken += float(hol_id.nos)/2
						else:
							pass

					holiday1 = self.env['hr.holidays'].search([('date_from','<=', date_to),('date_to','>=', date_to),('type','=','remove'),('leave_id','=',leave_type.leave_id.id),('employee_id','=', record.id),('state','=','validate')])
					for hol_id1 in holiday1:
						if hol_id1.attendance == 'full':
							taken += hol_id1.nos
						elif hol_id1.attendance == 'half':
							taken += float(hol_id1.nos)/2
						else:
							pass
					# print 'taken-------------------------', taken, lop_days
					status = self.env['month.leave.status'].search([('leave_id','=', leave_type.leave_id.id),('month_id','=',date_from.month),('status_id','=', record.id)], limit=1)
					if status.allowed < taken:
						days = taken - status.allowed
					lop_days = lop_days + days
				# print 'lop_days----------------------------', lop_days

				days = {'mon':0,'tue':1,'wed':2,'thu':3,'fri':4,'sat':5,'sun':6}

				delta_day = timedelta(days=1)
				dt = date_from
				while dt <= date_to:
					if dt.weekday() == days['sun']:
						week_start = dt - relativedelta(days=6)
						week_end = dt
						# print 'weekk------------------------------------', week_start, week_end
						full = self.env['hiworth.hr.attendance'].search([('attendance','=','full'),('name','=', record.id),('date','>',week_start),('date','<',week_end)])
						half = self.env['hiworth.hr.attendance'].search([('attendance','=','half'),('name','=', record.id),('date','>',week_start),('date','<',week_end)])
						print 'len(full) + len(half)-----------------', full, half, len(full) + len(half)
						# print 'chck22---------------------------------', lop_days
						if (len(full) + (len(half)/2)) < 3:
							lop_days = lop_days + 1
						# print 'chck11---------------------------------', lop_days
					dt += delta_day

				lop_amount = contract.wage/((abs((date_to - date_from).days)) + 1)
				wages_due = contract.wage - (lop_amount * lop_days)
				rule = self.env['hr.salary.rule'].search([('related_type','=','pf')], limit=1)
				if contract.wage <= rule.pf_sealing_limit:
					pf_wages = contract.wage
				if contract.wage > rule.pf_sealing_limit:
					pf_wages = rule.pf_sealing_limit
				edli = pf_wages * rule.edli_ratio/100
				employee_epf = pf_wages * rule.emloyee_ratio/100
				employer_epf = pf_wages * rule.employer_epf_ratio/100
				employer_eps = pf_wages * rule.eps_ratio/100

				values = {
					'employee_id': record.id,
					'attendance': ((abs((date_to - date_from).days)) + 1) - lop_days,
					'basic': contract.wage,
					'wages_due': wages_due,
					'pf_wages': pf_wages,
					'edli': edli,
					'employee_epf': employee_epf,
					'employer_epf': employer_epf,
					'employer_eps': employer_eps,
					'employer_amt_paid_by': contract_line.employer_amt_paid_by,

				}
				list.append((0, False, values))
				self.line_ids = list

class PFPaymentLine(models.Model):
	_name = 'pf.payment.line'

	line_id = fields.Many2one('hr.pf.payment')
	employee_id = fields.Many2one('hr.employee', 'Employee Name')
	attendance = fields.Float('Attendance')
	basic = fields.Float('Basic Pay')
	wages_due = fields.Float('Wages Due')
	pf_wages = fields.Float('PF Wages')
	edli = fields.Float('EDLI Amount')
	employee_epf = fields.Float('Employee EPF Amount')
	employer_epf = fields.Float('Employer EPF Amount')
	employer_eps = fields.Float('Employer EPS Amount')
	employer_amt_paid_by = fields.Selection([('employer','Paid by employer'),
		                               ('govt','Paid by government')
		                               ], string="Employer Percent")





class EmployeeWelfareFund(models.Model):
	_name = 'employee.welfare.fund'

	date = fields.Date('Date', default=fields.Date.today)
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
	journal_id = fields.Many2one('account.journal',string='Journal', domain="[('type','in',['cash','bank'])]")
	state = fields.Selection([('draft','Draft'),('active','Active'),('closed','Closed')], default="draft")
	employee_id = fields.Many2one('hr.employee', 'Employee Name')
	amount = fields.Float('Released Amount')
	repay_amount = fields.Float('Amount Paid by Employee')
	remarks = fields.Text('Remarks')

	@api.multi
	def button_release(self):
		print 'z-----------------------------------------------------------'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		for rec in self:
			
			if self.env['general.hr.configuration'].search([],limit=1).welfare_account.id == False:
				raise osv.except_osv(('Error'), ('Please configure a general account for EPF'));

			values = {
					'journal_id': self.journal_id.id,
					# 'date': rec.date,
					}
			move_id = move.create(values)

			values = {
					'account_id': self.env['general.hr.configuration'].search([],limit=1).welfare_account.id,
					'name': 'Welfare Fund Release',
					'debit': self.amount,
					'credit': 0,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values)

			
			values2 = {
					'account_id': self.journal_id.default_credit_account_id.id,
					'name': 'Welfare Fund Release',
					'debit': 0,
					'credit': self.amount,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values2)
			move_id.button_validate()
			self.state = 'active'
	
	





class GeneralHrConfigurationWizard(models.TransientModel):
	_name = 'general.hr.configuration.wizard'

	canteen_account = fields.Many2one('account.account', 'Canteen Account')
	canteen_amount = fields.Float('Canteen Amount')
	esi_payment_date = fields.Integer('Last Date of Payment')
	pf_payment_date = fields.Integer('Last Date of Payment')
	esi_account = fields.Many2one('account.account', 'ESI Account')
	epf_account = fields.Many2one('account.account', 'EPF Account')
	welfare_account = fields.Many2one('account.account', 'Employee Welfare Account')

	pf_extra_ids = fields.One2many('general.hr.configuration.wizard.line', 'line_id')

	fin1_start = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])

	fin1_end = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])
	fin2_start = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])
	fin2_end = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])

	@api.model
	def default_get(self, vals):
		res = super(GeneralHrConfigurationWizard, self).default_get(vals)
		config = self.env['general.hr.configuration'].search([], limit=1)
		line_ids2 = []
		for line in config.pf_extra_ids:
			values = {
				'name': line.name,
				'percent': line.percent
			}
			line_ids2.append((0, False, values ))

		res.update({
			'canteen_account': config.canteen_account.id,
			'canteen_amount': config.canteen_amount,
			'esi_account': config.esi_account.id,
			'epf_account': config.epf_account.id,
			'welfare_account': config.welfare_account.id,
			'esi_payment_date': config.esi_payment_date,
			'pf_payment_date': config.pf_payment_date,
			'fin1_start': config.fin1_start,
			'fin1_end': config.fin1_end,
			'fin2_start': config.fin2_start,
			'fin2_end': config.fin2_end,
			'pf_extra_ids': line_ids2,
		})
		return res

	@api.multi
	def excecute(self):
		# print 'test=========================', asd
		config = self.env['general.hr.configuration'].search([])
		for line in config:
			line.unlink()

		line_ids2 = []
		for line in self.pf_extra_ids:
			values = {
				'name': line.name,
				'percent': line.percent
			}
			line_ids2.append((0, False, values ))
		self.env['general.hr.configuration'].create({'canteen_account': self.canteen_account.id,
													'canteen_amount': self.canteen_amount,
													'esi_account': self.esi_account.id,
													'epf_account': self.epf_account.id,
													'welfare_account': self.welfare_account.id,
													'esi_payment_date': self.esi_payment_date,
													'pf_payment_date': self.pf_payment_date,
													'fin1_start': self.fin1_start,
													'fin1_end': self.fin1_end,
													'fin2_start': self.fin2_start,
													'fin2_end': self.fin2_end,
													'pf_extra_ids': line_ids2
													})

		rule_lines = self.env['contract.salary.rule'].search([('related_type','=', 'canteen')])
		for rule in rule_lines:
			if rule.contract_id.state != 'deactive':
				rule.is_related = True
				rule.per_day_amount = self.canteen_amount
			
		return {
			'type': 'ir.actions.client',
			'tag': 'reload',
		}
		
				
	@api.multi
	def cancel(self):
		return {
			'type': 'ir.actions.client',
			'tag': 'reload',
		}

class GeneralHrConfigurationWizardLine(models.TransientModel):
	_name = 'general.hr.configuration.wizard.line'

	line_id = fields.Many2one('general.hr.configuration.wizard')
	name = fields.Char('Name')
	percent = fields.Float('Percentage')


class GeneralHrConfiguration(models.Model):
	_name = 'general.hr.configuration'


	canteen_account = fields.Many2one('account.account', 'Canteen')
	canteen_amount = fields.Float('Canteen Amount')
	esi_account = fields.Many2one('account.account', 'ESI Account')
	pf_payment_date = fields.Integer('Last Date of Payment')
	esi_payment_date = fields.Integer('Last Date of Payment')
	epf_account = fields.Many2one('account.account', 'EPF Account')
	welfare_account = fields.Many2one('account.account', 'Employee Welfare Account')

	fin1_start = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])

	fin1_end = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])
	fin2_start = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])
	fin2_end = fields.Selection([('1','January'),
									('2','February'),
									('3','March'),
									('4','April'),
									('5','May'),
									('6','June'),
									('7','July'),
									('8','August'),
									('9','September'),
									('10','October'),
									('11','November'),
									('12','December'),
									])
	pf_extra_ids = fields.One2many('general.hr.configuration.line', 'line_id')


class GeneralHrConfigurationLine(models.Model):
	_name = 'general.hr.configuration.line'

	line_id = fields.Many2one('general.hr.configuration')
	name = fields.Char('Name')
	percent = fields.Float('Percentage')








