from openerp import fields, models, api
from datetime import datetime
import calendar
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx

class HiworthMaterialRequestWizard(models.TransientModel):
    _name='hiworth.material.request.wizard'

    #from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    #to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    date_today = fields.Date('Date',default = datetime.today())
    category = fields.Many2one('product.category')
    # Calculate default time range
    #@api.model
    #def default_time_range(self, type):
    #    year = datetime.date.today()
    #    month = datetime.date.today()
    #    last_day = calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1]
     #   first_day = 1
     #   if type=='from':
     #       return datetime.date(year, month, first_day)
     #   elif type=='to':
     #       return datetime.date(year, month, last_day)

   # @api.multi
   # def print_material_request_report(self):
   #     self.ensure_one()
    #    stockPicking = self.env['stock.picking']
    #    stockPickingRecs = stockPicking.search([('date','>=',self.from_date),('date','<=',self.to_date),('is_task_related','=',True)])

    #    if not stockPickingRecs:
    #        raise osv.except_osv(('Error'), ('There are no material requests to display. Please make sure material requests exist.'))

    #    datas = {
    #        'ids': stockPickingRecs._ids,
	#		'model': stockPicking._name,
	#		'form': stockPicking.read(),
	#		'context':self._context,
    #    }
    #    return{
    #        'type' : 'ir.actions.report.xml',
    #        'report_name' : 'hiworth_construction.report_material_request_template',
    #        'datas': datas,
    #        'context':{'start_date': self.from_date, 'end_date': self.to_date}
    #    }
        
    #@api.multi
   # def view_material_request_report(self):
     #   self.ensure_one()
    #    stockPicking = self.env['stock.picking']
    #    stockPickingRecs = stockPicking.search([('date','>=',self.from_date),('date','<=',self.to_date),('is_task_related','=',True)])

     #   if not stockPickingRecs:
      #      raise osv.except_osv(('Error'), ('There are no material requests to display. Please make sure material requests exist.'))
#
     #   datas = {
      #      'ids': self._ids,
       #     'model': self._name,
      #      'form': self.read(),
      #      'context':self._context,
       # }
       # return{
      #      'type' : 'ir.actions.report.xml',
      #      'report_name' : 'hiworth_construction.report_material_request_template_view',
      #      'datas': datas,
      #      'report_type': 'qweb-html',
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
      #  }
        
        
    #@api.multi
    #def get_picking(self):
     #   self.ensure_one() 
     #   stockPicking = self.env['stock.picking']
    #    stockPickingRecs = stockPicking.search([('date','>=',self.from_date),('date','<=',self.to_date),('is_task_related','=',True)]) 
    #    return stockPickingRecs
    @api.multi
    def generate_xls_report_materials(self):  
        
        return self.env["report"].get_action(self, report_name='custom.material_request_report.xlsx')


class BillReportXlsxDaily(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))
        #print 'ddddddddddddddddddddddddd',self
        #print 'iiiiiiiiiiiiiiiiiiiiiiiiii',invoices
        


        boldc = workbook.add_format({'bold': True,'align': 'center','bg_color':'#D3D3D3','font':'height 10'})
        heading_format = workbook.add_format({'bold': True,'align': 'center','size': 10})
        bold = workbook.add_format({'bold': True})
        rightb = workbook.add_format({'align': 'right','bold': True})
        right = workbook.add_format({'align': 'right'})
        regular=workbook.add_format({'align':'center','bold':False})
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
        row = 4
        col = 71
        row_1 = 5
        new_row_1 = row_1
        new_row = row 
        new_col = col

        worksheet.set_column('B:B',30)

        worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        #worksheet.merge_range('A2:S2',invoices.project_id.name or 'All Project',boldc)
        worksheet.merge_range('A2:S2','Shuttering & Scaffolding Materials Stock Details site wise as on '+invoices.date_today,boldc)
        worksheet.merge_range('A3:A4','Sl.NO',regular)
        worksheet.merge_range('B3:B4','Description',regular)
        worksheet.merge_range('C3:C4','unit',regular)
       # worksheet.merge_range('D4:F5','Receipt',regular)
        worksheet.merge_range('D3:D4','Total Received Qty',regular)
        worksheet.merge_range('E3:E4','Debited as on')
        #worksheet.merge_range('A4:O5','',regular)
        worksheet.merge_range('F3:F4','Actual Stock',regular)
        #worksheet.merge_range('G3:G4','Central s',regular)s
        #worksheet.merge_range('G4:I4','Issues',regular)
        #worksheet.write('G5','Balance',regular)
        #worksheet.merge_range('H4:J4','Physical stock',regular)
        sl_count = 1
        total_grr=0
        for rec in invoices:
            print 'llllllllllllllllllllllllllllll',rec
            if rec.category:
                product_id=self.env['product.product'].search([("categ_id","=",rec.category.id)])
                print 'idddddddddddddddd',product_id
                inventory = self.env['stock.inventory.line'].search([])
            else:
                product_id=self.env['product.product'].search([])
            for product in product_id:
                print 'iddddddddddddddddeeeeeeeeeeeesssssssssssssssssssssssssss',product_id
                worksheet.write('A%s'%(new_row_1),sl_count)
                worksheet.write('B%s'%(new_row_1),product.name)
                worksheet.write('C%s'%(new_row_1),product.uom_id.name)
                sl_count +=1
                new_row_1 += 1
                print 'cooooooooooooooooooooooooooooo',sl_count
        

                grr = self.env['goods.recieve.report.line'].search([('item_id','=',product.id)])
                print 'grrrrrrrrrrrrrrrrrrrr',grr
                for rec in grr:
                    total_grr += rec.quantity_accept
                    print 'totaaaaaaaaaaaaaaaaaal grrrrrrrrrrrrrrr',total_grr


        location=self.env['stock.location'].search([('usage','=','internal')])
        new_ncol = 65
        next_col = 65
        col_new = 65
        new_count = 0
        print 'caaaaaaaaaaaaaaaaaaaaaation',location
        loc_list=[]
        for loc in location:
            loc_list.append(loc.name)
            #print 'eeeeeeeeeeeeeeeeeeeee', loc_list
        count=0
        for i in range(len(loc_list)):
            #print 'lossssssssssssssssssssssss',loc_list[i],new_col,count
            if count != len(loc_list):
                if count<20:
                    worksheet.write('%s%s' % (chr(new_col),new_row),loc_list[i])
                    new_col = col + 1
                    col += 1
                    new_count = count
                else:

                    worksheet.write('%s%s%s' % (chr(new_ncol),chr(next_col),new_row),loc_list[i])
                    next_col = col_new + 1
                    col_new += 1
                    if count == new_count+26:
                        new_ncol += 1
                        next_col = 65
                        col_new = 65
                        new_count = count

               # for col_cells in worksheet.iter_cols(min_col=4, max_col=len(loc_list)):
                   # for cell in col_cells:
                       # print('%s: cell.value=%s' % (cell,loc_list[i]))
                count += 1

        



BillReportXlsxDaily('report.custom.material_request_report.xlsx','hiworth.material.request.wizard')
