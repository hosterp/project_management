from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz


class LabourDetailsWizard(models.TransientModel):
    _name = 'labour.details.wizard'
    
    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', 'Company')
    
    partner_select = fields.Selection([('sub', 'Subcontractor Labour'),
                                       ('com', 'Company Labour')], 'Labour Type', default='com')
    project_id = fields.Many2one('project.project')
    labour_id = fields.Many2one('hr.employee', "Labour")
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
                              ('December', 'December')], 'Month', )
    sub_contractor_id = fields.Many2one('res.partner',string="Subcontractor",domain="[('labour_contractor','=',True)]")
    _defaults = {
        'date_today': datetime.today(),
        # 'from_date': '2017-04-01',
        # 'to_date': fields.Date.today(),
    }
    
    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 ' + self.month + ' ' + str(datetime.now().year)
            print
            'ddddddddddddddddddd', date
            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)
            print
            'sssssssssssssssss', end_date
            self.to_date = end_date
    
    @api.multi
    def generate_xls_report(self):
        return self.env["report"].get_action(self, report_name='labour_details_wizard.xlsx')


class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))
        
        boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'size': 12})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True, 'align': 'center','size': 10})
        rightb = workbook.add_format({'align': 'right', 'bold': True})
        right = workbook.add_format({'align': 'right'})
        regular = workbook.add_format({'align': 'center', 'bold': False, 'size': 8})
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D3D3D3',
            'font_color': '#000000',
        })
        format_hidden = workbook.add_format({
            'hidden': True
        })
        align_format = workbook.add_format({
            'align': 'right',
        })
        row = 6
        col = 1
        new_row = row
        
        worksheet.set_column('A:A', 13)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('D:S', 13)
        partner_select = ''
        if invoices.partner_select == 'com':
            partner_select = "Company Labour"
        else:
            partner_select = "Subcontractor Labour : " + invoices.sub_contractor_id.name
        
        worksheet.merge_range('A1:J1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:J2', partner_select, boldc)
        worksheet.merge_range('A3:J3', 'PAYMENT FOR THE PERIOD OF %s TO %s'%(datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%d/%m/%Y"),datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%d/%m/%Y")) , boldc)



        
        
        count = 1
        for rec in invoices:
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")
            labour_total = 0
            if rec.partner_select == 'com':
                if rec.labour_id:
                    worksheet.merge_range('A%s:J%s' % (new_row,new_row), rec.labour_id.name, bold)
                    new_row+=1

                    worksheet.write('A%s'%(new_row), 'Date', bold)

                    worksheet.write('B%s'%(new_row), 'SITE', bold)
                    worksheet.write('C%s'%(new_row), 'Supervisor/User', bold)
                    worksheet.write('D%s'%(new_row), 'Time IN', bold)
                    worksheet.write('E%s'%(new_row), 'Time OUT', bold)
                    worksheet.write('F%s'%(new_row), 'DUTY/DAY', bold)
                    worksheet.write('G%s'%(new_row), 'RATE', bold)
                    worksheet.write('H%s'%(new_row), 'OT/HR', bold)
                    worksheet.write('I%s'%(new_row), 'OT RATE', bold)

                    worksheet.write('J%s'%(new_row), 'TOTAL', bold)
                    new_row+=1
                    labour_report = self.env['labour.activities.sheet'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to), ('partner_select', '=', rec.partner_select),
                         ('employee_id', '=', rec.labour_id.id)],order='date asc')
                    for labour in labour_report:

                        worksheet.write('A%s' % (new_row), datetime.strptime(labour.date, "%Y-%m-%d").strftime("%d-%m-%Y"), regular)

                        worksheet.write('B%s' % (new_row), labour.project_id.name, regular)
                        worksheet.write('C%s' % (new_row), labour.supervisor_id.name, regular)
                        if labour.time_in:
                            from_zone = tz.gettz('UTC')
                            to_zone = tz.gettz('Asia/Kolkata')
                            # from_zone = tz.tzutc()
                            # to_zone = tz.tzlocal()
                            utc = datetime.strptime(labour.time_in, '%Y-%m-%d %H:%M:%S')
                            utc = utc.replace(tzinfo=from_zone)
                            central = utc.astimezone(to_zone)
                            central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S').strftime(
                "%d-%m-%Y %H:%M:%S")
                            worksheet.write('D%s' % (new_row), central, regular)
                        if labour.time_out:
                            from_zone = tz.gettz('UTC')
                            to_zone = tz.gettz('Asia/Kolkata')
                            # from_zone = tz.tzutc()
                            # to_zone = tz.tzlocal()
                            utc = datetime.strptime(labour.time_out, '%Y-%m-%d %H:%M:%S')
                            utc = utc.replace(tzinfo=from_zone)
                            central = utc.astimezone(to_zone)
                            central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                        '%Y-%m-%d %H:%M:%S').strftime(
                                "%d-%m-%Y %H:%M:%S")
                            worksheet.write('E%s' % (new_row), central, regular)
                        worksheet.write('F%s' % (new_row), labour.day, regular)
                        worksheet.write('G%s' % (new_row), labour.rate, regular)

                        worksheet.write('H%s' % (new_row), labour.over_time, regular)

                        worksheet.write('I%s' % (new_row), labour.ot_rate, regular)


                        worksheet.write('J%s' % (new_row), (labour.rate*labour.day) + labour.ot_amount, regular)
                        labour_total += (labour.rate*labour.day) + labour.ot_amount
                        count += 1
                        new_row += 1
                    if labour_report:
                        worksheet.merge_range('A%s:I%s' % (new_row, new_row), "TOTAL", bold)
                        worksheet.write('J%s' % (new_row), labour_total, bold)
                        new_row += 1
                    # worksheet.write('R%s' % (new_row), driver.remark, regular)

                else:

                    labour_dict = {}
                    for labour_de in self.env['hr.employee'].search([('user_category', '=', 'ylabour')],order='labour_id asc'):
                        labour_total = 0
                        labour_report = self.env['labour.activities.sheet'].search(
                            [('date', '>=', date_from), ('date', '<=', date_to),
                             ('partner_select', '=', rec.partner_select), ('employee_id', '=', labour_de.id)],
                            order='date asc')
                        if labour_report:
                            worksheet.merge_range('A%s:J%s' % (new_row, new_row), labour_de.name, bold)
                            new_row += 1

                            worksheet.write('A%s' % (new_row), 'Date', bold)

                            worksheet.write('B%s' % (new_row), 'SITE', bold)
                            worksheet.write('C%s' % (new_row), 'Supervisor/User', bold)
                            worksheet.write('D%s' % (new_row), 'Time IN', bold)
                            worksheet.write('E%s' % (new_row), 'Time OUT', bold)
                            worksheet.write('F%s' % (new_row), 'DUTY/DAY', bold)
                            worksheet.write('G%s' % (new_row), 'RATE', bold)
                            worksheet.write('H%s' % (new_row), 'OT/HR', bold)
                            worksheet.write('I%s' % (new_row), 'OT RATE', bold)

                            worksheet.write('J%s' % (new_row), 'TOTAL', bold)
                            new_row += 1



                        labour_list = []


                        for labour in labour_report:

                            worksheet.write('A%s' % (new_row),datetime.strptime(labour.date, "%Y-%m-%d").strftime("%d-%m-%Y"), regular)


                            worksheet.write('B%s' % (new_row), labour.project_id.name, regular)
                            worksheet.write('C%s' % (new_row), labour.supervisor_id.name, regular)
                            if labour.time_in:
                                from_zone = tz.gettz('UTC')
                                to_zone = tz.gettz('Asia/Kolkata')
                                # from_zone = tz.tzutc()
                                # to_zone = tz.tzlocal()
                                utc = datetime.strptime(labour.time_in, '%Y-%m-%d %H:%M:%S')
                                utc = utc.replace(tzinfo=from_zone)
                                central = utc.astimezone(to_zone)
                                central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                            '%Y-%m-%d %H:%M:%S').strftime(
                                    "%d-%m-%Y %H:%M:%S")
                                worksheet.write('D%s' % (new_row), central, regular)
                            if labour.time_out:
                                from_zone = tz.gettz('UTC')
                                to_zone = tz.gettz('Asia/Kolkata')
                                # from_zone = tz.tzutc()
                                # to_zone = tz.tzlocal()
                                utc = datetime.strptime(labour.time_out, '%Y-%m-%d %H:%M:%S')
                                utc = utc.replace(tzinfo=from_zone)
                                central = utc.astimezone(to_zone)
                                central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                            '%Y-%m-%d %H:%M:%S').strftime(
                                    "%d-%m-%Y %H:%M:%S")
                                worksheet.write('E%s' % (new_row), central, regular)
                            worksheet.write('F%s' % (new_row), labour.day, regular)
                            worksheet.write('G%s' % (new_row), labour.rate, regular)

                            worksheet.write('H%s' % (new_row), labour.over_time, regular)

                            worksheet.write('I%s' % (new_row), labour.ot_rate, regular)


                            worksheet.write('J%s' % (new_row), (labour.rate*labour.day) + labour.ot_amount, regular)
                            labour_total += (labour.rate * labour.day) + labour.ot_amount
                            count += 1
                            new_row += 1
                        if labour_report:
                            worksheet.merge_range('A%s:I%s' % (new_row, new_row), "TOTAL", bold)
                            worksheet.write('J%s' % (new_row), labour_total, bold)
                            new_row += 1
            else:
                labour_dict = {}
                count = 1
                for labour_de in self.env['subcontractor.labour'].search([('contractor_id', '=', rec.sub_contractor_id.id)],
                                                                order='labour_id asc'):
                    labour_total = 0
                    labour_report = self.env['labour.activities.sheet'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to),
                         ('partner_select', '=', rec.partner_select), ('labour_id', '=', labour_de.id)],
                        order='date asc')
                    if labour_report:
                        worksheet.merge_range('A%s:J%s' % (new_row, new_row), labour_de.name, bold)
                        new_row += 1

                        worksheet.write('A%s' % (new_row), 'Date', bold)

                        worksheet.write('B%s' % (new_row), 'SITE', bold)
                        worksheet.write('C%s' % (new_row), 'Supervisor/User', bold)
                        worksheet.write('D%s' % (new_row), 'Time IN', bold)
                        worksheet.write('E%s' % (new_row), 'Time OUT', bold)
                        worksheet.write('F%s' % (new_row), 'DUTY/DAY', bold)
                        worksheet.write('G%s' % (new_row), 'RATE', bold)
                        worksheet.write('H%s' % (new_row), 'OT/HR', bold)
                        worksheet.write('I%s' % (new_row), 'OT RATE', bold)

                        worksheet.write('J%s' % (new_row), 'TOTAL', bold)
                        new_row += 1

                    labour_list = []

                    for labour in labour_report:

                        worksheet.write('A%s' % (new_row),
                                        datetime.strptime(labour.date, "%Y-%m-%d").strftime("%d-%m-%Y"), regular)

                        worksheet.write('B%s' % (new_row), labour.project_id.name, regular)
                        worksheet.write('C%s' % (new_row), labour.supervisor_id.name, regular)
                        if labour.time_in:
                            from_zone = tz.gettz('UTC')
                            to_zone = tz.gettz('Asia/Kolkata')
                            # from_zone = tz.tzutc()
                            # to_zone = tz.tzlocal()
                            utc = datetime.strptime(labour.time_in, '%Y-%m-%d %H:%M:%S')
                            utc = utc.replace(tzinfo=from_zone)
                            central = utc.astimezone(to_zone)
                            central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                        '%Y-%m-%d %H:%M:%S').strftime(
                                "%d-%m-%Y %H:%M:%S")
                            worksheet.write('D%s' % (new_row), central, regular)
                        if labour.time_out:
                            from_zone = tz.gettz('UTC')
                            to_zone = tz.gettz('Asia/Kolkata')
                            # from_zone = tz.tzutc()
                            # to_zone = tz.tzlocal()
                            utc = datetime.strptime(labour.time_out, '%Y-%m-%d %H:%M:%S')
                            utc = utc.replace(tzinfo=from_zone)
                            central = utc.astimezone(to_zone)
                            central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                        '%Y-%m-%d %H:%M:%S').strftime(
                                "%d-%m-%Y %H:%M:%S")
                            worksheet.write('E%s' % (new_row), central, regular)
                        worksheet.write('F%s' % (new_row), labour.day, regular)
                        worksheet.write('G%s' % (new_row), labour.rate, regular)

                        worksheet.write('H%s' % (new_row), labour.over_time, regular)

                        worksheet.write('I%s' % (new_row), labour.ot_rate, regular)

                        worksheet.write('J%s' % (new_row), (labour.rate * labour.day) + labour.ot_amount, regular)
                        labour_total += (labour.rate * labour.day) + labour.ot_amount
                        count += 1
                        new_row += 1
                    if labour_report:
                        worksheet.merge_range('A%s:I%s' % (new_row, new_row), "TOTAL", bold)
                        worksheet.write('J%s' % (new_row), labour_total, bold)
                        new_row += 1

                # worksheet.write('R%s' % (new_row), driver.remark, regular)


BillReportXlsx('report.labour_details_wizard.xlsx', 'labour.details.wizard')




