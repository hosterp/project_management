from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone



class RentVehiclesReportWizard(models.TransientModel):
    _name = 'rent.vehicles.report.wizard'

    @api.onchange('rent_vehicle_owner_id')
    def onchange_rent_vehicle_owner_id(self):
        for rec in self:
            vehicle = self.env['fleet.vehicle'].search([('vehicle_under', '=', rec.rent_vehicle_owner_id.id)])
        return {'domain': {'rent_vehicle_id': [('id', 'in', vehicle.ids)]}}

    from_date = fields.Date('Date From', required=True)
    to_date = fields.Date('Date To', required=True)
    # location_id = fields.Many2one('stock.location', 'Location')
    rent_vehicle_owner_id = fields.Many2one('res.partner', "Rent Vehicle/Equipment Owner",
                                            domain="[('is_rent_mach_owner','=',True)]")
    rent_vehicle_id = fields.Many2one('fleet.vehicle',
                                      domain="['|',('rent_vehicle','=',True),('is_rent_mach','=',True)]")


    project_id = fields.Many2one('project.project')








    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Rent Vehicle Report.xlsx')



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
        worksheet.merge_range('A2:S2', invoices.project_id and invoices.project_id.name or 'All Project', boldc)
        worksheet.merge_range('A3:S3', '%s Details From %s To %s' % (invoices.rent_vehicle_owner_id and invoices.rent_vehicle_owner_id.name or ' ',
        datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%d-%m-%Y")), boldc)
        worksheet.merge_range('A4:A5', 'SL NO', bold)
        worksheet.merge_range('B4:B5', 'DATE', bold)
        worksheet.merge_range('C4:C5', 'VEH.NO', bold)

        worksheet.write('D5', 'FROM', bold)
        worksheet.write('E5', 'TO', bold)

        worksheet.write('F5', 'MR NO', bold)
        worksheet.write('G5', 'INVOICE NO', bold)
        worksheet.write('H5', 'NO OF LOAD', bold)
        # worksheet.merge_range('A4:O5','',regular)
        worksheet.write('I5', 'KM', bold)
        worksheet.write('J5', 'RATE', bold)

        worksheet.write('K5', 'AMOUNT', bold)

        count = 1
        for rec in invoices:
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")

            domain = []
            domain.append(('rent_vehicle', '=', True))
            if rec.from_date:
                domain.append(('Date','>=',date_from))
            if rec.to_date:
                domain.append(('Date','<=',date_to))
            if rec.rent_vehicle_owner_id:
                domain.append(('rent_vehicle_owner_id', '=', rec.rent_vehicle_owner_id.id))
            if rec.rent_vehicle_id:
                domain.append(('rent_vehicle_id', '=', rec.rent_vehicle_id.id))
            if rec.project_id:
                domain.append(('project_location_id', '=', rec.project_id.location_id.id))


            goods_receive = self.env['goods.recieve.report'].search(domain,order='Date asc')

            total_qty = 0
            total_amt = 0


            for goods in goods_receive:


                worksheet.write('A%s' % (new_row), count, regular)
                worksheet.write('B%s' % (new_row),datetime.strptime(goods.Date, "%Y-%m-%d").strftime("%d-%m-%Y")
                                , regular)
                worksheet.write('C%s' % (new_row), goods.rent_vehicle_id.name, regular)
                worksheet.write('D%s' % (new_row), goods.supplier_id.name, regular)

                worksheet.write('E%s' % (new_row), goods.project_id and goods.project_id.name or goods.project_location_id.name, regular)
                worksheet.write('F%s' % (new_row), goods.mr_slip, regular)

                worksheet.write('G%s' % (new_row), goods.invoice_no, regular)
                worksheet.write('H%s' % (new_row), len(goods.goods_recieve_report_line_ids.ids), regular)
                km = self.env['km.details.config'].search([('supplier_id','=',goods.supplier_id.id),('from_location_id','=',goods.project_location_id.id)],limit=1,order='with_effect desc')
                worksheet.write('I%s' % (new_row), km.km, regular)
                rent_km = 0.0
                for rent in goods.rent_vehicle_owner_id.rent_vehicle_km_ids.sorted(key=lambda r: r.with_effect):
                    rent_km = rent.rate_km


                worksheet.write('J%s' % (new_row), rent_km, regular)
                worksheet.write('K%s' % (new_row), rent_km * km.km * len(goods.goods_recieve_report_line_ids.ids), regular)

                total_amt += rent_km * km.km * len(goods.goods_recieve_report_line_ids.ids)
                new_row +=1


                count += 1
            worksheet.merge_range("A%s:J%s" % (new_row, new_row), "Current Total", bold)

            worksheet.write('K%s' % (new_row), total_amt, bold)
            new_row += 2

            worksheet.merge_range('A%s:A%s'%(new_row,new_row), 'SL NO', bold)
            worksheet.merge_range('B%s:B%s'%(new_row,new_row), 'DATE', bold)
            worksheet.merge_range('C%s:C%s'%(new_row,new_row), 'VEH.NO', bold)

            worksheet.write('D%s'%(new_row), 'DIESEL FILLED FROM', bold)
            worksheet.write('E%s'%(new_row), 'BILL NO', bold)

            worksheet.write('F%s'%(new_row), 'LITRE', bold)
            worksheet.write('G%s'%(new_row), 'RATE', bold)
            worksheet.write('J%s'%(new_row), 'AMOUNT', bold)
            new_row+=1
            domain = []
            domain.append(('rent_vehicle', '=', True))
            if rec.from_date:
                domain.append(('date', '>=', date_from))
            if rec.to_date:
                domain.append(('date', '<=', date_to))
            if rec.rent_vehicle_owner_id:
                domain.append(('rent_vehicle_partner_id', '=', rec.rent_vehicle_owner_id.id))
            if rec.rent_vehicle_id:
                domain.append(('rent_vehicle_id', '=', rec.rent_vehicle_id.id))
            if rec.project_id:
                domain.append(('project_id', '=', rec.project_id.id))

            diesel = self.env['diesel.pump.line'].search(domain, order='date asc')
            count = 1
            pump_total_amt = 0
            for dies in diesel:
                worksheet.write('A%s' % (new_row), count, regular)
                worksheet.write('B%s' % (new_row), datetime.strptime(dies.date, "%Y-%m-%d").strftime("%d-%m-%Y")
                                , regular)
                worksheet.write('C%s' % (new_row), dies.rent_vehicle_id.name, regular)
                # worksheet.write('D%s' % (new_row), dies.diesel_tanker and dies.diesel_tanker.name or dies.diesel_pump and dies.diesel_pump.name, regular)
                if dies.diesel_tanker:
                    worksheet.write('D%s' % (new_row), dies.diesel_tanker.name, regular)
                if dies.diesel_pump:
                    worksheet.write('D%s' % (new_row), dies.diesel_pump.name, regular)

                worksheet.write('E%s' % (new_row),dies.pump_bill_no, regular)

                litre = 0
                if dies.litre != 0:
                    litre = dies.litre
                if dies.total_diesel !=0:
                    litre = dies.total_diesel
                worksheet.write('F%s' % (new_row), litre, regular)
                per_litre = self.env['diesel.pump.line'].search([('diesel_mode','=','pump'),('date', '=', dies.date),('fuel_product_id','=','DIESEL FUEL')], order='per_litre desc',limit=1)
                worksheet.write('G%s' % (new_row),(per_litre.per_litre +1) , regular)

                worksheet.write('J%s' % (new_row), (per_litre.per_litre +1) *litre ,
                                regular)

                pump_total_amt += (per_litre.per_litre +1) *litre
                new_row += 1

                count += 1
            worksheet.merge_range("A%s:I%s" % (new_row, new_row), "Current Total", bold)

            worksheet.write('J%s' % (new_row), pump_total_amt, bold)
            worksheet.write('K%s' % (new_row), round(pump_total_amt,2), bold)
            new_row += 2


            worksheet.merge_range("A%s:I%s" % (new_row, new_row), "TOTAL OF VEHICLE RENT", bold)
            worksheet.write('K%s' % (new_row), round(total_amt, 2), bold)
            new_row +=1
            worksheet.merge_range("A%s:I%s" % (new_row, new_row), "LESS:DIESEL FILLED", bold)
            worksheet.write('K%s' % (new_row), round(pump_total_amt, 2), bold)
            new_row += 1
            worksheet.merge_range("A%s:I%s" % (new_row, new_row), "BALANCE OF RENT", bold)
            new_row+=1
            worksheet.merge_range("A%s:K%s"%(new_row,new_row), "OPENING BALANCE", bold)
            new_row += 1
            worksheet.merge_range("A%s:K%s" % (new_row, new_row), "PAID ON ", bold)
            new_row += 1
            worksheet.merge_range("A%s:K%s" % (new_row, new_row), "BALANCE", bold)

        new_row+=2
        worksheet.merge_range("A%s:C%s"%(new_row,new_row),"Generated By",bold)

        worksheet.merge_range("D%s:G%s"%(new_row,new_row),self.env.user.name,bold)
        new_row += 1
        date = workbook.add_format({'num_format': 'YYYY-MM-DD HH:DD:SS'})
        worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Generated ON", bold)

        worksheet.merge_range("D%s:F%s" % (new_row,new_row), datetime.now().strftime("%d-%m-%Y"), date)
        new_row += 1
                # worksheet.write('R%s' % (new_row), driver.remark, regular)



BillReportXlsx('report.Rent Vehicle Report.xlsx', 'rent.vehicles.report.wizard')




