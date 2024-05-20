from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz


class CleanerBataReport(models.TransientModel):
    _name = 'cleaner.bata.report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', 'Company')


    project_id = fields.Many2one('project.project')
    cleaner_id = fields.Many2one('hr.employee')
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
                              ('December', 'December')], 'Month',)
    _defaults = {
        'date_today': datetime.today(),
        # 'from_date': '2017-04-01',
        # 'to_date': fields.Date.today(),
    }

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 ' + self.month + ' ' + str(datetime.now().year)
            
            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)
            
            self.to_date = end_date


    @api.multi
    def get_details(self):
        for rec in self:
            date_from = datetime.strptime(rec.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(rec.to_date, "%Y-%m-%d")

            if rec.cleaner_id:

                driver_daily = self.env['driver.daily.statement'].search(
                    [('date', '>=', date_from), ('date', '<=', date_to), ('cleaners_name', '=', rec.cleaner_id.id)])
            else:
                driver_daily = self.env['driver.daily.statement'].search(
                    [('date', '>=', date_from), ('date', '<=', date_to),('cleaners_name','!=',False)])

            return driver_daily



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
            'report_name': 'hiworth_construction.report_cleaner_bata_report_wise',
            'datas': datas,
            #             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'category': self.category.id},
            'report_type': 'qweb-html',
        }

    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='cleaner_bata_report.xlsx')


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

            count = 1
            for rec in invoices:
                date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
                date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")

                if rec.cleaner_id:
                    vehicle_row = 0

                    driver_daily = self.env['driver.daily.statement'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to), ('cleaners_name', '=', rec.cleaner_id.id),
                         ], order='vehicle_no asc')

                    if len(driver_daily) != 0:
                        worksheet.merge_range('A%s:F%s' % (new_row, new_row), rec.driver_id.name, boldc)
                        vehicle_row = new_row

                        new_row += 1
                        worksheet.write('A%s' % (new_row), 'Date', bold)
                        worksheet.write('B%s' % (new_row), 'Vehicle', bold)
                        worksheet.write('C%s' % (new_row), 'Total KM', bold)
                        worksheet.write('D%s' % (new_row), 'Time IN', bold)
                        worksheet.write('E%s' % (new_row), 'Time OUT', bold)
                        worksheet.write('F%s' % (new_row), 'Site', bold)
                        worksheet.write('G%s' % (new_row), 'From', bold)
                        worksheet.write('H%s' % (new_row), 'To', bold)
                        worksheet.write('I%s' % (new_row), 'Trip ', bold)
                        worksheet.write('J%s' % (new_row), 'Rent', bold)
                        worksheet.write('K%s' % (new_row), 'OT', bold)

                        worksheet.write('L%s' % (new_row), 'OT Amount', bold)
                        worksheet.write('M%s' % (new_row), 'Food Allowance', bold)
                        worksheet.write('N%s' % (new_row), 'Subtotal', bold)
                        worksheet.write('O%s' % (new_row), 'Deposit/KM', bold)
                        worksheet.write('P%s' % (new_row), 'Total', bold)
                        spec = new_row
                        new_row += 1
                        driver_subtotal = 0
                        driver_deposit = 0
                        driver_total = 0
                        total_cum_tran = 0
                        total_during_mont = 0
                        total_cum_issue = 0
                        total_book_balance = 0

                        projects = self.env['project.project'].search([])
                        for pro in projects:
                            first_row = new_row
                            pro_total = 0
                            f_driver_daily = self.env['driver.daily.statement'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to),
                                 ('cleaners_name', '=', rec.cleaner_id.id),
                                 ('project_id', '=', pro.id)])
                            for driver in f_driver_daily:
                                sl_count = 0
                                total = 0
                                worksheet.merge_range('G%s:O%s' % (vehicle_row, vehicle_row),
                                                      driver.vehicle_no.name, boldc)
                                worksheet.write('M%s' % (new_row), driver.deposit, regular)

                                if len(driver.driver_stmt_line) == 0:
                                    worksheet.write('A%s' % (new_row),
                                                    datetime.strptime(driver.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                                                    regular)
                                    worksheet.write('B%s' % (new_row), driver.vehicle_no.name, regular)
                                    worksheet.write('C%s' % (new_row), driver.running_km, regular)
                                    if driver.start_time:
                                        from_zone = tz.gettz('UTC')
                                        to_zone = tz.gettz('Asia/Kolkata')
                                        # from_zone = tz.tzutc()
                                        # to_zone = tz.tzlocal()
                                        utc = datetime.strptime(driver.start_time, '%Y-%m-%d %H:%M:%S')
                                        utc = utc.replace(tzinfo=from_zone)
                                        central = utc.astimezone(to_zone)
                                        central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    '%Y-%m-%d %H:%M:%S').strftime(
                                            "%d-%m-%Y %H:%M:%S")

                                        worksheet.write('D%s' % (new_row), central, regular)
                                    if driver.end_time:
                                        utc = datetime.strptime(driver.end_time, '%Y-%m-%d %H:%M:%S')
                                        utc = utc.replace(tzinfo=from_zone)
                                        central = utc.astimezone(to_zone)
                                        central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    '%Y-%m-%d %H:%M:%S').strftime(
                                            "%d-%m-%Y %H:%M:%S")
                                        worksheet.write('E%s' % (new_row), central, regular)
                                    if first_row == new_row:
                                        worksheet.write('F%s' % (new_row), driver.project_id.name, regular)
                                    else:
                                        worksheet.merge_range('F%s:F%s' % (first_row, new_row),
                                                              driver.project_id.name, regular)
                                    worksheet.write('G%s' % (new_row), '', regular)
                                    worksheet.write('H%s' % (new_row), '', regular)

                                    worksheet.write('I%s' % (new_row), 1, regular)

                                    worksheet.write('J%s' % (new_row), driver.cleaner_bata, regular)

                                    worksheet.write('K%s' % (new_row), 0, regular)

                                    total += driver.cleaner_bata * 1
                                    worksheet.write('L%s' % (new_row), 0, regular)
                                    worksheet.write('N%s' % (new_row), total, regular)
                                    driver_subtotal += total
                                    total += 0
                                    driver_deposit += 0
                                    worksheet.write('O%s' % (new_row), 0, regular)

                                    pro_total += total
                                    if first_row == new_row:
                                        worksheet.write("P%s" % (new_row), pro_total, regular)
                                    else:
                                        worksheet.merge_range("P%s:P%s" % (first_row, new_row), pro_total, regular)
                                    driver_total += total
                                    count += 1
                                    new_row += 1
                                    # worksheet.write('R%s' % (new_row), driver.remark, regular)
                            driver_stmt_line = self.env['driver.daily.statement.line'].search(
                                [('line_id', 'in', driver_daily.ids), ('project_id', '=', pro.id)],
                                order='invoice_date desc,vehicle_no asc')
                            sl_count = 0
                            date = invoices.to_date
                            # first_row = new_row
                            for driver_line in driver_stmt_line:
                                worksheet.merge_range('A%s:F%s' % (spec - 1, spec - 1),
                                                      driver_line.line_id.cleaners_name.name, bold)
                                worksheet.merge_range('G%s:O%s' % (spec - 1, spec - 1),
                                                      driver_line.line_id.vehicle_no.name,
                                                      bold)
                                total = 0
                                if driver_line.invoice_date != date:
                                    worksheet.write('M%s' % (new_row), driver_line.line_id.deposit, regular)


                                    date = driver_line.invoice_date
                                # worksheet.write('A%s' % (new_row), count, regular)

                                worksheet.write('A%s' % (new_row),
                                                datetime.strptime(driver_line.line_id.date, "%Y-%m-%d").strftime(
                                                    "%d-%m-%Y"),
                                                regular)
                                # worksheet.write('C%s' % (new_row), driver.remark, regular)

                                # worksheet.write('F%s' % (new_row), driver.start_km, regular)
                                # worksheet.write('G%s' % (new_row), driver.actual_close_km, regular)
                                worksheet.write('B%s' % (new_row), driver_line.line_id.vehicle_no.name, regular)
                                worksheet.write('C%s' % (new_row), driver_line.line_id.running_km, regular)

                                if driver_line.line_id.start_time:
                                    from_zone = tz.gettz('UTC')
                                    to_zone = tz.gettz('Asia/Kolkata')
                                    # from_zone = tz.tzutc()
                                    # to_zone = tz.tzlocal()
                                    utc = datetime.strptime(driver_line.line_id.start_time, '%Y-%m-%d %H:%M:%S')
                                    utc = utc.replace(tzinfo=from_zone)
                                    central = utc.astimezone(to_zone)
                                    central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                '%Y-%m-%d %H:%M:%S').strftime(
                                        "%d-%m-%Y %H:%M:%S")

                                    worksheet.write('D%s' % (new_row), central, regular)
                                if driver_line.line_id.end_time:
                                    from_zone = tz.gettz('UTC')
                                    to_zone = tz.gettz('Asia/Kolkata')
                                    # from_zone = tz.tzutc()
                                    # to_zone = tz.tzlocal()
                                    utc = datetime.strptime(driver_line.line_id.end_time, '%Y-%m-%d %H:%M:%S')
                                    utc = utc.replace(tzinfo=from_zone)
                                    central = utc.astimezone(to_zone)
                                    central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                '%Y-%m-%d %H:%M:%S').strftime(
                                        "%d-%m-%Y %H:%M:%S")

                                    worksheet.write('E%s' % (new_row), central, regular)
                                if first_row != new_row:
                                    worksheet.merge_range('F%s:F%s' % (first_row, new_row),
                                                          driver_line.project_id.name,
                                                          regular)
                                else:
                                    worksheet.write("F%s" % (new_row), driver_line.project_id.name, regular)
                                worksheet.write('G%s' % (new_row),
                                                driver_line.from_id2 and driver_line.from_id2.name or driver_line.location_id.name,
                                                regular)
                                worksheet.write('H%s' % (new_row), driver_line.to_id2.name, regular)
                                worksheet.write('I%s' % (new_row), 1, regular)

                                worksheet.write('J%s' % (new_row), driver_line.bata_cleaner, regular)

                                worksheet.write('K%s' % (new_row), 0, regular)

                                worksheet.write('L%s' % (new_row),
                                               0,
                                                regular)

                                total += driver_line.bata_cleaner * 1

                                worksheet.write('N%s' % (new_row), total, regular)
                                driver_subtotal += total
                                worksheet.write('O%s' % (new_row), 0, regular)


                                pro_total += total
                                if first_row != new_row:
                                    worksheet.merge_range('P%s:P%s' % (first_row, new_row), pro_total, regular)
                                else:
                                    worksheet.write("P%s" % (new_row), pro_total, regular)
                                driver_total += total
                                count += 1
                                new_row += 1
                    if len(f_driver_daily) != 0:
                        worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Total", boldc)
                        worksheet.write('N%s' % (new_row), driver_subtotal, boldc)
                        worksheet.write('O%s' % (new_row), driver_deposit, boldc)
                        worksheet.write('P%s' % (new_row), driver_total, boldc)
                        new_row += 2

                else:
                    driver_list = []
                    driver_name = []
                    for category in self.env['vehicle.category.type'].search([], order='priority asc'):

                        for vehicle in self.env['fleet.vehicle'].search([('vehicle_categ_id', '=', category.id)],
                                                                        order='name asc'):

                            for driver in self.env['hr.employee'].search(
                                    [('user_category', 'in', ['tppdriver', 'tpoperators_helpers']),
                                     ('cost_type', 'in', ['wages', 'salary_bata'])]):
                                driver_daily = self.env['driver.daily.statement'].search(
                                    [('date', '>=', date_from), ('date', '<=', date_to),
                                     ('vehicle_no', '=', vehicle.id), ('cleaners_name', '=', driver.id)])
                                if driver_daily:
                                    if driver not in driver_list:
                                        driver_list.append(driver)
                                    if driver.name not in driver_name:
                                        driver_name.append(driver)

                    for driver in driver_list:

                        vehicle_row = 0
                        driver_daily = self.env['driver.daily.statement'].search(
                            [('date', '>=', date_from), ('date', '<=', date_to), ('cleaners_name', '=', driver.id),
                             ], order='vehicle_no asc')
                        vehicle_row = new_row

                        if len(driver_daily) != 0:
                            worksheet.merge_range('A%s:F%s' % (new_row, new_row), driver.name, boldc)

                            new_row += 1
                            worksheet.write('A%s' % (new_row), 'Date', bold)
                            worksheet.write('B%s' % (new_row), 'Vehicle No', bold)
                            worksheet.write('C%s' % (new_row), 'Total KM', bold)
                            worksheet.write('D%s' % (new_row), 'Time IN', bold)
                            worksheet.write('E%s' % (new_row), 'Time OUT', bold)
                            worksheet.write('F%s' % (new_row), 'Site', bold)
                            worksheet.write('G%s' % (new_row), 'From', bold)
                            worksheet.write('H%s' % (new_row), 'To', bold)
                            worksheet.write('I%s' % (new_row), 'Trip ', bold)
                            worksheet.write('J%s' % (new_row), 'Rent', bold)
                            worksheet.write('K%s' % (new_row), 'OT', bold)

                            worksheet.write('L%s' % (new_row), 'OT Amount', bold)
                            worksheet.write('M%s' % (new_row), 'Food Allowance', bold)
                            worksheet.write('N%s' % (new_row), 'Subtotal', bold)
                            worksheet.write('O%s' % (new_row), 'Deposit/KM', bold)
                            worksheet.write('P%s' % (new_row), 'Total', bold)
                            spec = new_row
                            new_row += 1
                            driver_subtotal = 0
                            driver_deposit = 0
                            driver_total = 0
                            total_cum_tran = 0
                            total_during_mont = 0
                            total_cum_issue = 0
                            total_book_balance = 0

                            projects = self.env['project.project'].search([])
                            for pro in projects:
                                pro_total = 0
                                first_row = new_row
                                f_driver_daily = self.env['driver.daily.statement'].search(
                                    [('date', '>=', date_from), ('date', '<=', date_to),
                                     ('cleaners_name', '=', driver.id),
                                     ('project_id', '=', pro.id)], order='vehicle_no asc')
                                for driver_d in f_driver_daily:
                                    sl_count = 0
                                    total = 0
                                    worksheet.merge_range('G%s:O%s' % (vehicle_row, vehicle_row),
                                                          driver_d.vehicle_no.name, bold)
                                    worksheet.write('M%s' % (new_row), driver_d.deposit, regular)

                                    if len(driver_d.driver_stmt_line) == 0:
                                        worksheet.write('A%s' % (new_row),
                                                        datetime.strptime(driver_d.date, "%Y-%m-%d").strftime(
                                                            "%d-%m-%Y"),
                                                        regular)
                                        worksheet.write('B%s' % (new_row), driver_d.vehicle_no.name, regular)
                                        worksheet.write('C%s' % (new_row), driver_d.running_km, regular)
                                        if driver_d.start_time:
                                            from_zone = tz.gettz('UTC')
                                            to_zone = tz.gettz('Asia/Kolkata')
                                            # from_zone = tz.tzutc()
                                            # to_zone = tz.tzlocal()
                                            utc = datetime.strptime(driver_d.start_time, '%Y-%m-%d %H:%M:%S')
                                            utc = utc.replace(tzinfo=from_zone)
                                            central = utc.astimezone(to_zone)
                                            central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                        '%Y-%m-%d %H:%M:%S').strftime(
                                                "%d-%m-%Y %H:%M:%S")

                                            worksheet.write('D%s' % (new_row), central, regular)
                                        if driver_d.end_time:
                                            utc = datetime.strptime(driver_d.end_time, '%Y-%m-%d %H:%M:%S')
                                            utc = utc.replace(tzinfo=from_zone)
                                            central = utc.astimezone(to_zone)
                                            central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                        '%Y-%m-%d %H:%M:%S').strftime(
                                                "%d-%m-%Y %H:%M:%S")
                                            worksheet.write('E%s' % (new_row), central, regular)
                                        if first_row == new_row:
                                            worksheet.write('F%s' % (new_row), driver_d.project_id.name, regular)
                                        else:
                                            worksheet.merge_range('F%s:F%s' % (first_row, new_row),
                                                                  driver_d.project_id.name, regular)
                                        worksheet.write('G%s' % (new_row), '', regular)
                                        worksheet.write('H%s' % (new_row), '', regular)

                                        worksheet.write('I%s' % (new_row), 1, regular)

                                        worksheet.write('J%s' % (new_row), driver_d.cleaner_bata, regular)

                                        worksheet.write('K%s' % (new_row), 0, regular)

                                        total += driver_d.cleaner_bata * 1
                                        worksheet.write('L%s' % (new_row), 0,
                                                        regular)
                                        worksheet.write('N%s' % (new_row), total, regular)
                                        driver_subtotal += total
                                        total += 0
                                        driver_deposit += 0
                                        worksheet.write('O%s' % (new_row), 0, regular)
                                        pro_total += total
                                        if first_row == new_row:
                                            worksheet.write("P%s" % (new_row), pro_total, regular)
                                        else:
                                            worksheet.merge_range("P%s:P%s" % (first_row, new_row), pro_total,
                                                                  regular)
                                        driver_total += total
                                        count += 1
                                        new_row += 1
                                        # worksheet.write('R%s' % (new_row), driver.remark, regular)
                                driver_stmt_line = self.env['driver.daily.statement.line'].search(
                                    [('line_id', 'in', driver_daily.ids), ('project_id', '=', pro.id)],
                                    order='invoice_date desc')
                                sl_count = 0
                                date = invoices.to_date
                                # first_row = new_row
                                for driver_line in driver_stmt_line:

                                    total = 0
                                    if driver_line.invoice_date != date:
                                        worksheet.write('M%s' % (new_row), driver_line.line_id.deposit, regular)


                                        date = driver_line.invoice_date
                                    # worksheet.write('A%s' % (new_row), count, regular)

                                    worksheet.write('A%s' % (new_row),
                                                    datetime.strptime(driver_line.line_id.date,
                                                                      "%Y-%m-%d").strftime(
                                                        "%d-%m-%Y"),
                                                    regular)
                                    # worksheet.write('C%s' % (new_row), driver.remark, regular)

                                    # worksheet.write('F%s' % (new_row), driver.start_km, regular)
                                    # worksheet.write('G%s' % (new_row), driver.actual_close_km, regular)
                                    worksheet.write('B%s' % (new_row), driver_line.line_id.vehicle_no.name, regular)
                                    worksheet.write('C%s' % (new_row), driver_line.line_id.running_km, regular)

                                    if driver_line.line_id.start_time:
                                        from_zone = tz.gettz('UTC')
                                        to_zone = tz.gettz('Asia/Kolkata')
                                        # from_zone = tz.tzutc()
                                        # to_zone = tz.tzlocal()
                                        utc = datetime.strptime(driver_line.line_id.start_time, '%Y-%m-%d %H:%M:%S')
                                        utc = utc.replace(tzinfo=from_zone)
                                        central = utc.astimezone(to_zone)
                                        central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    '%Y-%m-%d %H:%M:%S').strftime(
                                            "%d-%m-%Y %H:%M:%S")

                                        worksheet.write('D%s' % (new_row), central, regular)
                                    if driver_line.line_id.end_time:
                                        from_zone = tz.gettz('UTC')
                                        to_zone = tz.gettz('Asia/Kolkata')
                                        # from_zone = tz.tzutc()
                                        # to_zone = tz.tzlocal()
                                        utc = datetime.strptime(driver_line.line_id.end_time, '%Y-%m-%d %H:%M:%S')
                                        utc = utc.replace(tzinfo=from_zone)
                                        central = utc.astimezone(to_zone)
                                        central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    '%Y-%m-%d %H:%M:%S').strftime(
                                            "%d-%m-%Y %H:%M:%S")

                                        worksheet.write('E%s' % (new_row), central, regular)
                                    if first_row != new_row:
                                        worksheet.merge_range('F%s:F%s' % (first_row, new_row),
                                                              driver_line.project_id.name,
                                                              regular)
                                    else:
                                        worksheet.write("F%s" % (new_row), driver_line.project_id.name, regular)
                                    worksheet.write('G%s' % (new_row),
                                                    driver_line.from_id2 and driver_line.from_id2.name or driver_line.location_id.name,
                                                    regular)
                                    worksheet.write('H%s' % (new_row), driver_line.to_id2.name, regular)
                                    worksheet.write('I%s' % (new_row), 1, regular)

                                    worksheet.write('J%s' % (new_row), driver_line.bata_cleaner, regular)

                                    worksheet.write('K%s' % (new_row), driver_line.line_id.ot_time, regular)

                                    worksheet.write('L%s' % (new_row),
                                                    0,
                                                    regular)

                                    total += driver_line.bata_cleaner * 1

                                    worksheet.write('N%s' % (new_row), total, regular)
                                    driver_subtotal += total
                                    worksheet.write('O%s' % (new_row), 0, regular)

                                    pro_total += total
                                    if first_row != new_row:
                                        worksheet.merge_range('P%s:P%s' % (first_row, new_row), pro_total, regular)
                                    else:
                                        worksheet.write("P%s" % (new_row), pro_total, regular)
                                    driver_total += total
                                    count += 1
                                    new_row += 1
                            if len(driver_daily) != 0:
                                worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Total", boldc)
                                worksheet.write('N%s' % (new_row), driver_subtotal, boldc)
                                worksheet.write('O%s' % (new_row), driver_deposit, boldc)
                                worksheet.write('P%s' % (new_row), driver_total, boldc)
                                new_row += 2

    BillReportXlsx('report.cleaner_bata_report.xlsx', 'cleaner.bata.report')





