from openerp import models, fields, api
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp.osv import osv
from lxml import etree




# 
class hr_attendance(osv.osv):
    _inherit = "hr.attendance"
     
    def _altern_si_so(self, cr, uid, ids, context=None):
        """ Alternance sign_in/sign_out check.
            Previous (if exists) must be of opposite action.
            Next (if exists) must be of opposite action.
        """
#         for att in self.browse(cr, uid, ids, context=context):
#             # search and browse for first previous and first next records
#             prev_att_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '<', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name DESC')
#             next_add_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '>', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name ASC')
#             prev_atts = self.browse(cr, uid, prev_att_ids, context=context)
#             next_atts = self.browse(cr, uid, next_add_ids, context=context)
#             # check for alternance, return False if at least one condition is not satisfied
#             if prev_atts and prev_atts[0].action == att.action: # previous exists and is same action
#                 return False
#             if next_atts and next_atts[0].action == att.action: # next exists and is same action
#                 return False
#             if (not prev_atts) and (not next_atts) and att.action != 'sign_in': # first attendance must be sign_in
#                 return False
        return True
         
         
    _constraints = [(_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]
    

class HiworthHrAttendance(models.Model):
    _name='hiworth.hr.attendance'
    _order = "date desc"


    @api.model
    def _cron_attendance_entry_creation(self):
        today = datetime.today()
        # print 'v-----------------------------------------', today
        holiday = self.env['public.holiday'].search([('date','=',today)])
        if not holiday:
            # print 'hjkh--------------------------------'
            employees = self.env['hr.employee'].search([('cost_type','=','permanent')])
            for emp_id in employees:
                attendance = self.env['hiworth.hr.attendance'].search([('name','=', emp_id.id),('date','=',today)])
                # print 'attendance------------------', attendance
                if not attendance:
                    self.env['hiworth.hr.attendance'].create({'name' : emp_id.id,
                                                            'date' : today,
                                                            'attendance' : 'absent'
                                                            })

        

    name = fields.Many2one('hr.employee')
    sign_in = fields.Datetime()
    sign_out = fields.Datetime()
    location = fields.Many2one('stock.location','Location')
    state = fields.Char()
    attendance_signin_id = fields.Integer()
    attendance_signout_id = fields.Integer()
    employee_type = fields.Char()
    attendance = fields.Selection([('full', 'Full Present'),
                                   ('half','Half Present'),
                                   ('absent','Absent'),
                                   ('leave','Approved Leave'),
                                   ('day','Day/Night'),
                                   ('compens','Compensation')], default='full', string='Attendance')
    # attendance = fields.Selection([('full', 'Full'),('half','Half')], default='full', string='Attendance')
    date = fields.Date('Date')

    # @api.onchange('name')
    # def _onchange_name(self):
    #     if self.name:
    #         self.employee_type = self.name.employee_type


    # @api.model
    # def create(self, vals):
    #     if vals.get('name') and vals.get('date'):
    #         record = self.env['hiworth.hr.attendance'].search([('date','=',vals.get('date')),('name','=', vals.get('name'))])
    #         if record:
    #             raise osv.except_osv(_('Warning!'), _("Already entered attendance for Employee '%s'") % (vals.get('name').name,))
    #         else:
    #             pass

    # @api.model
    # def create(self, vals):
    #     if self._context['default_check'] == 0:
    #     # Find latest record and its state
    #         odoo_last_attendance_rec = self.env['hr.attendance'].search([('employee_id','=',self._context['default_name'])], order='id desc', limit=1)
    #         state = 'sign_out'
    #         if odoo_last_attendance_rec.action=='sign_out' or not odoo_last_attendance_rec:
    #             state = 'sign_in'

    #         # Make sure both the calculated state from odoo_last_attendance_rec and state from the wizard are same, return name of employee otherwise
    #         if vals['state'] != state:
    #             return self._context['default_name']

    #         '''
    #         Check if signout is on the same date as the last singin
    #         Prevent signing out the employee from a different date than the last sign in date
    #         '''
    #         if (state == 'sign_out') and ( ((datetime.strptime(odoo_last_attendance_rec.name, '%Y-%m-%d %H:%M:%S')+timedelta(hours=5, minutes=30)).date()) != (datetime.strptime(vals['sign_out'], '%Y-%m-%d %H:%M:%S')+timedelta(hours=5, minutes=30)).date() ):
    #             raise osv.except_osv(('Error'), ('Please sign out the employee on the same date as the last sign in date.'));
    #         if state == 'sign_in':
    #             hr_attendance_rec=self.env['hr.attendance'].create({'action': 'sign_in', 'employee_id': vals['name'], 'name': vals['sign_in'] , 'action_desc': False})
    #             #signin vals {'sign_in': '2017-05-17 12:19:25', 'state': 'sign_in', 'sign_out': False, 'name': 1}
    #             vals['attendance_signin_id']=hr_attendance_rec.id
    #             res = super(HiworthHrAttendance, self).create(vals)
    #         else:
    #             # signout vals {'sign_in': False, 'state': 'sign_out', 'sign_out': '2017-05-20 12:21:41', 'name': 1}
    #             hr_attendance_rec=self.env['hr.attendance'].create({'action': 'sign_out', 'employee_id': vals['name'], 'name': vals['sign_out'] , 'action_desc': False})
    #             # attendance_recs = self.env['hiworth.hr.attendance'].search([('name','=',self._context['default_name'])])
    #             attendance_rec = self.env['hiworth.hr.attendance'].search([('name','=',self._context['default_name'])], order='id desc', limit=1)
    #             # attendance_rec = attendance_recs and attendance_recs[-1]
    #             attendance_rec.write({'sign_out': vals['sign_out'], 'attendance_signout_id': hr_attendance_rec.id})
    #             res = attendance_rec
    #     else:
    #         hr_attendance_rec1=self.env['hr.attendance'].create({'action': 'sign_in', 'employee_id': vals['name'], 'name': vals['sign_in'] , 'action_desc': False})
    #         vals['attendance_signin_id']= hr_attendance_rec1.id
    #         # attendance_rec1 = self.env['hiworth.hr.attendance'].create({'sign_in': vals['sign_in'], 'name': vals['name']})
    #         # vals['attendance_signin_id']=hr_attendance_rec1.id
    #         hr_attendance_rec=self.env['hr.attendance'].create({'action': 'sign_out', 'employee_id': vals['name'], 'name': vals['sign_out'] , 'action_desc': False})
    #         vals['attendance_signout_id']= hr_attendance_rec.id
    #         # attendance_rec = self.env['hiworth.hr.attendance'].create({'name':self._context['default_name'],'sign_in':vals['sign_in'],'sign_out':vals['sign_out'],'attendance_signin_id':vals['attendance_signin_id'],'attendance_signout_id':vals['attendance_signout_id']})
    #         res =  super(HiworthHrAttendance, self).create(vals)

    #     return res

    # @api.multi
    # def unlink(self):
    #     for item in self:
    #         self.env['hr.attendance'].browse([item.attendance_signin_id, item.attendance_signout_id]).unlink()
    #         super(HiworthHrAttendance, item).unlink()

    # @api.model
    # def default_get(self, vals):
    #     res = super(HiworthHrAttendance, self).default_get(vals)
    #     # Find latest record and its state
    #     attendance_rec = self.env['hiworth.hr.attendance'].search([('name','=',self._context['default_name'])], order='id desc', limit=1)
    #     # attendance_rec = attendance_recs and attendance_recs[-1]
    #     state = 'sign_out'
    #     if attendance_rec.sign_out or not attendance_rec:
    #         state = 'sign_in'
    #     if self._context['default_check'] == 1:
    #         state = 'sign_in'
    #     # Update default valuse
    #     res.update({
    #         'name': self._context['default_name'],
    #         'state': state
    #     })
    #     return res
