from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz


class report_location_stock(models.TransientModel):
    _name='report.location.stock'


    from_date=fields.Date('Date From')
    to_date=fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    company_id =fields.Many2one('res.company','Company')
    date_today = fields.Date('Date')
    category = fields.Many2one('product.category')
    project_id = fields.Many2one('project.project')
    product_id = fields.Many2one('product.product')
    month = fields.Selection([('January','January'),
                                ('February','February'),
                                ('March','March'),
                                ('April','April'),
                                ('May','May'),
                                ('June','June'),
                                ('July','July'),
                                ('August','August'),
                                ('September','September'),
                                ('October','October'),
                                ('November','November'),
                                ('December','December')], 'Month',required = True)
    _defaults = {
        'date_today': datetime.today(),
        #'from_date': '2017-04-01',
        #'to_date': fields.Date.today(),
    }

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 '+self.month+' '+str(datetime.now().year)

            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)
            self.to_date = end_date


    @api.onchange('company_id')
    def onchange_field(self):
        if self.company_id.id != False:
            return {
                'domain': {
                'account_id': [('company_id', '=', self.company_id.id),('type', '=', 'view')],
                },
            }

   # @api.multi
    #def print_report_location_stock(self):
      #  self.ensure_one()
     #   if self.location_id.id == False:
     #       raise osv.except_osv(('Error'), ('Please select a proper location'))

      #  locations = self.env['stock.location']
      #  locationrecs = locations.search([('id','=',self.location_id.id)])

      #  datas = {
       #     'ids': locationrecs._ids,
      #      'model': locations._name,
      #      'form': locations.read(),
      #      'context':self._context,
      #  }

      #  return{
      #      'type' : 'ir.actions.report.xml',
      #      'report_name' : 'hiworth_construction.report_location_stock',
      #      'datas': datas,
      #      'context':{'start_date': self.from_date, 'end_date': self.to_date, 'category': self.category.id}
      #  }
        
        
    @api.multi
    def view_report_location_stock(self):
        self.ensure_one()

        if self.location_id.id == False:

            raise osv.except_osv(('Error'), ('Please select a proper location'))

        locations = self.env['stock.location']
        locationrecs = locations.search([('id','=',self.location_id.id)])

                
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.view_stock_report',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'category': self.category.id},
            'report_type': 'qweb-html',         
        }
        
    @api.multi
    def get_products(self):
        self.ensure_one()
        start_date = self.from_date
        end_date = self.to_date
        category = self.category

        if category.id != False:
            product_recs = self.env['product.product'].search([('type','=','product')]).filtered(lambda r: r.categ_id.id == category.id).sorted(lambda r: r.categ_id)
        else:
            product_recs = self.env['product.product'].search([('type','=','product')]).sorted(lambda r: r.categ_id.name)
            
            
        
        for line in product_recs:
            temp_in = 0.0
            temp_out = 0.0
            line.temp_remain = 0.0
#             if line.balance!=0.0:
            move_lines = self.env['stock.move'].search([('location_id','=',self.location_id.id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
            for moves in move_lines:
                temp_out+=moves.product_uom_qty

            move_lines = self.env['stock.move'].search([('location_dest_id','=',self.location_id.id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
            for moves in move_lines:
                temp_in+=moves.product_uom_qty
            line.temp_remain = temp_in - temp_out

        return product_recs

    @api.multi
    def generate_xls_report(self):  
        
        return self.env["report"].get_action(self, report_name='custom.stock_report.xlsx')

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
       
        

        worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:S2',invoices.project_id.name or 'All Project',boldc)
        worksheet.merge_range('A3:S3','SUMMARY OF MATERIALS FOR THE MONTH OF '+invoices.month,boldc)
        worksheet.merge_range('A4:A5','Sl.NO',regular)
        worksheet.merge_range('B4:B5','Description',regular)
        worksheet.merge_range('C4:C5','unit',regular)
       # worksheet.merge_range('D4:F5','Receipt',regular)
        worksheet.merge_range('D4:F4','Receipt',regular)
        worksheet.write('D5','Opening Balance',regular)
        #worksheet.merge_range('A4:O5','',regular)
        worksheet.write('E5','During the month',regular)
        worksheet.write('F5','Cum Receipt',regular)
        worksheet.merge_range('G4:I4','Issues',regular)
        #worksheet.write('G5','Balance',regular)
        #worksheet.merge_range('H4:J4','Physical stock',regular)
        worksheet.write('G5','Cumlative Transfer',regular)
        worksheet.write('H5','During the month',regular)
        worksheet.write('I5','Cum:issue',regular)
        worksheet.merge_range('J4:L4','Balance',regular)
        worksheet.write('J5','Book Balance',regular)
        worksheet.write('K5','Physical Stock',regular)
        worksheet.write('L5','Variation',regular)
        worksheet.merge_range('M4:N4','Cons:as per DPR',regular)
        worksheet.write('M5','During the month',regular)
        worksheet.write('N5','Cumulative',regular)
        worksheet.merge_range('O4:Q4','Diff:Actual-DPR',regular)
        worksheet.write('O5','8 & 13',regular)
        worksheet.write('P5','9 & 14',regular)
        worksheet.write('Q5','-',regular)
        worksheet.merge_range('R4:S4','Remarks/Can be spared',regular)
        resource_list = self.env['stock.history'].search([('location_id', '=', invoices.project_id.location_id.id)])
        product_list = []
        for res in resource_list:
            product_list.append(res.product_id.id)

        product_list = self.env['product.product'].search([]).ids
        count=1
        for rec in invoices:
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Kolkata')
            # from_zone = tz.tzutc()
            # to_zone = tz.tzlocal()
            utc = datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
            utc = utc.replace(tzinfo=to_zone)
            central = utc.astimezone(from_zone)

            # date_today = utcc.replace(tzinfo=from_zone)
            date_to = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S').strftime(
                "%Y-%m-%d %H:%M:%S")
            utcc = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
            date_from = utcc.replace(tzinfo=from_zone)
            date_from = datetime.strptime(date_from.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S').strftime(
                "%Y-%m-%d %H:%M:%S")
            if rec.category:
                product_id=self.env['product.product'].search([("categ_id","=",rec.category.id)])
                worksheet.write('A%s' % (new_row), rec.category.name, regular)
                new_row += 1
                product_id = self.env['product.product'].search([("categ_id", "=", rec.category.id),('id','in',product_list)])
                total_opening = 0
                total_during_rec = 0
                total_cum_reci = 0
                total_cum_tran = 0
                total_during_mont = 0
                total_cum_issue = 0
                total_book_balance = 0
                for product in product_id:
                    book_balance = 0
                    opening = 0

                    if invoices.project_id:
                        goods_recieve_report = self.env['goods.recieve.report'].search(
                            [('Date', '<=', date_to), ('project_id', '=', invoices.project_id.id)
                             ])
                    else:
                        goods_recieve_report = self.env['goods.recieve.report'].search(
                            [('Date', '<=', date_to),
                             ])

                    total = 0
                    for good_recieve in goods_recieve_report:
                        for line in good_recieve.goods_recieve_report_line_ids:
                            if line.item_id.id == product.id:
                                total += line.quantity_accept

                    goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                        [('goods_transfer_bool', '=', True), ('to_project_id', '=', invoices.project_id.id),
                         ('rece_date', '<=', date_to), ('state', '=', 'recieve')])

                    for goods_transfer in goods_transfer_note_in:
                        for line in goods_transfer.transfer_list_ids:
                            if line.item_id.id == product.id:
                                total += line.qty

                    if invoices.project_id:
                        stock_inventory = self.env['stock.inventory'].search(
                            [('date', '<=', date_to), ('state', '=', 'done'),
                             ('location_id', '=', invoices.project_id.location_id.id)])
                    else:
                        stock_inventory = self.env['stock.inventory'].search(
                            [('date', '<=', date_to), ('state', '=', 'done')])
                    for inv in stock_inventory:
                        for inv_line in inv.line_ids:
                            if inv_line.product_id.id == product.id:
                                total += inv_line.product_qty

                    total_cum_reci += total
                    if total_cum_reci!=0:
                        worksheet.write('A%s' % (new_row), count, regular)
                        worksheet.write('B%s' % (new_row), product.name, regular)
                        worksheet.write('C%s' % (new_row), product.uom_id.name, regular)


                        total = 0
                        if invoices.project_id:
                            location_id = invoices.project_id.location_id.id
                            inventory = self.env['stock.history'].search(
                                [("product_id", "=", product.id), ("date", "<", date_from),
                                 ('location_id', '=', location_id)])
                        else:
                            location = self.env['stock.location'].search([('usage', '=', 'internal')])
                            inventory = self.env['stock.history'].search(
                                [("product_id", "=", product.id), ("date", "<", date_from),
                                 ('location_id', 'in', location.ids)])

                        # new_row+=1
                        for inv in inventory:
                            total += sum(inv.mapped('quantity'))
                        book_balance += total
                        total_opening += total
                        opening +=total
                        worksheet.write('D%s' % (new_row), round(total,4), regular)

                        if invoices.project_id:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '>=', date_from), ('Date', '<=', date_to),
                                 ('project_id', '=', invoices.project_id.id)])


                        else:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '>=', invoices.from_date), ('Date', '<=', invoices.to_date),
                                 ])

                        total = 0
                        for good_recieve in goods_recieve_report:
                            for line in good_recieve.goods_recieve_report_line_ids:
                                if line.item_id.id == product.id:
                                    total += line.quantity_accept

                        if invoices.project_id:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', True), ('to_project_id', '=', invoices.project_id.id),
                                 ('rece_date', '<=', invoices.to_date), ('rece_date', '>=', invoices.from_date), ('state', '=', 'recieve')])
                        else:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', True),
                                 ('rece_date', '<=', date_to), ('rece_date', '>=', date_from), ('state', '=', 'recieve')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty

                        if invoices.project_id:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to),
                                 ("project_id", "=", invoices.project_id.id)
                                    , ('is_receive', '=', True)])
                        else:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to), ('is_receive', '=', True)])
                        for material in material_issue_slip:
                            for line in material.material_issue_slip_lines_ids:
                                if line.item_id.id == product.id:
                                    total += line.req_qty

                        book_balance += total
                        total_during_rec += total
                        worksheet.write('E%s' % (new_row), total, regular)
                        if invoices.project_id:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '<=', invoices.to_date), ('project_id', '=', invoices.project_id.id)
                                 ])
                        else:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '<=', date_to),
                                 ])

                        total = 0
                        for good_recieve in goods_recieve_report:
                            for line in good_recieve.goods_recieve_report_line_ids:
                                if line.item_id.id == product.id:
                                    total += line.quantity_accept

                        goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                            [('goods_transfer_bool', '=', True),('to_project_id','=',invoices.project_id.id),
                             ('rece_date', '<=', date_to), ('state', '=', 'recieve')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty


                        if invoices.project_id:
                            stock_inventory = self.env['stock.inventory'].search([('date','<=',date_to),('state','=','done'),
                                                                                  ('location_id','=',invoices.project_id.location_id.id)])
                        else:
                            stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_to),('state','=','done')])
                        for inv in stock_inventory:
                            for inv_line in inv.line_ids:
                                if inv_line.product_id.id == product.id:
                                    total+=inv_line.product_qty

                        total_cum_reci += total
                        worksheet.write('F%s' % (new_row), total, regular)
                        total = 0
                        if invoices.project_id:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),('date', '>=', date_from),
                                 ('date', '<=', date_to), ('state', '=', 'transfer')])
                        else:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False),('date', '>=', date_from),
                                 ('date', '<=', date_to), ('state', '=', 'transfer')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty
                        total_cum_tran += total
                        book_balance -= total
                        worksheet.write('G%s' % (new_row), total, regular)
                        total = 0
                        if invoices.project_id:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_to), ('date', '>=', date_from),('is_receive','=',False),
                                 ("project_id", "=", invoices.project_id.id)])
                        else:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_to), ('date', '>=', date_from),('is_receive','=',False)])
                        for material in material_issue_slip:
                            for line in material.material_issue_slip_lines_ids:
                                if line.item_id.id == product.id:
                                    total += line.req_qty



                        book_balance -= total
                        total_during_mont += total
                        worksheet.write('H%s' % (new_row), total, regular)
                        total = 0
                        if invoices.project_id:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_to), ("project_id", "=", invoices.project_id.id),('is_receive','=',False)])
                        else:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_to),('is_receive','=',False)])
                        for material in material_issue_slip:
                            for line in material.material_issue_slip_lines_ids:
                                if line.item_id.id == product.id:
                                    total += line.req_qty

                        if invoices.project_id:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),
                                 ('date', '<=', date_to), ('state', '=', 'transfer')])
                        else:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False),
                                 ('date', '<=', date_to), ('state', '=', 'transfer')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty

                        if invoices.project_id:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to),
                                 ("project_id", "=", invoices.project_id.id)
                                    , ('is_receive', '=', True)])
                        else:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to), ('is_receive', '=', True)])
                        for material in material_issue_slip:
                            for line in material.material_issue_slip_lines_ids:
                                if line.item_id.id == product.id:
                                    total -= line.req_qty

                        total_cum_issue += total
                        worksheet.write('I%s' % (new_row), total, regular)

                        total_book_balance += book_balance
                        worksheet.write('J%s' % (new_row), round(book_balance,4), regular)
                        count += 1
                        new_row += 1
            else:
                categ_list = []
                for product in product_list:
                    product = self.env['product.product'].browse(product)
                    categ_list.append(product.categ_id.id)
                categ_list = list(set(categ_list))
                product_categ = self.env['product.category'].search([('id', 'in', categ_list)])

                for product_cate in product_categ:
                    worksheet.write('A%s' % (new_row), product_cate.name, regular)
                    new_row+=1
                    product_id=self.env['product.product'].search([("categ_id","=",product_cate.id),('id','in',product_list)])
                    total_opening = 0
                    total_during_rec = 0
                    total_cum_reci = 0
                    total_cum_tran = 0
                    total_during_mont = 0
                    total_cum_issue = 0
                    total_book_balance = 0
                    for product in product_id:
                        book_balance = 0
                        total_cum_reci = 0

                        if invoices.project_id:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '<=', invoices.to_date), ('project_id', '=', invoices.project_id.id)
                                 ])
                        else:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '<=', date_to),
                                 ])

                        total = 0
                        for good_recieve in goods_recieve_report:
                            for line in good_recieve.goods_recieve_report_line_ids:
                                if line.item_id.id == product.id:
                                    total += line.quantity_accept

                        goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                            [('goods_transfer_bool', '=', True), ('to_project_id', '=', invoices.project_id.id),
                             ('rece_date', '<=', invoices.to_date), ('state', '=', 'recieve')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty

                        if invoices.project_id:
                            stock_inventory = self.env['stock.inventory'].search(
                                [('date', '<=', date_to), ('state', '=', 'done'),
                                 ('location_id', '=',
                                  invoices.project_id.location_id.id)])
                        else:
                            stock_inventory = self.env['stock.inventory'].search(
                                [('date', '<=', date_to), ('state', '=', 'done')])
                        for inv in stock_inventory:
                            for inv_line in inv.line_ids:
                                if inv_line.product_id.id == product.id:
                                    total += inv_line.product_qty
                        total_cum_reci += total
                        if total_cum_reci != 0:
                            worksheet.write('A%s'%(new_row),count,regular)
                            worksheet.write('B%s'%(new_row),product.name,regular)
                            worksheet.write('C%s'%(new_row),product.uom_id.name,regular)

                            total_cum_reci = 0
                            total = 0
                            if invoices.project_id:
                                location_id = invoices.project_id.location_id.id
                                inventory = self.env['stock.history'].search([("product_id","=",product.id),("date","<",date_from),('location_id','=',location_id)])
                            else:
                                location = self.env['stock.location'].search([('usage','=','internal')])
                                inventory = self.env['stock.history'].search(
                                    [("product_id", "=", product.id), ("date", "<", date_from),
                                     ('location_id', 'in', location.ids)])

                            #new_row+=1
                            for inv in inventory:
                                total += sum(inv.mapped('quantity'))
                            book_balance += total
                            total_opening +=total
                            worksheet.write('D%s'%(new_row),round(total,4),regular)

                            if invoices.project_id:
                                goods_recieve_report = self.env['goods.recieve.report'].search([('Date','>=',invoices.from_date),('Date','<=',invoices.to_date),('project_id','=',invoices.project_id.id)])


                            else:
                                goods_recieve_report = self.env['goods.recieve.report'].search(
                                    [ ('Date', '>=', date_from), ('Date', '<=', date_to),
                                    ])

                            total = 0
                            for good_recieve in goods_recieve_report:
                                for line in good_recieve.goods_recieve_report_line_ids:
                                    if line.item_id.id == product.id:
                                        total += line.quantity_accept

                            if invoices.project_id:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search([('goods_transfer_bool','=',True),('to_project_id','=',invoices.project_id.id),
                                                                                              ('rece_date','<=',invoices.to_date),('rece_date','>=',invoices.from_date),('state','=','recieve')])
                            else:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', True),
                                     ('rece_date', '<=', date_to), ('rece_date', '>=', date_from),('state','=','recieve')])

                            for goods_transfer in goods_transfer_note_in:
                                for line in goods_transfer.transfer_list_ids:
                                    if line.item_id.id == product.id:
                                        total+=line.qty

                            if invoices.project_id:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '>=', date_from),('date', '<=', date_to), ("project_id", "=", invoices.project_id.id)
                                        , ('is_receive', '=', True)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '>=', date_from), ('date', '<=', date_to),('is_receive', '=', True)])
                            for material in material_issue_slip:
                                for line in material.material_issue_slip_lines_ids:
                                    if line.item_id.id == product.id:
                                        total += line.req_qty
                            book_balance += total
                            total_during_rec+=total
                            worksheet.write('E%s' % (new_row), total,regular)
                            if invoices.project_id:
                                goods_recieve_report = self.env['goods.recieve.report'].search(
                                    [('Date', '<=', invoices.to_date),('project_id','=',invoices.project_id.id)
                                     ])
                            else:
                                goods_recieve_report = self.env['goods.recieve.report'].search(
                                    [('Date', '<=', date_to),
                                     ])

                            total = 0
                            for good_recieve in goods_recieve_report:
                                for line in good_recieve.goods_recieve_report_line_ids:
                                    if line.item_id.id == product.id:
                                        total += line.quantity_accept

                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', True),('to_project_id','=',invoices.project_id.id),
                                 ('rece_date', '<=', invoices.to_date), ('state', '=', 'recieve')])

                            for goods_transfer in goods_transfer_note_in:
                                for line in goods_transfer.transfer_list_ids:
                                    if line.item_id.id == product.id:
                                        total += line.qty


                            if invoices.project_id:
                                stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_to),('state','=','done'),
                                                                                      ('location_id', '=',
                                                                                       invoices.project_id.location_id.id)])
                            else:
                                stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_to),('state','=','done')])
                            for inv in stock_inventory:
                                for inv_line in inv.line_ids:
                                    if inv_line.product_id.id == product.id:
                                        total += inv_line.product_qty
                            total_cum_reci +=total
                            worksheet.write('F%s' % (new_row), total,regular)
                            total = 0
                            if invoices.project_id:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),
                                     ('date', '<=', date_to),('date', '>=', date_from), ('state', '=', 'transfer')])
                            else:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False),
                                     ('date', '<=', date_to),('date', '>=', date_from),('state', '=', 'transfer')])

                            for goods_transfer in goods_transfer_note_in:
                                for line in goods_transfer.transfer_list_ids:
                                    if line.item_id.id == product.id:
                                        total += line.qty
                            total_cum_tran +=total
                            book_balance -= total
                            worksheet.write('G%s' % (new_row), total,regular)
                            total = 0
                            if invoices.project_id:
                                material_issue_slip=self.env['material.issue.slip'].search([('date', '<=', date_to), ('date', '>=', date_from),("project_id","=",invoices.project_id.id),('is_receive','=',False)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '<=', date_to), ('date', '>=', date_from),('is_receive','=',False)])
                            for material in material_issue_slip:
                                for line in material.material_issue_slip_lines_ids:
                                    if line.item_id.id == product.id:
                                        total +=line.req_qty


                            book_balance -= total
                            total_during_mont +=total
                            worksheet.write('H%s'%(new_row),total,regular)
                            total = 0
                            if invoices.project_id:
                                material_issue_slip=self.env['material.issue.slip'].search([('date', '<=', date_to), ("project_id","=",invoices.project_id.id),('is_receive','=',False)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '<=', date_to),('is_receive','=',False)])
                            for material in material_issue_slip:
                                for line in material.material_issue_slip_lines_ids:
                                    if line.item_id.id == product.id:
                                        total +=line.req_qty


                            if invoices.project_id:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),
                                     ('date', '<=', date_to), ('state', '=', 'transfer')])
                            else:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False),
                                     ('date', '<=', date_to), ('state', '=', 'transfer')])

                            for goods_transfer in goods_transfer_note_in:
                                for line in goods_transfer.transfer_list_ids:
                                    if line.item_id.id == product.id:
                                        total += line.qty

                            if invoices.project_id:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '>=', date_from), ('date', '<=', date_to),
                                     ("project_id", "=", invoices.project_id.id)
                                        , ('is_receive', '=', True)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '>=', date_from), ('date', '<=', date_to), ('is_receive', '=', True)])
                            for material in material_issue_slip:
                                for line in material.material_issue_slip_lines_ids:
                                    if line.item_id.id == product.id:
                                        total -= line.req_qty
                            total_cum_issue += total
                            worksheet.write('I%s' % (new_row), total, regular)

                            total_book_balance +=book_balance
                            worksheet.write('J%s' % (new_row), round(book_balance,4), regular)
                            count +=1
                            new_row +=1
BillReportXlsx('report.custom.stock_report.xlsx','report.location.stock')

class StockLocation(models.Model):
    _inherit='stock.location'

    @api.model
    def get_products(self, location_id):
        start_date = self._context['start_date']
        end_date = self._context['end_date']
        category = self._context['category']


        if category:
            product_recs = self.env['product.product'].search([('type','=','product')]).filtered(lambda r: r.categ_id.id == category).sorted(lambda r: r.categ_id)
        else:
            product_recs = self.env['product.product'].search([('type','=','product')]).sorted(lambda r: r.categ_id.name)
        for line in product_recs:
            temp_in = 0.0
            temp_out = 0.0
            line.temp_remain = 0.0
#             if line.balance!=0.0:
            move_lines = self.env['stock.move'].search([('location_id','=',location_id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
            for moves in move_lines:
                temp_out+=moves.product_uom_qty

            move_lines = self.env['stock.move'].search([('location_dest_id','=',location_id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
            for moves in move_lines:
                temp_in+=moves.product_uom_qty
            line.temp_remain = temp_in - temp_out


        return product_recs


class report_location_stock_daily(models.TransientModel):

    _name='report.location.stock.daily'


    #date=fields.Date('Date From')
    #date=fields.Date('Date To')
    location_id = fields.Many2one('stock.location', 'Location')
    company_id =fields.Many2one('res.company','Company')
    date_today = fields.Date('Date',required = True)
    category = fields.Many2one('product.category')
    project_id = fields.Many2one('project.project')
    #product_id = fields.Many2one('product.product')
    defaults = {
        'date_today': datetime.now(),
        #'from_date': '2017-04-01',
        #'to_date': fields.Date.today(),
    }
    @api.multi
    def generate_xls_report_daily(self):  
        
        return self.env["report"].get_action(self, report_name='custom.stock_report_daily.xlsx')



