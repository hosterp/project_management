from openerp import fields, models, api
from datetime import datetime,timedelta
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta

class BillReportXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
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

        worksheet.set_column('A:A', 25)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('F:IV', 13)

        worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:S2', 'All Project', boldc)
        worksheet.merge_range('A3:S3', 'SUMMARY OF Issue of Diesel  FOR THE MONTH OF ' + invoices.month, boldc)
        worksheet.merge_range('A4:A5', 'Sl.NO', regular)
        worksheet.merge_range('B4:B5', 'Vehicle Type', regular)
        worksheet.merge_range('C4:C5', 'Vehicle No', regular)
        worksheet.merge_range('D4:D5','Fuel Type',regular)
        worksheet.merge_range('E4:E5', 'Unit of Measure', regular)
        worksheet.merge_range('F4:F5', 'Receipt Qty', regular)
        date_from = datetime.strptime(invoices.from_date, '%Y-%m-%d')
        to_date = datetime.strptime(invoices.to_date, '%Y-%m-%d')
        date_diff = to_date - date_from
        row_val = 71
        row_count = 1
        new_row_val = 65
        new_row_val_j = 65
        spl_count = 21
        for rangeg in range(date_diff.days + 1):

            if row_count < 21:

                worksheet.write('%s4:%s4' % (chr(row_val), chr(row_val)), date_from.strftime("%d-%m-%Y"),
                                      regular)

                worksheet.write('%s5:%s5' % (chr(row_val), chr(row_val)), "Issued Qty", regular)
                from_date = date_from + timedelta(days=1)
                date_from = from_date
                row_val += 1
                row_count += 1
            else:
                if spl_count + 26 == row_count:
                    new_row_val += 1
                    spl_count = row_count
                    new_row_val_j = 65
                worksheet.write(
                    '%s%s4' % (chr(new_row_val), chr(new_row_val_j)),
                    date_from.strftime("%d-%m-%Y"), regular)

                worksheet.write(
                    '%s%s5' % (chr(new_row_val), chr(new_row_val_j)),
                    "Issued Qty", regular)
                from_date = date_from + timedelta(days=1)
                date_from = from_date
                new_row_val_j+=1
                row_count += 1


        worksheet.write(
            '%s%s4' % (chr(new_row_val), chr(new_row_val_j)), 'Total',
            regular)

        worksheet.write('%s%s5' % (chr(new_row_val), chr(new_row_val_j)),
                        "Issued Qty", regular)
        new_row_val_j+=1
        worksheet.merge_range('%s%s4:%s%s5' % (chr(new_row_val), chr(new_row_val_j),chr(new_row_val), chr(new_row_val_j)),
                        "Start Reading", regular)
        new_row_val_j+=1
        worksheet.merge_range(
            '%s%s4:%s%s5' % (chr(new_row_val), chr(new_row_val_j), chr(new_row_val), chr(new_row_val_j)),
            "End Reading", regular)
        new_row_val_j += 1
        worksheet.merge_range(
            '%s%s4:%s%s5' % (chr(new_row_val), chr(new_row_val_j), chr(new_row_val), chr(new_row_val_j)),
            "Mileage", regular)
        count = 1
        full_receipt=0
        full_issue = 0
        for rec in invoices:

            vehicle_list = self.env['fleet.vehicle'].search([])
            for vehicle in vehicle_list:
                total_consumption = 0
                date_from = datetime.strptime(invoices.from_date, '%Y-%m-%d')
                to_date = datetime.strptime(invoices.to_date, '%Y-%m-%d')

                if vehicle.vehicle_ok == True or vehicle.machinery == True or vehicle.other == True:
                    monthly_start_reading = diesel_entry = self.env['diesel.pump.line'].search(
                        [('vehicle_id', '=', vehicle.id), ('date', '>=', rec.from_date),('date','<=',rec.to_date),('state','=','confirm')],order='date asc, id asc',limit=1).start_km
                    monthly_close_reading = diesel_entry = self.env['diesel.pump.line'].search(
                        [('vehicle_id', '=', vehicle.id), ('date', '>=', rec.from_date), ('date', '<=', rec.to_date),('state','=','confirm')],
                        order='date desc ,id desc', limit=1).close_km

                    diesel_entry = self.env['diesel.pump.line'].search(
                        [('vehicle_id', '=', vehicle.id), ('date', '>=', rec.from_date), ('date', '<=', rec.to_date),])
                else:
                    monthly_start_reading = diesel_entry = self.env['diesel.pump.line'].search(
                        [('rent_vehicle_id', '=', vehicle.id), ('date', '>=', rec.from_date), ('date', '<=', rec.to_date),
                         ('state', '=', 'confirm')], order='date asc, id asc', limit=1).start_km
                    monthly_close_reading = diesel_entry = self.env['diesel.pump.line'].search(
                        [('rent_vehicle_id', '=', vehicle.id), ('date', '>=', rec.from_date), ('date', '<=', rec.to_date),
                         ('state', '=', 'confirm')],
                        order='date desc ,id desc', limit=1).close_km

                    diesel_entry = self.env['diesel.pump.line'].search(
                        [('rent_vehicle_id', '=', vehicle.id), ('date', '>=', rec.from_date), ('date', '<=', rec.to_date)])

                date_diff = to_date - date_from
                row_val = 71
                row_count = 1
                new_row_val = 65
                new_row_val_j = 65
                spl_count = 21
                if len(diesel_entry) != 0:
                    diesel_dom = []
                    worksheet.write('A%s' % (new_row), count, regular)
                    worksheet.write('B%s' % (new_row), vehicle.vehicle_categ_id.name, regular)
                    worksheet.write('C%s' % (new_row), vehicle.license_plate, regular)
                    worksheet.write('E%s' % (new_row), "Litre", regular)
                    total = 0
                    total_receipt=0
                    diesel_dom.append(('date','>=', rec.from_date))
                    diesel_dom.append(('date', '<=', rec.to_date))
                    if rec.project_id:
                        diesel_dom.append(('project_id', '=', rec.project_id.id))
                    if rec.product_id:
                        diesel_dom.append(('fuel_product_id', '=', rec.product_id.id))
                    if vehicle.vehicle_ok == True or vehicle.machinery == True or vehicle.other == True:
                        diesel_dom.append(('vehicle_id', '=', vehicle.id))

                    else:
                        diesel_dom.append(('rent_vehicle_id', '=', vehicle.id))

                    diesel_entry = self.env['diesel.pump.line'].search(diesel_dom)
                    for diesel in diesel_entry:

                        total_receipt += diesel.litre


                    worksheet.write('F%s' % (new_row), round(total_receipt,2), regular)
                    full_receipt += total_receipt
                    total_issue = 0

                    for rangeg in range(date_diff.days + 1):
                        issue_diesel_dom = []
                        total=0

                        issue_qty = 0
                        if rec.product_id:
                            issue_diesel_dom.append(('fuel_product_id', '=', rec.product_id.id))
                        if rec.project_id:
                            issue_diesel_dom.append(('project_id', '=', rec.project_id.id))
                        if vehicle.vehicle_ok == True or vehicle.machinery == True or vehicle.other == True:
                            issue_diesel_dom.append(('vehicle_id', '=', vehicle.id))
                            issue_diesel_dom.append(('date', '=', date_from))

                        else:
                            issue_diesel_dom.append(('rent_vehicle_id', '=', vehicle.id))
                            issue_diesel_dom.append(('date', '=', date_from))
                        diesel_entry = self.env['diesel.pump.line'].search(issue_diesel_dom)
                        for diesel in diesel_entry:
                            worksheet.write('D%s' % (new_row), diesel.fuel_product_id.name, regular)




                            if diesel.diesel_mode == 'tanker':
                                issue_qty += diesel.total_diesel
                                total+=diesel.total_diesel
                            elif diesel.vehicle_id.tanker_bool != True:
                                total += diesel.litre


                        if row_count < 21:

                            worksheet.write('%s%s' % (chr(row_val), new_row), round(total,2), regular)
                            row_val += 1

                            row_count += 1
                        else:
                            worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row),  round(total,2),
                                                                     regular)
                            new_row_val_j +=1
                            row_count += 1
                        from_date = date_from + timedelta(days=1)
                        total_issue+=total
                        date_from = from_date

                    worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row),  round(total_issue,2),
                                     regular)
                    new_row_val_j += 1
                    worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row), monthly_start_reading,
                                    regular)
                    new_row_val_j += 1
                    worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row), monthly_close_reading,
                                    regular)
                    new_row_val_j += 1
                    mileage = (monthly_close_reading - monthly_start_reading)/total_issue
                    worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row), round(mileage,2),
                                    regular)


                    # new_row +=1

                    new_row += 1
                    count += 1

            worksheet.write('F%s' % (new_row), round(full_receipt,2), regular)


            new_row += 3

            vehicle_tank = self.env['fleet.vehicle'].search([('tanker_bool', '=', True)])
            for tanker in vehicle_tank:
                tanker_stock = sum(self.env['stock.history'].search(
                    [('date', '<', rec.from_date), ('location_id', '=', tanker.location_id.id)]).mapped('quantity'))

                worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Diesel Tanker Opening Stock %s" % (tanker.name),
                                      bold)
                worksheet.write('G%s' % (new_row), tanker_stock, bold)
                new_row += 1

            for tanker in vehicle_tank:
                diesel_issued = sum(self.env['diesel.pump.line'].search(
                    [('date', '>=', rec.from_date),('date', '<=', rec.to_date), ('diesel_tanker', '=', tanker.id)
                    ]).mapped('total_diesel'))

                worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Diesel Tanker Issued %s" % (tanker.name), bold)
                worksheet.write('G%s' % (new_row), diesel_issued, bold)
                new_row += 1

            for tanker in vehicle_tank:
                tanker_stock = sum(self.env['stock.history'].search(
                    [('date', '<', rec.from_date), ('location_id', '=', tanker.location_id.id)]).mapped('quantity'))

                diesel_issued = sum(self.env['diesel.pump.line'].search(
                    [('date', '>=', rec.from_date),('date', '<=', rec.to_date), ('diesel_tanker', '=', tanker.id)
                     ]).mapped('total_diesel'))

                diesel_entry = sum(self.env['diesel.pump.line'].search(
                    [('vehicle_id', '=', tanker.id), ('date', '>=', rec.from_date),('date', '<=', rec.to_date)]).mapped('litre'))

                used = 0.0
                used += tanker_stock + diesel_entry - diesel_issued

                worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Diesel Tanker Closing Stock %s" % (tanker.name),
                                      bold)
                worksheet.write('G%s' % (new_row), used, bold)
                new_row += 1

            vehicle_pump = self.env['res.partner'].search([('is_fuel_station', '=', True)])

            total_pump = 0

            worksheet.merge_range('C%s:D%s' % (new_row, new_row), "Diesel Receipt from Pump", bold)
            new_row += 1

            for pump in vehicle_pump:
                diesel_issued = self.env['diesel.pump.line'].search(
                    [('date', '>=', rec.from_date),('date', '<=', rec.to_date), ('diesel_pump', '=', pump.id),
                     ])
                pump_issue  = 0
                for iss in diesel_issued:

                    if iss.fuel_product_id.default_code == 'FUEL-1':
                        pump_issue += round(iss.litre,2)


                if pump_issue!=0:
                    worksheet.merge_range('C%s:D%s' % (new_row, new_row), "Pump :  %s  " % (pump.name), regular)
                    worksheet.write('E%s' % (new_row),round(pump_issue,2) , regular)
                    total_pump += pump_issue
                    new_row += 1

            worksheet.merge_range('C%s:D%s' % (new_row, new_row), "Petrol Receipt from Pump", bold)
            new_row += 1

            for pump in vehicle_pump:
                diesel_issued = self.env['diesel.pump.line'].search(
                    [('date', '>=', rec.from_date),('date', '<=', rec.to_date), ('diesel_pump', '=', pump.id),
                    ])
                pump_issue = 0
                for iss in diesel_issued:
                    if iss.fuel_product_id.default_code == 'FUEL-2':

                        pump_issue += round(iss.litre, 2)
                if pump_issue!=0:
                    worksheet.merge_range('C%s:D%s' % (new_row, new_row), "Pump : %s " % (pump.name), regular)
                    worksheet.write('E%s' % (new_row), round(pump_issue,2), regular)
                    total_pump += pump_issue
                    new_row += 1

            worksheet.write('E%s' % (new_row), total_pump, regular)



BillReportXlsx('report.custom.diesel.vehicle.monthly.xlsx', 'report.diesel.vehicle')

# total_receipt = 0
# total_issue = 0
# for rangeg in range(date_diff.days + 1):
#
#     receipt_qty = 0
#     issue_qty = 0
#     diesel_entry = self.env['diesel.pump.line'].search(
#         [('vehicle_id', '=', vehicle.id), ('date', '=', date_from)])
#     for diesel in diesel_entry:
#         if diesel.diesel_mode == 'pump':
#             worksheet.write('D%s' % (new_row), diesel.fuel_product_id.name, regular)
#             receipt_qty += diesel.litre
#
#         else:
#             issue_qty += diesel.total_diesel
#
#     # total_consumption += daily_statement.consumption_rate
#     # total_fuel += total
#
#     if row_count < 21:
#
#         worksheet.write('%s%s' % (chr(row_val), new_row), receipt_qty, regular)
#         row_val += 1
#         worksheet.write('%s%s' % (chr(row_val), new_row), issue_qty, regular)
#         row_count += 2
#     else:
#         if spl_count + 26 == row_count:
#             new_row_val += 1
#             spl_count = row_count
#             new_row_val_j = 65
#         worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row), receipt_qty, regular)
#         # new_row_val_j += 1
#         # worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row), receipt_qty,
#         #                 regular)
#         total_receipt += receipt_qty
#         new_row_val_j += 1
#         worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j + 1), new_row), issue_qty,
#                         regular)
#         total_issue += issue_qty
#         # new_row_val_j += 1
#
#         if new_row_val_j == 90:
#             new_row_val_j = 64
#             new_row_val += 1
#
#     # total_consumption += total
#     from_date = date_from + timedelta(days=1)
#     date_from = from_date
#     row_val += 1
# worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row), total_receipt,
#                 regular)
# new_row_val_j += 1
# worksheet.write('%s%s%s' % (chr(new_row_val), chr(new_row_val_j), new_row), total_issue,
#                 regular)
# date_from = datetime.strptime(invoices.from_date, '%Y-%m-%d')
#         to_date = datetime.strptime(invoices.to_date, '%Y-%m-%d')
#         date_diff = to_date - date_from
#         row_val = 71
#         row_count = 1
#         new_row_val = 65
#         new_row_val_j = 65
#         spl_count = 21
#         for rangeg in range(date_diff.days+1):
#
#             if row_count <21:
#
#                 worksheet.merge_range('%s4:%s4'%(chr(row_val),chr(row_val+1)),date_from.strftime("%d-%m-%Y") , regular)
#                 worksheet.write('%s5:%s5'%(chr(row_val),chr(row_val)),"Receipt Qty",regular)
#                 row_val +=1
#                 worksheet.write('%s5:%s5' % (chr(row_val), chr(row_val)), "Issued Qty", regular)
#                 from_date = date_from + timedelta(days=1)
#                 date_from = from_date
#                 row_val +=1
#                 row_count +=2
#             else:
#                 if spl_count + 26==row_count:
#                     new_row_val +=1
#                     spl_count = row_count
#                     new_row_val_j = 65
#                 worksheet.merge_range('%s%s4:%s%s4' % (chr(new_row_val), chr(new_row_val_j),chr(new_row_val),chr(new_row_val_j+1)), date_from.strftime("%d-%m-%Y"), regular)
#                 worksheet.write('%s%s5:%s%s5' % (chr(new_row_val), chr(new_row_val_j),chr(new_row_val),chr(new_row_val_j)), "Receipt Qty", regular)
#                 new_row_val_j += 1
#                 worksheet.write('%s%s5:%s%s5' % (chr(new_row_val), chr(new_row_val_j),chr(new_row_val),chr(new_row_val_j)), "Issued Qty", regular)
#                 from_date = date_from + timedelta(days=1)
#                 date_from = from_date
#                 row_count += 2
#
#                 new_row_val_j+=1
#
#         worksheet.merge_range('%s%s4:%s%s4'%(chr(new_row_val),chr(new_row_val_j),chr(new_row_val),chr(new_row_val_j+1)), 'Total', regular)
#         worksheet.write('%s%s5:%s%s5' % (chr(new_row_val), chr(new_row_val_j), chr(new_row_val), chr(new_row_val_j)),
#                         "Receipt Qty", regular)
#         worksheet.write('%s%s5:%s%s5' % (chr(new_row_val), chr(new_row_val_j), chr(new_row_val), chr(new_row_val_j)),
#                         "Issued Qty", regular)