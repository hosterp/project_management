from openerp import fields, models, api,_
from datetime import datetime,timedelta
from openerp.exceptions import except_orm, ValidationError


class LabourSheet(models.Model):
	_name = "labour.sheet"
	_rec_name = "id"

	date = fields.Date()
	labour_sheet_activities_line_ids = fields.One2many('labour.activities.sheet', 'labour_sheet_id')
	state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft')


	@api.multi
	def action_confirm(self):
		for rec in self.labour_sheet_activities_line_ids:
			rec.action_confirm()
		self.state = 'confirm'


class LabourSheetActivities(models.Model):

	_name = 'labour.activities.sheet'

	@api.depends('ot_rate','over_time')
	def compute_ot_amount(self):
		for rec in self:
			rec.ot_amount = rec.over_time*rec.ot_rate

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		for rec in self:
			if rec.employee_id:
				rec.name = rec.employee_id.name
				rec.position = rec.employee_id.labour_id
				rec.ot_rate = rec.employee_id.over_time_labour
				rec.rate = rec.employee_id.labour_wage
				rec.designation_id = rec.employee_id.designation_id.id
				
				
	@api.model
	def create(self,vals):
		vals.update({'number':self.env['ir.sequence'].next_by_code('labour.entry.code')})
		if not self.env.user.has_group("hiworth_hr_attendance.group_labour"):
			date = datetime.now() - timedelta(days=3)
			if datetime.strptime(vals['date'], "%Y-%m-%d") < date:
				raise except_orm(_('Warning'),
								 _("You Don't have access to create daily statement for more than 3 days Back"))
		driver_daily = self.env['labour.activities.sheet'].search(
			[('date', '=', vals['date']),
			 ('employee_id', '=', vals['employee_id']), ('labour_id','=',vals['labour_id'])])
		if driver_daily:
			raise except_orm(_('Warning'),
							 _('Already created Labour sheet for employee on %s' % (
							vals['date'])))
		res = super(LabourSheetActivities, self).create(vals)
		return res

	@api.multi
	def action_confirm(self):
		for rec in self:
			rec.state = 'confirm'

	@api.onchange('sub_contractor')
	def onchange_subcontractor_id(self):
		for rec in self:
			return {'domain':{'labour_id':[('contractor_id','=',rec.sub_contractor.id)]}}

	@api.onchange('labour_id')
	def onchange_sub_labour_id(self):
		for rec in self:
			rec.name = rec.labour_id.name
			rec.position = rec.labour_id.labour_id
			rec.ot_rate = rec.labour_id.overtime_wage
			rec.rate = rec.labour_id.labour_wage
			rec.designation_id = rec.labour_id.designation_id.id

	@api.depends('employee_id','labour_id')
	def compute_rate(self):
		for rec in self:
			if rec.employee_id:
				rec.rate = rec.employee_id.labour_wage
				rec.ot_rate = rec.employee_id.over_time_labour
			if rec.labour_id:
				rec.ot_rate = rec.labour_id.overtime_wage
				rec.rate = rec.labour_id.labour_wage

	labour_sheet_id = fields.Many2one('labour.sheet')

	date = fields.Date('Date')
	employee_id = fields.Many2one('hr.employee','Name')
	position = fields.Char('ID No')
	project_id = fields.Many2one('project.project','Project')
	time_in = fields.Datetime('Time IN')
	over_time = fields.Float('OT')
	ot_amount = fields.Float('OT Amount',compute="compute_ot_amount")
	ot_rate = fields.Float('OT Rate', compute="compute_rate")
	time_out = fields.Datetime('Time OUT')
	work_done = fields.Many2one('workdone.labour.sheet','Workdone')
	sub_contractor = fields.Many2one('res.partner',"Subcontractor")
	labour_id = fields.Many2one('subcontractor.labour',"Labour ")
	name = fields.Char('Labour Name')
	partner_select = fields.Selection([('sub','Subcontractor Labour'),
										('com','Company Labour')],'Labour Type',default='com')
	rate = fields.Float('Rate', compute="compute_rate")
	day = fields.Float('Duty/Day',default=1)
	lab_no= fields.Char('Labour Sheet No')
	supervisor_id = fields.Many2one('hr.employee','Supervisor/User')
	remarks = fields.Char("Remarks")
	number = fields.Char("Reference No")
	state = fields.Selection([('draft','Draft'),('confirm','Confirm')],default='draft')
	designation_id = fields.Many2one('hr.designation',"Designation")
	category = fields.Selection([('skilled','Skilled'),('unskilled','Unskilled'),('survey',"Survey"),('union',"Union")],"Category")
	report_id = fields.Many2one('partner.daily.statement')
	category_id = fields.Many2one('task.category',"Catgory")



class WorkdoneLabourSheet(models.Model):

	_name = 'workdone.labour.sheet'

	name = fields.Char('Workdone')

class ResPartner(models.Model):
	_inherit = 'res.partner'

	labour_contractor = fields.Boolean("Labour Contractor")
	labour_wage = fields.Float("Labour Wage")
	overtime_wage = fields.Float("Overtime Wage")

class SubcontractorLabour(models.Model):
	_name = 'subcontractor.labour'

	name = fields.Char("Name")
	labour_id = fields.Char("Labour ID")
	aadhar_no = fields.Char("Aadhar No")
	designation_id = fields.Many2one('hr.designation',"Designation")
	labour_wage = fields.Float("Labour Wage")
	overtime_wage = fields.Float("Overtime Wage")
	contractor_id = fields.Many2one('res.partner',"Subcontractor",domain="[('labour_contractor','=',True)]")