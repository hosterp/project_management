from openerp import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class VehicleUtilizationReport(models.TransientModel):
    _name = 'vehicle.utilization.report'

    from_date = fields.Date('Date from')
    to_date = fields.Date('Date To')
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
                              ('December', 'December')], 'Month', required=True)
    current_year = datetime.now().year
    year = fields.Char(string='Year', default=current_year)
    project_id = fields.Many2one('project.project', "Project")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    # vehicle_type = fields.Char('Vehicle type')

    # @api.multi
    # def get_project_(self):

    @api.multi
    def get_details(self):
        for rec in self:
            driver_daily = self.env['driver.daily.statement'].search(
                [('date', '>', rec.from_date), ('date', '<', rec.to_date)])
            if driver_daily != []:
                return driver_daily
            else:
                return False

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 ' + self.month + ' ' + str(datetime.now().year)
            date_month = self.month + ' ' + str(datetime.now().year)
            print
            'dddddddddddddddaaaaa', date
            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)
            self.to_date = end_date

    @api.multi
    def get_month_year(self):
        date_month = self.month + ' ' + str(datetime.now().year)
        month_year = {'month': self.month + ' ' + str(datetime.now().year)}

    @api.multi
    def print_monthly_utilization_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,

        }

        return {
            'name': 'Diesel Tanker Report',
            'type': 'ir.actions.report.xml',
            'report_name': "hiworth_tms.monthly_utilization_report_template_view",
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='custom.vehicle_utilization_report.xlsx')


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

        worksheet.set_column('A:A', 13)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('D:S', 13)

        worksheet.merge_range('A1:J1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:J2', 'Monthly Utilization Report - ' + invoices.month, boldc)
        worksheet.write('A4', 'Sl.NO', regular)
        worksheet.write('B4', 'Date', regular)
        worksheet.write('C4', 'TYPE OF EQUIPMENT/VEHICLE', regular)
        worksheet.write('D4', 'FLEET NO.', regular)
        worksheet.write('E4', 'REG NO.', regular)
        worksheet.write('F4', 'START', regular)
        worksheet.write('G4', 'CLOSE', regular)
        worksheet.write('H4', 'TOTAL', regular)
        worksheet.write('I4', 'HSD', regular)
        worksheet.write('J4', 'Consumption', regular)

        row = 6
        new_row = row
        count = 0

        for rec in invoices:
            if not rec.vehicle_id:
                vehicle_list = self.env['fleet.vehicle'].search([])
            else:
                vehicle_list = rec.vehicle_id
            for vehicle in vehicle_list:
                driver_daily = self.env['driver.daily.statement'].search([('date', '>', rec.from_date),
                                                                          ('date', '<', rec.to_date),
                                                                          ('vehicle_no', '=', vehicle.id)])
                for driver in driver_daily:
                    worksheet.write('A%s' % (new_row), count, regular)
                    worksheet.write('B%s' % (new_row), driver.date, regular)
                    worksheet.write('C%s' % (new_row), vehicle.vehicle_categ_id.name, regular)
                    worksheet.write('D%s' % (new_row), vehicle.model_id.name, regular)
                    worksheet.write('E%s' % (new_row), vehicle.license_plate, regular)
                    worksheet.write('F%s' % (new_row), driver.start_km, regular)
                    worksheet.write('G%s' % (new_row), driver.actual_close_km, regular)
                    worksheet.write('H%s' % (new_row), driver.running_km, regular)
                    diesel_entry = self.env['diesel.pump.line'].search(
                        [('vehicle_id', '=', vehicle.id), ('date', '=', driver.date)])
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
                    worksheet.write('I%s' % (new_row), fuel, regular)
                    worksheet.write('J%s' % (new_row), mileage, regular)




                    count += 1
                    new_row += 1




BillReportXlsx('report.custom.vehicle_utilization_report.xlsx', 'vehicle.utilization.report')
