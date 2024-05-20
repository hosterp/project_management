from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from datetime import datetime

class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        dom = []
        if invoices.vehicle_id:
            dom.append(('id','=',invoices.vehicle_id.id))
        veh_dict = {}
        veh_list = []
        for vehicle in self.env['fleet.vehicle'].search(dom):
            vehicle_expense = 0
            if len(vehicle.name) <=30:
                name = vehicle.name.replace('/','-')
            else:
                name = vehicle.name[0:29].replace('/','-')
            worksheet = workbook.add_worksheet("%s"%(name))
            # raise UserError(str(invoices.invoice_no.id))

            boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'font': 'height 10'})
            heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
            bold = workbook.add_format({'bold': True})
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

            worksheet.merge_range('A1:A2', 'Date', regular)
            worksheet.merge_range('B1:B2', invoices.date_from + '-' + invoices.date_to, regular)
            worksheet.write('C1', 'Vehicle/Reg. No', regular)
            worksheet.merge_range('D1:E1', vehicle.name, regular)
            worksheet.write('C2', 'Type of Vehicle', regular)
            worksheet.merge_range('D2:E2', vehicle.vehicle_categ_id.name, regular)


            row = 4
            new_row = row
            count = 0
            from_date = datetime.strptime(invoices.date_from, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
            to_date = datetime.strptime(invoices.date_to, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
            material_issue_slip = self.env['material.issue.slip'].search([('date','>=',from_date),('date','<=',to_date),('vehicle_id','=',vehicle.id)])
            worksheet.write('A%s' % (new_row), 'Date', regular)
            worksheet.write('B%s' % (new_row), 'Description', regular)
            worksheet.write('C%s' % (new_row), 'Amount', regular)
            worksheet.write('D%s' % (new_row), 'Total Expense', regular)
            new_row += 1
            for rec in material_issue_slip:
                merge_row = new_row
                total_expense = 0
                for line in rec.material_issue_slip_lines_ids:
                    if merge_row != new_row:
                        worksheet.merge_range('A%s:A%s' % (merge_row,new_row), rec.date, regular)
                    else:
                        worksheet.write('A%s:A%s' % (merge_row, new_row), rec.date, regular)
                    worksheet.write('B%s' % (new_row), line.desc, regular)
                    worksheet.write('C%s' % (new_row), line.amount, regular)
                    total_expense += line.amount
                    if merge_row != new_row:
                        worksheet.merge_range('D%s:D%s' % (merge_row, new_row), total_expense, regular)
                    else:
                        worksheet.write('D%s:D%s' % (merge_row, new_row), total_expense, regular)
                    new_row += 1
                vehicle_expense += total_expense
            worksheet.write('D%s' % (new_row), vehicle_expense, regular)
            veh_list.append({'veh_name':vehicle.name,
                             'total':vehicle_expense,
                             'type':vehicle.vehicle_categ_id.name})
        worksheet = workbook.add_worksheet("Summary")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'font': 'height 10'})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True})
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

        worksheet.merge_range('A1:A2', 'Date', regular)
        worksheet.merge_range('B1:B2', invoices.date_from + '-' + invoices.date_to, regular)


        row = 4
        new_row = row
        count = 0
        worksheet.write('A%s' % (new_row), 'Vehicle/Reg. No', regular)
        worksheet.write('B%s' % (new_row), 'Type of Vehicle', regular)
        worksheet.write('C%s' % (new_row), 'Total Expense', regular)

        new_row += 1
        for rec in veh_list:

                worksheet.write('A%s' % (new_row), rec['veh_name'], regular)
                worksheet.write('B%s' % (new_row), rec['type'], regular)
                worksheet.write('C%s' % (new_row), rec['total'], regular)
                new_row+=1





BillReportXlsx('report.vehicle.maintenance.report.xlsx', 'vehicle.maintenance.wizard')
