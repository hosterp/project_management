from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import except_orm, ValidationError


class AttendanceRequest(models.TransientModel):
	_name = 'attendance.request'



	@api.onchange('user')
	def onchange_attendance_request(self):
		self.designation_id = self.env.user.employee_id.designation_id.id
		self.project_ids = [(6,0,self.env.user.employee_id.project_ids.ids)]
		employees = self.env['hr.employee'].search([
													('project_ids','=',self.project_ids.ids)])
		emp_list = []
		for emp in employees:
			emp_list.append((0,0,{'employee_id':emp.id,
								  'designation_id':emp.designation_id.id}))
		self.attendance_request_line_ids = emp_list


	user = fields.Many2one('res.users','Logged User')
	designation_id = fields.Many2one('hr.designation',"Designation")
	project_ids = fields.Many2many('project.project','attendace_request_project_rel','attendance_request_id','project_id',"Projects")
	attendance_request_line_ids = fields.One2many('attendance.request.line','attendace_request_id',"Attendance requset line",)

	_defaults = {
		'user':lambda obj, cr, uid, ctx=None: uid,
		}

	@api.multi
	def request_attendance(self):
		for line in self.attendance_request_line_ids:
			self.env['pending.attendance.request'].create({'employee_id':line.employee_id.id,
												    'designation_id':line.designation_id.id,
												   'full_present':line.full_present,
												   'half_present':line.half_present,
												   'absent':line.absent,
												   'night':line.night,
														   'remarks':line.remarks,
														 })


class AttendanceRequestLine(models.TransientModel):
	_name = 'attendance.request.line'

	@api.onchange('full_present')
	def onchange_full_present(self):
		for rec in self:
			rec.half_present = False
			rec.absent = False
			rec.night = False

	@api.onchange('half_present')
	def onchange_half_present(self):
		for rec in self:
			rec.full_present = False
			rec.absent = False
			rec.night = False

	@api.onchange('absent')
	def onchange_absent(self):
		for rec in self:
			rec.full_present = False
			rec.half_present = False
			rec.night = False

	@api.onchange('night')
	def onchange_night(self):
		for rec in self:
			rec.full_present = False
			rec.absent = False
			rec.half_present = False

	employee_id = fields.Many2one('hr.employee',"Employee")
	designation_id = fields.Many2one('hr.designation',"Designation")
	full_present = fields.Boolean("Full Present")
	half_present = fields.Boolean("Half Present")
	absent = fields.Boolean("Absent")
	night = fields.Boolean("Night")
	remarks = fields.Char("Remarks")
	attendace_request_id = fields.Many2one('attendance.request',"Attendance Request")


class PendingRequests(models.Model):
	_name = 'pending.attendance.request'

	@api.onchange('full_present')
	def onchange_full_present(self):
		for rec in self:
			rec.half_present = False
			rec.absent = False
			rec.night = False

	@api.onchange('half_present')
	def onchange_half_present(self):
		for rec in self:
			rec.full_present = False
			rec.absent = False
			rec.night = False

	@api.onchange('absent')
	def onchange_absent(self):
		for rec in self:
			rec.full_present = False
			rec.half_present = False
			rec.night = False

	@api.onchange('night')
	def onchange_night(self):
		for rec in self:
			rec.full_present = False
			rec.absent = False
			rec.half_present = False

	employee_id = fields.Many2one('hr.employee', "Employee")
	designation_id = fields.Many2one('hr.designation', "Designation")
	location_ids = fields.Many2many('stock.location','pending_attendance_location_rel','pending_attendance_id','location_id',"Locations")
	full_present = fields.Boolean("Full Present")
	half_present = fields.Boolean("Half Present")
	absent = fields.Boolean("Absent")
	night = fields.Boolean("Night")
	remarks = fields.Char("Remarks")
	state = fields.Selection([('pending','Pending'),('approved','Approved')],default="pending")



	@api.multi
	def approve_attendance(self):
		self.state = 'approved'
		entry = self.env['hiworth.hr.attendance'].search([('name','=',self.employee_id.id),('date','=',self.create_date)])

		attendance = ''
		if self.full_present:
			attendance = 'full'
		if self.half_present:
			attendance = 'half'
		if self.absent:
			attendance='absent'
		if self.night:
			attendance='day'
		if len(entry) != 0:
			raise except_orm(_('Warning'), _("Already entered attendance for employee '%s'") % (self.employee_id.name,))


		else:
			self.env['hiworth.hr.attendance'].with_context(default_name=self.employee_id.id,default_check=1).create({
												  'name':self.employee_id.id,
												  'attendance':attendance,
												  'date':self.create_date,
												  })



