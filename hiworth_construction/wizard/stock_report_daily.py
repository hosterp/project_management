from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz


class BillReportXlsxDaily(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")


        
        boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'font': 'height 10'})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True})
        rightb = workbook.add_format({'align': 'right', 'bold': True})
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
        worksheet.set_column('B:B', 25)
        worksheet.set_column('D:S', 13)
        
        worksheet.merge_range('A1:S1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:S2', invoices.project_id.name or 'All Project', boldc)
        worksheet.merge_range('A3:S3', 'Daily material stock status as of ' + datetime.strptime(invoices.date_today,"%Y-%m-%d").strftime("%d-%m-%Y"), boldc)
        worksheet.merge_range('A4:A5', 'Sl.NO', regular)
        worksheet.merge_range('B4:B5', 'Description', regular)
        worksheet.merge_range('C4:C5', 'unit', regular)
        # worksheet.merge_range('D4:F5','Receipt',regular)
        worksheet.merge_range('D4:F4', 'Receipt', regular)
        worksheet.write('D5', 'Opening Balance')
        # worksheet.merge_range('A4:O5','',regular)
        worksheet.write('E5', 'Todays Receipt', regular)
        worksheet.write('F5', 'Cum Receipt', regular)
        worksheet.merge_range('G4:I4', 'Issues', regular)
        # worksheet.write('G5','Balance',regular)
        # worksheet.merge_range('H4:J4','Physical stock',regular)
        worksheet.write('G5', 'Transfer', regular)
        worksheet.write('H5', 'Todays Issue', regular)
        worksheet.write('I5', 'Cum:issue', regular)
        worksheet.merge_range('J4:L4', 'Book Balance', regular)
        worksheet.write('J5', 'Book Balance', regular)
        worksheet.write('K5', 'Physical Stock', regular)
        worksheet.write('L5', 'Variation', regular)
        worksheet.merge_range('M4:N4', 'Cons:as per DPR', regular)
        worksheet.write('M5', 'Todays', regular)
        worksheet.write('N5', 'Cumulative', regular)
        worksheet.merge_range('O4:Q4', 'Diff:Actual-DPR', regular)
        worksheet.write('O5', '8 & 13', regular)
        worksheet.write('P5', '9 & 14', regular)
        worksheet.write('Q5', '-', regular)
        worksheet.merge_range('R4:S4', 'Remarks/Can be spared', regular)
        resource_list = self.env['stock.history'].search([('location_id','=',invoices.project_id.location_id.id)])
        product_list = []
        for res in resource_list:
            product_list.append(res.product_id.id)

        product_list = self.env['product.product'].search([]).ids
        count = 1
        for rec in invoices:
            date_today2 = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
            date_today = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
            actual_date = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime("%d-%m-%Y")
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Kolkata')
            # from_zone = tz.tzutc()
            # to_zone = tz.tzlocal()
            utc = datetime.strptime(date_today2, '%Y-%m-%d %H:%M:%S')
            utc = utc.replace(tzinfo=from_zone)
            central = utc.astimezone(from_zone)
            #
            # date_today = utcc.replace(tzinfo=from_zone)
            date_today2 = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S').strftime(
                "%Y-%m-%d %H:%M:%S")
            utcc = datetime.strptime(date_today, '%Y-%m-%d %H:%M:%S')
            date_today = utcc.replace(tzinfo=from_zone)
            date_today = datetime.strptime(date_today.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S').strftime(
                "%Y-%m-%d %H:%M:%S")

            if rec.category:

                product_id = self.env['product.product'].search([("categ_id", "=", rec.category.id),('id','in',product_list)])

                worksheet.write('A%s' % (new_row), rec.category.name, regular)
                new_row += 1
                # product_id = self.env['product.product'].search([("categ_id", "=", rec.category.id)])
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
                    # date_today = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
                    # date_today2 = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")

                    if invoices.project_id:
                        goods_recieve_report = self.env['goods.recieve.report'].search(
                            [('Date', '<=', invoices.date_today), ('project_id', '=', invoices.project_id.id)
                             ])
                    else:
                        goods_recieve_report = self.env['goods.recieve.report'].search(
                            [('Date', '<=', invoices.date_today)
                             ])

                    total = 0

                    for good_recieve in goods_recieve_report:
                        for line in good_recieve.goods_recieve_report_line_ids:

                            if line.item_id.id == product.id:

                                total += line.quantity_accept

                    goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                        [('goods_transfer_bool', '=', True), ('to_project_id', '=', invoices.project_id.id),
                         ('rece_date', '<=', invoices.date_today), ('state', '=', 'recieve')])

                    for goods_transfer in goods_transfer_note_in:
                        for line in goods_transfer.transfer_list_ids:

                            if line.item_id.id == product.id:
                                total += line.qty

                    if invoices.project_id:
                        stock_inventory = self.env['stock.inventory'].search(
                            [('date', '<=', date_today2), ('state', '=', 'done'),
                             ('location_id', '=',
                              invoices.project_id.location_id.id)])
                    else:
                        stock_inventory = self.env['stock.inventory'].search(
                            [('date', '<=', date_today2), ('state', '=', 'done')])
                    for inv in stock_inventory:
                        for inv_line in inv.line_ids:
                            if inv_line.product_id.id == product.id:
                                total += inv_line.product_qty
                    total_cum_reci += total

                    if total_cum_reci !=0:
                        total_cum_reci = 0
                        worksheet.write('A%s' % (new_row), count, regular)
                        worksheet.write('B%s' % (new_row), product.name, regular)
                        worksheet.write('C%s' % (new_row), product.uom_id.name, regular)


                        total = 0
                        if invoices.project_id:
                            location_id = invoices.project_id.location_id.id
                            inventory = self.env['stock.history'].search(
                                [("product_id", "=", product.id), ("date", "<", date_today),
                                 ('location_id', '=', location_id)])

                        else:
                            location = self.env['stock.location'].search([('usage', '=', 'internal')])
                            inventory = self.env['stock.history'].search(
                                [("product_id", "=", product.id), ("date", "<", date_today),
                                 ('location_id', 'in', location.ids)])

                        # new_row+=1

                        for inv in inventory:
                            total += sum(inv.mapped('quantity'))
                        book_balance += total
                        total_opening += total
                        worksheet.write('D%s' % (new_row), round(total,4), regular)

                        if invoices.project_id:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '=', invoices.date_today),
                                 ('project_id', '=', invoices.project_id.id)])



                        else:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '=', invoices.date_today)
                                 ])

                        total = 0
                        for good_recieve in goods_recieve_report:
                            for line in good_recieve.goods_recieve_report_line_ids:
                                if line.item_id.id == product.id:
                                    total += line.quantity_accept

                        if invoices.project_id:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', True), ('to_project_id', '=', invoices.project_id.id),
                                 ('rece_date', '=', invoices.date_today), ('state', '=', 'recieve')])
                        else:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', True),
                                 ('rece_date', '=', invoices.date_today), ('state', '=', 'recieve')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty


                        if invoices.project_id:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_today2),('date', '>=', date_today),
                                 ("project_id", "=", invoices.project_id.id),('is_receive','=',True)])
                        else:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_today2),('date', '>=', date_today)])
                        for material in material_issue_slip:
                            for line in material.material_issue_slip_lines_ids:
                                if line.item_id.id == product.id:
                                    total += line.req_qty

                        book_balance += total
                        total_during_rec += total

                        worksheet.write('E%s' % (new_row), total, regular)
                        if invoices.project_id:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '<=', invoices.date_today), ('project_id', '=', invoices.project_id.id)
                                 ])
                        else:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '<=', invoices.date_today)
                                 ])

                        total = 0
                        for good_recieve in goods_recieve_report:
                            for line in good_recieve.goods_recieve_report_line_ids:
                                if line.item_id.id == product.id:
                                    total += line.quantity_accept

                        goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                            [('goods_transfer_bool', '=', True),('to_project_id','=',invoices.project_id.id),
                             ('rece_date', '<=', invoices.date_today), ('state', '=', 'recieve')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty



                        if invoices.project_id:
                            stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_today2),('state','=','done'),
                                                                                  ('location_id', '=',
                                                                                   invoices.project_id.location_id.id)])
                        else:
                            stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_today2),('state','=','done')])
                        for inv in stock_inventory:
                            for inv_line in inv.line_ids:
                                if inv_line.product_id.id == product.id:
                                    total += inv_line.product_qty

                        total_cum_reci += total
                        worksheet.write('F%s' % (new_row), total, regular)
                        total = 0
                        if invoices.project_id:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),
                                 ('date', '>=', date_today),('date','<=',date_today2), ('state', '=', 'transfer')])
                        else:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False),
                                 ('date', '>=', date_today), ('date','<=',date_today2),('state', '=', 'transfer')])

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
                                [('date', '<=', date_today2),('date', '>=', date_today),('is_receive','=',False),
                                 ("project_id", "=", invoices.project_id.id)])
                        else:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_today2),('date', '>=', date_today),('is_receive','=',False)])
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
                                [('date', '<=', date_today2), ("project_id", "=", invoices.project_id.id),('is_receive','=',False)])
                        else:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '<=', date_today2),('is_receive','=',False)])
                        for material in material_issue_slip:
                            for line in material.material_issue_slip_lines_ids:
                                if line.item_id.id == product.id:
                                    total += line.req_qty

                        if invoices.project_id:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),
                                  ('date', '<=', date_today2), ('state', '=', 'transfer')])
                        else:
                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', False),
                                ('date', '<=', date_today2), ('state', '=', 'transfer')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty

                        if invoices.project_id:
                            material_issue_slip = self.env['material.issue.slip'].search(
                                [('date', '>=', date_today), ('date', '<=', date_today2),
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
                product_categ = self.env['product.category'].search([('id','in',categ_list)])


                for product_cate in product_categ:
                    # date_today2 = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
                    worksheet.write('A%s' % (new_row), product_cate.name, regular)
                    new_row += 1
                    product_id = self.env['product.product'].search([("categ_id", "=", product_cate.id),('id','in',product_list)])
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
                                [('Date', '<=', invoices.date_today), ('project_id', '=', invoices.project_id.id)
                                 ])
                        else:
                            goods_recieve_report = self.env['goods.recieve.report'].search(
                                [('Date', '<=', date_today2)
                                 ])

                        total = 0
                        for good_recieve in goods_recieve_report:
                            for line in good_recieve.goods_recieve_report_line_ids:
                                if line.item_id.id == product.id:
                                    total += line.quantity_accept

                        goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                            [('goods_transfer_bool', '=', True),('to_project_id','=',invoices.project_id.id),
                             ('rece_date', '<=', invoices.date_today), ('state', '=', 'recieve')])

                        for goods_transfer in goods_transfer_note_in:
                            for line in goods_transfer.transfer_list_ids:
                                if line.item_id.id == product.id:
                                    total += line.qty



                        if invoices.project_id:
                            stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_today2),('state','=','done'),
                                                                                  ('location_id', '=',
                                                                                   invoices.project_id.location_id.id)])
                        else:
                            stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_today2),('state','=','done')])
                        for inv in stock_inventory:
                            for inv_line in inv.line_ids:
                                if inv_line.product_id.id == product.id:
                                    total += inv_line.product_qty
                        total_cum_reci += total

                        if total_cum_reci !=0:
                            worksheet.write('A%s' % (new_row), count, regular)
                            worksheet.write('B%s' % (new_row), product.name, regular)
                            worksheet.write('C%s' % (new_row), product.uom_id.name, regular)

                            # date_today = datetime.strptime(invoices.date_today, "%Y-%m-%d").strftime(
                            #     "%Y-%m-%d 00:00:00")


                            total_cum_reci = 0
                            total = 0
                            if invoices.project_id:
                                location_id = invoices.project_id.location_id.id
                                inventory = self.env['stock.history'].search(
                                    [("product_id", "=", product.id), ("date", "<", date_today),
                                     ('location_id', '=', location_id)])
                            else:
                                location = self.env['stock.location'].search([('usage', '=', 'internal')])
                                inventory = self.env['stock.history'].search(
                                    [("product_id", "=", product.id), ("date", "<", date_today),
                                     ('location_id', 'in', location.ids)])

                            # new_row+=1
                            for inv in inventory:
                                total += sum(inv.mapped('quantity'))
                            book_balance += total
                            total_opening += total
                            worksheet.write('D%s' % (new_row), round(total,4), regular)

                            if invoices.project_id:
                                goods_recieve_report = self.env['goods.recieve.report'].search(
                                    [('Date', '=', invoices.date_today),
                                     ('project_id', '=', invoices.project_id.id)])


                            else:
                                goods_recieve_report = self.env['goods.recieve.report'].search(
                                    [('Date', '>=', date_today),('Date', '<=', date_today2),
                                     ])

                            total = 0
                            for good_recieve in goods_recieve_report:
                                for line in good_recieve.goods_recieve_report_line_ids:
                                    if line.item_id.id == product.id:




                                        total += line.quantity_accept

                            if invoices.project_id:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', True), ('to_project_id', '=', invoices.project_id.id),
                                     ('rece_date', '=', invoices.date_today), ('state', '=', 'recieve')])
                            else:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', True),
                                     ('rece_date', '>=', date_today), ('rece_date', '<=', date_today2), ('state', '=', 'recieve')])

                            for goods_transfer in goods_transfer_note_in:
                                for line in goods_transfer.transfer_list_ids:
                                    if line.item_id.id == product.id:
                                        total += line.qty

                            if invoices.project_id:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '>=', date_today),('date', '<=', date_today2), ("project_id", "=", invoices.project_id.id)
                                        , ('is_receive', '=', True)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '>=', date_today), ('date', '<=', date_today2),('is_receive', '=', True)])
                            for material in material_issue_slip:
                                for line in material.material_issue_slip_lines_ids:
                                    if line.item_id.id == product.id:
                                        total += line.req_qty


                            book_balance += total
                            total_during_rec += total
                            worksheet.write('E%s' % (new_row), total, regular)
                            if invoices.project_id:
                                goods_recieve_report = self.env['goods.recieve.report'].search(
                                    [('Date', '<=', invoices.date_today), ('project_id', '=', invoices.project_id.id)
                                     ])
                            else:
                                goods_recieve_report = self.env['goods.recieve.report'].search(
                                    [('Date', '<=', date_today2),
                                     ])

                            total = 0
                            for good_recieve in goods_recieve_report:
                                for line in good_recieve.goods_recieve_report_line_ids:
                                    if line.item_id.id == product.id:
                                        total += line.quantity_accept

                            goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                [('goods_transfer_bool', '=', True),('to_project_id','=',invoices.project_id.id),
                                 ('rece_date', '<=', invoices.date_today), ('state', '=', 'recieve')])

                            for goods_transfer in goods_transfer_note_in:
                                for line in goods_transfer.transfer_list_ids:
                                    if line.item_id.id == product.id:
                                        total += line.qty



                            if invoices.project_id:
                                stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_today2),('state','=','done'),
                                                                                      ('location_id', '=',
                                                                                       invoices.project_id.location_id.id)])
                            else:
                                stock_inventory = self.env['stock.inventory'].search([('date', '<=', date_today2),('state','=','done')])
                            for inv in stock_inventory:
                                for inv_line in inv.line_ids:
                                    if inv_line.product_id.id == product.id:
                                        total += inv_line.product_qty
                            total_cum_reci += total
                            worksheet.write('F%s' % (new_row), total, regular)
                            total = 0
                            if invoices.project_id:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),
                                     ('date', '>=', date_today),('date', '<=', date_today2), ('state', '=', 'transfer')])
                            else:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False),
                                     ('date', '>=', date_today), ('date', '<=', date_today2), ('state', '=', 'transfer')])

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
                                    [('date', '>=', date_today),('date', '<=', date_today2),('is_receive','=',False),
                                     ("project_id", "=", invoices.project_id.id)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '>=', date_today),('date', '<=', date_today2),('is_receive','=',False)])
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
                                    [('date', '<=', date_today2), ("project_id", "=", invoices.project_id.id),('is_receive','=',False)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '<=', date_today2),('is_receive','=',False)])
                            for material in material_issue_slip:
                                for line in material.material_issue_slip_lines_ids:
                                    if line.item_id.id == product.id:
                                        total += line.req_qty

                            if invoices.project_id:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False), ('project_id', '=', invoices.project_id.id),
                                     ('date', '<=', date_today2), ('state', '=', 'transfer')])
                            else:
                                goods_transfer_note_in = self.env['goods.transfer.note.in'].search(
                                    [('goods_transfer_bool', '=', False),
                                     ('date', '<=', date_today2), ('state', '=', 'transfer')])

                            for goods_transfer in goods_transfer_note_in:
                                for line in goods_transfer.transfer_list_ids:
                                    if line.item_id.id == product.id:
                                        total += line.qty

                            if invoices.project_id:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [ ('date', '<=', date_today2),
                                     ("project_id", "=", invoices.project_id.id)
                                        , ('is_receive', '=', True)])
                            else:
                                material_issue_slip = self.env['material.issue.slip'].search(
                                    [('date', '<=', date_today2), ('is_receive', '=', True)])
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

BillReportXlsxDaily('report.custom.stock_report_daily.xlsx', 'report.location.stock.daily')