from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone



class StockReportLocationWizard(models.TransientModel):
    _name = 'stock.report.location.wizard'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    category_id= fields.Many2one('product.category',"Category")

    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='Stock Location Report.xlsx')



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

        worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:S2',  'All Project', boldc)
        worksheet.merge_range('A3:S3', 'Stock Details From %s To %s' % (
        datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%d-%m-%Y")), boldc)
        worksheet.merge_range('A4:A5', 'Sl.NO', bold)
        worksheet.merge_range('B4:B5', 'Product', bold)
        worksheet.merge_range('C4:C5', 'Unit', bold)
        location = self.env['project.project'].search([],order='id asc')
        row_count=0
        row_val = 68
        new_row_val = 65
        new_row_val_j = 65
        spl_count = 21
        for project in location:
            if row_count < 23:
                worksheet.write('%s5' % (chr(row_val)), project.location_id.name, regular)
                row_val += 1
                row_count += 1
            else:
                if spl_count + 26 == row_count:
                    new_row_val += 1
                    spl_count = row_count
                    new_row_val_j = 65
                worksheet.write(
                    '%s%s5' % (chr(new_row_val), chr(new_row_val_j)),
                    project.location_id.name, regular)



                new_row_val_j+=1
                row_count += 1
        count = 1
        for rec in invoices:
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")

            domain = []
            if rec.from_date:
                domain.append(('date','>=',date_from))
            if rec.to_date:
                domain.append(('date','<=',date_to))


            product_domain = []
            total_amt = 0
            if rec.category_id:
                product_domain.append(('categ_id','=',rec.category_id.id))
            proudct_list = self.env['product.product'].search(product_domain)

            for product in proudct_list:


                worksheet.write('A%s' % (new_row), count, regular)
                worksheet.write('B%s' % (new_row),product.name
                                , regular)
                worksheet.write('C%s' % (new_row), product.uom_id.name, regular)
                row_count = 0
                row_val = 68
                new_row_val = 65
                new_row_val_j = 65
                spl_count = 21
                for project in location:
                    if row_count < 21:
                        total_qty = 0
                        inventory = self.env['stock.history'].search(
                            [("product_id", "=", product.id), ("date", "<", date_from),
                             ('location_id', '=', project.location_id.id)])
                        for inv in inventory:
                            total_qty += inv.quantity
                        worksheet.write('%s%s' % (chr(row_val),new_row), total_qty, regular)
                        row_val += 1
                        row_count += 1
                    else:
                        if spl_count + 26 == row_count:
                            new_row_val += 1
                            spl_count = row_count
                            new_row_val_j = 65
                        total_qty = 0
                        inventory = self.env['stock.history'].search(
                            [("product_id", "=", product.id), ("date", "<", date_from),
                             ('location_id', '=', project.location_id.id)])
                        for inv in inventory:
                            total_qty += inv.quantity
                        worksheet.write(
                            '%s%s%s' % (chr(new_row_val), chr(new_row_val_j),new_row),
                            total_qty, regular)

                        new_row_val_j += 1
                        row_count += 1
                new_row+=1
                count+=1


        new_row+=1
        worksheet.merge_range("A%s:C%s"%(new_row,new_row),"Generated By",bold)

        worksheet.merge_range("D%s:G%s"%(new_row,new_row),self.env.user.name,bold)
        new_row += 1
        date = workbook.add_format({'num_format': 'YYYY-MM-DD HH:DD:SS'})
        worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Generated ON", bold)

        worksheet.merge_range("D%s:F%s" % (new_row,new_row), datetime.now().strftime("%d-%m-%Y"), date)
        new_row += 1
                # worksheet.write('R%s' % (new_row), driver.remark, regular)



BillReportXlsx('report.Stock Location Report.xlsx', 'stock.report.location.wizard')




