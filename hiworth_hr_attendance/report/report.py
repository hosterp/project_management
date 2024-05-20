from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class Employee(models.TransientModel):
    _name = 'hr.employee.wizard'

    user_category = fields.Selection([
        ('admin', 'Super User'),
        ('driver', 'Taurus Driver'),
        ('eicher_driver', 'Eicher Driver'),
        ('pickup_driver', 'Pick Up Driver'),
        ('lmv_driver', 'Light Motor Vehicle Driver'),
        ('directors', 'Directors'),
        ('project_manager', 'Project Manager'),
        ('office_manger', 'Office Manager'),
        ('project_eng', 'Project Engineer'),
        ('cheif_acc', 'Cheif Accountant'),
        ('sen_acc', 'Senior Accountant'),
        ('jun_acc', 'Junior Accountant'),
        ('cashier', 'Cashier'),
        ('project_cordinator', 'Project Cordinator'),
        ('technical_team', 'Technical Team'),
        ('telecome_bill', 'Telecome Billing'),
        ('survey_team', 'Survey Team'),
        ('quality', 'Quality'),
        ('tendor', 'Tendor'),
        ('interlocks', 'Interlocks'),
        ('liaisoning', 'Liaisoning'),
        ('hr', 'HR'),
        ('district_manager', 'District Manager'),
        ('site_eng', 'Captain/Site Engineer'),
        ('supervisor', 'Supervisor(Civil)'),
        ('super_telecome', 'Supervisor(Telecome)'),
        ('super_trainee', 'Supervisor(Trainee)'),
        ('operators', 'Operators'),
        ('helpers', 'Helpers'),
        ('vehicle_admin', 'Vehicle Administration'),
        ('purchase', 'Purchase'),
        ('civil_store', 'Civil Store'),
        ('telecome_store', 'Telecome Store'),
        ('security', 'Security'),
        ('labour', 'Labour'),
        ('civil_workshop', 'Civil Workshop'),
        ('vehicle_workshop', 'Vehicle Workshop'),
        ('all', 'All')
    ], default="all", string='User Category', required=True)

    @api.multi
    def action_employee_open_window(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_details_template',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def action_employee_open_window1(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_details_template',
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def get_special_details(self):
        list = []
        employees = self.env['hr.employee'].search([('user_category', '=', self.user_category)])
        if employees:
            for e in employees:
                esi = ''
                mediclaim = ''
                pf = ''
                qualification = ''
                training = ''
                if e.esi == True:
                    esi = "OK"
                if e.pf == True:
                    pf = "OK"
                if e.mediclaim == True:
                    mediclaim = "OK"
                for val in e.edu_qualify:
                    qualification += val.qualification + ','
                for val in e.tech_training:
                    training += val.name + ','
                basic_salary = self.env['hr.contract'].search([('employee_id', '=', e.id), ('state', '=', 'active')],
                                                              limit=1).wage
                ovt = []
                for ot in e.over_time_line:
                    ovt.append(ot)
                tpl = []
                for tl in e.trip_line:
                    tpl.append(tl)
                list.append({
                    'id_no': e.emp_code,
                    'employee_name': e.name,
                    'gender': e.gender,
                    'contact_no': e.mobile_phone,
                    'designation': e.user_category,
                    'date_joining': e.joining_date,
                    'no_months_job': e.no_mnth_job,
                    'year_service': e.year_service,
                    'age': e.age,
                    'basic_salary': basic_salary,
                    'pf': pf,
                    'mediclaim': mediclaim,
                    'esi': esi,
                    'ovt_sal': e.over_time_bata,
                    'esi_no': e.esi_no,
                    'over_time': ovt,
                    'tpl': tpl,
                })
        return list

    @api.multi
    def get_details(self):
        list = []
        if self.user_category == 'all':
            employees = self.env['hr.employee'].search([])
        else:
            employees = self.env['hr.employee'].search([('user_category', '=', self.user_category)])
        for empl_id in employees:
            esi = ''
            mediclaim = ''
            pf = ''
            qualification = ''
            training = ''
            if empl_id.esi == True:
                esi = "OK"
            if empl_id.pf == True:
                pf = "OK"
            if empl_id.mediclaim == True:
                mediclaim = "OK"
            for val in empl_id.edu_qualify:
                qualification += val.qualification + ','
            for val in empl_id.tech_training:
                training += val.name + ','
            basic_salary = self.env['hr.contract'].search([('employee_id', '=', empl_id.id), ('state', '=', 'active')],
                                                          limit=1).wage
            list.append({
                'id_no': empl_id.emp_code,
                'employee_name': empl_id.name,
                'gender': empl_id.gender,
                'contact_no': empl_id.mobile_phone,
                'qualification': qualification,
                'technical_training': training,
                'designation': empl_id.user_category,
                'department': empl_id.department_id.name,
                'date_joining': empl_id.joining_date,
                'no_months_job': empl_id.no_mnth_job,
                'year_service': empl_id.year_service,
                'age': empl_id.age,
                'dob': empl_id.birthday,
                'blood_group': empl_id.blood_group,
                'basic_salary': basic_salary,
                'pf': pf,
                'mediclaim': mediclaim,
                'esi': esi,
                'esi_no': empl_id.esi_no,
            })
        return list


class JoiningEmployees(models.Model):
    _name = 'employee.joinees.wizard'

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    user_category = fields.Selection([('admin', 'Super User'),
                                      ('driver', 'Taurus Driver'),
                                      ('eicher_driver', 'Eicher Driver'),
                                      ('pickup_driver', 'Pick Up Driver'),
                                      ('lmv_driver', 'Light Motor Vehicle Driver'),
                                      ('directors', 'Directors'),
                                      ('project_manager', 'Project Manager'),
                                      ('office_manger', 'Office Manager'),
                                      ('project_eng', 'Project Engineer'),
                                      ('cheif_acc', 'Cheif Accountant'),
                                      ('sen_acc', 'Senior Accountant'),
                                      ('jun_acc', 'Junior Accountant'),
                                      ('cashier', 'Cashier'),
                                      ('project_cordinator', 'Project Cordinator'),
                                      ('technical_team', 'Technical Team'),
                                      ('telecome_bill', 'Telecome Billing'),
                                      ('survey_team', 'Survey Team'),
                                      ('quality', 'Quality'),
                                      ('tendor', 'Tendor'),
                                      ('interlocks', 'Interlocks'),
                                      ('liaisoning', 'Liaisoning'),
                                      ('hr', 'HR'),
                                      ('district_manager', 'District Manager'),
                                      ('site_eng', 'Captain/Site Engineer'),
                                      ('supervisor', 'Supervisor(Civil)'),
                                      ('super_telecome', 'Supervisor(Telecome)'),
                                      ('super_trainee', 'Supervisor(Trainee)'),
                                      ('operators', 'Operators'),
                                      ('helpers', 'Helpers'),
                                      ('vehicle_admin', 'Vehicle Administration'),
                                      ('purchase', 'Purchase'),
                                      ('civil_store', 'Civil Store'),
                                      ('telecome_store', 'Telecome Store'),
                                      ('security', 'Security'),
                                      ('labour', 'Labour'),
                                      ('civil_workshop', 'Civil Workshop'),
                                      ('vehicle_workshop', 'Vehicle Workshop'),
                                      ('all', 'All')
                                      ], default="all", string='User Category', required=True)

    @api.multi
    def action_open_window(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Site Joinees',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_site_joinees_template',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def action_open_window1(self):

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Site Joinees',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_site_joinees_template',
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def get_details(self):

        list = []
        if self.user_category == 'all':
            employees = self.env['hr.employee'].search(
                [('joining_date', '>=', self.date_from), ('joining_date', '<=', self.date_to)])
        else:
            employees = self.env['hr.employee'].search(
                [('user_category', '=', self.user_category), ('joining_date', '>=', self.date_from),
                 ('joining_date', '<=', self.date_to)])
        for empl_id in employees:
            list.append({
                'id_no': empl_id.emp_id_no,
                'employee_name': empl_id.name,
                'designation': empl_id.user_category,
                'joining_date': empl_id.joining_date,
            })

        return list


class ResigningEmployees(models.Model):
    _name = 'employee.resign.wizard'

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    user_category = fields.Selection([('admin', 'Super User'),
                                      ('driver', 'Taurus Driver'),
                                      ('eicher_driver', 'Eicher Driver'),
                                      ('pickup_driver', 'Pick Up Driver'),
                                      ('lmv_driver', 'Light Motor Vehicle Driver'),
                                      ('directors', 'Directors'),
                                      ('project_manager', 'Project Manager'),
                                      ('office_manger', 'Office Manager'),
                                      ('project_eng', 'Project Engineer'),
                                      ('cheif_acc', 'Cheif Accountant'),
                                      ('sen_acc', 'Senior Accountant'),
                                      ('jun_acc', 'Junior Accountant'),
                                      ('cashier', 'Cashier'),
                                      ('project_cordinator', 'Project Cordinator'),
                                      ('technical_team', 'Technical Team'),
                                      ('telecome_bill', 'Telecome Billing'),
                                      ('survey_team', 'Survey Team'),
                                      ('quality', 'Quality'),
                                      ('tendor', 'Tendor'),
                                      ('interlocks', 'Interlocks'),
                                      ('liaisoning', 'Liaisoning'),
                                      ('hr', 'HR'),
                                      ('district_manager', 'District Manager'),
                                      ('site_eng', 'Captain/Site Engineer'),
                                      ('supervisor', 'Supervisor(Civil)'),
                                      ('super_telecome', 'Supervisor(Telecome)'),
                                      ('super_trainee', 'Supervisor(Trainee)'),
                                      ('operators', 'Operators'),
                                      ('helpers', 'Helpers'),
                                      ('vehicle_admin', 'Vehicle Administration'),
                                      ('purchase', 'Purchase'),
                                      ('civil_store', 'Civil Store'),
                                      ('telecome_store', 'Telecome Store'),
                                      ('security', 'Security'),
                                      ('labour', 'Labour'),
                                      ('civil_workshop', 'Civil Workshop'),
                                      ('vehicle_workshop', 'Vehicle Workshop'),
                                      ('all', 'All')
                                      ], default="all", string='User Category', required=True)

    @api.multi
    def action_open_window(self):

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Site Resignation',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_site_resign_template',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def action_open_window1(self):

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Site Resignation',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_site_resign_template',
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def get_details(self):

        list = []
        if self.user_category == 'all':
            employees = self.env['hr.employee'].search(
                [('joining_date', '>=', self.date_from), ('joining_date', '<=', self.date_to)])
        else:
            employees = self.env['hr.employee'].search(
                [('user_category', '=', self.user_category), ('joining_date', '>=', self.date_from),
                 ('joining_date', '<=', self.date_to)])
        for empl_id in employees:
            list.append({
                'id_no': empl_id.emp_id_no,
                'employee_name': empl_id.name,
                'designation': empl_id.user_category,
                'joining_date': empl_id.joining_date,
            })

        return list


class EmployeelnsuranceReport(models.Model):
    _name = 'employee.insurance.report'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    policy_id = fields.Many2one('policy.type', string='Type of Policy')
    state = fields.Selection([('all', 'All'),
                              ('draft', 'draft'),
                              ('paid', 'Paid'),
                              ('closed', 'Collected')
                              ], default='all')

    @api.multi
    def action_employee_insurance_open_window(self):
        print 'a------------------------------------------------'

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_insurance_details_template',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def action_employee_open_insurance_window1(self):
        print 'b------------------------------------------------'

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_insurance_details_template',
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def get_details(self):

        list = []
        if self.state == 'all':
            insurance = self.env['employee.insurance'].search(
                [('policy_id', '=', self.policy_id.id), ('commit_date', '>=', self.date_from),
                 ('commit_date', '<=', self.date_to)])
        else:
            insurance = self.env['employee.insurance'].search(
                [('state', '=', self.state), ('policy_id', '=', self.policy_id.id),
                 ('commit_date', '>=', self.date_from), ('commit_date', '<=', self.date_to)])
        print 'insurance--------------------------------------', insurance
        for ins_id in insurance:
            list.append({
                'id_no': ins_id.employee_id.emp_code,
                'employee_name': ins_id.employee_id.name,
                'designation': ins_id.user_category,
                'mobile_no': ins_id.work_phone,
                'gender': ins_id.gender,
                'dob': ins_id.birthday,
                'age': ins_id.age,
                'policy_type': ins_id.policy_id.name,
                'claim_duration': ins_id.claim_duration,
                'premium_amt': ins_id.premium_amount,
                'company_amt': ins_id.comp_contribution,
                'staff_amt': ins_id.empol_contribution,
                'no_persons': ins_id.no_of_person,
                'policy_no': ins_id.policy_no,
                'insured_no': ins_id.insured_code,
                'commit_date': ins_id.commit_date,
                'renew_date': ins_id.renew_date,
                # 'sponsored_by': ins_id.joining_date,
            })

        return list


class EmployeelnsuranceRenewalReport(models.Model):
    _name = 'insurance.renewal.report'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    policy_id = fields.Many2one('policy.type', string='Type of Policy')

    @api.multi
    def action_employee_insurance_open_window(self):
        print 'a------------------------------------------------'

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_insurance_renewal_template',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def action_employee_open_insurance_window1(self):
        print 'b------------------------------------------------'

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_insurance_renewal_template',
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def get_details(self):
        list = []
        insurance = self.env['employee.insurance'].search(
            [('policy_id', '=', self.policy_id.id), ('renew_date', '>=', self.date_from),
             ('renew_date', '<=', self.date_to)])
        print 'insurance--------------------------------------', insurance
        for ins_id in insurance:
            list.append({
                'id_no': ins_id.employee_id.emp_code,
                'employee_name': ins_id.employee_id.name,
                'designation': ins_id.user_category,
                'mobile_no': ins_id.work_phone,
                'gender': ins_id.gender,
                'dob': ins_id.birthday,
                'age': ins_id.age,
                'policy_type': ins_id.policy_id.name,
                'claim_duration': ins_id.claim_duration,
                'premium_amt': ins_id.premium_amount,
                'company_amt': ins_id.comp_contribution,
                'staff_amt': ins_id.empol_contribution,
                'no_persons': ins_id.no_of_person,
                'policy_no': ins_id.policy_no,
                'insured_no': ins_id.insured_code,
                'commit_date': ins_id.commit_date,
                'renew_date': ins_id.renew_date,
                # 'sponsored_by': ins_id.joining_date,
            })

        return list


class PF_ESIReport(models.Model):
    _name = 'pf_esi.wizard'

    month = fields.Selection([('January', 'January'),
                              ('February', 'February'),
                              ('March', 'March'),
                              ('April', 'April'),
                              ('May', 'May'),
                              ('June', 'June'),
                              ('July', 'July'),
                              ('August', 'August'),
                              ('September', 'September'),
                              ('October', 'October'),
                              ('November', 'November'),
                              ('December', 'December')], 'Month')

    year = fields.Selection([(num, str(num)) for num in range(1900, 2080)], 'Year', default=(datetime.now().year))

    @api.multi
    def action_employee_pf_esi_open_window(self):
        print 'a------------------------------------------------'

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_pf_esi_template',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def action_employee_pf_esi_open_window1(self):
        print 'b------------------------------------------------'

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'name': 'Employee Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_hr_attendance.report_employee_pf_esi_template',
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def get_esi_pf_details(self):

        list = []
        basic = 0
        attendance = 0
        wages_due = 0
        employee_amount = 0
        employer_amount = 0
        pf_wages = 0
        edli = 0
        employer_epf = 0
        employee_epf = 0
        employer_eps = 0
        esi = self.env['hr.esi.payment'].search([('month', '=', self.month), ('year', '=', self.year)], limit=1)
        pf = self.env['pf.payment'].search([('month', '=', self.month), ('year', '=', self.year)], limit=1)
        employees = self.env['hr.employee'].search(['|', ('esi', '=', True), ('pf', '=', True)])
        for empl_id in employees:
            print ', limit=1----------------------------', empl_id, esi, pf
            if esi:
                line1 = self.env['esi.payment.line'].search(
                    [('line_id', '=', esi.id), ('employee_id', '=', empl_id.id)])
                if line1:
                    basic = line1.basic
                    attendance = line1.attendance
                    wages_due = line1.wages_due
                    employee_amount = line1.employee_amount
                    employer_amount = line1.employer_amount
            print '22222222222222222222222222222222222222222222222'
            if pf:
                line2 = self.env['pf.payment.line'].search([('line_id', '=', pf.id), ('employee_id', '=', empl_id.id)])
                if line2:
                    pf_wages = line2.pf_wages
                    edli = line2.edli
                    employer_epf = line2.employer_epf
                    employee_epf = line2.employee_epf
                    employer_eps = line2.employer_eps

            print '11111111111111111111111111111111111111111111111'
            list.append({
                'employee_name': empl_id.name,
                'basic_pay': basic,
                'attendance': attendance,
                'wages_due': wages_due,
                'employee_esi': employee_amount,
                'employer_esi': employer_amount,
                'pf_wages': pf_wages,
                'edli': edli,
                'employer_epf': employer_epf,
                'employee_epf': employee_epf,
                'eps': employer_eps,
            })
            print 'list---------------------------------------', list

        return list

    @api.multi
    def get_final_amount(self):

        list = []
        esi_employee_amount = 0
        esi_employer_amount = 0
        esi_amount_total = 0
        pf_employee_amount = 0
        pf_employer_amount = 0
        eps_amount = 0
        edli_amount = 0
        admin_amount = 0
        pf_amount_total = 0

        esi = self.env['hr.esi.payment'].search([('month', '=', self.month), ('year', '=', self.year)], limit=1)
        esi_employee_amount = esi.employee_amount
        esi_employer_amount = esi.employer_amount
        esi_amount_total = esi.amount_total

        pf = self.env['pf.payment'].search([('month', '=', self.month), ('year', '=', self.year)], limit=1)
        pf_employee_amount = pf.employee_amount
        pf_employer_amount = pf.employer_amount
        eps_amount = pf.eps_amount
        admin_amount = pf.admin_amount
        pf_amount_total = pf.amount_total
        list.append({
            'employee_esi': esi_employee_amount,
            'employer_esi': esi_employer_amount,
            'net_esi': esi_amount_total,
            'employee_epf': pf_employee_amount,
            'employer_epf': pf_employer_amount,
            'employer_eps': eps_amount,
            'edli': edli_amount,
            'admin_charge': admin_amount,
            'net_epf': pf_amount_total,
        })

        return list

    @api.multi
    def get_head(self):

        list = []
        esi_rule = self.env['hr.salary.rule'].search([('related_type', '=', 'esi')])
        pf_rule = self.env['hr.salary.rule'].search([('related_type', '=', 'pf')])
        list.append({
            'edli': pf_rule.edli_ratio,
            'employee_epf': pf_rule.emloyee_ratio,
            'employer_epf': pf_rule.employer_epf_ratio,
            'eps': pf_rule.eps_ratio,
            'employer_esi': esi_rule.emloyer_ratio,
            'employee_esi': esi_rule.emloyee_ratio,
        })

        return list
