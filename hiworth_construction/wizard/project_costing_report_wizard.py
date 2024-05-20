from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone



class ProjectCostingReportWizard(models.TransientModel):
    _name = 'project.costing.report.wizard'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')


    project_id = fields.Many2one('project.project')




    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Project Costing Report.xlsx')



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
        worksheet.merge_range('A2:H2', "PERIOD From %s To %s"%(invoices.from_date,invoices.to_date), boldc)
        worksheet.merge_range('A2:D3', "Performance of Major Items", boldc)
        new_row=4
        worksheet.write("A%s"%(new_row),"SN",regular)
        worksheet.write("B%s" % (new_row), "Description", regular)
        worksheet.write("C%s" % (new_row), "Unit", regular)
        worksheet.write("D%s" % (new_row), "Original Scope", regular)
        worksheet.write("E%s" % (new_row), "Expected Scope", regular)
        worksheet.write("F%s" % (new_row), "Today's Production", regular)
        worksheet.write("G%s" % (new_row), "This Month Programme", regular)
        worksheet.merge_range("H%s:J%s" % (new_row,new_row), "THIS MONTH (PRORATED TILL DATE)", regular)
        worksheet.write("H%s"%(new_row+1),"PLANNED",regular)
        worksheet.write("I%s" % (new_row + 1), "ACTUAL", regular)
        worksheet.write("J%s" % (new_row + 1), "%", regular)
        worksheet.merge_range("K%s:O%s" % (new_row, new_row), "CUMULATIVE TO DATE", regular)
        worksheet.write("K%s" % (new_row + 1), "BUDGETED", regular)
        worksheet.write("L%s" % (new_row + 1), "PLANNED", regular)
        worksheet.write("M%s" % (new_row + 1), "ACTUAL", regular)
        worksheet.write("N%s" % (new_row + 1), "BILLED", regular)
        worksheet.write("O%s" % (new_row + 1), "%", regular)
        worksheet.write("P%s" % (new_row + 1), "Balance Scope", regular)
        new_row +=2
        count = 1

        for rec in invoices:
            project_task = rec.project_id.task_ids
            for task in project_task:
                for line in task.task_line:

                    if line.major_item == True:

                        worksheet.write("A%s"%(new_row),count,regular)
                        worksheet.write("B%s" % (new_row), line.name.name, regular)
                        worksheet.write("C%s" % (new_row), line.unit.name, regular)
                        worksheet.write("D%s" % (new_row), line.amt, regular)
                        count +=1
                        new_row +=1

        worksheet.merge_range('A%s:H%s'%(new_row,new_row), "KEY ITEM COSTS (FOR THE MONTH)", boldc)
        new_row +=1
        worksheet.write("A%s" % (new_row), "SN", regular)
        worksheet.write("B%s" % (new_row), "Description", regular)
        worksheet.write("C%s" % (new_row), "Unit", regular)
        worksheet.write("D%s" % (new_row), "BOQ NO", regular)
        worksheet.write("E%s" % (new_row), "BUD/BOQ %", regular)
        worksheet.merge_range("F%s:J%s" % (new_row, new_row), "BUDGET RATE vs ACTUAL", regular)
        new_row +=1
        worksheet.write("F%s" % (new_row), "BOQ", regular)
        worksheet.write("G%s" % (new_row), "BUDGET", regular)
        worksheet.write("H%s" % (new_row), "ACTUAL", regular)
        worksheet.write("I%s" % (new_row), "DIFF", regular)
        worksheet.write("J%s" % (new_row), "%", regular)
        new_row +=2
        count = 1
        for rec in invoices:
            project_task = rec.project_id.task_ids
            for task in project_task:
                for line in task.task_line:
                    if line.major_item == True:
                        worksheet.write("A%s" % (new_row), count, regular)
                        worksheet.write("B%s" % (new_row), line.name.name, regular)
                        worksheet.write("C%s" % (new_row), line.unit.name, regular)
                        worksheet.write("F%s" % (new_row), line.qty, regular)
                        count += 1
                        new_row += 1

        worksheet.merge_range('A%s:H%s' % (new_row, new_row), "PROFITABILITY", boldc)
        new_row += 1
        worksheet.write("A%s" % (new_row), "SN", regular)
        worksheet.write("B%s" % (new_row), "Description", regular)
        worksheet.merge_range("D%s:H%s" % (new_row, new_row), "THIS MONTH", regular)
        new_row +=1
        worksheet.write("D%s" % (new_row), "BUDGETED", regular)
        worksheet.write("E%s" % (new_row), "PLANNED", regular)
        worksheet.write("F%s" % (new_row), "ACTUAL", regular)
        worksheet.write("G%s" % (new_row), "BILLED", regular)
        worksheet.write("H%s" % (new_row), "%", regular)
        worksheet.merge_range("I%s:M%s" % (new_row-1, new_row-1), "CUMULATIVE TO DATE", regular)

        worksheet.write("I%s" % (new_row), "BUDGETED", regular)
        worksheet.write("J%s" % (new_row), "PLANNED", regular)
        worksheet.write("K%s" % (new_row), "ACTUAL", regular)
        worksheet.write("L%s" % (new_row), "BILLED", regular)
        worksheet.write("M%s" % (new_row), "%", regular)
        worksheet.write("N%s"%(new_row),"COST AT COMPLETION",regular)
        new_row +=2
        count = 1
        for rec in invoices:
            project_task = rec.project_id.task_ids
            for task in project_task:
                for line in task.task_line:
                    for costing in line.costing_project_ids:


                            worksheet.write("A%s" % (new_row), count, regular)
                            worksheet.write("B%s" % (new_row), "Material", regular)
                            amt = 0
                            for material in costing.material_cost_ids:
                                amt +=material.amount
                            worksheet.write("D%s" % (new_row),amt, regular)
                            worksheet.write("E%s" % (new_row), amt, regular)
                            count += 1
                            new_row +=1
                            worksheet.write("A%s" % (new_row), count, regular)
                            worksheet.write("B%s" % (new_row), "Labour", regular)
                            amt = 0
                            for labour in costing.labour_cost_project_ids:
                                amt += labour.amount
                            worksheet.write("D%s" % (new_row), amt, regular)
                            worksheet.write("E%s" % (new_row), amt, regular)
                            count += 1
                            new_row =1
                            worksheet.write("A%s" % (new_row), count, regular)
                            worksheet.write("B%s" % (new_row), "Equipment", regular)
                            amt = 0
                            for equipment in costing.vehicle_category_cost_ids:
                                amt += equipment.amount
                            worksheet.write("D%s" % (new_row), amt, regular)
                            worksheet.write("E%s" % (new_row), amt, regular)
                            count += 1
                            new_row = 1


                            new_row += 1

BillReportXlsx('report.Project Costing Report.xlsx', 'project.costing.report.wizard')




