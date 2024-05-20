from openerp import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class ReportDailyProgressReport(models.TransientModel):
    _name = 'report.daily.progress.report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    project_id = fields.Many2one('project.project', "Project")
    company_id = fields.Many2one('res.company', "Company")


    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='custom.daily_progress_report.xlsx')


class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Site")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format(
            {'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'font': 'height 10', 'border': 1})
        boldlwb = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'top', 'bg_color': '#ffffff ', 'font': 'height 10', 'right': 1})
        boldlbborder = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'top', 'bg_color': '#ffffff ', 'font': 'height 10', 'bottom': 1,
             'right': 1})
        boldl = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'top', 'bg_color': '#ffffff ', 'font': 'height 10', 'border': 1})
        boldm = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'vcenter', 'bg_color': '#ffffff ', 'font': 'height 10'})
        boldb = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'bottom', 'bg_color': '#ffffff ', 'font': 'height 10',
             'border': 1})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True, 'align': 'center', 'size': 8, 'text_wrap': True,})
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
        worksheet.merge_range('A1:F2', "Begorra Infrastructure and Developers PVT LTD", boldlwb)
        worksheet.merge_range('A3:F4', 'DAILY PROGRESS REPORT', boldlwb)
        worksheet.merge_range('A5:F6', 'NAME OF WORK :%s'%(invoices.project_id.name), boldlbborder)
        worksheet.merge_range('G1:L3', 'ESTIMATED PAC :', boldb)
        worksheet.merge_range('G4:L6', 'ESTIMATED PAC :', boldl)
        worksheet.merge_range('M1:S2', 'Agreement No: %s'%(invoices.project_id.agrrement_no), boldlwb)
        worksheet.merge_range('M3:S3', 'Site handed over date:%s'%(invoices.project_id.site_hand_date), boldlwb)
        worksheet.merge_range('M4:S4', 'Completion date:%s'%(invoices.project_id.date_end), boldlwb)
        worksheet.merge_range('M5:S5', 'Project Duration(Days):', boldlwb)
        worksheet.merge_range('M6:S6', 'Completed days as on:', boldlbborder)

        row=7
        worksheet.merge_range("A%s:I%s"%(row,row),"A. Manpower Expenses",bold)
        row+=1
        worksheet.set_column('D:D', 8)
        worksheet.set_column('A:A', 21)
        worksheet.set_column('J:J', 18)
        worksheet.set_column('AJ:AJ', 18)
        worksheet.set_column('Z:Z', 10)
        worksheet.write("A%s"%(row),"Trade",bold)
        worksheet.write("B%s"%(row),"Unit",bold)
        worksheet.write("C%s"%(row),"Rate",bold)
        worksheet.merge_range("D%s:D%s"%(row,row+1),"Upto Previous Quantity",bold)
        worksheet.merge_range("E%s:E%s"%(row,row+1),"Upto Previous Amount",bold)
        worksheet.merge_range("F%s:F%s"%(row,row+1),"Current Quantity",bold)
        worksheet.merge_range("G%s:G%s"%(row,row+1),"Current Amount",bold)
        worksheet.merge_range("H%s:H%s"%(row,row+1),"Upto Date Quantity",bold)
        worksheet.merge_range("I%s:I%s"%(row,row+1),"Upto Date Amount",bold)
        labour_sheet = self.env['labour.activities.sheet'].search([('date','>=',invoices.from_date),('date','<=',invoices.to_date),('project_id','=',invoices.project_id.id)])
        upto_labour = self.env['labour.activities.sheet'].search([('date','<',invoices.from_date),('project_id','=',invoices.project_id.id)])
        row+=2
        worksheet.write("A%s"%(row),"Workers",bold)
        row+=1
        worksheet.write("A%s"%(row),"Skilled Labours",regular)
        man_total_upto = 0
        man_total_current=0
        upto =0
        current = 0
        for labour in upto_labour:
            if labour.category == 'skilled':
                upto += (labour.rate * labour.day) + (labour.ot_amount)
                man_total_upto +=(labour.rate * labour.day) + ( labour.ot_amount)

        worksheet.write("E%s"%(row),upto,regular)
        for labour in labour_sheet:
            if labour.category == 'skilled':
                current +=(labour.rate * labour.day) + (labour.ot_amount)
                man_total_current += (labour.rate * labour.day) + ( labour.ot_amount)

        worksheet.write("G%s" % (row), current, regular)
        worksheet.write("I%s" % (row), current+upto, regular)
        row+=1
        worksheet.write("A%s" % (row), "Unskilled Labours", regular)
        upto = 0
        current = 0
        for labour in upto_labour:
            if labour.category == 'unskilled':
                upto += (labour.rate * labour.day) + (labour.ot_amount)
                man_total_upto += (labour.rate * labour.day) + ( labour.ot_amount)

        worksheet.write("E%s" % (row), upto, regular)
        for labour in labour_sheet:
            if labour.category == 'unskilled':
                current += (labour.rate * labour.day) + ( labour.ot_amount)
                man_total_current += (labour.rate * labour.day) + ( labour.ot_amount)
        worksheet.write("G%s" % (row), current, regular)
        worksheet.write("I%s" % (row), current + upto, regular)
        row+=1
        worksheet.write("A%s" % (row), "Survey Labours", regular)
        upto = 0
        current = 0
        for labour in upto_labour:
            if labour.category == 'survey':
                upto += (labour.rate * labour.day) + ( labour.ot_amount)
                man_total_upto += (labour.rate * labour.day) + ( labour.ot_amount)

        worksheet.write("E%s" % (row), upto, regular)
        for labour in labour_sheet:
            if labour.category == 'survey':
                current += (labour.rate * labour.day) + ( labour.ot_amount)
                man_total_current += (labour.rate * labour.day) + ( labour.ot_amount)
        worksheet.write("G%s" % (row), current, regular)
        worksheet.write("I%s" % (row), current + upto, regular)
        row+=1
        worksheet.write("A%s" % (row), "Union Labours", regular)
        upto = 0
        current = 0
        for labour in upto_labour:
            if labour.category == 'union':
                upto += (labour.rate * labour.day) + ( labour.ot_amount)
                man_total_upto += (labour.rate * labour.day) + ( labour.ot_amount)

        worksheet.write("E%s" % (row), upto, regular)
        for labour in labour_sheet:
            if labour.category == 'union':
                current += (labour.rate * labour.day) + (labour.ot_amount)
                man_total_current += (labour.rate * labour.day) + ( labour.ot_amount)
        worksheet.write("G%s" % (row), current, regular)
        worksheet.write("I%s" % (row), current + upto, regular)
        row += 1
        worksheet.write("A%s" % (row), "Other Labours", regular)
        upto = 0
        current = 0
        for labour in upto_labour:
            if not labour.category:
                upto += (labour.rate * labour.day) + ( labour.ot_amount)
                man_total_upto += (labour.rate * labour.day) + ( labour.ot_amount)


        worksheet.write("E%s" % (row), upto, regular)
        for labour in labour_sheet:
            if not labour.category:
                current += (labour.rate * labour.day) + ( labour.ot_amount)
                man_total_current += (labour.rate * labour.day) + ( labour.ot_amount)

        worksheet.write("G%s" % (row), current, regular)
        worksheet.write("I%s" % (row), current + upto, regular)

        row+=3
        worksheet.write("A%s"%(row),"Total A. (ManPower)",bold)
        worksheet.write("E%s" % (row), man_total_upto, bold)
        worksheet.write("G%s" % (row), man_total_current, bold)
        worksheet.write("I%s" % (row), man_total_current + man_total_upto, bold)
        row+=1

        worksheet.write("A%s"%(row),"B. General Expenses",bold)
        row+=1
        worksheet.write("A%s"%(row),"Description",bold)
        worksheet.write("B%s"%(row),"Unit",bold)
        worksheet.write("C%s"%(row),"Rate",bold)
        worksheet.merge_range("E%s:E%s"%(row,row+1),"Upto Previous Amount",bold)
        worksheet.merge_range("G%s:G%s"%(row,row+1),"Current Amount",bold)
        worksheet.merge_range("I%s:I%s"%(row,row+1),"Upto Date Amount",bold)
        row+=2
        upto_daily = self.env['partner.daily.statement'].search([('date','<',invoices.from_date),('project_id','=',invoices.project_id.id)])
        curr_daily = self.env['partner.daily.statement'].search([('date','>=',invoices.from_date),('date','<=',invoices.to_date),('project_id','=',invoices.project_id.id)])
        gen_total_upto =0
        gen_total_curr = 0
        worksheet.write("A%s"%(row),"Rent",regular)
        upto = 0
        curr = 0
        for daily in upto_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'rent':
                    upto += expense.total
                    gen_total_upto+=upto
        worksheet.write("E%s"%(row),upto,regular)
        for daily in curr_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'rent':
                    curr += expense.total
                    gen_total_curr+=curr
        worksheet.write("G%s"%(row),curr,regular)
        worksheet.write("I%s" % (row), curr+upto, regular)
        row+=1
        worksheet.write("A%s" % (row), "Bank Guarantee Charges", regular)
        upto = 0
        curr = 0
        for daily in upto_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'bank_guarantee':
                    upto += expense.total
                    gen_total_upto += upto
        worksheet.write("E%s" % (row), upto, regular)
        for daily in curr_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'bank_guarantee':
                    curr += expense.total
                    gen_total_curr += curr
        worksheet.write("G%s" % (row), curr, regular)
        worksheet.write("I%s" % (row), curr + upto, regular)
        row+=1
        worksheet.write("A%s" % (row), "General Expenses", regular)
        upto = 0
        curr = 0
        for daily in upto_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'general':
                    upto += expense.total
                    gen_total_upto += upto
        worksheet.write("E%s" % (row), upto, regular)
        for daily in curr_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'general':
                    curr += expense.total
                    gen_total_curr += curr
        worksheet.write("G%s" % (row), curr, regular)
        worksheet.write("I%s" % (row), curr + upto, regular)
        row+=1
        worksheet.write("A%s" % (row), "Survey Expenses", regular)
        upto = 0
        curr = 0
        for daily in upto_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'survey':
                    upto += expense.total
                    gen_total_upto += upto
        worksheet.write("E%s" % (row), upto, regular)
        for daily in curr_daily:
            for expense in daily.expense_line_ids:
                if expense.item == 'survey':
                    curr += expense.total
                    gen_total_curr += curr
        worksheet.write("G%s" % (row), curr, regular)
        worksheet.write("I%s" % (row), curr + upto, regular)
        row+=5
        worksheet.write("A%s"%(row),"Total B. (General Expenses)",bold)
        worksheet.write("E%s" % (row), gen_total_upto, bold)
        worksheet.write("G%s" % (row), gen_total_curr, bold)
        worksheet.write("I%s" % (row), gen_total_curr + gen_total_upto, bold)
        row+=2

        worksheet.write("A%s"%(row),"C. Subcontract",bold)
        row+=1
        worksheet.write("A%s"%(row),"Item Description",bold)
        worksheet.write("B%s"%(row),"Unit",bold)
        worksheet.write("C%s"%(row),"Rate",bold)
        worksheet.merge_range("D%s:D%s"%(row,row+1),"Upto Previous Qty",bold)
        worksheet.merge_range("E%s:E%s"%(row,row+1),"Upto Previous Amount",bold)
        worksheet.merge_range("F%s:F%s"%(row,row+1),"Current Day Qty",bold)
        worksheet.merge_range("G%s:G%s"%(row,row+1),"Current Day Amount",bold)
        worksheet.merge_range("H%s:H%s"%(row,row+1),"Upto Date Qty",bold)
        worksheet.merge_range("I%s:I%s"%(row,row+1),"Upto Date Amount",bold)
        row+=2
        worksheet.merge_range("A%s:D%s"%(row,row),"Amount of closed Sub-contractors Bills ",bold)
        row+=1
        sub_contracor = self.env['work.order.payment'].search(
            [('project_id', '=', invoices.project_id.id),
             ])
        sub_total_upto = 0
        sub_total_curr =0
        workorder = self.env['work.order'].search([('project_id', '=', invoices.project_id.id),('state','=','start')])
        for work in workorder:
            for lines in work.order_lines:
                worksheet.write("A%s" % (row), lines.item_work_id.name, regular)
                worksheet.write("B%s" % (row), lines.uom_id.name, regular)
                worksheet.write("C%s" % (row), lines.rate, regular)
                for sub in sub_contracor:
                    for line in sub.master_plan_line:
                        if line.name.id == lines.item_work_id.id:
                            upto = 0
                            curr= 0
                            for detail in line.detailed_ids:
                                if detail.date < invoices.from_date:
                                    upto +=detail.qty

                                if detail.date >= invoices.from_date and detail.date <= invoices.to_date:
                                    curr += detail.qty

                            worksheet.write("D%s" % (row), upto, regular)
                            worksheet.write("E%s" % (row), line.rate*upto, regular)
                            sub_total_upto += line.rate*upto
                            worksheet.write("F%s" % (row), curr, regular)
                            worksheet.write("G%s" % (row), line.rate*curr, regular)
                            sub_total_curr += line.rate*curr
                            worksheet.write("H%s" % (row), upto + curr, regular)
                            worksheet.write("I%s" % (row), line.rate * (upto+curr), regular)
                row+=1
        worksheet.write("A%s"%(row),"Total C. (Subcontract)",bold)
        worksheet.write("E%s" % (row), sub_total_upto, bold)
        worksheet.write("G%s" % (row), sub_total_curr, bold)
        worksheet.write("I%s" % (row), sub_total_curr + sub_total_upto, bold)
        row+=1
        worksheet.merge_range("A%s:A%s"%(row,row+2),"Description",bold)
        worksheet.merge_range("B%s:B%s" % (row, row + 2), "Unit", bold)
        worksheet.merge_range("C%s:E%s" % (row, row), "Material Received", bold)
        worksheet.merge_range("C%s:C%s" % (row+1, row+2), "Up to Previous", bold)
        worksheet.merge_range("D%s:D%s" % (row+1, row + 2), "Today", bold)
        worksheet.merge_range("E%s:E%s" % (row+1, row + 2), "Up to date", bold)
        worksheet.merge_range("F%s:H%s" % (row, row), "Consumption", bold)
        worksheet.merge_range("F%s:F%s" % (row+1, row + 2), "Up to Previous", bold)
        worksheet.merge_range("G%s:G%s" % (row+1, row + 2), "Today", bold)
        worksheet.merge_range("H%s:H%s" % (row+1, row + 2), "Up to date", bold)
        worksheet.merge_range("I%s:I%s" % (row+1, row + 2), "Up to Date Stock", bold)
        row+=3
        products = self.env['product.product'].search([])

        for prod in products:
            upto = 0
            curr = 0

            cons_upto = 0
            cons_curr = 0
            for daily in upto_daily:
                for pro in daily.received_ids:
                    if pro.product_id.id == prod.id:
                        upto += pro.qty
                        cons_upto+=pro.product_qty


            for daily in curr_daily:
                for pro in daily.received_ids:
                    if pro.product_id.id == prod.id:
                        curr += pro.qty
                        cons_curr += pro.product_qty



            if upto != 0 or curr != 0 or cons_upto!=0 or cons_curr!=0:
                worksheet.write("A%s" % (row), prod.name, regular)
                worksheet.write("B%s" % (row), prod.uom_id.name, regular)
                worksheet.write("C%s" % (row), upto, regular)
                worksheet.write("D%s" % (row), curr, regular)
                worksheet.write("E%s" % (row), upto +curr, regular)
                worksheet.write("F%s" % (row), cons_upto, regular)
                worksheet.write("G%s" % (row), cons_curr, regular)
                worksheet.write("H%s" % (row), cons_upto + cons_curr, regular)
                worksheet.write("I%s" % (row),(upto +curr) -  (cons_upto + cons_curr), regular)
                row += 1

        worksheet.write("A%s"%(row),"Remarks:",bold)
        row=7
        worksheet.write("J%s"%(row),"D. Equipment Expenses",bold)
        row+=1
        worksheet.write("J%s"%(row),"Description",bold)
        worksheet.write("K%s"%(row),"Unit",bold)
        worksheet.write("L%s"%(row),"Rate",bold)
        worksheet.merge_range("M%s:M%s"%(row,row+1),"Upto Previous Day",bold)
        worksheet.merge_range("N%s:N%s"%(row,row+1),"Upto Previous Amount",bold)
        worksheet.merge_range("O%s:O%s"%(row,row+1),"Current Day Qty",bold)
        worksheet.merge_range("P%s:P%s"%(row,row+1),"Amount",bold)
        worksheet.merge_range("Q%s:Q%s"%(row,row+1),"Upto Date Quantity",bold)
        worksheet.merge_range("R%s:R%s"%(row,row+1),"Upto Date Amount",bold)
        row+=2
        mach_total_upto = 0
        mach_total_curr = 0

        machineries = self.env['fleet.vehicle'].search([])
        for mach in machineries:
            rent = 0
            worksheet.write("J%s"%(row),mach.name,regular)
            unit = ''
            if mach.machinery == True:
                unit = "Hours"
            if mach.vehicle_ok ==True:
                unit = 'KM'
            if mach.rent_vehicle or mach.is_rent_mach:
                for owner in mach.vehicle_under:
                    for rent in owner.rent_vehicle_bata_ids:
                        if rent.vehicle_categ_id.id == mach.vehicle_categ_id.id:
                            if rent.mode_of_rate == 'per_day':
                                unit = 'Days'
                            if rent.mode_of_rate == 'per_month':
                                unit = 'Months'
                            if rent.mode_of_rate == 'per_hour':
                                unit = 'Hour'
            if unit == '':
                unit = "KM"
            upto = 0
            curr =0
            worksheet.write("K%s"%(row),unit,regular)
            worksheet.write("L%s" % (row), mach.per_day_rent, regular)
            for daily in upto_daily:
                for machin in daily.operator_daily_stmts:
                    if machin.machinery_id.id == mach.id:
                        upto += machin.quantity
            mach_total_upto += upto * mach.per_day_rent
            for daily in curr_daily:
                for machin in daily.operator_daily_stmts:
                    if machin.machinery_id.id == mach.id:
                        curr += machin.quantity
            mach_total_curr += curr * mach.per_day_rent
            worksheet.write("M%s" % (row), upto, regular)
            worksheet.write("N%s" % (row), upto * mach.per_day_rent, regular)
            worksheet.write("O%s" % (row), curr, regular)
            worksheet.write("P%s" % (row), curr * mach.per_day_rent, regular)
            worksheet.write("Q%s" % (row), upto + curr, regular)
            worksheet.write("R%s" % (row), mach.per_day_rent*(upto + curr), regular)
            row+=1
        row+=2
        worksheet.write("J%s"%(row),"Total C. (Equipment)",bold)
        worksheet.write("N%s" % (row), mach_total_upto, bold)
        worksheet.write("P%s" % (row), mach_total_curr, bold)
        worksheet.write("R%s" % (row), mach_total_upto + mach_total_curr, bold)

        row+=1
        worksheet.write("J%s"%(row),"E. Material Expenses",bold)
        row+=1
        worksheet.write("J%s"%(row),"Description",bold)
        worksheet.write("K%s"%(row),"Unit",bold)
        worksheet.write("L%s"%(row),"Rate",bold)
        worksheet.merge_range("M%s:M%s"%(row,row+1),"Upto Previous Day",bold)
        worksheet.merge_range("N%s:N%s"%(row,row+1),"Upto Previous Amount",bold)
        worksheet.merge_range("O%s:O%s"%(row,row+1),"Current Day QTY",bold)
        worksheet.merge_range("P%s:P%s"%(row,row+1),"Current Amount",bold)
        worksheet.merge_range("Q%s:Q%s"%(row,row+1),"Upto Date QTY",bold)
        worksheet.merge_range("R%s:R%s"%(row,row+1),"Upto Date Amount",bold)
        row+=2
        products = self.env['product.product'].search([])
        mat_total_upto = 0
        mat_total_curr = 0
        for prod in products:
            upto = 0
            curr =0
            qty =0
            rate = 0
            for daily in upto_daily:
                for pro in daily.received_ids:
                    if pro.product_id.id == prod.id:
                        upto += pro.product_qty

                        rate = pro.rate
                        mat_total_upto += upto * pro.rate
            for daily in curr_daily:
                for pro in daily.received_ids:
                    if pro.product_id.id == prod.id:
                        curr += pro.product_qty

                        rate = pro.rate
                        mat_total_curr += curr * pro.rate

            if upto!= 0 or curr != 0:
                worksheet.write("J%s"%(row),prod.name,regular)
                worksheet.write("K%s"%(row),prod.uom_id.name,regular)
                worksheet.write("L%s"%(row),rate,regular)
                worksheet.write("M%s"%(row),upto,regular)
                worksheet.write("N%s" % (row), upto * rate, regular)
                worksheet.write("O%s" % (row), curr, regular)
                worksheet.write("P%s" % (row), curr * rate, regular)
                worksheet.write("Q%s" % (row), upto + curr, regular)
                worksheet.write("R%s" % (row), (upto + curr)*rate, regular)
                row+=1
        row+=2
        worksheet.write("J%s"%(row),"E. Material Total",bold)
        worksheet.write("N%s" % (row), mat_total_upto, regular)
        worksheet.write("P%s" % (row), mat_total_curr, regular)
        worksheet.write("R%s" % (row), mat_total_upto +mat_total_curr , regular)
        row+=2
        row=8
        worksheet.write("S%s"%(row),"Sl No",bold)
        worksheet.write("T%s"%(row),"Boq Ref",bold)
        worksheet.write("U%s"%(row),"Boq Item",bold)
        worksheet.write("V%s"%(row),"Unit",bold)
        worksheet.write("W%s"%(row),"Rate",bold)
        worksheet.merge_range("X%s:Y%s"%(row,row),"Estimate",bold)
        worksheet.write("X%s"%(row+1),"Qty",bold)
        worksheet.write("Y%s"%(row+1),"Amount",bold)
        worksheet.write("Z%s"%(row),"Proposed",bold)
        worksheet.write("Z%s"%(row+1),"Qty",bold)
        worksheet.merge_range("AA%s:AC%s" % (row, row), "Billed Quantity", bold)
        worksheet.merge_range("AA%s:AB%s" % (row+1, row+1), "Qty", bold)
        worksheet.write("AC%s" % (row + 1), "Amount", bold)
        worksheet.merge_range("AD%s:AE%s" % (row, row), "Upto Previous", bold)
        worksheet.write("AD%s" % (row + 1), "Qty", bold)
        worksheet.write("AE%s" % (row + 1), "Amount", bold)
        worksheet.merge_range("AF%s:AG%s" % (row, row), "Current", bold)
        worksheet.write("AF%s" % (row + 1), "Qty", bold)
        worksheet.write("AG%s" % (row + 1), "Amount", bold)
        worksheet.merge_range("AH%s:AI%s" % (row, row), "Upto Date", bold)
        worksheet.write("AH%s" % (row + 1), "Qty", bold)
        worksheet.write("AI%s" % (row + 1), "Amount", bold)
        worksheet.write("AJ%s" % (row), "% of Completion", bold)
        row+=2
        count=1
        work_total_est= 0
        work_total_upto = 0
        work_total_curr = 0
        budget_estimation = self.env['project.task'].search([('project_id','=',invoices.project_id.id)])
        estimation = self.env['work.estimation'].search([('project_id','=',invoices.project_id.id)])
        for budget in budget_estimation:
            for lines in budget.task_line:
                worksheet.write("S%s" % (row), count, regular)
                worksheet.write("T%s" % (row), lines.category.name, regular)
                worksheet.write("U%s" % (row), lines.name.name, regular)
                worksheet.write("V%s" % (row), lines.unit.name, regular)
                worksheet.write("W%s" % (row), lines.rate, regular)
                worksheet.write("X%s" % (row), lines.qty, regular)
                worksheet.write("Y%s" % (row), lines.amt, regular)
                work_total_est += lines.amt
                for esti in estimation:
                    if esti.work_id.id == lines.name.id:

                        upto = 0
                        curr = 0
                        for detail in esti.estimation_line_ids:
                            if detail.date < invoices.from_date:
                                upto += detail.qty

                            if detail.date >= invoices.from_date and detail.date <= invoices.to_date:
                                curr += detail.qty
                        work_total_upto += upto *esti.rate
                        work_total_curr += curr * esti.rate
                        worksheet.write("AD%s" % (row), upto, regular)
                        worksheet.write("AE%s" % (row), upto *esti.rate , regular)
                        worksheet.write("AF%s" % (row), curr, regular)
                        worksheet.write("AG%s" % (row), curr * esti.rate, regular)
                        worksheet.write("AH%s" % (row), upto + curr, regular)
                        worksheet.write("AI%s" % (row), (upto + curr)*esti.rate, regular)
                        worksheet.write("AJ%s" % (row), (upto + curr) / esti.qty_estimate, regular)

                count += 1
                row+=1
        worksheet.write("Y%s" % (row), work_total_est, bold)
        worksheet.write("AE%s" % (row), work_total_upto, regular)
        worksheet.write("AG%s" % (row), work_total_curr, regular)
        worksheet.write("AI%s" % (row),work_total_upto + work_total_curr, regular)
        worksheet.write("AJ%s" % (row), work_total_upto + work_total_curr, regular)
        row+=1
        curr_row = row
        worksheet.merge_range("AA%s:AI%s" % (row, row), "SUMMARY - INCOME Vs. EXPENDITURE", bold)
        row +=1
        worksheet.write("AA%s"%(row),"SL No",bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "Description", bold)
        worksheet.merge_range("AF%s:AF%s" % (row,row+1), "Upto Previous", bold)
        worksheet.merge_range("AG%s:AG%s" % (row,row+1), "Today", bold)
        worksheet.merge_range("AH%s:AH%s" % (row,row+1), "Upto Date", bold)
        worksheet.merge_range("AI%s:AI%s" % (row,row+1), "% of Expenses per day", bold)
        worksheet.merge_range("AJ%s:AJ%s" % (row,row+1), "% of Expenses Up to date", bold)
        row+=2
        full_total = (man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto+man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr)
        full_total_upto = (man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto)
        man_power_total = man_total_upto +man_total_current

        per_man_per_day = full_total_upto != 0 and man_total_upto/full_total_upto or 0
        per_man_upto = full_total != 0 and man_power_total/full_total or 0
        worksheet.write("AA%s" % (row), "A.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "Manpower", bold)
        worksheet.write("AF%s" % (row), man_total_upto, bold)
        worksheet.write("AG%s" % (row), man_total_current, bold)
        worksheet.write("AH%s" % (row), man_power_total , bold)
        worksheet.write("AI%s" % (row),per_man_per_day, bold)
        worksheet.write("AJ%s" % (row),per_man_upto , bold)
        row+=1
        gen_full_total = gen_total_upto + gen_total_curr
        worksheet.write("AA%s" % (row), "B.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "General Expenses", bold)
        worksheet.write("AF%s" % (row), gen_total_upto, bold)
        worksheet.write("AG%s" % (row), gen_total_curr, bold)
        worksheet.write("AH%s" % (row), gen_full_total, bold)
        worksheet.write("AI%s" % (row), full_total_upto != 0.0 and gen_total_upto/full_total_upto or 0, bold)
        worksheet.write("AJ%s" % (row), full_total != 0.0 and gen_full_total/full_total or 0, bold)
        row+=1
        sub_full_total = sub_total_upto + sub_total_curr
        worksheet.write("AA%s" % (row), "C.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "SubContract", bold)
        worksheet.write("AF%s" % (row), sub_total_upto, bold)
        worksheet.write("AG%s" % (row), sub_total_curr, bold)
        worksheet.write("AH%s" % (row),sub_full_total , bold)
        worksheet.write("AI%s" % (row), full_total_upto !=0 and sub_total_upto/full_total_upto or 0, bold)
        worksheet.write("AJ%s" % (row), sub_full_total/full_total, bold)
        row+=1
        mach_full_total = mach_total_upto + mach_total_curr
        worksheet.write("AA%s" % (row), "D.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "Equipment ", bold)
        worksheet.write("AF%s" % (row), mach_total_upto, bold)
        worksheet.write("AG%s" % (row), mach_total_curr, bold)
        worksheet.write("AH%s" % (row), mach_full_total, bold)
        worksheet.write("AI%s" % (row), full_total_upto !=0 and mach_total_upto/full_total_upto or 0.0, bold)
        worksheet.write("AJ%s" % (row), mach_full_total/full_total, bold)
        row+=1
        mat_full_total = mat_total_upto + mat_total_curr
        worksheet.write("AA%s" % (row), "E.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), " Materials ", bold)
        worksheet.write("AF%s" % (row), mat_total_upto, bold)
        worksheet.write("AG%s" % (row), mat_total_curr, bold)
        worksheet.write("AH%s" % (row),mat_full_total , bold)
        worksheet.write("AI%s" % (row), full_total_upto !=0 and mat_total_upto/full_total_upto or 0.0, bold)
        worksheet.write("AJ%s" % (row), mat_full_total/full_total, bold)
        row+=1
        over_head_total = work_total_upto*.2 + work_total_curr*.2
        worksheet.write("AA%s" % (row), "F.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), " Over head charges 20% ", bold)
        worksheet.write("AF%s" % (row), work_total_upto*.2, bold)
        worksheet.write("AG%s" % (row), work_total_curr*.2, bold)
        worksheet.write("AH%s" % (row),over_head_total, bold)
        worksheet.write("AI%s" % (row),full_total_upto !=0 and work_total_upto*.2/full_total_upto or 0.0, bold)
        worksheet.write("AJ%s" % (row),over_head_total/full_total, bold)
        row+=1
        worksheet.write("AA%s" % (row), "G.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), " Total Expenses", bold)
        worksheet.write("AF%s" % (row),full_total_upto, bold)
        worksheet.write("AG%s" % (row), man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr, bold)
        worksheet.write("AH%s" % (row), full_total, bold)
        worksheet.write("AI%s" % (row), 0, bold)
        worksheet.write("AJ%s" % (row), 0, bold)
        row+=1
        worksheet.write("AA%s" % (row), "H.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "Total Income ", bold)
        worksheet.write("AF%s" % (row), work_total_upto, bold)
        worksheet.write("AG%s" % (row), work_total_curr, bold)
        worksheet.write("AH%s" % (row), work_total_upto + work_total_curr, bold)
        worksheet.write("AI%s" % (row), 0, bold)
        worksheet.write("AJ%s" % (row), 0, bold)
        row+=1
        worksheet.write("AA%s" % (row), "I.", bold)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "Contribution", bold)
        worksheet.write("AF%s" % (row),work_total_upto - (man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto), bold)
        worksheet.write("AG%s" % (row), work_total_curr - (man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr), bold)
        worksheet.write("AH%s" % (row), (work_total_upto + work_total_curr) - (man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto+man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr), bold)
        worksheet.write("AI%s" % (row), 0, bold)
        worksheet.write("AJ%s" % (row), 0, bold)
        row+=1
        worksheet.write("AA%s" % (row), "J.", bold)
        cont_total = man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto
        cont_curr = (man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr)
        cont_upto = (man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto+man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr)
        worksheet.merge_range("AB%s:AE%s" % (row, row), "% Contribution ", bold)
        worksheet.write("AF%s" % (row), cont_total != 0.0 and (work_total_upto - (man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto))/cont_total or 0.0, bold)
        worksheet.write("AG%s" % (row),cont_curr != 0.0 and  (work_total_curr - (man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr))/cont_curr or 0.0, bold)
        worksheet.write("AH%s" % (row),cont_upto and  ((work_total_upto + work_total_curr) - (man_total_upto + gen_total_upto+mach_total_upto + mat_total_upto +sub_total_upto+man_total_current + gen_total_curr + mach_total_curr + mat_total_curr + sub_total_curr))/cont_upto or 0.0, bold)
        worksheet.write("AI%s" % (row), 0, bold)
        worksheet.write("AJ%s" % (row), 0, bold)
        row+=1
        worksheet.merge_range("AA%s:AD%s" % (row, row), "Prepared By", bold)
        worksheet.merge_range("AE%s:AF%s" % (row, row), "Checked By", bold)
        worksheet.merge_range("AG%s:AH%s" % (row, row), "Reviewed By", bold)
        worksheet.merge_range("AI%s:AJ%s" % (row, row), "Approved By", bold)

        row = curr_row
        worksheet.merge_range("S%s:Z%s"%(row,row),"Today",bold)
        row+=1
        worksheet.merge_range("S%s:S%s"%(row,row+1),"SL No",bold)
        worksheet.merge_range("T%s:U%s"%(row,row+1),"Designation",bold)
        worksheet.merge_range("V%s:W%s"%(row,row+1),"Name of Staff",bold)
        worksheet.write("X%s"%(row),"Income",bold)
        worksheet.write("Y%s" % (row), "Expense", bold)
        worksheet.write("Z%s" % (row), "Contribution", bold)
        row+=3
        count=1
        worksheet.write("S%s"%(row),count,regular)
        worksheet.merge_range("T%s:U%s"%(row,row),invoices.project_id.user_id.name,regular)
        worksheet.merge_range("V%s:W%s" % (row, row), invoices.project_id.user_id.employee_id.designation_id.name, regular)
        row+=1
        count+=1
        for emp in self.env['hr.employee'].search([('loc_id','=',invoices.project_id.location_id.id)],order = 'id asc'):
            worksheet.write("S%s" % (row), count, regular)
            worksheet.merge_range("T%s:U%s" % (row, row), emp.name, regular)
            worksheet.merge_range("V%s:W%s" % (row, row), emp.designation_id.name,
                                  regular)
            count+=1
            row+=1

        worksheet = workbook.add_worksheet("Machineries")


BillReportXlsx('report.custom.daily_progress_report.xlsx', 'report.daily.progress.report')
