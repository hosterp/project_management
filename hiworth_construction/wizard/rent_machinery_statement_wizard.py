from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone



class RentMachineryReportWizard(models.TransientModel):
    _name = 'rent.machinary.report.wizard'

    @api.onchange('rent_vehicle_owner_id')
    def onchange_rent_vehicle_owner_id(self):
        for rec in self:
            vehicle = self.env['fleet.vehicle'].search([('vehicle_under', '=', rec.rent_vehicle_owner_id.id)])
        return {'domain': {'rent_vehicle_id': [('id', 'in', vehicle.ids)]}}

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    rent_vehicle_owner_id = fields.Many2one('res.partner', "Rent Vehicle/Equipment Owner",
                                            domain="[('is_rent_mach_owner','=',True)]")
    rent_vehicle_id = fields.Many2one('fleet.vehicle',
                                      domain="['|',('rent_vehicle','=',True),('is_rent_mach','=',True)]")

    project_id = fields.Many2one('project.project',"Project")









    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Rent Machinary Report.xlsx')



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
        row = 7
        col = 1
        new_row = row

        worksheet.set_column('A:A', 13)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('D:S', 25)

        worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:S2', invoices.project_id and invoices.project_id.name or 'All Projects', boldc)
        worksheet.merge_range('A3:S3', '%s Details From %s To %s' % (invoices.rent_vehicle_owner_id and invoices.rent_vehicle_owner_id.name or ' ',
        datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%d-%m-%Y")), boldc)
        worksheet.merge_range('A4:A5', 'SL NO', bold)
        worksheet.merge_range('B4:B5', 'DATE', bold)
        worksheet.merge_range('C4:C5', 'VEH.NO', bold)

        worksheet.write('D5', 'TS NO', bold)
        worksheet.write('E5', 'STR.KM', bold)

        worksheet.write('F5', 'CLO.KM', bold)
        worksheet.write('G5', 'TOT.KM', bold)
        worksheet.write('H5', 'TIME IN', bold)
        # worksheet.merge_range('A4:O5','',regular)
        worksheet.write('I5', 'TIME OUT', bold)
        worksheet.write('J5', 'SITE', bold)

        worksheet.write('K5', 'SUPERVISOR', bold)
        worksheet.write('L5', 'REMARK', bold)

        count = 1
        for rec in invoices:
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")

            domain = []
            diesel_domain = []
            domain.append(('rent_vehicle', '=', True))
            if rec.from_date:
                domain.append(('date','>=',date_from))
            if rec.to_date:
                domain.append(('date','<=',date_to))
            if rec.rent_vehicle_owner_id:
                domain.append(('rent_vehicle_partner_id', '=', rec.rent_vehicle_owner_id.id))
            if rec.rent_vehicle_id:
                domain.append(('rent_vehicle_id', '=', rec.rent_vehicle_id.id))
            if rec.project_id:
                domain.append(('project_id', '=', rec.project_id.id))


            driver_daily = self.env['driver.daily.statement'].search(domain,order='date asc')

            total_km = 0
            total_amt = 0
            mode_of_rate = ''
            mode_of_bata = ''
            rate = 0
            bata = 0
            h_f_day = 0
            parti = ''
            for daily in driver_daily:
                if daily.full_day:
                    h_f_day += 1
                if daily.half_day:
                    h_f_day += .5

                worksheet.write('A%s' % (new_row), count, regular)
                worksheet.write('B%s' % (new_row),datetime.strptime(daily.date, "%Y-%m-%d").strftime("%d-%m-%Y")
                                , regular)
                worksheet.write('C%s' % (new_row), daily.rent_vehicle_id.name, regular)
                worksheet.write('D%s' % (new_row), daily.trip_sheet_no, regular)

                worksheet.write('E%s' % (new_row), daily.start_km, regular)
                worksheet.write('F%s' % (new_row), daily.actual_close_km, regular)

                worksheet.write('G%s' % (new_row), round(daily.running_km,2), regular)
                parti = ''
                for rate_bata in rec.rent_vehicle_owner_id.rent_vehicle_bata_ids:
                    if rate_bata.vehicle_categ_id.id == daily.rent_vehicle_id.vehicle_categ_id.id:
                        mode_of_rate = rate_bata.mode_of_rate
                        mode_of_bata = rate_bata.mode_of_bata
                        rate = rate_bata.rate
                        bata = rate_bata.bata
                        if rate_bata.mode_of_rate == 'per_day':
                            parti = 'Day'
                        if rate_bata.mode_of_rate == 'per_month':
                            parti = 'Month'
                        if rate_bata.mode_of_rate == 'per_hour':
                            parti = 'Hrs'

                total_km+=round(daily.running_km,2)
                if daily.start_time:
                    from_zone = tz.gettz('UTC')
                    to_zone = tz.gettz('Asia/Kolkata')

                    utc = datetime.strptime(daily.start_time, '%Y-%m-%d %H:%M:%S')
                    utc = utc.replace(tzinfo=from_zone)
                    central = utc.astimezone(to_zone)
                    central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                '%Y-%m-%d %H:%M:%S').strftime(
                        "%H:%M %p")
                    worksheet.write('H%s' % (new_row), central, regular)
                if daily.end_time:
                    from_zone = tz.gettz('UTC')
                    to_zone = tz.gettz('Asia/Kolkata')

                    utc = datetime.strptime(daily.end_time, '%Y-%m-%d %H:%M:%S')
                    utc = utc.replace(tzinfo=from_zone)
                    central = utc.astimezone(to_zone)
                    central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                '%Y-%m-%d %H:%M:%S').strftime(
                        "%I:%M %p")
                    worksheet.write('I%s' % (new_row), central, regular)
                worksheet.write('J%s' % (new_row), daily.project_id.name, regular)
                worksheet.write('K%s' % (new_row), daily.user_id.name, regular)
                worksheet.write('L%s' % (new_row), daily.remark, regular)
                new_row += 1

                count += 1
            worksheet.merge_range('A%s:F%s' % (new_row, new_row), 'Total %s'%(parti), bold)
            if parti == 'Day':
                total_km = len(driver_daily.ids)
            worksheet.write("G%s"%(new_row),total_km,bold)
            new_row += 2
            worksheet.merge_range('A%s:A%s'%(new_row,new_row+1), 'SL NO', bold)
            worksheet.merge_range('B%s:B%s'%(new_row,new_row+1), 'DATE', bold)
            worksheet.merge_range('C%s:C%s'%(new_row,new_row+1), 'VEH.NO', bold)
            worksheet.write('D%s'%(new_row+1), 'DIESEL', bold)
            worksheet.write('E%s'%(new_row+1), 'RATE', bold)
            worksheet.write('F%s'%(new_row+1), 'AMOUNT', bold)
                # worksheet.write('L%s' % (new_row), daily.user_id.name, regular)
            diesel_domain = []
            new_row += 3
            diesel_domain.append(('rent_vehicle', '=', True))

            if rec.from_date:
                diesel_domain.append(('date', '>=', date_from))
            if rec.to_date:
                diesel_domain.append(('date', '<=', date_to))
            if rec.rent_vehicle_owner_id:
                diesel_domain.append(('rent_vehicle_partner_id', '=', rec.rent_vehicle_owner_id.id))
            if rec.rent_vehicle_id:
                diesel_domain.append(('rent_vehicle_id', '=', rec.rent_vehicle_id.id))
            if rec.project_id:
                diesel_domain.append(('project_id', '=', rec.project_id.id))
            diesel = self.env['diesel.pump.line'].search(diesel_domain, order='date asc')
            total_diesel = 0
            diesel_rate = 0
            count=1
            for dies in diesel:
                if dies.diesel_mode == 'tanker':
                    total_diesel = dies.total_diesel
                else:
                    total_diesel = dies.litre

                # else:
                #     total_diesel += dies.total_diesel
                per_litre = self.env['diesel.pump.line'].search(
                    [('diesel_mode', '=', 'pump'), ('date', '=', dies.date), ('fuel_product_id', '=', 'DIESEL FUEL')],
                    order='per_litre desc', limit=1)

                worksheet.write('A%s' % (new_row), count, regular)
                worksheet.write('B%s' % (new_row), datetime.strptime(dies.date, "%Y-%m-%d").strftime("%d-%m-%Y")
                                , regular)
                worksheet.write('C%s' % (new_row), dies.rent_vehicle_id.name, regular)

                worksheet.write("D%s" % (new_row), total_diesel, regular)
                worksheet.write("E%s" % (new_row), (per_litre.per_litre +1), regular)
                worksheet.write("F%s" % (new_row), total_diesel * (per_litre.per_litre +1), regular)
                total_amt += total_diesel * (per_litre.per_litre + 1)
                new_row += 1

                count += 1
            new_row +=1
            new_row +=1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "TOTAL DIESEL FILLED", bold)
            worksheet.write("F%s" % (new_row), total_amt, bold)
            new_row += 3

            count += 1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "TOTAL %s"%(parti), bold)
            worksheet.write("G%s"%(new_row),total_km,bold)
            new_row +=1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "RATE/%s"%(parti), bold)
            worksheet.write('G%s' % (new_row), rate, bold)
            new_row += 1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "SUB TOTAL", bold)
            worksheet.write('G%s' % (new_row), rate * total_km, bold)
            new_row += 1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "BATA  (%s x %s)"%(bata,h_f_day), bold)
            worksheet.write('G%s' % (new_row), bata * h_f_day, bold)
            new_row += 1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "TOTAL BATA", bold)
            worksheet.write('G%s' % (new_row), (bata * len(driver_daily.ids))+(rate * total_km), bold)
            new_row += 1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "LESS: DIESEL FILLED", bold)
            worksheet.write('G%s' % (new_row), total_amt, bold)
            new_row += 1
            worksheet.merge_range("A%s:E%s" % (new_row, new_row), "BALANCE PAYABLE", bold)
            worksheet.write('G%s' % (new_row),(bata * len(driver_daily.ids))+(rate * total_km) - total_amt, bold)
        new_row+=2
        worksheet.merge_range("A%s:C%s"%(new_row,new_row),"Generated By",bold)

        worksheet.merge_range("D%s:G%s"%(new_row,new_row),self.env.user.name,bold)
        new_row += 1
        date = workbook.add_format({'num_format': 'YYYY-MM-DD HH:DD:SS'})
        worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Generated ON", bold)

        worksheet.merge_range("D%s:F%s" % (new_row,new_row), datetime.now().strftime("%d-%m-%Y"), date)
        new_row += 1
                # worksheet.write('R%s' % (new_row), driver.remark, regular)



BillReportXlsx('report.Rent Machinary Report.xlsx', 'rent.machinary.report.wizard')




