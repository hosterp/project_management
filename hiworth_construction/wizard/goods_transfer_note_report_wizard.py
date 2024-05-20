from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone



class GoodsTransferNoteReportWizard(models.TransientModel):
    _name = 'goods.transfer.note.report.wizard'

    till_date = fields.Date('Date From')
    category_id = fields.Many2one('product.category',"Category")


    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='GTN Report.xlsx')

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

        worksheet.merge_range('A1:E1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:E2', invoices.category_id.name or 'All Project', boldc)
        worksheet.merge_range('A3:E3', 'Details Till %s' % (datetime.strptime(invoices.till_date, "%Y-%m-%d").strftime("%d-%m-%Y")), boldc)
        worksheet.write('A4', 'Sl.NO', bold)
        worksheet.write('B4', 'From', bold)
        worksheet.write('C4', 'To', bold)
        worksheet.write('D4', 'Item', bold)
        worksheet.write('E4', 'Quantity', bold)


        count = 1
        for rec in invoices:
            date_till = datetime.strptime(invoices.till_date, "%Y-%m-%d")


            domain = []
            if rec.till_date:
                domain.append(('date','<=',rec.till_date))
                domain.append(('state', '=', 'transfer'))



            goods_receive = self.env['goods.transfer.note.in'].search(domain,order='date asc')

            total_qty = 0
            total_amt = 0

            transfer_list ={}
            for goods in goods_receive:
                key_name = goods.project_id.name + '-' + goods.to_project_id.name
                if key_name in transfer_list.keys():
                    for line in goods.transfer_list_ids:
                        if line.item_id.categ_id.id == invoices.category_id.id:
                            if line.item_id.name in transfer_list[key_name].keys():
                                transfer_list[key_name][line.item_id.name]['qty'] = transfer_list[key_name][line.item_id.name]['qty'] + line.qty

                            else:
                                transfer_list[key_name].update({line.item_id.name:{'name':line.item_id.name,
                                                                                     'qty':line.qty,
                                                                                     }})
                else:
                    for line in goods.transfer_list_ids:
                        if line.item_id.categ_id.id == invoices.category_id.id:
                            transfer_list.update({key_name:{line.item_id.name:{'name':line.item_id.name,
                                                                                     'qty':line.qty,
                                                                                     }}})
            for key,value in transfer_list.items():
                worksheet.write('A%s' % (new_row), count, regular)
                loc_name = key.split('-')

                worksheet.write('B%s' % (new_row),loc_name[0]
                                , regular)
                worksheet.write('C%s' % (new_row), loc_name[1]
                                , regular)
                for new_key,new_value in value.items():
                    worksheet.write('D%s' % (new_row), new_key, regular)
                    worksheet.write('E%s' % (new_row),value[new_key]['qty'], regular)

                    new_row +=1


                count += 1
                new_row += 1


        new_row+=1
        worksheet.merge_range("A%s:C%s"%(new_row,new_row),"Generated By",bold)

        worksheet.merge_range("D%s:G%s"%(new_row,new_row),self.env.user.name,bold)
        new_row += 1
        date = workbook.add_format({'num_format': 'YYYY-MM-DD HH:DD:SS'})
        worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Generated ON", bold)

        worksheet.merge_range("D%s:F%s" % (new_row,new_row), datetime.now().strftime("%d-%m-%Y"), date)
        new_row += 1
                # worksheet.write('R%s' % (new_row), driver.remark, regular)


BillReportXlsx('report.GTN Report.xlsx', 'goods.transfer.note.report.wizard')




