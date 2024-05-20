from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone



class GoodsRecieveReportWizard(models.TransientModel):
    _name = 'goods.recieve.report.wizard'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', 'Company')

    project_id = fields.Many2one('project.project')
    supplier_id = fields.Many2one('res.partner',"Supplier",domain="[('supplier','=',True)]")
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
                              ('December', 'December')], 'Month', )

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 ' + self.month + ' ' + str(datetime.now().year)

            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)

            self.to_date = end_date


    @api.multi
    def get_product_details(self):
        for rec in self:

            date_from = datetime.strptime(rec.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(rec.to_date, "%Y-%m-%d")

            domain = []
            if rec.from_date:
                domain.append(('Date', '>=', date_from))
            if rec.to_date:
                domain.append(('Date', '<=', date_to))
            if rec.supplier_id:
                domain.append(('supplier_id', '=', rec.supplier_id.id))
            if rec.project_id:
                domain.append(('project_id', '=', rec.project_id.id))
            goods_receive = self.env['goods.recieve.report'].search(domain, order='Date asc,invoice_no asc')
            produtc_dict = {}
            for goods in goods_receive:
                for line in goods.goods_recieve_report_line_ids:
                    if line.item_id.name in produtc_dict.keys():
                        produtc_dict[line.item_id.name]['qty'] = produtc_dict[line.item_id.name][
                                                                     'qty'] + line.quantity_accept
                        produtc_dict[line.item_id.name]['total'] = produtc_dict[line.item_id.name][
                                                                       'total'] + line.total_amount
                    else:
                        produtc_dict.update({line.item_id.name: {'name': line.item_id.name,
                                                                 'qty': line.quantity_accept,
                                                                 'total': line.total_amount}})
            return produtc_dict
    @api.multi
    def get_details(self):
        for rec in self:
            date_from = datetime.strptime(rec.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(rec.to_date, "%Y-%m-%d")

            domain = []
            if rec.from_date:
                domain.append(('Date', '>=', date_from))
            if rec.to_date:
                domain.append(('Date', '<=', date_to))
            if rec.supplier_id:
                domain.append(('supplier_id', '=', rec.supplier_id.id))
            if rec.project_id:
                domain.append(('project_id', '=', rec.project_id.id))

            goods_receive = self.env['goods.recieve.report'].search(domain, order='Date asc,invoice_no asc')
            return goods_receive
    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Goods Receive Report.xlsx')

    @api.multi
    def print_report(self):
        # return self.env["report"].get_action(self, report_name='report_bata_report_wise')
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_construction.goods_receive_report_pdf_template',
            'datas': datas,
            #             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'category': self.category.id},
            'report_type': 'qweb-html',
        }
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
        worksheet.set_column('D:S', 13)
        if (invoices.project_id and invoices.supplier_id) or invoices.supplier_id:
            worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
            worksheet.merge_range('A2:S2', invoices.project_id.name or 'All Project', boldc)
            worksheet.merge_range('A3:S3', '%s Details From %s To %s' % (invoices.supplier_id.name,
            datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
            datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%d-%m-%Y")), boldc)
            worksheet.write('A5', 'Sl.NO', bold)
            worksheet.write('B5', 'Invoice Date', bold)
            worksheet.write('C5', 'Created By', bold)
            worksheet.write('D5', 'Date', bold)
            worksheet.write('E5', 'Project', bold)
            worksheet.write('F5', 'GRR No', bold)

            worksheet.write('G5', 'Supplier Invoice Number', bold)
            worksheet.write('H5', 'MR Slip', bold)
            worksheet.write('I5', 'Vehicle No', bold)
            # worksheet.merge_range('A4:O5','',regular)
            worksheet.write('J5', 'Item Name', bold)
            worksheet.write('K5', 'Unit', bold)

            worksheet.write('L5', 'Quantity', bold)
            worksheet.write('M5', 'Price', bold)
            worksheet.write('N5', 'SubTotal', bold)
            worksheet.write('O5', 'GST', bold)

            worksheet.write('P5', 'IGST', bold)
            worksheet.write('Q5', 'TCS', bold)
            worksheet.write('R5', 'Round off', bold)
            worksheet.write('S5', 'Total', bold)
            worksheet.merge_range("A6:K6","Opening Balance",bold)
            count = 1
            for rec in invoices:
                date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
                date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")

                domain = []
                if rec.from_date:
                    domain.append(('Date','>=',date_from))
                if rec.to_date:
                    domain.append(('Date','<=',date_to))
                if rec.supplier_id:
                    domain.append(('supplier_id', '=', rec.supplier_id.id))
                if rec.project_id:
                    domain.append(('project_id', '=', rec.project_id.id))


                goods_receive = self.env['goods.recieve.report'].search(domain,order='Date asc,invoice_no asc')

                total_qty = 0
                total_amt = 0


                for goods in goods_receive:


                    worksheet.write('A%s' % (new_row), count, regular)
                    worksheet.write('B%s' % (new_row),datetime.strptime(goods.Date, "%Y-%m-%d").strftime("%d-%m-%Y")
                                    , regular)
                    worksheet.write('C%s' % (new_row), goods.create_uid.name, regular)
                    worksheet.write('D%s' % (new_row), datetime.strptime(goods.invoice_date, "%Y-%m-%d").strftime("%d-%m-%Y"), regular)
                    worksheet.write('E%s' % (new_row), goods.project_id.name, regular)
                    worksheet.write('F%s' % (new_row), goods.grr_no, regular)

                    worksheet.write('G%s' % (new_row), goods.invoice_no, regular)
                    worksheet.write('H%s' % (new_row), goods.mr_slip, regular)
                    vehicle_name = ''
                    if goods.vehicle_id:
                        vehicle_name = goods.vehicle_id.name
                    if goods.rent_vehicle_id:
                        vehicle_name = goods.rent_vehicle_id.name
                    if goods.vehicle_no:
                        vehicle_name = goods.vehicle_no
                    worksheet.write('I%s' % (new_row),vehicle_name , regular)
                    for line in goods.goods_recieve_report_line_ids:
                        worksheet.write('J%s' % (new_row), line.item_id.name, regular)
                        worksheet.write('K%s' % (new_row), line.unit_id.name, regular)
                        worksheet.write('L%s' % (new_row), line.quantity_accept, regular)
                        total_qty +=line.quantity_accept
                        worksheet.write('M%s' % (new_row),line.rate , regular)
                        worksheet.write('N%s' % (new_row), line.sub_total, regular)
                        worksheet.write('O%s' % (new_row), line.cgst_amount +line.sgst_amount , regular)

                        worksheet.write('P%s' % (new_row), line.igst_amount, regular)
                        worksheet.write('Q%s' % (new_row), line.tcs_amount, regular)
                        worksheet.write('R%s' % (new_row), line.round_off_amount, regular)
                        worksheet.write('S%s' % (new_row), line.total_amount, regular)
                        total_amt += line.total_amount
                        new_row +=1


                    count += 1
                worksheet.merge_range("A%s:K%s" % (new_row, new_row), "Current Total", bold)
                worksheet.write('L%s' % (new_row), total_qty, bold)
                worksheet.write('S%s' % (new_row), total_amt, bold)
                new_row += 1
                worksheet.merge_range("A%s:K%s" % (new_row, new_row), "Paid ON", bold)
                new_row +=1
                worksheet.merge_range("A%s:K%s"%(new_row,new_row), "Closing Balance", bold)
        else:
            worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
            worksheet.merge_range('A2:S2', invoices.project_id.name , boldc)
            worksheet.merge_range('A3:S3', 'Details From %s To %s' % (
                                                                         datetime.strptime(invoices.from_date,
                                                                                           "%Y-%m-%d").strftime(
                                                                             "%d-%m-%Y"),
                                                                         datetime.strptime(invoices.to_date,
                                                                                           "%Y-%m-%d").strftime(
                                                                             "%d-%m-%Y")), boldc)
            worksheet.write('A5', 'Sl.NO', bold)
            worksheet.write('B5', 'Invoice Date', bold)
            worksheet.write('C5', 'Created By', bold)
            worksheet.write('D5', 'Date', bold)
            worksheet.write('E5', 'Project', bold)
            worksheet.write('F5', 'GRR No', bold)
            worksheet.write('G5', 'Supplier Name', bold)
            worksheet.write('H5', 'Supplier Invoice Number', bold)
            worksheet.write('I5', 'MR Slip', bold)
            worksheet.write('J5', 'Vehicle No', bold)
            # worksheet.merge_range('A4:O5','',regular)
            worksheet.write('K5', 'Item Name', bold)
            worksheet.write('L5', 'Unit', bold)

            worksheet.write('M5', 'Quantity', bold)
            worksheet.write('N5', 'Price', bold)
            worksheet.write('O5', 'SubTotal', bold)
            worksheet.write('P5', 'GST', bold)

            worksheet.write('Q5', 'IGST', bold)
            worksheet.write('R5', 'TCS Amount', bold)
            worksheet.write('S5', 'Round off', bold)
            worksheet.write('T5', 'Total', bold)
            worksheet.merge_range("A6:K6", "Opening Balance", bold)
            count = 1
            for rec in invoices:
                date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
                date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")

                domain = []
                if rec.from_date:
                    domain.append(('Date', '>=', date_from))
                if rec.to_date:
                    domain.append(('Date', '<=', date_to))
                if rec.supplier_id:
                    domain.append(('supplier_id', '=', rec.supplier_id.id))
                if rec.project_id:
                    domain.append(('project_id', '=', rec.project_id.id))

                goods_receive = self.env['goods.recieve.report'].search(domain, order='Date asc,invoice_no asc')

                total_qty = 0
                total_amt = 0

                for goods in goods_receive:

                    worksheet.write('A%s' % (new_row), count, regular)
                    worksheet.write('B%s' % (new_row), datetime.strptime(goods.Date, "%Y-%m-%d").strftime("%d-%m-%Y")
                                    , regular)
                    worksheet.write('C%s' % (new_row), goods.create_uid.name, regular)
                    worksheet.write('D%s' % (new_row),
                                    datetime.strptime(goods.invoice_date, "%Y-%m-%d").strftime("%d-%m-%Y"), regular)
                    worksheet.write('E%s' % (new_row), goods.project_id.name, regular)
                    worksheet.write('F%s' % (new_row), goods.grr_no, regular)
                    worksheet.write('G%s' % (new_row), goods.supplier_id.name, regular)
                    worksheet.write('H%s' % (new_row), goods.invoice_no, regular)
                    worksheet.write('I%s' % (new_row), goods.mr_slip, regular)
                    vehicle_name = ''
                    if goods.vehicle_id:
                        vehicle_name = goods.vehicle_id.name
                    if goods.rent_vehicle_id:
                        vehicle_name = goods.rent_vehicle_id.name
                    if goods.vehicle_no:
                        vehicle_name = goods.vehicle_no
                    worksheet.write('J%s' % (new_row), vehicle_name, regular)
                    for line in goods.goods_recieve_report_line_ids:
                        worksheet.write('K%s' % (new_row), line.item_id.name, regular)
                        worksheet.write('L%s' % (new_row), line.unit_id.name, regular)
                        worksheet.write('M%s' % (new_row), line.quantity_accept, regular)
                        total_qty += line.quantity_accept
                        worksheet.write('N%s' % (new_row), line.rate, regular)
                        worksheet.write('O%s' % (new_row), line.sub_total, regular)
                        worksheet.write('P%s' % (new_row), line.cgst_amount + line.sgst_amount, regular)

                        worksheet.write('Q%s' % (new_row), line.igst_amount, regular)
                        worksheet.write('R%s' % (new_row), line.tcs_amount, regular)
                        worksheet.write('S%s' % (new_row), line.round_off_amount, regular)
                        worksheet.write('T%s' % (new_row), line.total_amount, regular)
                        total_amt += line.total_amount
                        new_row += 1

                    count += 1
                worksheet.merge_range("A%s:K%s" % (new_row, new_row), "Current Total", bold)
                worksheet.write('M%s' % (new_row), total_qty, bold)
                worksheet.write('T%s' % (new_row), total_amt, bold)
                new_row += 1
                worksheet.merge_range("A%s:K%s" % (new_row, new_row), "Paid ON", bold)
                new_row += 1
                worksheet.merge_range("A%s:K%s" % (new_row, new_row), "Closing Balance", bold)

        new_row+=1
        worksheet.merge_range("A%s:C%s"%(new_row,new_row),"Generated By",bold)

        worksheet.merge_range("D%s:G%s"%(new_row,new_row),self.env.user.name,bold)
        new_row += 1
        date = workbook.add_format({'num_format': 'YYYY-MM-DD HH:DD:SS'})
        worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Generated ON", bold)

        worksheet.merge_range("D%s:F%s" % (new_row,new_row), datetime.now().strftime("%d-%m-%Y"), date)
        new_row += 1
                # worksheet.write('R%s' % (new_row), driver.remark, regular)

        goods_receive = self.env['goods.recieve.report'].search(domain, order='Date asc,invoice_no asc')
        produtc_dict = {}
        for goods in goods_receive:
            for line in goods.goods_recieve_report_line_ids:
                if line.item_id.name in produtc_dict.keys():
                    produtc_dict[line.item_id.name]['qty'] = produtc_dict[line.item_id.name]['qty'] + line.quantity_accept
                    produtc_dict[line.item_id.name]['total'] = produtc_dict[line.item_id.name]['total'] + line.total_amount
                else:
                    produtc_dict.update({line.item_id.name:{'name':line.item_id.name,
                                                            'qty':line.quantity_accept,
                                                            'total':line.total_amount}})

        worksheet.write("A%s" % (new_row), "SL No", bold)
        worksheet.merge_range("B%s:C%s"%(new_row,new_row),"Item Name",bold)
        worksheet.write("D%s"%(new_row),"Quantity",bold)
        worksheet.write("E%s" % (new_row), "Total Amount", bold)
        new_row+=1
        count=1
        for key,value in produtc_dict.items():
            worksheet.write("A%s" % (new_row),count, regular)
            worksheet.merge_range("B%s:C%s" % (new_row, new_row), produtc_dict[key]['name'], regular)
            worksheet.write("D%s" % (new_row),produtc_dict[key]['qty'], regular)
            worksheet.write("E%s" % (new_row), produtc_dict[key]['total'], regular)
            new_row+=1
            count+=1


BillReportXlsx('report.Goods Receive Report.xlsx', 'goods.recieve.report.wizard')




