from openerp import models, fields, api,_
from openerp.exceptions import except_orm, ValidationError
from datetime import datetime,date,timedelta
from openerp import tools
from dateutil.relativedelta import relativedelta



class ApprovedPersons(models.Model):
	_name = 'approved.persons'


	name = fields.Many2one('res.users')
	app_id = fields.Many2one('hr.holidays')
	date_today = fields.Datetime('Date')

class HrHolidays(models.Model):
	_inherit = 'hr.holidays'
	_order = 'id desc'


	@api.onchange('leave_id','employee_id')
	def onchange_leave_id(self):
		if self.leave_id:
			if self.employee_id:
				leave_obj = self.env['employee.leave'].search([('employee_id','=',self.employee_id.id),('state','=','active'),('leave_id','=',self.leave_id.id)])
				if leave_obj:
					self.remaining = leave_obj.remaining

	status = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	# admin = fields.Many2one('res.users','Admin')
	next_approver = fields.Many2one('res.users',readonly=True)
	approved_persons = fields.One2many('approved.persons','app_id',readonly=True)
	state = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'),('confirm', 'To Approve'),('validated','Validated'), ('refuse', 'Refused'), ('validate1', 'Second Approval'), ('validate', 'Approved')],
			'Status', readonly=True, copy=False,default="confirm")
	lop_emp = fields.Float(string="Loss Of Pay/Not")
	leave_ids = fields.One2many('employee.leave', 'holiday_id', 'Leaves')
	holiday_status_id = fields.Many2one("hr.holidays.status", "Leave Type", required=False)
	allocation_date_from = fields.Date('Date From')
	allocation_date_to = fields.Date('Date To')
	date_from = fields.Date('Start Date', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, select=True, copy=False)
	date_to = fields.Date('End Date', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, copy=False)
	leave_id = fields.Many2one('hr.holidays.status', 'Leave Type')
	nos = fields.Float('No of Days', compute="_compute_no_days_new", store=True)
	remaining = fields.Integer('Remaining', compute="_compute_no_days_new", store=True)
	attendance = fields.Selection([('full', 'Full'),('half','Half')], default='full', string='Attendance')

	@api.multi
	@api.depends('date_from','date_to','employee_id','leave_id','attendance')
	def _compute_no_days_new(self):
		for record in self:
			if record.date_from and record.date_to:
				d1 = datetime.strptime(record.date_from, tools.DEFAULT_SERVER_DATE_FORMAT)
				d2 = datetime.strptime(record.date_to, tools.DEFAULT_SERVER_DATE_FORMAT)
				delta = d2 - d1
				if record.attendance == 'full':
					record.nos = (delta.days) + 1
				elif record.attendance == 'half':
					record.nos = (delta.days) + 0.5
				else:
					pass
			# empl = self.env['hr.employee'].search([('id','=', record.employee_id.id)])
			# for ids in empl.leave_ids:
			# 	if ids.leave_id.id == record.leave_id.id: 
			# 		record.remaining = ids.remaining
			if record.leave_id:
				if record.employee_id:
					leave_obj = self.env['employee.leave'].search([('employee_id','=',record.employee_id.id),('state','=','active'),('leave_id','=',record.leave_id.id)])
					if leave_obj:
						record.remaining = leave_obj.remaining


	def _compute_number_of_days(self, cr, uid, ids, name, args, context=None):
		pass

	def onchange_date_from(self, cr, uid, ids, date_to, date_from):
		pass

	def onchange_date_to(self, cr, uid, ids, date_to, date_from):
		pass


	# @api.multi
	# def validate_leave(self):
	# 	list = []
	# 	print "111111111111111"
	# 	if self.next_approver:
	# 		print "22222222222222222"
	# 		if self.env.user.id == self.next_approver.id or self.env.user.id == 1:
	# 			print "33333333333333333333"
	# 			rec = self.env['approved.persons'].create({'date_today':fields.Datetime.now(),
	# 															'name':self.next_approver.id,
	# 															'app_id':self.id})
	# 			print "4444444444444444"
	# 			list.append(rec.id)
	# 			print "55555555555555"
	# 			for ids in self.approved_persons:
	# 				list.append(ids.id)
	# 			print "6666666666666666"
	# 			if self.next_approver.employee_id.parent_id.id:
	# 				print "777777777777777777777777777"
	# 				self.next_approver = self.next_approver.employee_id.parent_id.id
	# 			else:
	# 				if self.next_approver.id == 1:
	# 					self.state = 'validated'
	# 					print "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"
	# 				self.next_approver = False

	# 			print "++++++++++++++++++++++++"
	# 			self.sudo().write({'approved_persons':[(6,0,list)],'status':'draft'})
	# 			print "------------------------"
	# 			print "9999999999999999999999"
	# 			# self.status = 'draft'
	# 		else:
	# 			raise except_orm(_('Warning'),
	# 						 _('You are not the next approver'))



	@api.model
	def create(self,vals):
		result = super(HrHolidays, self).create(vals)
		if result.type == 'remove':
			if result.employee_id.parent_id:
				user = self.env['res.users'].sudo().search([('employee_id','=',result.employee_id.parent_id.id)])
				if user:
					result.next_approver = user.id
		return result

	@api.multi
	def write(self, vals):
		result = super(HrHolidays, self).write(vals)
		if vals.get('employee_id') and vals.get('type') == 'remove':
			if result['employee_id'].parent_id:
				user = self.env['res.users'].sudo().search([('employee_id','=',result['employee_id'].parent_id.id)])
				if user:
					result['next_approver'] = user.id

		return result


	@api.multi
	def get_notifications(self):
		result = []
		for obj in self:
			result.append({
				# 'admin':obj.admin.name,
				'status': obj.status,
				'employee_id':obj.employee_id.name,
				'id': obj.id,
				'next_approver': obj.next_approver.name
			})
		return result


	# @api.multi
	# def action_validate(self):
	# 	obj_emp = self.env['hr.employee']
	# 	for record in self:
	# 		if record.holiday_type == 'employee':
	# 			leave_obj = self.env['employee.leave']
	# 			for line in record.leave_ids:
	# 				leave_val = {
	# 					'leave_id': line.leave_id.id,
	# 					'nos': line.nos,        
	# 					'remaining': line.nos,        
	# 					'employee_id': record.employee_id.id
	# 				}   
	# 				leave_obj.create(leave_val)
	# 		elif record.holiday_type == 'category':
	# 			emp_ids = obj_emp.search( [('category_ids', 'child_of', [record.category_id.id])])
	# 			leave_obj = self.env['employee.leave']
	# 			for employee in emp_ids:
	# 				for line in record.leave_ids:
	# 					leave_val = {
	# 						'leave_id': line.leave_id.id,
	# 						'nos': line.nos,      
	# 						'remaining': line.nos,        
	# 						'employee_id': record.employee_id.id
	# 					}   
	# 					leave_obj.create(leave_val)

	# 		record.state = 'validate'
	# 	return True

	@api.multi
	def action_validate(self):
		obj_emp = self.env['hr.employee']
		for record in self:
			# print 'rescord.type========================',record.type
			if record.type == 'add':
				if record.holiday_type == 'employee':
					for line in record.leave_ids:
						leave_obj = self.env['employee.leave'].search([('employee_id','=',record.employee_id.id),('state','=','active'),('leave_id','=',line.leave_id.id)])
						if len(leave_obj) > 0:
							raise except_orm(_('Warning'),_('Already leave allocated for this type leave. If you want to reallocate please deactivate it from Employee Details'))
						leave_val = {
							'from_date': record.allocation_date_from,
							'to_date': record.allocation_date_to,
							'leave_id': line.leave_id.id,
							'nos': line.nos,        
							'remaining': line.nos,        
							'employee_id': record.employee_id.id,
							'state': 'active',
						}   
						leave_obj.create(leave_val)
				elif record.holiday_type == 'category':
					emp_ids = obj_emp.search( [('category_ids', 'child_of', [record.category_id.id])])
					leave_obj = self.env['employee.leave']
					for employee in emp_ids:
						for line in record.leave_ids:
							leave_val = {
								'from_date': record.allocation_date_from,
								'to_date': record.allocation_date_to,
								'leave_id': line.leave_id.id,
								'nos': line.nos,      
								'remaining': line.nos,        
								'employee_id': record.employee_id.id,
								'state': 'active',
							}   
							leave_obj.create(leave_val)

				record.state = 'validate'

			if record.type == 'remove':

				if record.holiday_type == 'employee':
					leave_obj = self.env['employee.leave'].search([('employee_id','=',record.employee_id.id),('leave_id','=', record.leave_id.id),('state','=','active')], limit=1)
					print 'leave_obj==========================', leave_obj, leave_obj.remaining, leave_obj.taken_leaves, record.nos
					print 'leave_obj==========================', leave_obj.taken_leaves + record.nos
					if leave_obj:
						if record.nos <= leave_obj.remaining:
							leave_obj.update({'remaining': leave_obj.remaining - record.nos,
											'taken_leaves': leave_obj.taken_leaves + record.nos
											})
							record.state = 'validate'

						else:
							leave_obj.update({
											'taken_leaves': leave_obj.taken_leaves + record.nos
												})
							record.state = 'validate'

		return True


	@api.multi
	def approve_leave(self):
		view_id = self.env.ref('hiworth_hr_attendance.view_wizard_approve_lop').id
		return {
			'name':'Loss Of Pay',
			'view_type':'form',
			'view_mode':'form',
			'res_model':'loss.pay',
			'view_id': False,
			'views': [(view_id, 'form'),],
			# 'view_id':view_id,
			'type':'ir.actions.act_window',
			'target':'new',
			'context':{'default_rec': self.id,'default_name':self.number_of_days_temp},
		}



class HrHolidaysStatus(models.Model):
	_inherit = 'hr.holidays.status'

	effective_monthly_leave = fields.Integer('Effective Monthly Leave')


class PublicHoliday(models.Model):
	_name = 'public.holiday'

	name = fields.Char('Description')
	date = fields.Date('Date')

class MonthLeaveStatus(models.Model):
	_name = 'month.leave.status'

	status_id = fields.Many2one('hr.employee')
	leave_id = fields.Many2one('hr.holidays.status')
	month_id = fields.Integer('Month')
	allowed = fields.Float(default=1)



	@api.model
	def _cron_monthly_status_entries(self):
		print '-----------------------------------------------------', self.env['hr.employee'].search([('cost_type','=','permanent')])
		
		for day in self.env['hr.employee'].search([('cost_type','=','permanent')]):
		# for day in self.env['hr.holidays'].search([('type','=','add')]):
			for day1 in day.leave_ids:
				if day1.leave_id.effective_monthly_leave != 0:
					status = self.env['month.leave.status'].search([('status_id','=', day.id),('leave_id','=', day1.leave_id.id)], limit=1)
					today = date.today()
					d = today - relativedelta(months=1)
					print 'month----------------------------', day.name, today.month, d.month
					start = date(d.year, d.month, 1)
					end = date(today.year, today.month, 1) - relativedelta(days=1)
					taken = 0
					holiday = self.env['hr.holidays'].search([('type','=','remove'),('employee_id','=', day.id)])
					for hol_id in holiday:
						
						if (str(start) <= hol_id.date_from <= str(end)) or (str(start) <= hol_id.date_to<= str(end)):
							date_from = datetime.strptime(hol_id.date_from, '%Y-%m-%d').date()
							date_to = datetime.strptime(hol_id.date_to, '%Y-%m-%d').date()
							delta = date_to - date_from
							
							if hol_id.attendance == 'full':
								for i in range(delta.days + 1):
									if (date_from + timedelta(i)).month == d.month:
										taken += 1

							elif hol_id.attendance == 'half':
								for i in range(delta.days + 1):
									if (date_from + timedelta(i)).month == d.month:
										taken += 0.5
							else:
								pass
					bal_leave = 0
					allowed = 0
					print 'status---------------', status.allowed,taken
					if status:
						bal_leave = status.allowed - taken

					if bal_leave > 0:
						allowed = bal_leave + day1.leave_id.effective_monthly_leave
					elif bal_leave < 0:
						allowed = day1.leave_id.effective_monthly_leave
					else:
						allowed = day1.leave_id.effective_monthly_leave
					
					self.env['month.leave.status'].create({
												'status_id':day.id,
												'leave_id':day1.leave_id.id,
												'month_id': today.month,
												'allowed': allowed,
												 })



