from openerp import models, fields, api, _
from datetime import datetime
from openerp.exceptions import except_orm, ValidationError



class EmployeeAdvance(models.Model):
	_name = 'employee.advance'

	employee_id = fields.Many2one('hr.employee', string='Employees', required=True)
	date = fields.Date(string='Date',default=datetime.today(),required=True,readonly=True)
	advance_amount = fields.Float('Advance Amount',required = True)
	current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)

class Employeeloan(models.Model):
	_name = 'employee.loan'
	_rec_name = 'loan_id'
	

	@api.multi
	# @api.depends('loan_amount','rate')
	def _compute_loan(self):
		for record in self:
			balance = 0
			payslip = self.env['hr.payslip'].search([('state','=','done'),('employee_id', '=',record.employee_id.id)])
			
			
			for line in payslip:
				for ids in line.line_ids:
					if record.balance_amount== 0:
						record.balance_amount=record.loan_amount
						record.total_paid = 0
					else:
						if ids.rule_id.related_type == 'loan':
							balance += ids.total
							


			record.balance_amount = record.total_loan-balance
			record.total_paid = balance
			# record.total_loan = loan_amount_cal
			# print "########^^^^^^^^^^^^^",balance





	@api.multi
	# @api.depends('loan_amount','rate')
	def _compute_instalment(self):
		for record in self:
			record.instalment_amount = 0

			payslip = self.env['hr.payslip'].search([('state','=','done'),('employee_id', '=',record.employee_id.id)])
			for line in payslip:
				for ids in line.line_ids:
					if ids.rule_id.related_type == 'loan':
						record.instalment_amount = ids.total
						print ' ids total=============================',ids.total
						
			print 'ins=====================================',record.instalment_amount



		


	@api.multi
	@api.depends('loan_amount','rate')
	def _compute__total_loan(self):
		for rec in self:
			rec.total_loan = rec.loan_amount+ rec.loan_amount*rec.rate/100

	# seq = fields.Integer('seq')
	loan_id = fields.Char('Loan ID',readonly = True)
	employee_id = fields.Many2one('hr.employee', string='Employees', required=True)
	date = fields.Date(string='Date',default=datetime.today(),required=True,readonly=True)
	loan_amount = fields.Float('Loan Amount',required = True)
	current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
	rate = fields.Float('Interest Rate(%)',required = True)
	duration = fields.Integer('Duration(in months)',required= True)
	total_loan= fields.Float('Total Loan Amount',compute ="_compute__total_loan")
	balance_amount = fields.Float('Balance Amount',compute = "_compute_loan")
	total_paid = fields.Float('Total Paid',compute = "_compute_loan")
	instalment_amount = fields.Float('Instalment',compute = "_compute_instalment")
	state = fields.Selection([
			('draft', 'Draft'),
			('approved', 'Approved'),
			('payment', 'Payment'),
			('close', 'Close'),
			('cancel', 'Cancel')],
			default='draft')
	loan_line = fields.One2many('employee.loan.line','line_id' )
	# ins_amount = fields.Float('Ins amount')




	
	@api.multi
	def action_close(self):
		print 'close============================================='
		for rec in self:
			if rec.total_loan == rec.total_paid :
				self.write({
							'state': 'close'
							})
			else:
				raise except_orm(_('Warning'),_('PAID AMOUNT STILL NOT CLOSE'))

	

	@api.multi
	def approved_progressbar(self):
		for rec in self:
			# cnt = rec.employee_id
			# cnt_val = self.env['hr.payslip'].browse(cnt)
			# print '#########++++++++++++++++++++++++++++',rec.employee_id,cnt,cnt_val
			rec.loan_id = self.env['ir.sequence'].next_by_code('loan.seq.new')
			print 'rec.loan_id================================',rec.loan_id

			self.write({
						'state': 'approved'
						})



	@api.multi
	def loan_payment_approve(self):

		inv_approve_obj = self.env['employee.loan']
		res = {
			'name': 'Payment Details',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hiworth.invoice.payment.wizard',
			# 'domain': [('line_id', '=', self.id),('date','=',_self.date)],
			'context': { 'default_payment_amount': self.instalment_amount },
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',

		}
		return res



	@api.multi
	def action_cancel(self):
		for line in self:
			line.state = 'cancel'

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state not in ('draft', 'cancel'):
				raise except_orm(_('Warning'),_('You cannot delete an invoice which is not draft or cancelled.'))

		return super(Employeeloan, self).unlink()




			
class Employeeloanline(models.Model):
	_name = 'employee.loan.line'
	

	line_id = fields.Many2one('employee.loan','Loan')

	date = fields.Date(string='Date' , required=True,readonly=True)
	paid_amount = fields.Float('Paid Amount',readonly = True)








	

			





	