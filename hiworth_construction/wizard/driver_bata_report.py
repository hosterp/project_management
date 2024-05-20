from openerp import fields, models, api
from datetime import datetime,timedelta
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone


class DriverBataReport(models.TransientModel):
    _name = 'driver.bata.report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', 'Company')
    date_wise = fields.Boolean("Date Wise",default=False)

    project_id = fields.Many2one('project.project')
    driver_id = fields.Many2one('hr.employee')
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

            if rec.driver_id:

                driver_daily = self.env['driver.daily.statement'].search(
                    [('date', '>=', date_from), ('date', '<=', date_to), ('driver_name', '=', rec.driver_id.id)])
            else:
                driver_daily = self.env['driver.daily.statement'].search(
                    [('date', '>=', date_from), ('date', '<=', date_to)])

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
            'report_name': 'hiworth_construction.report_bata_report_wise',
            'datas': datas,
            #             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'category': self.category.id},
            'report_type': 'qweb-html',
        }

    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='driver_bata_report.xlsx')


class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'size': 16,'text_wrap': True,'border':True})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10,'border':True})
        bold = workbook.add_format({'bold': True,'align': 'center', 'size': 14,'text_wrap': True,'border':True})
        rightb = workbook.add_format({'align': 'right', 'bold': True,'text_wrap': True,'border':True})
        right = workbook.add_format({'align': 'right'})
        regular = workbook.add_format({'align': 'center', 'bold': False, 'size': 12,'text_wrap': True,'border':True})
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



        # worksheet.merge_range('A4:O5','',regular)


        count = 1
        for rec in invoices:
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")
            worksheet.merge_range('A1:P1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)

            worksheet.merge_range('A2:P2', 'Details From %s To %s' % (date_from.strftime("%d-%m-%Y"),date_to.strftime("%d-%m-%Y")),boldc)

            f_driver_daily = []
            driver_total = 0
            driver_deposit = 0
            driver_subtotal = 0
            
            if not invoices.date_wise:
                if rec.driver_id:
                    vehicle_row =0

                    driver_daily = self.env['driver.daily.statement'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to), ('driver_name', '=', rec.driver_id.id),
                         ],order='vehicle_no asc')



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
                                [('date', '>=', date_from), ('date', '<=', date_to), ('driver_name', '=', rec.driver_id.id),
                                 ('project_id','=',pro.id)])
                            for driver in f_driver_daily:
                                sl_count = 0
                                total = 0
                                worksheet.merge_range('G%s:O%s' % (vehicle_row, vehicle_row), driver.vehicle_no.name, boldc)
                                worksheet.write('M%s' % (new_row), driver.deposit, regular)

                                if len(driver.driver_stmt_line)==0:
                                    worksheet.write('A%s' % (new_row), datetime.strptime(driver.date, "%Y-%m-%d").strftime("%d-%m-%Y"), regular)
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
                                        central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S').strftime(
                            "%d-%m-%Y %H:%M:%S")

                                        worksheet.write('D%s' % (new_row), central, regular)
                                    if driver.end_time:

                                        utc = datetime.strptime(driver.end_time, '%Y-%m-%d %H:%M:%S')
                                        utc = utc.replace(tzinfo=from_zone)
                                        central = utc.astimezone(to_zone)
                                        central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S').strftime(
                            "%d-%m-%Y %H:%M:%S")
                                        worksheet.write('E%s' % (new_row), central, regular)
                                    if first_row == new_row:
                                        worksheet.write('F%s' % (new_row), driver.project_id.name, regular)
                                    else:
                                        worksheet.merge_range('F%s:F%s' % (first_row,new_row), driver.project_id.name, regular)
                                    worksheet.write('G%s' % (new_row), '', regular)
                                    worksheet.write('H%s' % (new_row), '', regular)

                                    worksheet.write('I%s' % (new_row), 1, regular)

                                    worksheet.write('J%s' % (new_row), driver.driver_bata, regular)

                                    worksheet.write('K%s' % (new_row), driver.ot_time, regular)

                                    total += driver.driver_bata * 1 + (driver.ot_time * driver.ot_rate)
                                    worksheet.write('L%s' % (new_row),(driver.ot_time * driver.ot_rate), regular)
                                    worksheet.write('N%s' % (new_row),total, regular)
                                    driver_subtotal+=total
                                    total += 0
                                    driver_deposit += 0
                                    worksheet.write('O%s' % (new_row),0, regular)

                                    pro_total += total
                                    if first_row == new_row:
                                        worksheet.write("P%s" % (new_row), pro_total, regular)
                                    else:
                                        worksheet.merge_range("P%s:P%s" % (first_row,new_row), pro_total, regular)
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
                                                      driver_line.line_id.driver_name.name, bold)
                                worksheet.merge_range('G%s:O%s' % (spec - 1, spec - 1), driver_line.line_id.vehicle_no.name,
                                                      bold)
                                total = 0
                                if driver_line.invoice_date != date:
                                    worksheet.write('M%s' % (new_row), driver_line.line_id.deposit, regular)
                                    total += driver_line.line_id.deposit

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
                                    worksheet.merge_range('F%s:F%s' % (first_row, new_row), driver_line.project_id.name,
                                                          regular)
                                else:
                                    worksheet.write("F%s" % (new_row), driver_line.project_id.name, regular)
                                worksheet.write('G%s' % (new_row),
                                                driver_line.from_id2 and driver_line.from_id2.name or driver_line.location_id.name,
                                                regular)
                                worksheet.write('H%s' % (new_row), driver_line.to_id2.name, regular)
                                worksheet.write('I%s' % (new_row), 1, regular)

                                worksheet.write('J%s' % (new_row), driver_line.bata_driver, regular)

                                worksheet.write('K%s' % (new_row), driver_line.line_id.ot_time, regular)

                                worksheet.write('L%s' % (new_row),
                                                (driver_line.line_id.ot_time * driver_line.line_id.ot_rate), regular)

                                total += driver_line.bata_driver * 1 + (
                                            driver_line.line_id.ot_time * driver_line.line_id.ot_rate)

                                worksheet.write('N%s' % (new_row), total, regular)
                                driver_subtotal += total
                                worksheet.write('O%s' % (new_row), driver_line.km_deposit, regular)
                                total += driver_line.km_deposit
                                driver_deposit += driver_line.km_deposit
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
                        worksheet.write('N%s'%(new_row),driver_subtotal,boldc)
                        worksheet.write('O%s' % (new_row), driver_deposit, boldc)
                        worksheet.write('P%s' % (new_row), driver_total, boldc)
                        new_row += 2

                else:
                    driver_list =[]
                    driver_name = []
                    for category in self.env['vehicle.category.type'].search([], order='priority asc'):



                        for vehicle in self.env['fleet.vehicle'].search([('vehicle_categ_id', '=', category.id)],
                                                                        order='name asc'):

                            for driver in self.env['hr.employee'].search(
                                [('user_category', 'in', ['tppdriver', 'tpoperators_helpers']),
                                 ('cost_type', 'in', ['wages', 'salary_bata'])]):
                                driver_daily = self.env['driver.daily.statement'].search(
                                    [('date', '>=', date_from), ('date', '<=', date_to),
                                     ('vehicle_no', '=', vehicle.id), ('driver_name', '=', driver.id)])
                                if driver_daily:
                                    if driver not in driver_list:
                                        driver_list.append(driver)
                                    if driver.name not in driver_name:
                                        driver_name.append(driver)

                    for driver in driver_list:



                        vehicle_row = 0
                        driver_daily = self.env['driver.daily.statement'].search(
                            [('date', '>=', date_from), ('date', '<=', date_to), ('driver_name', '=', driver.id),
                            ],order='vehicle_no asc')
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
                            worksheet.write('Q%s' % (new_row), 'Remarks', bold)
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
                                     ('driver_name', '=', driver.id),
                                      ('project_id', '=', pro.id)], order='vehicle_no asc')
                                for driver_d in f_driver_daily:
                                    sl_count = 0
                                    total=0
                                    worksheet.merge_range('G%s:O%s' % (vehicle_row, vehicle_row), driver_d.vehicle_no.name, bold)
                                    worksheet.write('M%s' % (new_row), driver_d.deposit, regular)

                                    if len(driver_d.driver_stmt_line) == 0:
                                        worksheet.write('A%s' % (new_row),
                                                        datetime.strptime(driver_d.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
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
                                            worksheet.merge_range('F%s:F%s' % (first_row,new_row), driver_d.project_id.name, regular)
                                        worksheet.write('G%s' % (new_row), '', regular)
                                        worksheet.write('H%s' % (new_row), '', regular)

                                        worksheet.write('I%s' % (new_row), 1, regular)

                                        worksheet.write('J%s' % (new_row), driver_d.driver_bata, regular)

                                        worksheet.write('K%s' % (new_row), driver_d.ot_time, regular)

                                        total += driver_d.driver_bata * 1 + (driver_d.ot_time * driver_d.ot_rate)
                                        worksheet.write('L%s' % (new_row), (driver_d.ot_time * driver_d.ot_rate), regular)
                                        worksheet.write('N%s' % (new_row), total, regular)
                                        driver_subtotal += total
                                        total += 0
                                        driver_deposit += 0
                                        worksheet.write('O%s' % (new_row), 0, regular)
                                        pro_total += total
                                        if first_row == new_row:
                                            worksheet.write("P%s" % (new_row), pro_total, regular)
                                        else:
                                            worksheet.merge_range("P%s:P%s" % (first_row,new_row), pro_total, regular)
                                        driver_total += total
                                        worksheet.write("Q%s" % (new_row), driver_d.remark,regular)
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
                                        total += driver_line.line_id.deposit

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

                                    worksheet.write('J%s' % (new_row), driver_line.bata_driver, regular)

                                    worksheet.write('K%s' % (new_row), driver_line.line_id.ot_time, regular)

                                    worksheet.write('L%s' % (new_row),
                                                    (driver_line.line_id.ot_time * driver_line.line_id.ot_rate),
                                                    regular)

                                    total += driver_line.bata_driver * 1 + (
                                            driver_line.line_id.ot_time * driver_line.line_id.ot_rate)

                                    worksheet.write('N%s' % (new_row), total, regular)
                                    driver_subtotal += total
                                    worksheet.write('O%s' % (new_row), driver_line.km_deposit, regular)
                                    total += driver_line.km_deposit
                                    driver_deposit += driver_line.km_deposit
                                    pro_total += total
                                    if first_row != new_row:
                                        worksheet.merge_range('P%s:P%s' % (first_row, new_row), pro_total, regular)
                                    else:
                                        worksheet.write("P%s" % (new_row), pro_total, regular)
                                    driver_total += total
                                    worksheet.write("Q%s"%(new_row),driver_line.remarks,regular)
                                    count += 1
                                    new_row += 1
                            if len(driver_daily) != 0:
                                worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Total", boldc)
                                worksheet.write('N%s' % (new_row), driver_subtotal, boldc)
                                worksheet.write('O%s' % (new_row), driver_deposit, boldc)
                                worksheet.write('P%s' % (new_row), driver_total, boldc)
                                new_row += 2
            else:
                if rec.driver_id:
                    vehicle_row = 0

                    driver_daily = self.env['driver.daily.statement'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to), ('driver_name', '=', rec.driver_id.id),
                         ],order='date asc,vehicle_no asc')

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
                        worksheet.write('Q%s' % (new_row), 'Remarks', bold)
                        spec = new_row
                        new_row += 1
                        driver_subtotal = 0
                        driver_deposit = 0
                        driver_total = 0
                        total_cum_tran = 0
                        total_during_mont = 0
                        total_cum_issue = 0
                        total_book_balance = 0
                        pro_total = 0
                        f_driver_daily = self.env['driver.daily.statement'].search(
                            [('date', '>=', date_from), ('date', '<=', date_to),
                             ('driver_name', '=', rec.driver_id.id)],order='date asc,vehicle_no asc')
                        for driver in f_driver_daily:
                            sl_count = 0
                            total = 0
                            worksheet.merge_range('G%s:O%s' % (vehicle_row, vehicle_row), driver.vehicle_no.name,
                                                  boldc)
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
                                worksheet.write('F%s' % (new_row), driver.project_id.name, regular)
                                worksheet.write('G%s' % (new_row), '', regular)
                                worksheet.write('H%s' % (new_row), '', regular)

                                worksheet.write('I%s' % (new_row), 1, regular)

                                worksheet.write('J%s' % (new_row), driver.driver_bata, regular)

                                worksheet.write('K%s' % (new_row), driver.ot_time, regular)

                                total += driver.driver_bata * 1 + (driver.ot_time * driver.ot_rate)
                                worksheet.write('L%s' % (new_row), (driver.ot_time * driver.ot_rate), regular)
                                worksheet.write('N%s' % (new_row), total, regular)
                                driver_subtotal += total
                                total += 0
                                driver_deposit += 0
                                worksheet.write('O%s' % (new_row),0, regular)
                                worksheet.write("P%s" % (new_row), total, regular)
                                worksheet.write("Q%s" % (new_row), driver.remark or '', regular)
                                driver_total += total
                                count += 1
                                new_row += 1
                                    # worksheet.write('R%s' % (new_row), driver.remark, regular)
                        driver_stmt_line = self.env['driver.daily.statement.line'].search(
                            [('line_id', 'in', driver_daily.ids)],
                            order='invoice_date desc,vehicle_no asc')
                        sl_count = 0
                        date = invoices.to_date
                        first_row = new_row
                        ot_count = 0
                        for driver_line in driver_stmt_line:
                            worksheet.merge_range('A%s:F%s' % (spec - 1, spec - 1),
                                                  driver_line.line_id.driver_name.name, bold)
                            worksheet.merge_range('G%s:O%s' % (spec - 1, spec - 1),
                                                  driver_line.line_id.vehicle_no.name,
                                                  bold)
                            total = 0
                            if driver_line.invoice_date != date:
                                worksheet.write('M%s' % (new_row), driver_line.line_id.deposit, regular)
                                total += driver_line.line_id.deposit

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

                            worksheet.write("F%s" % (new_row), driver_line.project_id.name, regular)
                            worksheet.write('G%s' % (new_row),
                                            driver_line.from_id2 and driver_line.from_id2.name or driver_line.location_id.name,
                                            regular)
                            worksheet.write('H%s' % (new_row), driver_line.to_id2.name, regular)
                            worksheet.write('I%s' % (new_row), 1, regular)

                            worksheet.write('J%s' % (new_row), driver_line.bata_driver, regular)
                            if ot_count == 0:
                                worksheet.write('K%s' % (new_row), driver_line.line_id.ot_time, regular)

                                worksheet.write('L%s' % (new_row),
                                                (driver_line.line_id.ot_time * driver_line.line_id.ot_rate), regular)
                                total +=  (
                                        driver_line.line_id.ot_time * driver_line.line_id.ot_rate)
                                ot_count = 1
                            total += driver_line.bata_driver * 1

                            worksheet.write('N%s' % (new_row), total, regular)
                            driver_subtotal += total
                            worksheet.write('O%s' % (new_row), driver_line.km_deposit, regular)
                            total += driver_line.km_deposit
                            driver_deposit += driver_line.km_deposit
                            pro_total += total

                            worksheet.write("P%s" % (new_row), total, regular)
                            worksheet.write("Q%s"%(new_row),driver_line.remarks)
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
                                     ('vehicle_no', '=', vehicle.id), ('driver_name', '=', driver.id)])
                                if driver_daily:
                                    if driver not in driver_list:
                                        driver_list.append(driver)


                    for driver in driver_list:

                        vehicle_row = 0
                        driver_daily = self.env['driver.daily.statement'].search(
                            [('date', '>=', date_from), ('date', '<=', date_to), ('driver_name', '=', driver.id),
                             ],order='date asc,vehicle_no asc')
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
                            worksheet.write('Q%s' % (new_row), 'Remarks', bold)
                            spec = new_row
                            new_row += 1
                            driver_subtotal = 0
                            driver_deposit = 0
                            driver_total = 0
                            total_cum_tran = 0
                            total_during_mont = 0
                            total_cum_issue = 0
                            total_book_balance = 0


                            f_driver_daily = self.env['driver.daily.statement'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to),
                                 ('driver_name', '=', driver.id),
                                 ],order='date asc,vehicle_no asc')


                            date_diff = date_to - date_from
                            from_date = date_from
                            project_dict ={}
                            for rangeg in range(date_diff.days + 1):

                                sl_count = 0
                                total = 0
                                driver_dl = self.env['driver.daily.statement'].search(
                                [('date', '=', from_date),
                                 ('driver_name', '=', driver.id),
                                 ],order='date asc,vehicle_no asc')

                                for driver_d in driver_dl:
                                    pro_sub = 0
                                    pro_deposit = 0
                                    pro_total =0
                                    total = 0
                                    worksheet.merge_range('G%s:O%s' % (vehicle_row, vehicle_row),
                                                          driver_d.vehicle_no.name, bold)
                                    date_row = new_row
                                    if date_row == new_row:
                                        worksheet.write('M%s' % (new_row), driver_d.deposit, regular)
                                    else:
                                        worksheet.write('M%s' % (new_row), driver_d.deposit, regular)
                                        worksheet.write('M%s' % (date_row), "0", regular)
                                        # worksheet.merge_range('M%s:M%s' % (date_row, new_row),
                                        #                       driver_d.deposit, regular)


                                    total += driver_d.deposit

                                    if len(driver_d.driver_stmt_line) == 0:
                                        if date_row == new_row:

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
                                        else:
                                            worksheet.merge_range('A%s:A%s' % (date_row,new_row),
                                                            datetime.strptime(driver_d.date, "%Y-%m-%d").strftime(
                                                                "%d-%m-%Y"),
                                                            regular)
                                            worksheet.merge_range('B%s:B%s' % (date_row,new_row), driver_d.vehicle_no.name, regular)
                                            worksheet.merge_range('C%s:C%s' % (date_row,new_row), driver_d.running_km, regular)
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

                                                worksheet.merge_range('D%s:D%s' % (date_row,new_row), central, regular)
                                            if driver_d.end_time:
                                                utc = datetime.strptime(driver_d.end_time, '%Y-%m-%d %H:%M:%S')
                                                utc = utc.replace(tzinfo=from_zone)
                                                central = utc.astimezone(to_zone)
                                                central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                            '%Y-%m-%d %H:%M:%S').strftime(
                                                    "%d-%m-%Y %H:%M:%S")
                                                worksheet.merge_range('E%s:E%s' % (date_row,new_row), central, regular)


                                        worksheet.write('F%s' % (new_row), driver_d.project_id.name, regular)
                                        worksheet.write('G%s' % (new_row), '', regular)
                                        worksheet.write('H%s' % (new_row), '', regular)

                                        worksheet.write('I%s' % (new_row), 1, regular)

                                        worksheet.write('J%s' % (new_row), driver_d.driver_bata, regular)

                                        worksheet.write('K%s' % (new_row), driver_d.ot_time, regular)

                                        total += driver_d.driver_bata * 1 + (driver_d.ot_time * driver_d.ot_rate)
                                        worksheet.write('L%s' % (new_row), (driver_d.ot_time * driver_d.ot_rate),
                                                        regular)
                                        worksheet.write('N%s' % (new_row), total, regular)
                                        driver_subtotal += total
                                        pro_sub = total
                                        total += 0
                                        driver_deposit += 0
                                        pro_deposit = 0
                                        worksheet.write('O%s' % (new_row), 0, regular)
                                        worksheet.write("P%s" % (new_row), total, regular)
                                        worksheet.write("Q%s" % (new_row), driver_d.remark or '', regular)
                                        driver_total += total
                                        pro_total = total
                                        count += 1
                                        new_row += 1
                                        if driver_d.project_id.name in project_dict.keys():
                                            project_dict[driver_d.project_id.name]['pro_sub'] = project_dict[driver_d.project_id.name]['pro_sub'] + pro_sub
                                            project_dict[driver_d.project_id.name]['pro_deposit'] = project_dict[driver_d.project_id.name]['pro_deposit'] + pro_deposit
                                            project_dict[driver_d.project_id.name]['pro_total']=project_dict[driver_d.project_id.name]['pro_total'] + pro_total
                                        else:
                                            project_dict.update({driver_d.project_id.name:{'pro_sub':pro_sub,
                                                                                       'pro_deposit':pro_deposit,
                                                                                       'pro_total':pro_total}})
                                    else:

                                        sub_total = 0
                                        line_count = 0
                                        ot_count = 0
                                        for driver_line in driver_d.driver_stmt_line:
                                            line_count +=1
                                            if line_count==1:

                                                curr_total = total
                                            else:
                                                curr_total = 0
                                            if date_row == new_row:

                                                worksheet.write('M%s' % (new_row), driver_line.line_id.deposit, regular)
                                            else:
                                                worksheet.write('M%s' % (date_row), driver_line.line_id.deposit, regular)
                                                worksheet.write('M%s' % (new_row), "0", regular)
                                            #     worksheet.merge_range('M%s:M%s' % (date_row, new_row),driver_line.line_id.deposit, regular)
                                            # total += driver_line.line_id.deposit

                                            date = driver_line.invoice_date
                                            # worksheet.write('A%s' % (new_row), count, regular)
                                            if date_row == new_row:

                                                worksheet.write('A%s' % (new_row),
                                                                datetime.strptime(driver_d.date, "%Y-%m-%d").strftime(
                                                                    "%d-%m-%Y"),
                                                                regular)
                                                worksheet.write('B%s' % (new_row), driver_line.line_id.vehicle_no.name,
                                                                regular)
                                                worksheet.write('C%s' % (new_row), driver_line.line_id.running_km,
                                                                regular)

                                                if driver_line.line_id.start_time:
                                                    from_zone = tz.gettz('UTC')
                                                    to_zone = tz.gettz('Asia/Kolkata')
                                                    # from_zone = tz.tzutc()
                                                    # to_zone = tz.tzlocal()
                                                    utc = datetime.strptime(driver_line.line_id.start_time,
                                                                            '%Y-%m-%d %H:%M:%S')
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
                                                    utc = datetime.strptime(driver_line.line_id.end_time,
                                                                            '%Y-%m-%d %H:%M:%S')
                                                    utc = utc.replace(tzinfo=from_zone)
                                                    central = utc.astimezone(to_zone)
                                                    central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                                '%Y-%m-%d %H:%M:%S').strftime(
                                                        "%d-%m-%Y %H:%M:%S")

                                                    worksheet.write('E%s' % (new_row), central, regular)

                                            else:
                                                worksheet.merge_range('A%s:A%s' % (date_row, new_row),
                                                                      datetime.strptime(driver_d.date,
                                                                                        "%Y-%m-%d").strftime(
                                                                          "%d-%m-%Y"),regular),
                                                worksheet.merge_range('B%s:B%s' % (date_row, new_row), driver_line.line_id.vehicle_no.name,
                                                                regular)
                                                worksheet.merge_range('C%s:C%s' % (date_row, new_row), driver_line.line_id.running_km,
                                                                regular)

                                                if driver_line.line_id.start_time:
                                                    from_zone = tz.gettz('UTC')
                                                    to_zone = tz.gettz('Asia/Kolkata')
                                                    # from_zone = tz.tzutc()
                                                    # to_zone = tz.tzlocal()
                                                    utc = datetime.strptime(driver_line.line_id.start_time,
                                                                            '%Y-%m-%d %H:%M:%S')
                                                    utc = utc.replace(tzinfo=from_zone)
                                                    central = utc.astimezone(to_zone)
                                                    central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                                '%Y-%m-%d %H:%M:%S').strftime(
                                                        "%d-%m-%Y %H:%M:%S")

                                                    worksheet.merge_range('D%s:D%s' % (date_row, new_row), central, regular)
                                                if driver_line.line_id.end_time:
                                                    from_zone = tz.gettz('UTC')
                                                    to_zone = tz.gettz('Asia/Kolkata')
                                                    # from_zone = tz.tzutc()
                                                    # to_zone = tz.tzlocal()
                                                    utc = datetime.strptime(driver_line.line_id.end_time,
                                                                            '%Y-%m-%d %H:%M:%S')
                                                    utc = utc.replace(tzinfo=from_zone)
                                                    central = utc.astimezone(to_zone)
                                                    central = datetime.strptime(central.strftime("%Y-%m-%d %H:%M:%S"),
                                                                                '%Y-%m-%d %H:%M:%S').strftime(
                                                        "%d-%m-%Y %H:%M:%S")

                                                    worksheet.merge_range('E%s:E%s' % (date_row, new_row),central, regular)

                                            # worksheet.write('A%s' % (new_row),
                                            #                 datetime.strptime(driver_line.line_id.date, "%Y-%m-%d").strftime(
                                            #                     "%d-%m-%Y"),
                                            #                 regular)
                                            # worksheet.write('C%s' % (new_row), driver.remark, regular)

                                            # worksheet.write('F%s' % (new_row), driver.start_km, regular)
                                            # worksheet.write('G%s' % (new_row), driver.actual_close_km, regular)

                                            worksheet.write("F%s" % (new_row), driver_line.project_id.name, regular)
                                            worksheet.write('G%s' % (new_row),
                                                            driver_line.from_id2 and driver_line.from_id2.name or driver_line.location_id.name,
                                                            regular)
                                            worksheet.write('H%s' % (new_row), driver_line.to_id2.name, regular)
                                            worksheet.write('I%s' % (new_row), 1, regular)

                                            worksheet.write('J%s' % (new_row), driver_line.bata_driver, regular)
                                            if ot_count != 0:
                                                worksheet.write('K%s' % (new_row), "0", regular)

                                                worksheet.write('L%s' % (new_row), "0", regular)

                                            if ot_count == 0:

                                                worksheet.write('K%s' % (new_row), driver_line.line_id.ot_time, regular)

                                                worksheet.write('L%s' % (new_row),
                                                                (driver_line.line_id.ot_time * driver_line.line_id.ot_rate),
                                                                regular)
                                                curr_total += (
                                                        driver_line.line_id.ot_time * driver_line.line_id.ot_rate)
                                                ot_count =1

                                            curr_total += driver_line.bata_driver * 1
                                            driver_subtotal+=curr_total
                                            pro_sub = curr_total
                                            worksheet.write('N%s' % (new_row), curr_total, regular)
                                            sub_total += curr_total
                                            worksheet.write('O%s' % (new_row), driver_line.km_deposit, regular)
                                            curr_total += driver_line.km_deposit
                                            driver_deposit += driver_line.km_deposit
                                            pro_deposit = driver_line.km_deposit
                                            worksheet.write("P%s" % (new_row), curr_total, regular)
                                            worksheet.write("Q%s" % (new_row), driver_line.remarks or '', regular)
                                            driver_total += curr_total
                                            pro_total = curr_total
                                            count += 1
                                            new_row += 1
                                            if driver_line.project_id.name in project_dict.keys():
                                                project_dict[driver_line.project_id.name]['pro_sub'] = \
                                                project_dict[driver_line.project_id.name]['pro_sub'] + pro_sub
                                                project_dict[driver_line.project_id.name]['pro_deposit'] = \
                                                project_dict[driver_line.project_id.name]['pro_deposit'] + pro_deposit
                                                project_dict[driver_line.project_id.name]['pro_total'] = \
                                                project_dict[driver_line.project_id.name]['pro_total'] + pro_total
                                            else:
                                                project_dict.update({driver_line.project_id.name: {'pro_sub': pro_sub,
                                                                                                'pro_deposit': pro_deposit,
                                                                                                'pro_total': pro_total}})


                                        sub_total += total

                                from_date = from_date + timedelta(days=1)

                                        # worksheet.write('R%s' % (new_row), driver.remark, regular)
                            # driver_stmt_line = self.env['driver.daily.statement.line'].search(
                            #     [('line_id', 'in', driver_daily.ids)],
                            #     order='invoice_date asc,vehicle_no asc')
                            # sl_count = 0
                            # date = invoices.to_date
                            # first_row = new_row
                            #
                            #
                            #     total = 0

                            if len(driver_daily) != 0:
                                worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Total", boldc)
                                worksheet.write('N%s' % (new_row), driver_subtotal, boldc)
                                worksheet.write('O%s' % (new_row), driver_deposit, boldc)
                                worksheet.write('P%s' % (new_row), driver_total, boldc)
                                new_row += 2
                                worksheet.merge_range('A%s:F%s' % (new_row, new_row), "Project", boldc)
                                worksheet.write('N%s' % (new_row), "Subtotal", boldc)
                                worksheet.write('O%s' % (new_row), "Deposit", boldc)
                                worksheet.write('P%s' % (new_row), "Total", boldc)
                                new_row += 1

                                for key,value in project_dict.items():
                                    worksheet.merge_range('A%s:F%s' % (new_row, new_row), key, boldc)
                                    worksheet.write('N%s' % (new_row), project_dict[key]['pro_sub'], boldc)
                                    worksheet.write('O%s' % (new_row), project_dict[key]['pro_deposit'], boldc)
                                    worksheet.write('P%s' % (new_row), project_dict[key]['pro_total'], boldc)
                                    new_row+=1
                                new_row+=4






                            # worksheet.merge_range('O%s:O%s' % (first_row, new_row-1), pro_total, regular)



BillReportXlsx('report.driver_bata_report.xlsx', 'driver.bata.report')




