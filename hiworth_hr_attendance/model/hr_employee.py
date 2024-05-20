from openerp import models, fields, api, _
from openerp import exceptions
import dateutil.parser
from dateutil.relativedelta import relativedelta
import time
from datetime import datetime, date, timedelta
import openerp.addons.decimal_precision as dp
import calendar
from openerp import tools
from openerp.exceptions import except_orm, ValidationError
import calendar
from datetime import *
from dateutil.relativedelta import *

class BranchProject(models.Model):
    _name = 'branch.project'

    name = fields.Char('Branch Name',required=True)
    code = fields.Char('Code',required=True)

class ResPartner1(models.Model):
    _inherit = 'res.partner'

    contractor = fields.Boolean('Contractor')
    res_company_new = fields.Boolean(default=False)


class CompanyNew(models.Model):
    _name='res.company.new'
    _inherits = {'res.partner':'partner_id'}

    @api.model
    def create(self,vals):
        vals['res_company_new'] = True
        return super(CompanyNew, self).create(vals)

class TechnicalTraining(models.Model):
    _name='technical.training'

    emp_id = fields.Many2one('hr.employee')
    name = fields.Char(string="Training")
    year_pass = fields.Char(string="Year of Passing")
    
class HrDesignation(models.Model):
    _name = 'hr.designation'
    
    name = fields.Char(string="Name")
    attendance_time = fields.Float("Attendance Time")
    attendance_designation_id = fields.Many2one('hr.designation',"Attendance Designation")
    leave_appr_designation_id = fields.Many2one('hr.designation',"Leave Approve Designation")

class TransferDetails(models.Model):
    _name = 'transfer.details'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    location_id = fields.Many2one('stock.location',string = 'Location')
    remarks = fields.Char('Remarks')
    hr_employee_id = fields.Many2one('hr.employee')

class HrEmployee(models.Model):
    _inherit='hr.employee'
    _order='priority asc'

    loc_id = fields.Many2one('stock.location',string='Location')
    location_ids = fields.Many2many('stock.location','employee_location_rel','employee_id','location_id',"Locations")
    transfer_details_ids = fields.One2many('transfer.details','hr_employee_id')
    project_id = fields.Many2one('project.project','Project')
    project_ids = fields.Many2many('project.project','employee_project_rel','employee_id','project_id',"Projects")

    @api.multi
    def cash_transfer(self):
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_cash_transfer_amount')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Cash Transfer'),
           'res_model': 'cash.transfer',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'new',
           'context': {'default_name':self.id}
       }
        return res

    @api.multi
    def view_stmts(self):
        view_id = self.env.ref('hiworth_accounting.view_account_form_hiworth').id
        return {
            'name':'Balance',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'form')],
            'res_model':'account.account',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':self.payment_account.id,
            'target':'new',
            'context':{},
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrEmployee, self).fields_view_get(view_id=view_id,view_type=view_type,toolbar=toolbar,submenu=submenu)
        if res.get('toolbar', False) and res.get('toolbar').get('print', False):
            reports = res.get('toolbar').get('print')
            for report in reports:
                if report.get('string') == 'Attendance Error Report':
                    res['toolbar']['print'].remove(report)
        return res

    @api.model
    def _cron_casual_employee(self):
        employee_ids = self.env['hr.employee'].search([])
        for employee in employee_ids:
            employee.casual_leave = employee.casual_leave +1

    monthly_status_ids = fields.One2many('month.leave.status', 'status_id', 'Status')
    attendance_ids = fields.One2many('hiworth.hr.attendance', 'name')
    emp_code = fields.Char('Order Reference', required=False, copy=False,readonly=True,)
    street = fields.Char('Street')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state')
    zip = fields.Char('Zip')
    street2 = fields.Char()
    street1 = fields.Char('Street')
    city1 = fields.Char('City')
    state_id1 = fields.Many2one('res.country.state')
    zip1 = fields.Char('Zip')
    street3 = fields.Char()
    country_id1 = fields.Many2one('res.country')
    type_of_card = fields.Selection([('passport','Passport'),('aadharcard','Aadhar Card'),('voterid','VoterId'),('pancard','PanCard'),('license','License')],string="Type Of Card")
    present = fields.Boolean(default=False)
    location = fields.Many2one('stock.location','Location')
    father = fields.Char('Name Of Father')
    mother = fields.Char('Name Of Mother')
    hus_wife = fields.Char('Name Of Husband/Wife')
    emergency_person = fields.Char('Emergency Contact Person')
    emergency_no = fields.Char('Emergency Contact No.')
    height = fields.Char('Height(cm)')
    weight = fields.Char('Weight')
    adhar_no = fields.Char('Adhar No.')
    pan = fields.Char('PAN')
    passport = fields.Char('Passport No.')
    licence = fields.Char('Licence No')
    vehicle_no = fields.Char('Vehicle No')
    hus_wife = fields.Char('Name Of Husband/Wife')
    joining_date = fields.Date('Date of Joining')
    employee_type = fields.Selection([('trainee','Trainee'),('employee','Employee'),('manager','Manager'),('others','Others')],'Employee Type',required=False)
    worker_type = fields.Selection([('mason','Mason'),('helper','Helper')],'Worker Type')
    edu_qualify = fields.One2many('edu.qualify','edu_id')
    wedding_anniversary = fields.Date('Wedding Anniversary')
    petty_cash_account = fields.Many2one('account.account','Petty Cash Account')
    payment_account = fields.Many2one('account.account','Payment Account')

    user_category = fields.Selection([('admin','Managers'),
                                      ('cheif_acc', 'Finance & Admin'),
                                      ('hr', 'HR'),
                                      ('icivil_store', 'Store'),
                                      ('jpurchase', 'Purchase'),
                                      ('planning', 'Planning'),
                                      ('project_manager', 'Project Manager'),
                                      ('site_eng', 'Site Engineer'),
                                      ('supervisor', 'Supervisor'),
                                      ('suplevels', 'Survey & Levels'),
                                      ('tplant_mechanics', 'Plant & Machinary'),
                                      ('tpoperators_helpers', 'Operators & Helpers'),
                                      ('tppdriver','Drivers & Helpers'),
                                      ('ybill','Billing'),
                                      ('yqc','QC'),
                                      ('yhouse_keeping','House Keeping'),
                                      ('ylabour','Labour'),
                                      ('ymess','Mess')
                                    ],default='admin',string='User Category',required=True)
    attendance_category = fields.Selection([('office_staff','Office Staff'),
                                    ('site_employee','Site Employee'),
                                    ('taurus_driver','Taurus Driver'),
                                    ('eicher_driver','Eicher Driver'),
                                    ('pickup_driver','Pick Up Driver'),
                                    ('operators','Operators'),
                                    ('cleaners','Cleaners')
                                    ],default='office_staff',string='Attendance Category')
    payroll_required = fields.Boolean('Payroll Required/Not')
    new_company_id = fields.Many2one('res.company.new', string="Company")
    sign = fields.Binary('Sign')
    per_day_eicher_rate = fields.Float('Per Day Rate')
    labour_accnt = fields.Many2one('account.account','Labour Account')
    reset_pswd = fields.Boolean(default=False)
    cost_type = fields.Selection([('permanent','Salary'),
                                  ('wages','Bata'),
                                  ('salary_bata','Salary + Bata')], 'Cost Type')
    leave_ids = fields.One2many('employee.leave', 'employee_id', 'Leaves')
    driver_ok = fields.Boolean('Driver Ok')
    zone_id = fields.Many2one('hr.employee.zone','Zone')
    age = fields.Char('Age', compute="_get_age")
    blood_group = fields.Char('Blood Group')
    no_mnth_job = fields.Char('No of months in job', compute="_get_working_month_year")
    year_service = fields.Char('Year of service', compute="_get_working_month_year")
    remarks = fields.Text('Remarks')
    resigning_date = fields.Date('Date of Resignation')
    status1 = fields.Selection([('active','Active'),
                                ('resign','Resigned')
                                ], default="active", string="State")

    insurance_ids = fields.One2many('employee.insurance','employee_id', string="Employee Insurance")
    pf = fields.Boolean(string="PF")
    mediclaim = fields.Boolean(string="Mediclaim")
    esi = fields.Boolean(string="ESI")
    esi_no = fields.Char(string="ESI No.")
    tech_training = fields.One2many('technical.training','emp_id')
    canteen = fields.Boolean(string="Is Canteen", default=False)
    phn_no2 = fields.Char('Phone No.')
    mobile_no = fields.Char('Mobile No.')
    house_ownership = fields.Selection([('rented','Rented'),('own','Own')], string="Rented/Own")
    house_area = fields.Char('Total Area of House in Sqft')
    building_roof = fields.Selection([('concrete','Concrete'),('sheet','Sheet'),('tile','Tile')], string="Buliding Roof")
    is_truss_house = fields.Boolean(string="Truss House(Pipe & Sheet / Tile) if yes kindly tick", default=False)
    family_ids = fields.One2many('hr.employee.family','family_id')
    no_sibilings = fields.Char('No. of Brothers & Sisters')
    total_running = fields.Float('Total Running')
    over_time_bata = fields.Float('Over Time Bata')
    over_time_line = fields.One2many('over.time', 'employee_id', 'Over Time Bata')
    designation_id = fields.Many2one('hr.designation',string="Designation")
    labour_category = fields.Selection([('sub_labour','Sub Labour'),
                                        ('company_labour','Company Labour')],default='company_labour', string="Labour Category")
    priority = fields.Integer(string="Priority")
    sub_department_id = fields.Many2one('hr.department',"Sub Department")


    @api.multi
    def view_action_resign(self):
        res = {
            'name': 'Resignation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.employee.resignation',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_resign_id': self.id},
        }
        return res

    @api.multi
    def view_action_appraisal(self):
        active_contract = self.env['hr.contract'].search([('employee_id','=', self.id),('state','=','active')], limit=1)
        if active_contract:
            if not active_contract.date_end:
                raise exceptions.ValidationError('Please enter end date of existing active contract of this employee.')
            active_contract.action_deactive()
            line_ids = []
            if active_contract.struct_id:
                for rule in active_contract.struct_id.rule_ids:
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
                    line_ids.append((0, False, values ))
            res_id = self.env['hr.contract'].create({'name': active_contract.name,
                                                    'employee_id': active_contract.employee_id.id,
                                                    'job_id': active_contract.job_id.id,
                                                    'type_id': active_contract.type_id.id,
                                                    'struct_id': active_contract.struct_id.id,
                                                    'wage': active_contract.wage,
                                                    'rule_lines': line_ids,
                                                    })
            res = {
                'name': 'Appraisal',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.contract',
                'res_id': res_id.id,
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            raise exceptions.ValidationError('There is no active contract for this employee.')
        return res

    @api.multi
    @api.depends('birthday')
    def _get_age(self):
        for record in self:
            if record.birthday:
                d1 = datetime.strptime(record.birthday, "%Y-%m-%d")
                date_today = fields.Date.today()
                d2 = datetime.strptime(date_today, "%Y-%m-%d")
                record.age = (int(d2.year)-int(d1.year))

    @api.multi
    @api.depends('joining_date')
    def _get_working_month_year(self):
        for record in self:
            if record.joining_date:
                d1 = datetime.strptime(record.joining_date, "%Y-%m-%d")
                date_today = fields.Date.today()
                d2 = datetime.strptime(date_today, "%Y-%m-%d")
                r = relativedelta(d2, d1)
                record.no_mnth_job = r.months + (12*(int(d2.year)-int(d1.year)))
                record.year_service = ((r.months%10)*0.1) + (int(d2.year)-int(d1.year))

    @api.onchange('user_category')
    def onchange_user_category(self):
        if self.user_category:
            if self.user_category == 'driver':
                self.driver_ok = True
            else:
                self.driver_ok = False

    @api.onchange('job_id')
    def onchange_job_id(self):
        if self.job_id.name == 'Manager.':
            self.employee_type = 'manager'
        elif self.job_id.name == 'Employee.':
            self.employee_type = 'employee'
        elif self.job_id.name == 'Trainee.':
            self.employee_type = 'trainee'
        else:
            self.employee_type = 'others'

    @api.multi
    def unlink(self):
        for rec in self:
            rec.active = False
        return

    @api.multi
    def get_employee_code(self, o):
        return self.env['hr.employee'].search([('id','=',o.id)]).emp_code

    @api.multi 
    def get_location_ml(self,o,day):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        for r in rec:
            if dateutil.parser.parse(r.sign_in).date() == day[0]:
                return r.location.name

    @api.model
    def create(self, vals):

        result = super(HrEmployee, self).create(vals)
        if result.emp_code == False:
            result.emp_code = self.env['ir.sequence'].next_by_code('hr.employee') or '/'
        if result.work_email:
            v = {
             'active': True,
             'name': result.name,
             'login': result.work_email,
             'company_id': 1,
             'employee_id':result.id,
            }
            user_id1 = self.env['res.users'].sudo().create(v)
            result.user_id = user_id1.id
        return result

    @api.multi
    def write(self, vals):

        result = super(HrEmployee, self).write(vals)
        if vals.get('user_category') or vals.get('name'):
            rec = self.env['res.users'].sudo().search([('employee_id','=',self.id)])
            if vals.get('name'):
                rec.write({'name':vals.get('name')})

        return result

    @api.multi
    def change_password(self):
        for rec in self:
            return {
                    'name': rec.name,
                    'view_mode': 'form,tree',
                    'res_model': 'hr.password.reset',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    "context": {'default_employee_id': rec.id,'default_user_id': rec.user_id.id,}
                }
        user_id = rec.user_id
        user_id.write({'password': "admin3"})

    @api.multi
    def load_employee_attendance(self):
        return {
                    'name': self[0].name,
                    'view_mode': 'calendar,form,tree',
                    'res_model': 'hiworth.hr.attendance',
                    'type': 'ir.actions.act_window',
                    "views": [[self.env.ref("hiworth_hr_attendance.hiworth_hr_attendance_view_employee_attendance_tree").id, "tree"], [False, "form"]],
                    'domain': [('name','=',self[0].id)],
                    "context": {'default_name': self[0].id}
                }

class OverTimeLine(models.Model):

    _name = 'over.time'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    date = fields.Date('Date')
    project_id = fields.Many2many('project.project', string='Work')
    time = fields.Float('Time')

class HrEmployeeFamily(models.Model):
    _name = 'hr.employee.family'

    family_id = fields.Many2one('hr.employee')
    relation = fields.Char('Relation')
    name = fields.Char('Name')
    age = fields.Char('Age')
    dob = fields.Date('DOB')
    occupation_institution = fields.Char('Occupation Institution')
    studying_institution = fields.Char('Studying Institution')

class HrPasswordReset(models.Model):
    _name = 'hr.password.reset'

    employee_id = fields.Many2one('hr.employee')
    user_id = fields.Many2one('res.users')
    new_password = fields.Char('New Password')

    @api.multi
    def change_password(self):
        for rec in self:
            rec.employee_id.reset_pswd = True
            user_id = rec.user_id
            user_id.write({'password': rec.new_password})    

class EduQualify(models.Model):
    _name = 'edu.qualify'

    edu_id = fields.Many2one('hr.employee')
    qualification = fields.Char('Qualification')
    year = fields.Char('Year Of Passing')
    unvrsty = fields.Char('University/College')

class LossPay(models.Model):
    _name = 'loss.pay'

    name = fields.Float(string="Loss Of Pay/Not")
    rec = fields.Many2one('hr.holidays')

    @api.multi
    def confirm_edit(self):
        self.rec.holidays_validate()
        self.rec.lop_emp = self.name
       

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
        pass
        """
        @param employee: browse record of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        contract_obj = self.pool.get('hr.contract')
        clause = []
        clause_final =  ['&',('employee_id', '=', employee.id),('state', '=', 'active')]
        contract_ids = contract_obj.search(cr, uid, clause_final, context=context)
        return contract_ids

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 '+self.month+' '+str(datetime.now().year)
            date_object = datetime.strptime(date, '%d %B %Y')
            self.date_from = date_object
            end_date = date_object + relativedelta(day=31)
            self.date_to = end_date

    lop = fields.Float('Loss Of Pay Days', compute="_onchange_lop")
    advance = fields.Float('Advance', compute="_compute_advance_amount")
    state = fields.Selection([
            ('draft', 'Draft'),
            ('verify', 'Generated'),
            ('done', 'Confirmed'),
            ('paid', 'Paid'),
            ('cancel', 'Rejected'),
        ], 'Status', select=True, readonly=True, copy=False)
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
    line_ids = fields.One2many('hr.payslip.line', 'slip_id', 'Payslip Lines', readonly=True, states={'draft':[('readonly', False)], 'verify':[('readonly',False)]})

    @api.multi
    def do_cash_payment(self):
        res = {
            'name': 'Cash Payment',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'employee.payslip.cash.wizard',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        return res

    @api.multi
    def do_bank_payment(self):
        res = {
            'name': 'Bank Payment',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'employee.payslip.bank.wizard',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        return res

    @api.depends('employee_id')
    def _compute_advance_amount(self):
        recs = self.env['advance.pay'].search([])
        date_today = fields.Date.today()
        for rec in recs:
            if datetime.strptime(rec.date, "%Y-%m-%d").month == datetime.strptime(date_today, "%Y-%m-%d").month and datetime.strptime(rec.date, "%Y-%m-%d").year == datetime.strptime(date_today, "%Y-%m-%d").year:
                for lines in rec.advance_line:
                    if lines.employee.id == self.employee_id.id:
                        self.advance += lines.amount
            return

    @api.depends('employee_id')
    def _onchange_lop(self):
        recs = self.env['hr.holidays'].search([('employee_id','=',self.employee_id.id),('date_from','>=',self.date_from),('date_to','<=',self.date_to)])
        for rec in recs:
            self.lop += rec.lop_emp

    @api.multi
    def hr_verify_sheet(self):
        move = self.env['account.move']
        move_line = self.env['account.move.line']
        for rec in self:
            journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal'),('company_id','=',rec.company_id.id)])
            if not journal:
                raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
            if len(journal) > 1:
                raise except_orm(_('Warning!'),_('Multiple Journal with same name(Miscellaneous Journal)'))
            if rec.employee_id.payment_account.id == False:
                raise except_orm(_('Warning'),_('There is no payment account for this employee'))
            values = {
                    'journal_id': journal.id,
                    }
            move_id = move.create(values)
            amount = 0
            contract_id = self.env['hr.contract'].search([('employee_id','=',rec.employee_id.id),('state','=','active')], limit=1).id
            for line in rec.line_ids:
              
                if line.total != 0:
                    if not contract_id:
                        raise except_orm(_('Warning'),_('There is no Active contract for this employee'))
                    amount += line.total 
            values = {
                    'account_id': rec.employee_id.payment_account.id,
                    'name': rec.name,
                    'debit': amount,
                    'credit': 0,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values)
            values2 = {
                    'account_id': rec.employee_id.payment_account.id,
                    'name': 'Employee Salary',
                    'debit': 0,
                    'credit': amount,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values2)
            move_id.button_validate()
            rec.state = 'done'


    @api.multi
    def compute_sheet(self):
        slip_line_pool = self.env['hr.payslip.line']
        for rec in self:
            date_from = datetime.strptime(rec.date_from, '%Y-%m-%d')
            date_to = datetime.strptime(rec.date_to, '%Y-%m-%d')
            if date_from.month != date_to.month:
                raise exceptions.ValidationError('You cannot create employee payslip for multiple months')
            days = {'mon':0,'tue':1,'wed':2,'thu':3,'fri':4,'sat':5,'sun':6}
            date_start = datetime.strptime(rec.date_from,'%Y-%m-%d').date()
            date_end  = datetime.strptime(rec.date_to,'%Y-%m-%d').date()
            delta_day = timedelta(days=1)
            dt = date_start
            while dt <= date_end:
                if dt.weekday() != days['sun']:
                    full = self.env['hiworth.hr.attendance'].search([('attendance','=','full'),('name','=', rec.employee_id.id),('date','=',dt)])
                    if not full:
                        half = self.env['hiworth.hr.attendance'].search([('attendance','=','half'),('name','=', rec.employee_id.id),('date','=',dt)])
                        if half:
                            leave = self.env['hr.holidays'].search([('attendance','=','half'),('date_from','<=',dt),('date_to','>=',dt),('type','=','remove'),('employee_id','=', rec.employee_id.id),('state','=','validate')])
                            if not leave:
                                vals = self.env['hr.holidays'].create({'attendance' : 'half',
                                                                'employee_id' : rec.employee_id.id,
                                                                'name' : 'Leave for' + '' + rec.employee_id.name,
                                                                'date_from' : dt,
                                                                'date_to' : dt,
                                                                'type' : 'remove',
                                                                'leave_id': self.env.ref('hr_holidays.holiday_status_cl').id,
                                                                'state' : 'validate'
                                                                })
                                vals.action_validate()
                        else:
                            leave = self.env['hr.holidays'].search([('attendance','=','full'),('date_from','<=',dt),('date_to','>=',dt),('type','=','remove'),('employee_id','=', rec.employee_id.id),('state','=','validate')])
                            if not leave:
                                vals = self.env['hr.holidays'].create({'attendance' : 'full',
                                                                'employee_id' : rec.employee_id.id,
                                                                'name' : 'Leave for' + '' + rec.employee_id.name,
                                                                'date_from' : dt,
                                                                'date_to' : dt,
                                                                'type' : 'remove',
                                                                'leave_id': self.env.ref('hr_holidays.holiday_status_cl').id,
                                                                'state' : 'validate'
                                                                })
                                vals.action_validate()
                dt += delta_day
            amount = 0
            quantity=1
            day_count=0
            cant_amt = 0
            basic_amount = 0
            canteen_amount = 0
            canteen_amt = 0
            canteen_qty = 0
            lop_amount = 0
            insurance_amount = 0
            welfare_amount = 0
            other_amount = 0
            pf_amount = 0
            esi_amount = 0
            today = date.today()
            d = datetime.strptime(rec.date_from, '%Y-%m-%d') 
            start = date(d.year, d.month, 1)
            end = date(today.year, today.month, 1) - relativedelta(days=1)
            lop_days = 0
            allocation = self.env['hr.employee'].search([('id','=', rec.employee_id.id)])
            for leave_type in allocation.leave_ids:
                taken = 0.0
                days = 0
                holiday = self.env['hr.holidays'].search([('date_from','<=', rec.date_from),('date_to','>=', rec.date_from),('type','=','remove'),('leave_id','=',leave_type.leave_id.id),('employee_id','=', rec.employee_id.id),('state','=','validate')])
                for hol_id in holiday:
                    if hol_id.attendance == 'full':
                        taken += hol_id.nos
                    elif hol_id.attendance == 'half':
                        taken += float(hol_id.nos)/2
                    else:
                        pass
                holiday = self.env['hr.holidays'].search([('date_from','<=', rec.date_from),('date_to','>=', rec.date_from),('type','=','remove'),('leave_id','=',leave_type.leave_id.id),('employee_id','=', rec.employee_id.id),('state','=','validate')])
                for hol_id in holiday:
                    if hol_id.attendance == 'full':
                        taken += hol_id.nos
                    elif hol_id.attendance == 'half':
                        taken += float(hol_id.nos)/2
                    else:
                        pass
                status = self.env['month.leave.status'].search([('leave_id','=', leave_type.leave_id.id),('month_id','=',d.month),('status_id','=', allocation.id)], limit=1)
                if status.allowed < taken:
                    days = taken - status.allowed
                lop_days = lop_days + days
            days = {'mon':0,'tue':1,'wed':2,'thu':3,'fri':4,'sat':5,'sun':6}
            date_start = datetime.strptime(rec.date_from,'%Y-%m-%d').date()
            date_end  = datetime.strptime(rec.date_to,'%Y-%m-%d').date()
            delta_day = timedelta(days=1)
            dt = date_start
            while dt <= date_end:
                if dt.weekday() == days['sun']:
                    week_start = dt - relativedelta(days=6)
                    week_end = dt
                    full = self.env['hiworth.hr.attendance'].search([('attendance','=','full'),('name','=', rec.employee_id.id),('date','>',week_start),('date','<',week_end)])
                    half = self.env['hiworth.hr.attendance'].search([('attendance','=','half'),('name','=', rec.employee_id.id),('date','>',week_start),('date','<',week_end)])

                    if (len(full) + (len(half)/2)) < 3:
                        lop_days = lop_days + 1
                dt += delta_day
            lop_amount = rec.contract_id.wage/((abs((date_end - date_start).days)) + 1)
            for i in range(2):
                if i == 0:
                    for lines in rec.contract_id.rule_lines:
                        insurance_id = ''
                        if lines.rule_id.related_type == 'basic':
                            basic_amount = rec.contract_id.wage
                            amount = basic_amount
                            quantity = 1
                        elif lines.rule_id.related_type == 'canteen':
                            canteen = self.env['canteen.daily'].search([('employee_id','=', rec.employee_id.id),('date','>=', rec.date_from),('date','<=', rec.date_to)])
                            amount = self.env['general.hr.configuration'].search([],limit=1).canteen_amount
                            quantity = len(canteen)
                            canteen_amt = amount
                            canteen_qty = quantity
                        elif lines.rule_id.related_type == 'attendance':
                            
                                amount = lop_amount
                                quantity = lop_days

                        elif lines.rule_id.related_type == 'esi':
                            quantity = 1
                            contract_amt = 0
                            if basic_amount <= lines.rule_id.salary_limit:
                                contract_amt = basic_amount
                            else:
                                month = datetime.strptime(rec.date_from,'%Y-%m-%d').month
                                fin1 = self.env['general.hr.configuration'].search([('fin1_start','<=', month),('fin1_end','>=', month)])
                                if fin1:
                                    fin_date = date(datetime.strptime(rec.date_from, '%Y-%m-%d').year, fin1, 1)
                                    contract = self.env['hr.contract'].search([('date_start','<=',fin_date),('date_end','>=',fin_date),('employee_id','=', rec.employee_id.id)], limit=1).wage
                                    if contract <= lines.rule_id.salary_limit:
                                        contract_amt = lines.rule_id.salary_limit
                                
                                fin2 = self.env['general.hr.configuration'].search([('fin2_start','<=', month),('fin2_end','>=', month)])
                                if fin2:
                                    year = datetime.strptime(rec.date_from, '%Y-%m-%d').year
                                    fin_date = date(year, fin2, 1)
                                    contract = self.env['hr.contract'].search([('date_start','<=',fin_date),('date_end','>=',fin_date),('employee_id','=', rec.employee_id.id)], limit=1).wage
                                    if contract <= lines.rule_id.salary_limit:
                                        contract_amt = lines.rule_id.salary_limit
                            amount = (contract_amt - (lop_amount * lop_days))*(lines.rule_id.emloyee_ratio/100)
                            esi_amount = amount

                        elif lines.rule_id.related_type == 'pf':
                            quantity = 1
                            if basic_amount <= lines.rule_id.pf_sealing_limit:
                                amount = (basic_amount - (lop_amount * lop_days))*(lines.rule_id.emloyee_ratio/100)
                            else:
                                amount = (lines.rule_id.pf_sealing_limit - (lop_amount * lop_days))*(lines.rule_id.emloyee_ratio/100)
                            pf_amount = amount
                        elif lines.rule_id.related_type == 'insurance':
                            insurance = self.env['employee.insurance'].search([('policy_id','=',lines.rule_id.policy_id.id),('employee_id','=', rec.employee_id.id),('is_company_policy','=',True),('state','=','paid')], order='commit_date asc',limit=1)
                            amount = insurance.empol_contribution - insurance.emp_paid_amt
                            insurance_amount = insurance_amount + amount
                            insurance_id = insurance.id
                            quantity = 1
                        elif lines.rule_id.related_type == 'welfare':
                            amount = 0
                            welfares = self.env['employee.welfare.fund'].search([('state','=','active'),('employee_id','=', rec.employee_id.id)])
                            for welf_id in welfares:
                                amount += (welf_id.amount - welf_id.repay_amount)
                                quantity = 1
                            welfare_amount = amount
                        else:
                            amount = 0
                            if lines.is_related == True:
                                pass
                            else:
                                if lines.rule_id.rule_nature == 'allowance':
                                    if lines.rule_type == 'fixed':
                                        other_amount = other_amount + lines.amount
                                        amount = lines.amount
                                    if lines.rule_type == 'percent':
                                        other_amount = other_amount + ((lines.percentage * rec.contract_id.wage)/100)
                                        amount = ((lines.percentage * rec.contract_id.wage)/100)
                                if lines.rule_id.rule_nature == 'deduction':
                                    if lines.rule_type == 'fixed':
                                        other_amount = other_amount - lines.amount
                                        amount = lines.amount
                                    if lines.rule_type == 'percent':
                                        other_amount = other_amount - ((lines.percentage * rec.contract_id.wage)/100)
                                        amount = ((lines.percentage * rec.contract_id.wage)/100)
                        if amount != 0 and quantity != 0 and lines.rule_id.related_type != 'net':
                            values = {
                                'salary_rule_id': lines.rule_id.id,
                                'contract_id': rec.contract_id.id,
                                'name': lines.rule_id.name,
                                'rule_id': lines.rule_id.id,
                                'code': lines.rule_id.code,
                                'category_id': lines.rule_id.category_id.id,
                                'sequence': lines.rule_id.sequence,
                                'appears_on_payslip': lines.rule_id.appears_on_payslip,
                                'condition_select': lines.rule_id.condition_select,
                                'condition_python': lines.rule_id.condition_python,
                                'condition_range': lines.rule_id.condition_range,
                                'condition_range_min': lines.rule_id.condition_range_min,
                                'condition_range_max': lines.rule_id.condition_range_max,
                                'amount_select': lines.rule_id.amount_select,
                                'amount_fix': lines.rule_id.amount_fix,
                                'amount_python_compute': lines.rule_id.amount_python_compute,
                                'amount_percentage': lines.rule_id.amount_percentage,
                                'amount_percentage_base': lines.rule_id.amount_percentage_base,
                                'register_id': lines.rule_id.register_id.id,
                                'amount': amount,
                                'insurance_id':insurance_id,
                                'employee_id': rec.employee_id.id,
                                'quantity': quantity,
                                'rate': lines.amount,
                                'slip_id': rec.id
                            }
                            payslip = slip_line_pool.create(values)
                            payslip._calculate_total()
                if i == 1:
                    for lines in rec.contract_id.rule_lines:
                        amount = 0
                        insurance_id = ''
                        quantity=1

                        if lines.rule_id.related_type == 'net':
                            quantity=1
                            amount = basic_amount - (canteen_amt * canteen_qty) - (lop_amount * lop_days) - insurance_amount - welfare_amount - pf_amount - esi_amount + other_amount

                            values = {
                                'salary_rule_id': lines.rule_id.id,
                                'contract_id': rec.contract_id.id,
                                'name': lines.rule_id.name,
                                'rule_id': lines.rule_id.id,
                                'code': lines.rule_id.code,
                                'category_id': lines.rule_id.category_id.id,
                                'sequence': lines.rule_id.sequence,
                                'appears_on_payslip': lines.rule_id.appears_on_payslip,
                                'condition_select': lines.rule_id.condition_select,
                                'condition_python': lines.rule_id.condition_python,
                                'condition_range': lines.rule_id.condition_range,
                                'condition_range_min': lines.rule_id.condition_range_min,
                                'condition_range_max': lines.rule_id.condition_range_max,
                                'amount_select': lines.rule_id.amount_select,
                                'amount_fix': lines.rule_id.amount_fix,
                                'amount_python_compute': lines.rule_id.amount_python_compute,
                                'amount_percentage': lines.rule_id.amount_percentage,
                                'amount_percentage_base': lines.rule_id.amount_percentage_base,
                                'register_id': lines.rule_id.register_id.id,
                                'amount': amount,
                                'insurance_id':insurance_id,
                                'employee_id': rec.employee_id.id,
                                'quantity': quantity,
                                'rate': lines.amount,
                                'slip_id': rec.id
                            }
                            payslip = slip_line_pool.create(values)
                            payslip._calculate_total()
                        else:
                            pass
            rec.state = 'verify'
        return True   

class EmployeeLeave(models.Model):
    _inherit = 'res.company'

    salary_expense_id = fields.Many2one('account.account', 'Salary Expense Account')

class EmployeeLeave(models.Model):
    _name = 'employee.leave'

    leave_id = fields.Many2one('hr.holidays.status', 'Leave Type')
    nos = fields.Float('No of Days')
    remaining = fields.Float('Remaining')
    taken_leaves = fields.Float('Taken Leaves')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    holiday_id = fields.Many2one('hr.holidays', 'Leave Approve')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    state = fields.Selection([('active','Active'),
                              ('deactivate','Deactivate')], 'State')

    @api.multi
    def action_deactivate(self):
        self.state = 'deactivate'

class hr_payslip_line(models.Model):
    _inherit = 'hr.payslip.line'

    @api.multi
    @api.depends('quantity','amount')
    def _calculate_total(self):
        for record in self:
            record.total = record.quantity * record.amount

    amount = fields.Float('Amount', digits_compute=dp.get_precision('Payroll'), store=True)
    total = fields.Float(compute="_calculate_total", string='Total', digits_compute=dp.get_precision('Payroll'),store=True )
    rule_id = fields.Many2one('hr.salary.rule', string="Name")
    related_type = fields.Selection(related="rule_id.related_type", string="Related Process")
    insurance_id = fields.Many2one('employee.insurance','Employee Insurance')
    state = fields.Selection(related="slip_id.state")

    @api.multi
    def write(self, vals):
        result = super(hr_payslip_line, self).write(vals)
        if vals.get('amount') != None and vals.get('amount') != self.amount:
            deduction = 0
            allowance = 0
            lines = self.env['hr.payslip.line'].search([('slip_id','=',self.slip_id.id),('related_type','!=','net'),('related_type','!=',self.related_type)])

            for line_id in lines:
                if line_id.rule_id.rule_nature == 'deduction':
                    deduction += (line_id.amount * line_id.quantity)
                if line_id.rule_id.rule_nature == 'allowance':
                    allowance += (line_id.amount * line_id.quantity)
            if self.related_type == 'insurance':
                if self.rule_id.rule_nature == 'deduction':
                    deduction += (vals.get('amount') * self.quantity)
                if self.rule_id.rule_nature == 'allowance':
                    allowance += (vals.get('amount') * self.quantity)
            net = self.env['hr.payslip.line'].search([('slip_id','=',self.slip_id.id),('related_type','=','net')],limit=1)
            net.amount = allowance - deduction
            return result

class EmployeeZone(models.Model):
    _name = 'hr.employee.zone'

    name = fields.Char('Zone Name')

class HrEmployeeResignation(models.TransientModel):
    _name='hr.employee.resignation'

    resign_date = fields.Date('Released Date', default=fields.Date.today)
    resign_id =fields.Many2one('hr.employee')
    user_category = fields.Selection(related="resign_id.user_category")
    emp_code = fields.Char(related="resign_id.emp_code")
    mob_sim_return = fields.Boolean('Mobile - SIM Card Returned?')
    id_return = fields.Boolean('ID Card Returned?')
    atm_return = fields.Boolean('ATM Card Returned?')
    accounts_settled = fields.Boolean('Accounts Settled?')
    emp_satisfaction = fields.Text('Are you satisfied with this job?')
    reason_resign = fields.Text('Reason for resignation?')
    company_faults = fields.Text('Is there any fault from company side?')

    @api.multi
    def button_confirm(self):
        self.resign_id.resigning_date = self.resign_date
        self.resign_id.status1 = 'resign'

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    priority = fields.Boolean("Priority")