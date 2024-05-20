from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone



class ProjectWizardReport(models.TransientModel):
    _name = 'project.wizard.report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')


    project_id = fields.Many2one('project.project')




    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Project Report.xlsx')



class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'font': 'height 10'})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True, 'align': 'center',})
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

        worksheet.merge_range('A1:M1', 'PROJECT NAME :- %s'%(invoices.project_id.name), boldc)
        worksheet.merge_range('A2:H2', "Agreement No :%s"%(invoices.project_id.agrrement_no), boldc)
        worksheet.merge_range('J2:M2', 'Status On : %s' % (datetime.now().strftime("%d-%m-%Y")), boldc)

        worksheet.write("B%s"%(new_row),"LOA:",regular)
        worksheet.write("C%s"%(new_row),"",regular)
        worksheet.merge_range("E%s:F%s"%(new_row,new_row),"Agreement Date",regular)
        worksheet.write("G%s"%(new_row),invoices.project_id.agreement_date,regular)
        worksheet.merge_range("J%s:K%s" % (new_row, new_row), "Ts Approved", regular)
        worksheet.write("G%s" % (new_row), invoices.project_id.ts_approved_date, regular)
        new_row += 1
        worksheet.write("B%s" % (new_row), "Start:", regular)
        worksheet.write("C%s" % (new_row), invoices.project_id.start_date, regular)
        worksheet.merge_range("E%s:F%s" % (new_row, new_row), "Elapsed Duration", regular)
        worksheet.write("G%s" % (new_row), 0.0, regular)
        worksheet.merge_range("J%s:K%s" % (new_row, new_row), "Remaining Days", regular)
        worksheet.write("G%s" % (new_row), 0.0, regular)
        new_row += 1
        worksheet.write("B%s" % (new_row), "Finish:", regular)
        worksheet.write("C%s" % (new_row), invoices.project_id.date_end, regular)
        worksheet.merge_range("E%s:F%s" % (new_row, new_row), "EOT1", regular)
        worksheet.write("G%s" % (new_row),invoices.project_id.extend_time, regular)
        worksheet.merge_range("J%s:K%s" % (new_row, new_row), "EOT2", regular)
        worksheet.write("G%s" % (new_row), 0.0, regular)
        new_row += 2
        worksheet.merge_range("B%s:F%s"%(new_row,new_row), "Project Cost", regular)
        worksheet.write("G%s" % (new_row),0.0, regular)


BillReportXlsx('report.Project Report.xlsx', 'project.wizard.report')




