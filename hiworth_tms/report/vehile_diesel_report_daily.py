from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta


class BillReportXlsxDaily(ReportXlsx):


    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))
        # print 'ddddddddddddddddddddddddd',self
        # print 'iiiiiiiiiiiiiiiiiiiiiiiiii',invoices

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'font': 'height 10'})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True,'align': 'center','size': 8})
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
        worksheet.set_column('C:S', 13)

        worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:S2',  'All Project', boldc)
        worksheet.merge_range('A3:S3', 'Daily Diesel consumtion rate status as of ' + datetime.strptime(invoices.date_today,"%Y-%m-%d").strftime("%d-%m-%Y"), boldc)
        worksheet.merge_range('A4:A5', 'Sl.NO', regular)
        worksheet.merge_range('B4:B5', 'Type of Vehicle', regular)
        worksheet.merge_range('C4:C5', 'Vehicle No', regular)
        worksheet.merge_range('D4:D5', 'Fuel Type', regular)
        worksheet.merge_range('E4:E5', 'Unit of Measure', regular)
        worksheet.merge_range('F4:F5', 'Fuel Tanker', regular)
        worksheet.merge_range('G4:G5', 'Today Receipt', regular)
        worksheet.merge_range('H4:H5', datetime.strptime(invoices.date_today,"%Y-%m-%d").strftime("%d-%m-%Y"), regular)
        worksheet.merge_range('I4:I5', 'Pre Reading', regular)
        worksheet.merge_range('J4:J5', 'Current Reading', regular)
        worksheet.merge_range('K4:K5', 'Running KM', regular)
        worksheet.write('L5',"Mileage (KM)",regular)
        # worksheet.write('E5', "Closing KM", regular)
        # worksheet.write('F5', "Running KM", regular)
        # worksheet.write('G5', "Fuel Issue", regular)
        # worksheet.write('H5', "Consumption", regular)
        count = 1
        for rec in invoices:
            total_consumption = 0
            total_fuel = 0
            total_receipt = 0
            vehicle_list = self.env['fleet.vehicle'].search([])

            for vehicle in vehicle_list:
                diesel_dom = []
                diesel_dom.append(('date', '=', invoices.date_today))
                if rec.project_id:
                    diesel_dom.append(('project_id', '=', rec.project_id.id))

                if rec.product_id:
                    diesel_dom.append(('fuel_product_id', '=', rec.product_id.id))
                if vehicle.vehicle_ok == True or vehicle.machinery == True or vehicle.other == True:
                    diesel_dom.append(('vehicle_id', '=', vehicle.id))
                else:
                    diesel_dom.append(('rent_vehicle_id', '=', vehicle.id))

                diesel_entry = self.env['diesel.pump.line'].search(diesel_dom)
                if len(diesel_entry)!=0:
                    worksheet.write('A%s' % (new_row), count, regular)
                    worksheet.write('B%s' % (new_row), vehicle.vehicle_categ_id.name, regular)
                    worksheet.write('C%s' % (new_row), vehicle.license_plate, regular)

                    worksheet.write('E%s' % (new_row), "Litre", regular)
                    receipt_qty =0
                    for diesel in diesel_entry:
                        if diesel.diesel_mode == 'pump':
                            receipt_qty += diesel.litre
                            total_receipt += diesel.litre
                    total = 0
                    milege = 0
                    for diesel in diesel_entry:
                        worksheet.write('D%s' % (new_row),diesel.fuel_product_id.name, regular)
                        worksheet.write('F%s' % (new_row), diesel.diesel_tanker.name, regular)
                        total+=diesel.total_diesel
                        milege+=diesel.mileage
                    worksheet.write('G%s' % (new_row), receipt_qty, regular)
                    if vehicle.tanker_bool == False and total == 0 and total_receipt != 0:

                        worksheet.write('H%s' % (new_row), receipt_qty, regular)
                    else:

                        worksheet.write('H%s' % (new_row), total, regular)
                    date_today = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime(
                        "%Y-%m-%d 00:00:00")




                    if not rec.project_id:

                        diesel_entry_date_desc = self.env['diesel.pump.line'].search(
                            [('vehicle_id', '=', vehicle.id), ('date', '=', invoices.date_today)],order='id desc',limit=1)

                        diesel_entry_date_asc = self.env['diesel.pump.line'].search(
                            [('vehicle_id', '=', vehicle.id), ('date', '=', invoices.date_today)], order='id asc',
                            limit=1)
                    else:
                        diesel_entry_date_desc = self.env['diesel.pump.line'].search(
                            [('vehicle_id', '=', vehicle.id), ('date', '=', invoices.date_today),
                             ('project_id', '=', rec.project_id.id)],order='id desc',limit=1)

                        diesel_entry_date_asc = self.env['diesel.pump.line'].search(
                            [('vehicle_id', '=', vehicle.id), ('date', '=', invoices.date_today),
                             ('project_id', '=', rec.project_id.id)],order='id asc',limit=1)


                    total_fuel += total


                    worksheet.write('I%s' % (new_row), diesel_entry_date_desc.start_km, regular)
                    worksheet.write('J%s' % (new_row), diesel_entry_date_asc.close_km, regular)
                    worksheet.write('K%s' % (new_row), diesel_entry_date_asc.close_km - diesel_entry_date_desc.start_km, regular)
                    worksheet.write('L%s' % (new_row), milege, regular)
                    # worksheet.write('H%s' % (new_row), daily_statement.consumption_rate, regular)


                    new_row += 1
                    count +=1
            # worksheet.write('H%s' % (new_row), total_consumption, regular)
            worksheet.write('G%s' % (new_row), total_receipt, regular)
            worksheet.write('H%s' % (new_row), total_fuel, regular)
            new_row += 3
            vehicle_tank = self.env['fleet.vehicle'].search([('tanker_bool', '=', True)])
            for tanker in vehicle_tank:
                tanker_stock = sum(self.env['stock.history'].search(
                    [('date', '<', rec.date_today),('location_id','=',tanker.location_id.id)]).mapped('quantity'))




                worksheet.merge_range('A%s:F%s' % (new_row,new_row), "Diesel Tanker Opening Stock %s"%(tanker.name), bold)
                worksheet.write('G%s' % (new_row), tanker_stock, bold)
                new_row += 1

            for tanker in vehicle_tank:


                diesel_issued = sum(self.env['diesel.pump.line'].search(
                    [('date', '=', rec.date_today), ('diesel_tanker', '=', tanker.id),('fuel_product_id','=','DIESEL FUEL')]).mapped('total_diesel'))


                worksheet.merge_range('A%s:F%s' % (new_row,new_row), "Diesel Tanker Issued %s"%(tanker.name), bold)
                worksheet.write('G%s' % (new_row), diesel_issued, bold)
                new_row += 1

            for tanker in vehicle_tank:
                tanker_stock = sum(self.env['stock.history'].search(
                    [('date', '<', rec.date_today), ('location_id', '=', tanker.location_id.id)]).mapped('quantity'))

                diesel_issued = sum(self.env['diesel.pump.line'].search(
                    [('date', '=', rec.date_today), ('diesel_tanker', '=', tanker.id),
                     ('fuel_product_id', '=', 'DIESEL FUEL')]).mapped('total_diesel'))

                diesel_entry = sum(self.env['diesel.pump.line'].search(
                    [('vehicle_id', '=', tanker.id), ('date', '=', rec.date_today)]).mapped('litre'))

                used = 0.0
                used += tanker_stock + diesel_entry - diesel_issued


                worksheet.merge_range('A%s:F%s' % (new_row,new_row), "Diesel Tanker Closing Stock %s"%(tanker.name), bold)
                worksheet.write('G%s' % (new_row),used , bold)
                new_row+=1

            vehicle_pump = self.env['res.partner'].search([('is_fuel_station','=',True)])

            total_pump = 0

            worksheet.merge_range('C%s:D%s' % (new_row, new_row), "Diesel Receipt from Pump", bold)
            new_row += 1

            for pump in vehicle_pump:
                diesel_issued = sum(self.env['diesel.pump.line'].search(
                    [('date', '=', rec.date_today), ('diesel_pump', '=', pump.id),('fuel_product_id','=',4873)]).mapped('litre'))


                if diesel_issued:
                    worksheet.merge_range('C%s:D%s' % (new_row,new_row), "Pump :  %s  " % (pump.name), regular)
                    worksheet.write('E%s' % (new_row), diesel_issued, regular)
                    total_pump+= diesel_issued
                    new_row += 1

            worksheet.merge_range('C%s:D%s' % (new_row, new_row), "Petrol Receipt from Pump", bold)
            new_row += 1

            for pump in vehicle_pump:
                diesel_issued = sum(self.env['diesel.pump.line'].search(
                    [('date', '=', rec.date_today), ('diesel_pump', '=', pump.id),('fuel_product_id','=',4874)]).mapped('litre'))


                if diesel_issued:
                    worksheet.merge_range('C%s:D%s' % (new_row,new_row), "Pump : %s " % (pump.name), regular)
                    worksheet.write('E%s' % (new_row), diesel_issued, regular)
                    total_pump += diesel_issued
                    new_row += 1

            worksheet.write('E%s' % (new_row), total_pump, regular)
            
            
BillReportXlsxDaily('report.custom.diesel.vehicle.report.daily.xlsx', 'report.diesel.vehicle.daily')