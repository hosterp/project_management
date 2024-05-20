from openerp import models, fields, api
from datetime import datetime
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx

class DieselTankerReport(models.TransientModel):


    _name = 'diesel.tanker.report'


    from_date = fields.Date('From Date')
    to_date = fields.Date("To Date")
    diesel_tanker_id = fields.Many2one('fleet.vehicle','Diesel Tanker')
    machine_opening_reading = fields.Float('Machine Opening Reading')
    machine_closing_reading = fields.Float('Machine Closing Reading')
    diesel_opening_stock = fields.Float('Diesel Stock')
    total_diesel_filled = fields.Float("Total Diesel Filled")
    diesel_pump = fields.Char("Diesel pump")
    diesel_filled_date = fields.Date("Date")


    @api.multi
    def get_diesel_tanker(self):

        model=self.env['diesel.pump.line'].search([('diesel_tanker','=',self.diesel_tanker_id.id),('date','>=',self.from_date),('date','<=',self.to_date)],order='id asc')

        return model

    @api.multi
    def view_diesel_stock_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,

        }

        self.machine_opening_reading = self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '=', self.from_date)], order='id asc',
            limit=1).opening_reading

        self.machine_closing_reading = self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '=', self.to_date)], order='id desc',
            limit=1).closing_reading
        diesel_filled = sum(self.env['diesel.pump.line'].search(
            [('vehicle_id', '=', self.diesel_tanker_id.id), ('date', '<', self.from_date)]).mapped('litre'))
        diesel_used = sum(self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '<', self.from_date)]).mapped('litre'))
        self.diesel_opening_stock = diesel_filled - diesel_used
        model = self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '>=', self.from_date) ,('date', '<=', self.to_date)])
        total_diesel_filled = self.diesel_opening_stock - sum(model.mapped('total_diesel'))
        diesel = 0
        for die in self.env['diesel.pump.line'].search(
            [('vehicle_id', '=', self.diesel_tanker_id.id), ('date', '<=', self.to_date), ('date', '>=', self.from_date)]):
            diesel =die.litre
        self.total_diesel_filled =  diesel
        self.diesel_pump =''
        for pump in self.env['diesel.pump.line'].search(
            [('vehicle_id', '=', self.diesel_tanker_id.id), ('date', '>=', self.from_date),('date', '<=', self.to_date)]):
            if pump.diesel_pump:
                pum_name = pump.diesel_pump.name + ','
            else:
                pum_name = ''
            self.diesel_pump = self.diesel_pump + pum_name
        pump_list = self.diesel_pump.split(',')
        pump_list = list(set(pump_list))
        self.diesel_pump = ','.join(pump_list)
        self.diesel_filled_date = self.from_date

        return {
            'name': 'Diesel Tanker Report',
            'type': 'ir.actions.report.xml',
            'report_name': "hiworth_tms.report_diesel_tanker_template_view",
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def print_diesel_stock_report(self):
        datas = {
             'ids': self._ids,
              'model': self._name,
              'form': self.read(),
              'context': self._context,

                }

        self.machine_opening_reading = self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '=', self.from_date)], order='id asc',
            limit=1).opening_reading

        self.machine_closing_reading = self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '=', self.to_date)], order='id desc',
            limit=1).closing_reading
        diesel_filled = sum(self.env['diesel.pump.line'].search(
            [('vehicle_id', '=', self.diesel_tanker_id.id), ('date', '<', self.from_date)]).mapped('litre'))
        diesel_used = sum(self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '<', self.from_date)]).mapped('litre'))
        self.diesel_opening_stock = diesel_filled - diesel_used
        model = self.env['diesel.pump.line'].search(
            [('diesel_tanker', '=', self.diesel_tanker_id.id), ('date', '>=', self.from_date),
             ('date', '<=', self.to_date)])
        total_diesel_filled = self.diesel_opening_stock - sum(model.mapped('total_diesel'))
        diesel = 0
        for die in self.env['diesel.pump.line'].search(
                [('vehicle_id', '=', self.diesel_tanker_id.id), ('date', '<=', self.to_date),
                 ('date', '>=', self.from_date)]):
            diesel = die.litre
        self.total_diesel_filled = diesel
        self.diesel_pump = ''
        for pump in self.env['diesel.pump.line'].search(
                [('vehicle_id', '=', self.diesel_tanker_id.id), ('date', '>=', self.from_date),
                 ('date', '<=', self.to_date)]):
            if pump.diesel_pump:
                pum_name = pump.diesel_pump.name + ','
            else:
                pum_name = ''
            self.diesel_pump = self.diesel_pump + pum_name
        pump_list = self.diesel_pump.split(',')
        pump_list = list(set(pump_list))
        self.diesel_pump = ','.join(pump_list)

        self.diesel_filled_date = self.from_date
        return {
            'name': 'Diesel Tanker Report',
            'type': 'ir.actions.report.xml',
            'report_name': "hiworth_tms.report_diesel_tanker_template_view",
            'datas': datas,
            'report_type': 'qweb-pdf'
            }


class DieselPumpReport(models.TransientModel):
    _name = 'diesel.pump.report'

    today_date = fields.Date('Date From')
    to_date = fields.Date("Date To")
    diesel_pump_id = fields.Many2one('res.partner', 'Diesel Pump',domain=[('is_fuel_station','=',True)])
    machine_opening_reading = fields.Float('Machine Opening Reading')
    machine_closing_reading = fields.Float('Machine Closing Reading')
    diesel_opening_stock = fields.Float('Diesel Stock')
    total_diesel_filled = fields.Float("Total Diesel Filled")
    diesel_pump = fields.Char("Diesel pump")
    diesel_filled_date = fields.Date("Date")

    @api.multi
    def get_diesel_pump(self):
        model = self.env['diesel.pump.line'].search(
            [('diesel_pump', '=', self.diesel_pump_id.id), ('date', '<=', self.today_date)])

        return model

    @api.multi
    def view_diesel_stock_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,

        }


        return {
            'name': 'Diesel Tanker Report',
            'type': 'ir.actions.report.xml',
            'report_name': "hiworth_tms.report_diesel_pump_template_view",
            'datas': datas,
            'report_type': 'qweb-html'
        }

    @api.multi
    def print_diesel_stock_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,

        }


        return {
            'name': 'Diesel Tanker Report',
            'type': 'ir.actions.report.xml',
            'report_name': "hiworth_tms.report_diesel_pump_template_view",
            'datas': datas,
            'report_type': 'qweb-pdf'
        }


    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Diesel Pump Report.xlsx')


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
        date_from = datetime.strptime(invoices.today_date, "%Y-%m-%d")
        date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")
        worksheet.merge_range("A1:K1",invoices.diesel_pump_id.name,boldc)
        worksheet.merge_range("L1:O1","%s To %s"%(date_from.strftime("%d-%m-%Y"),date_to.strftime("%d-%m-%Y")),boldc)
        new_row=3
        count = 1
        for rec in invoices:
            worksheet.write("A2","Sl No",bold)
            worksheet.write("B2","DATE",bold)
            worksheet.write("C2","VEH.NO",bold)
            worksheet.write("D2","VEH TYPE",bold)
            worksheet.write("E2","BILL NO",bold)
            worksheet.write("F2","INDENT NO",bold)
            worksheet.write("G2","GRR NO",bold)
            worksheet.write("H2","LTR",bold)
            worksheet.write("I2","Rate",bold)
            worksheet.write("J2","Amount",bold)
            worksheet.write("K2","PRE REading",bold)
            worksheet.write("L2","Current Reading",bold)
            worksheet.write("M2","Running KM",bold)
            worksheet.write("N2","Mileage",bold)
            worksheet.write("O2","Remarks",bold)

            model = self.env['diesel.pump.line'].search(
                [('diesel_pump', '=', rec.diesel_pump_id.id), ('date', '>=', rec.today_date),('date', '<=', rec.to_date)])

            count =1
            new_row = 4
            total = 0
            worksheet.merge_range("B3:E3", "Opening Balance", bold)
            for mo in model:
                mo_date = datetime.strptime(mo.date, "%Y-%m-%d").strftime("%d-%m-%Y")
                worksheet.write("A%s"%(new_row), count, regular)
                worksheet.write("B%s"%(new_row), mo_date, regular)
                worksheet.write("C%s"%(new_row), mo.vehicle_id and mo.vehicle_id.name or mo.rent_vehicle_id.name, regular)
                worksheet.write("D%s"%(new_row), mo.vehicle_id and mo.vehicle_id.vehicle_categ_id.name or mo.rent_vehicle_id.vehicle_categ_id.name, regular)
                worksheet.write("E%s"%(new_row), mo.pump_bill_no, regular)
                worksheet.write("F%s"%(new_row), mo.indent_no, regular)
                worksheet.write("G%s"%(new_row), mo.goods_receive_id.grr_no, regular)
                worksheet.write("H%s"%(new_row), mo.litre, regular)
                worksheet.write("I%s"%(new_row), mo.per_litre, regular)
                worksheet.write("J%s"%(new_row), mo.total_litre_amount, regular)
                total += mo.total_litre_amount
                worksheet.write("K%s"%(new_row),mo.start_km, regular)
                worksheet.write("L%s"%(new_row), mo.close_km, regular)
                worksheet.write("M%s"%(new_row), mo.running_km, regular)
                worksheet.write("N%s"%(new_row),mo.mileage, regular)
                worksheet.write("O%s"%(new_row),mo.remark, regular)
                new_row+=1
                count +=1
            worksheet.merge_range("B%s:F%s"%(new_row,new_row), "Current Total", bold)
            worksheet.write("J%s" % (new_row), total, bold)
            new_row+=1
            worksheet.merge_range("B%s:F%s" % (new_row, new_row), "Paid ON", bold)
            new_row+=1
            worksheet.merge_range("B%s:F%s" % (new_row, new_row), "Closing Balance", bold)






BillReportXlsx('report.Diesel Pump Report.xlsx', 'diesel.pump.report')

           