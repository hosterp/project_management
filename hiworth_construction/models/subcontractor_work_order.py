from openerp import fields, models, api,_

class SubcontractorWork(models.Model):


	_name='subcontractor.work'


	contractor_id=fields.Many2one('hr.employee',string='Contractor')
	workorder_id=fields.Many2one('project.task',string='Work Order')
	voucher_no=fields.Char(string='VR NO')
	quantity=fields.Float(string='Quantity')
	rate=fields.Float(string='Rate')
	total=fields.Float(string='Total')
	payment=fields.Float(string='Payment')
	remarks=fields.Text(string='Remarks')
	supervisor_daily_statement_id=fields.Many2one('partner.daily.statement')
