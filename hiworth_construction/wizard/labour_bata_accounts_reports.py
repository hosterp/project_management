from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone


class LabourBataAccountsReport(models.TransientModel):
    _name = 'labour.bata.accounts.report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    partner_select = fields.Selection([('sub', 'Subcontractor Labour'),
                                       ('com', 'Company Labour')], 'Labour Type', default='com')

    sub_contractor_id = fields.Many2one('res.partner', string="Subcontractor",
                                        domain="[('labour_contractor','=',True)]")

    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Labour Bata Accounts.xlsx')


class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'size': 12})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True,'align': 'center', 'size': 10})
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
        row = 3
        col = 1
        new_row = row

        worksheet.set_column('A:A', 13)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('D:S', 13)
        date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
        date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")
        worksheet.merge_range("A1:I1","PAYMENT FOR THE PERIOD OF (%s TO %s)"%(date_from.strftime("%d-%m-%Y"),date_to.strftime("%d-%m-%Y")),boldc)
        partner_select = ''
        if invoices.partner_select == 'com':
            partner_select = "Company Labour"
        else:
            partner_select = "Subcontractor Labour : " + invoices.sub_contractor_id.name
        worksheet.merge_range("A2:I2",partner_select,boldc)
        new_row=3
        count = 1
        full_total_day = 0
        full_total_ot = 0
        full_total_amount = 0
        for rec in invoices:

            if rec.partner_select == 'com':
                vehicle_row = 0
                for project in self.env['project.project'].search([]):
                    total = 0
                    total_day = 0
                    total_ot = 0
                    count=1
                    project_sheet = self.env['labour.activities.sheet'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to),
                         ('project_id', '=', project.id)])
                    if len(project_sheet) != 0:
                        worksheet.merge_range("A%s:I%s" % (new_row, new_row), project.name, bold)
                        new_row+=1
                        worksheet.write("A%s" % (new_row), "SL No", bold)
                        worksheet.write("B%s" % (new_row), "NAME", bold)
                        worksheet.write("C%s" % (new_row), "ID NO", bold)
                        worksheet.write("D%s" % (new_row), "SITE", bold)
                        worksheet.write("E%s" % (new_row), "DUTY/DAY", bold)
                        worksheet.write("F%s" % (new_row), "RATE", bold)
                        worksheet.write("G%s" % (new_row), "OT/HR", bold)
                        worksheet.write("H%s" % (new_row), "RATE", bold)
                        worksheet.write("I%s" % (new_row), "TOTAL", bold)
                        new_row +=1
                    duty = 0
                    ot_hr = 0
                    total_amt = 0
                    for labour_de in self.env['hr.employee'].search([('user_category', '=', 'ylabour')],
                                                                    order='labour_id asc'):
                        labour_sheet = self.env['labour.activities.sheet'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to),
                                  ('project_id', '=', project.id), ('employee_id', '=', labour_de.id)])

                        duty = 0
                        ot_hr = 0
                        total_amt = 0
                        wage = 0
                        for labour in labour_sheet:
                            duty += labour.day
                            ot_hr += labour.over_time
                            wage = labour.rate
                            total_amt += (labour.day * labour.rate)+(labour.over_time*labour_de.over_time_labour)
                        total+=total_amt
                        total_day += duty
                        total_ot += ot_hr
                        if len(labour_sheet)!=0:
                            worksheet.write("A%s" % (new_row), count, regular)
                            worksheet.write("B%s"%(new_row),labour_de.name,regular)
                            worksheet.write("C%s"%(new_row),labour_de.labour_id,regular)
                            worksheet.write("D%s"%(new_row),project.name,regular)
                            worksheet.write("E%s"%(new_row),duty,regular)
                            worksheet.write("F%s"%(new_row),wage,regular)
                            worksheet.write("G%s"%(new_row),ot_hr,regular)
                            worksheet.write("H%s"%(new_row),labour_de.over_time_labour,regular)
                            worksheet.write("I%s"%(new_row),total_amt,regular)
                            new_row +=1
                            count+=1
                    if len(project_sheet)!=0:
                        worksheet.merge_range("A%s:D%s"%(new_row,new_row),"Total",bold)
                        worksheet.write("E%s" % (new_row), total_day, bold)
                        full_total_day += total_day
                        worksheet.write("G%s" % (new_row), total_ot, bold)
                        full_total_ot += total_ot
                        worksheet.write("I%s"%(new_row),total,bold)
                        full_total_amount += total
                        new_row+=1

                worksheet.merge_range("A%s:D%s" % (new_row, new_row), "Total", bold)
                worksheet.write("E%s" % (new_row), full_total_day, bold)
                worksheet.write("G%s" % (new_row), full_total_ot, bold)
                worksheet.write("I%s" % (new_row), full_total_amount, bold)
                new_row += 1
            else:
                vehicle_row = 0
                for project in self.env['project.project'].search([]):
                    total = 0
                    total_day = 0
                    total_ot = 0
                    count = 1
                    project_sheet = self.env['labour.activities.sheet'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to),
                         ('project_id', '=', project.id)])
                    if len(project_sheet) != 0:
                        worksheet.merge_range("A%s:I%s" % (new_row, new_row), project.name, bold)
                        new_row += 1
                        worksheet.write("A%s" % (new_row), "SL No", bold)
                        worksheet.write("B%s" % (new_row), "NAME", bold)
                        worksheet.write("C%s" % (new_row), "ID NO", bold)
                        worksheet.write("D%s" % (new_row), "SITE", bold)
                        worksheet.write("E%s" % (new_row), "DUTY/DAY", bold)
                        worksheet.write("F%s" % (new_row), "RATE", bold)
                        worksheet.write("G%s" % (new_row), "OT/HR", bold)
                        worksheet.write("H%s" % (new_row), "RATE", bold)
                        worksheet.write("I%s" % (new_row), "TOTAL", bold)
                        new_row += 1
                    duty = 0
                    ot_hr = 0
                    total_amt = 0
                    for labour_de in self.env['subcontractor.labour'].search([('contractor_id', '=', rec.sub_contractor_id.id)],
                                                                    order='labour_id asc'):
                        labour_sheet = self.env['labour.activities.sheet'].search(
                            [('date', '>=', date_from), ('date', '<=', date_to),
                             ('project_id', '=', project.id), ('labour_id', '=', labour_de.id)])

                        duty = 0
                        ot_hr = 0
                        total_amt = 0
                        wage = 0
                        for labour in labour_sheet:
                            duty += labour.day
                            ot_hr += labour.over_time
                            wage = labour.rate
                            total_amt += (labour.day * labour.rate) + (labour.over_time * rec.sub_contractor_id.overtime_wage)
                        total += total_amt
                        total_day += duty
                        total_ot += ot_hr
                        if len(labour_sheet) != 0:
                            worksheet.write("A%s" % (new_row), count, regular)
                            worksheet.write("B%s" % (new_row), labour_de.name, regular)
                            worksheet.write("C%s" % (new_row), labour_de.labour_id, regular)
                            worksheet.write("D%s" % (new_row), project.name, regular)
                            worksheet.write("E%s" % (new_row), duty, regular)
                            worksheet.write("F%s" % (new_row), wage, regular)
                            worksheet.write("G%s" % (new_row), ot_hr, regular)
                            worksheet.write("H%s" % (new_row), rec.sub_contractor_id.overtime_wage, regular)
                            worksheet.write("I%s" % (new_row), total_amt, regular)
                            new_row += 1
                            count += 1
                    if len(project_sheet) != 0:
                        worksheet.merge_range("A%s:D%s" % (new_row, new_row), "Total", bold)
                        worksheet.write("E%s" % (new_row), total_day, bold)
                        full_total_day += total_day
                        worksheet.write("G%s" % (new_row), total_ot, bold)
                        full_total_ot += total_ot
                        worksheet.write("I%s" % (new_row), total, bold)
                        full_total_amount += total
                        new_row += 1

                worksheet.merge_range("A%s:D%s" % (new_row, new_row), "Total", bold)
                worksheet.write("E%s" % (new_row), full_total_day, bold)
                worksheet.write("G%s" % (new_row), full_total_ot, bold)
                worksheet.write("I%s" % (new_row), full_total_amount, bold)
                new_row += 1








BillReportXlsx('report.Labour Bata Accounts.xlsx', 'labour.bata.accounts.report')




