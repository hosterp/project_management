from openerp import models, fields, api
import datetime, calendar, ast
import dateutil.parser
from datetime import timedelta


class HiworthHrLeave(models.Model):
    _name = 'hiworth.hr.leave'

    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    type_selection=fields.Selection([('approved','Approved'),('confirm','Confirmed'),('both','Both')], default='approved')
    attendance_type=fields.Selection([('daily','Daily'),('weekly','Weekly'),('monthly','Monthly')], default='monthly')
    active_ids=fields.Char()

    @api.multi
    def get_employee_code(self, o):
        return self.env['hr.employee'].search([('id','=',o.id)]).emp_code

    @api.multi
    def get_employee_designation(self, o):
        return self.env['hr.employee'].search([('id', '=', o.id)]).designation_id.name

    @api.multi
    def get_employee_doj(self, o):
        return self.env['hr.employee'].search([('id', '=', o.id)]).joining_date


    @api.multi 
    def get_location_ml(self,o,day):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        for r in rec:
            if dateutil.parser.parse(r.sign_in).date() == day[0]:
                return r.location.name

    @api.multi
    def get_employee_location(self, o, date):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        # ,('sign_in','>=',date),('sign_out','<=',date)
        for r in rec:
            if str(dateutil.parser.parse(r.sign_in).date()) == date:
                return r.location.name


    @api.onchange('attendance_type')
    def _onchange_attendance_type(self):
        if self.attendance_type:
            if self.attendance_type == 'daily':
                self.from_date = fields.date.today()
                self.to_date = fields.date.today()

    # Calculate default time ranges
    @api.model
    def default_time_range(self, type):
        year = datetime.date.today().year
        month = datetime.date.today().month
        last_day = calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1]
        first_day = 1
        if type=='from':
            return datetime.date(year, month, first_day)
        elif type=='to':
            return datetime.date(year, month, last_day)

    @api.model
    def print_hiworth_hr_leave_summary(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Attendance report filter",
            "res_model": "hiworth.hr.leave",
            "context": {'active_ids': self.env.context.get('active_ids',[])},
            "views": [[False, "form"]],
            "target": "new",
        }

    @api.multi
    def print_hiworth_hr_leave_summary_confirmed(self):
        self.ensure_one()
        hrEmployee = self.env['hr.employee']
        employees = hrEmployee.browse(self.env.context.get('active_ids',[]))
        datas = {
            'ids': employees._ids,
			'model': hrEmployee._name,
			'form': hrEmployee.read(),
			'context':self._context,
        }
        if self.attendance_type == 'monthly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary',
                'datas': datas,
                'context':{'start_date': self.from_date, 'end_date': self.to_date, 'type_selection': self.type_selection, }
            }
        if self.attendance_type == 'weekly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary',
                'datas': datas,
                'context':{'start_date': self.from_date, 'end_date': self.to_date, 'type_selection': self.type_selection, }
            }
        if self.attendance_type == 'daily':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary1',
                'datas': datas,
                'context':{'start_date': self.from_date, 'end_date': self.to_date, 'type_selection': self.type_selection, }
            }

    @api.multi
    def view_hiworth_hr_leave_summary_confirmed(self):
        self.ensure_one()

        self.active_ids=self.env.context.get('active_ids',[])
        if self.attendance_type == 'monthly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary_view',
                'report_type': 'qweb-html'
            }
        if self.attendance_type == 'weekly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary_view',
                'report_type': 'qweb-html'
            }
        if self.attendance_type == 'daily':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary_view1',
                'report_type': 'qweb-html'
            }


    def get_attendance_days(self, id, start_date, end_date):

        return self.env['hr.employee'].get_attendance_days(id, start_date, end_date)

    def get_selected_users(self, category_id):

        return self.env['hr.employee'].search([('user_category','=',category_id),('cost_type','!=','wages')])

    def get_selected_category(self):

        return ['admin',
                                      'cheif_acc',
                                      'hr',
                                      'icivil_store',
                                      'jpurchase',
                                      'planning',
                                      'project_manager',
                                      'site_eng',
                                      'supervisor',
                                      'suplevels',
                                      'tplant_mechanics',
                                      'tpoperators_helpers',
                                      'tppdriver',
                                      'ybill',
                                      'yqc',
                                      'yhouse_keeping',
                                      'ylabour',
                                      'ymess',
                                    ]

class HrEmployee(models.Model):
    _inherit='hr.employee'

    @api.multi
    def get_employee_location(self, o, date):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        # ,('sign_in','>=',date),('sign_out','<=',date)
        for r in rec:
            if str(dateutil.parser.parse(r.sign_in).date()) == date:
                return r.location.name


    @api.model
    def get_attendance_days(self, employee_id, start_date, end_date):
        # Find the list of days for which the report is to be generated
        delta=datetime.datetime.strptime(end_date, "%Y-%m-%d")-datetime.datetime.strptime(start_date, "%Y-%m-%d");
        selected_days=[(datetime.datetime.strptime(start_date, "%Y-%m-%d")+datetime.timedelta(days=day)).date() for day in range(delta.days+1)];

        '''
        Calculate all holidays including public holidays
        '''
        public_holidays = []
        public_holidays_recs = self.env['public.holiday'].search([ ('date','>=',(datetime.datetime.strptime(start_date, '%Y-%m-%d'))), ('date','<=',(datetime.datetime.strptime(end_date, '%Y-%m-%d')))])
        for public_holidays_rec in public_holidays_recs:
            public_holidays.append(public_holidays_rec.date)

        full_present = []
        full_present_recs = self.env['hiworth.hr.attendance'].search([('name','=',employee_id), ('attendance','=','full'), ('date','>=',(datetime.datetime.strptime(start_date, '%Y-%m-%d'))), ('date','<=',(datetime.datetime.strptime(end_date, '%Y-%m-%d')))])
        for full_present_rec in full_present_recs:
            full_present.append(full_present_rec.date)

        half_present = []
        half_present_recs = self.env['hiworth.hr.attendance'].search([('name','=',employee_id), ('attendance','=','half'), ('date','>=',(datetime.datetime.strptime(start_date, '%Y-%m-%d'))), ('date','<=',(datetime.datetime.strptime(end_date, '%Y-%m-%d')))])
        for half_present_rec in half_present_recs:
            half_present.append(half_present_rec.date)

        absent = []
        absent_recs = self.env['hiworth.hr.attendance'].search([('name','=',employee_id), ('attendance','=','absent'), ('date','>=',(datetime.datetime.strptime(start_date, '%Y-%m-%d'))), ('date','<=',(datetime.datetime.strptime(end_date, '%Y-%m-%d')))])
        for absent_rec in absent_recs:
            absent.append(absent_rec.date)


        '''
        Calculate the attendance of the employee
        'FP' marks the day for employee was present
        'HP' marks the day for employee was present
        'A' marks the day for employee was absent
        'H' public holidays or paid leaves
        'D' marks the a normal day of the week (non working day)

        selected_days_with_attendance = [(datetime.date(2017, 5, 1),), (datetime.date(2017, 5, 2),), ...]
        '''
        selected_days_with_attendance=[(day, ) for day in selected_days]
        for idx, day in enumerate(selected_days_with_attendance):
            # Check if day is sunday
            if datetime.datetime.strftime(day[0], "%Y-%m-%d") in public_holidays:
                selected_days_with_attendance[idx]+=("H",)

            elif day[0].isoweekday() in [7]:
                selected_days_with_attendance[idx]+=("S",)

            elif datetime.datetime.strftime(day[0], "%Y-%m-%d") in full_present:
                selected_days_with_attendance[idx]+=("FP",)

            elif datetime.datetime.strftime(day[0], "%Y-%m-%d") in half_present:
                selected_days_with_attendance[idx]+=("HP",)

            elif datetime.datetime.strftime(day[0], "%Y-%m-%d") in absent:
                selected_days_with_attendance[idx]+=("A",)

            elif day[0] > datetime.datetime.now().date():
                selected_days_with_attendance[idx]+=("D",)
            else:
                selected_days_with_attendance[idx]+=("A",)

        return selected_days_with_attendance;

    @api.model
    def get_total_public_holidays(self, selected_days_with_attendance):
        public_holidays = [day[0] for day in selected_days_with_attendance if day[1]=="H"]
        sundays = [day[0] for day in selected_days_with_attendance if day[1]=="S"]
        total_public_holidays = len(public_holidays) + len(sundays)
        return total_public_holidays

    @api.model
    def get_total_present_days1(self, selected_days_with_attendance,o,date):
        # print "selected ddayyyyyy", selected_days_with_attendance,o,date
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id),('sign_in','>=',date),('sign_out','<=',date)])
        # print "rec....................."  , rec
        if rec:
            return datetime.datetime.strptime(rec.sign_in, "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=5,minutes=30)
        else:
            return '---'

    @api.model
    def get_total_present_days(self, selected_days_with_attendance):
        full_present_days = [day[0] for day in selected_days_with_attendance if day[1]=="FP"]
        half_present_days = [day[0] for day in selected_days_with_attendance if day[1]=="HP"]
        total_present_days = len(full_present_days) + float(len(half_present_days))/2
        total_public_holidays = self.get_total_public_holidays(selected_days_with_attendance)
        return total_present_days+total_public_holidays

    @api.model
    def get_total_leaves1(self, selected_days_with_attendance,o,date):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id),('sign_in','>=',date),('sign_out','<=',date)])
        # print "rec....................."  , rec
        if rec:
            return datetime.datetime.strptime(rec.sign_out, "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=5,minutes=30)
        else:
            return '---'

    @api.model
    def get_total_leaves(self, selected_days_with_attendance):
        
        leave_days = [day[0] for day in selected_days_with_attendance if day[1]=="A"]
        total_leave_days = len(leave_days)
        return total_leave_days

    @api.model
    def get_previous_leaves(self, selected_days_with_attendance,employee_id, start_date, end_date):
        list = []
        print 'vals123--------------------------', employee_id, start_date, end_date
        print '--------------------------', datetime.datetime.strptime(start_date, '%Y-%m-%d').month
        pre_leaves = 0
        all_leaves = 0
        net_leaves = 0
        month = datetime.datetime.strptime(start_date, '%Y-%m-%d').month
        day = self.env['hr.employee'].search([('id','=',employee_id)])
        for day1 in day.leave_ids:
            if day1.leave_id.effective_monthly_leave != 0:
                status = self.env['month.leave.status'].search([('status_id','=', day.id),('leave_id','=', day1.leave_id.id),('month_id','=',month)], limit=1)
               
                taken = 0
                holiday = self.env['hr.holidays'].search([('type','=','remove'),('employee_id','=', day.id)])
                for hol_id in holiday:
                    
                    if (start_date <= hol_id.date_from <= end_date) or (start_date <= hol_id.date_to<= end_date):
                        date_from1 = datetime.datetime.strptime(hol_id.date_from, '%Y-%m-%d').date()
                        date_to1 = datetime.datetime.strptime(hol_id.date_to, '%Y-%m-%d').date()
                        delta = date_to1 - date_from1
                        
                        if hol_id.attendance == 'full':
                            for i in range(delta.days + 1):
                                if (date_from1 + timedelta(i)).month == month:
                                    taken += 1

                        elif hol_id.attendance == 'half':
                            for i in range(delta.days + 1):
                                if (date_from1 + timedelta(i)).month == month:
                                    taken += 0.5
                        else:
                            pass
                
                pre_leaves += status.allowed - day1.leave_id.effective_monthly_leave
                all_leaves += day1.leave_id.effective_monthly_leave
                net_leaves += status.allowed - taken
        list.append({
                    'pre_leaves': pre_leaves,
                    'all_leaves': all_leaves,
                    'net_leaves': net_leaves,
                    })

        return list



