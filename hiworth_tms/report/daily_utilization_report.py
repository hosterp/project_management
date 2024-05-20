from openerp import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx

class DailyUtilizationReport(models.TransientModel):


    _name = 'daily.utilization.report'

    @api.onchange('own_vehicle')
    def onchange_own_vehicle(self):
        for rec in self:
            rec.rent_vehicle = False
            rec.rent_vehicle_owner_id = False
            rec.rent_vehicle_id = False

    @api.onchange('rent_vehicle')
    def onchange_rent_vehicle(self):
        for rec in self:
            rec.own_vehicle = False
            rec.vehicle_id = False

    @api.onchange('rent_vehicle_owner_id')
    def onchange_rent_vehicle_owner_id(self):
        for rec in self:
            vehicle = self.env['fleet.vehicle'].search([('vehicle_under','=',rec.rent_vehicle_owner_id.id)])
        return {'domain':{'rent_vehicle_id':[('id','in',vehicle.ids)]}}
    date = fields.Date('Date')

    project_id = fields.Many2one('project.project',"Project")
    own_vehicle = fields.Boolean("Own Vehicle")
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle",domain="['|',('machinery','=',True),('vehicle_ok','=',True)]")
    rent_vehicle = fields.Boolean("Rent Vehicle")
    rent_vehicle_owner_id = fields.Many2one('res.partner',"Rent Vehicle/Equipment Owner",domain="[('is_rent_mach_owner','=',True)]")
    rent_vehicle_id = fields.Many2one('fleet.vehicle',domain="['|',('rent_vehicle','=',True),('is_rent_mach','=',True)]")

    @api.multi
    def generate_xls_report(self):  
        
        return self.env["report"].get_action(self, report_name='custom.daily_utilization_report.xlsx')

class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))
        
        


        boldc = workbook.add_format({'bold': True,'align': 'center','bg_color':'#D3D3D3','font':'height 10'})
        heading_format = workbook.add_format({'bold': True,'align': 'center','size': 10})
        bold = workbook.add_format({'bold': True})
        rightb = workbook.add_format({'align': 'right','bold': True})
        right = workbook.add_format({'align': 'right'})
        regular=workbook.add_format({'align':'center','bold':False,'size':8})
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
        worksheet.set_column('B:B',25)
        worksheet.set_column('D:S', 13)
       
        

        worksheet.merge_range('A1:J1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:J2','Utilization Report - '+datetime.strptime(invoices.date,"%Y-%m-%d").strftime("%d-%m-%Y"),boldc)
        worksheet.write('A4','Sl.NO',regular)
        worksheet.write('B4','TYPE OF EQUIPMENT/VEHICLE',regular)

        worksheet.write('C4','REG NO.',regular)

        worksheet.write('D4','START',regular)
        worksheet.write('E4','CLOSE',regular)
        worksheet.write('F4','TOTAL',regular)
        worksheet.write('G4','HSD',regular)
        worksheet.write('H4','Consumption',regular)

        row=6
        new_row = row
        count=1

        for rec in invoices:
            veh_domain = []

            if invoices.own_vehicle:
                veh_domain.append(('|'))
                veh_domain.append(('machinery','=',True))
                veh_domain.append(('vehicle_ok','=',True))
                if invoices.vehicle_id:
                    veh_domain.append(('id', '=', invoices.vehicle_id.id))
            if invoices.rent_vehicle:
                veh_domain.append(('|'))
                veh_domain.append(('rent_vehicle', '=', True))
                veh_domain.append(('is_rent_mach', '=', True))
                if invoices.rent_vehicle_id:
                    veh_domain.append(('id', '=', invoices.rent_vehicle_id.id))

            vehicle_list = self.env['fleet.vehicle'].search(veh_domain)
            for vehicle in vehicle_list:
                driv_domain = []
                diesel_domain = []

                if invoices.own_vehicle:
                    diesel_domain.append(('own_vehicle', '=', True))
                    driv_domain.append(('own_vehicle', '=', True))
                    if invoices.vehicle_id:
                        diesel_domain.append(('vehicle_id', '=', rec.vehicle_id.id))
                        driv_domain.append(('vehicle_no', '=', rec.vehicle_id.id))
                    else:
                        driv_domain.append(('vehicle_no', '=', vehicle.id))
                        diesel_domain.append(('vehicle_id', '=', vehicle.id))
                if invoices.rent_vehicle:
                    diesel_domain.append(('rent_vehicle', '=', True))
                    driv_domain.append(('rent_vehicle', '=', True))
                    if invoices.rent_vehicle_id:
                        diesel_domain.append(('rent_vehicle_id', '=', rec.rent_vehicle_id.id))
                        driv_domain.append(('rent_vehicle_id', '=', rec.rent_vehicle_id.id))
                    else:
                        diesel_domain.append(('rent_vehicle_id', '=', vehicle.id))
                        driv_domain.append(('rent_vehicle_id', '=', vehicle.id))
                if not invoices.own_vehicle and not invoices.rent_vehicle:
                    if vehicle.rent_vehicle or vehicle.is_rent_mach:
                        driv_domain.append(('rent_vehicle_id', '=', vehicle.id))

                        diesel_domain.append(('rent_vehicle_id', '=', vehicle.id))
                    if vehicle.vehicle_ok or vehicle.machinery:
                        driv_domain.append(('vehicle_no', '=', vehicle.id))

                        diesel_domain.append(('vehicle_id', '=', vehicle.id))
                if rec.date:
                    diesel_domain.append(('date', '=', rec.date))
                    driv_domain.append(('date', '=', rec.date))
                if rec.project_id:
                    diesel_domain.append(('project_id', '=', rec.project_id.id))
                    driv_domain.append(('project_id', '=', rec.project_id.id))

                driver_daily = self.env['driver.daily.statement'].search(driv_domain)


                for driver in driver_daily:
                    worksheet.write('A%s' % (new_row), count, regular)
                    if driver.own_vehicle:
                        worksheet.write('B%s' % (new_row), driver.vehicle_no.vehicle_categ_id.name, regular)

                        worksheet.write('C%s' % (new_row), driver.vehicle_no.license_plate, regular)
                    if driver.rent_vehicle:
                        worksheet.write('B%s' % (new_row), driver.rent_vehicle_id.vehicle_categ_id.name, regular)

                        worksheet.write('C%s' % (new_row), driver.rent_vehicle_id.license_plate, regular)

                    worksheet.write('D%s' %(new_row),driver.start_km,regular)
                    worksheet.write('E%s' %(new_row),driver.actual_close_km,regular)
                    worksheet.write('F%s' %(new_row),driver.running_km,regular)

                    #worksheet.write('L%s' %(new_row),driver.fuel,regular)
                    diesel_entry = self.env['diesel.pump.line'].search(diesel_domain)
                    fuel = 0
                    mileage = 0
                    fuel_amt = 0
                    for diesel in diesel_entry:
                        if diesel.diesel_mode == 'pump':
                            fuel += diesel.litre
                            fuel_amt += diesel.total_litre_amount
                        if diesel.diesel_mode == 'tanker':
                            fuel += diesel.total_diesel
                        mileage += diesel.mileage
                    worksheet.write('G%s' %(new_row),fuel,regular)
                    worksheet.write('H%s' % (new_row), mileage, regular)
                count+=1
                new_row += 1
            new_row += 1
            worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Generated By", bold)

            worksheet.merge_range("D%s:G%s" % (new_row, new_row), self.env.user.name, bold)
            new_row += 1
            date = workbook.add_format({'num_format': 'YYYY-MM-DD HH:DD:SS'})
            worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Generated ON", bold)

            worksheet.merge_range("D%s:F%s" % (new_row, new_row), datetime.now().strftime("%d-%m-%Y"), date)
            new_row += 1








       


BillReportXlsx('report.custom.daily_utilization_report.xlsx','daily.utilization.report')
