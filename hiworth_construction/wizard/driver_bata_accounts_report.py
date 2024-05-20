from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone


class DriverBataAccountsReport(models.TransientModel):
    _name = 'driver.bata.accounts.report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')

    @api.multi
    def generate_xls_report(self):
        return self.env["report"].get_action(self, report_name='Driver Bata Accounts.xlsx')


class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'size': 12})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
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
        date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
        date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")
        worksheet.merge_range("A1:F1",
                              "BATA(%s TO %s)" % (date_from.strftime("%d-%m-%Y"), date_to.strftime("%d-%m-%Y")), boldc)

        count = 1
        for rec in invoices:
            total = 0
            amount_total = 0
            deposit_total = 0
            worksheet.write("A2", "SL No", bold)
            worksheet.write("B2", "VEHICLE", bold)
            worksheet.write("C2", "NAME", bold)

            worksheet.write("D2", "AMOUNT", bold)
            worksheet.write("E2", "DEPOSIT", bold)
            worksheet.write("F2", "TOTAL", bold)
            vehicle_row = 0
            driver_daily = [1]
            driver_list = []
            for category in self.env['vehicle.category.type'].search([], order='priority asc'):
                vehicle_row = new_row
                for vehicle in self.env['fleet.vehicle'].search([('vehicle_categ_id', '=', category.id)],
                                                                order='name asc'):
                    vehicle_total = 0
                    first_row = new_row + 1
                    for driver in self.env['hr.employee'].search(
                            [('user_category', 'in', ['tppdriver', 'tpoperators_helpers']),
                             ('cost_type', 'in', ['wages', 'salary_bata'])]):
                        if driver.id not in driver_list:
                            driver_daily = self.env['driver.daily.statement'].search(
                                [('date', '>=', date_from), ('date', '<=', date_to), ('vehicle_no', '=', vehicle.id),
                                 ('driver_name', '=', driver.id)])
                            if len(driver_daily) != 0:
                                driver_daily = self.env['driver.daily.statement'].search(
                                    [('date', '>=', date_from), ('date', '<=', date_to),
                                     ('driver_name', '=', driver.id)])
                                worksheet.write("B%s" % vehicle_row, category.name, bold)
                                if vehicle_row == new_row:
                                    new_row += 1
                            rent = 0
                            rent_driver = 0
                            ot = 0
                            ot_amt = 0
                            amt = 0
                            deposit = 0
                            for daily in driver_daily:
                                rent_driver = daily.driver_bata
                                ot += daily.ot_time
                                ot_amt += daily.ot_rate
                                if len(daily.driver_stmt_line) >= 1:
                                    for line in daily.driver_stmt_line:
                                        rent = line.bata_driver
                                        deposit += line.km_deposit
                                        amt += line.bata_driver
                                    amt += daily.deposit

                                if len(daily.driver_stmt_line) == 0:
                                    amt += daily.deposit + daily.driver_bata
                                amt += daily.ot_amt

                            if len(driver_daily) != 0:
                                # if first_row == new_row:

                                worksheet.write("A%s" % (new_row), count, regular)
                                worksheet.write("B%s" % (new_row), vehicle.name, regular)
                                # else:
                                #     worksheet.write("A%s" % (first_row), count, regular)
                                #     worksheet.write("B%s" % (first_row), vehicle.name, regular)
                                # worksheet.merge_range("A%s:A%s" % (first_row,new_row), count, regular)
                                # worksheet.merge_range("B%s:B%s" % (first_row,new_row), vehicle.name, regular)
                                worksheet.write("C%s" % (new_row), driver.name, regular)

                                worksheet.write("D%s" % (new_row), amt, regular)
                                worksheet.write("E%s" % (new_row), deposit, regular)
                                driver_total = amt + deposit
                                vehicle_total += driver_total
                                total += driver_total
                                amount_total += amt
                                deposit_total += deposit
                                worksheet.write("F%s" % (new_row), driver_total, regular)
                                # else:
                                #     worksheet.merge_range("F%s:F%s"%(first_row,new_row),vehicle_total,regular)
                                new_row += 1
                                count += 1
                                driver_list.append(driver.id)
            worksheet.merge_range("A%s:C%s" % (new_row, new_row), "Total", bold)
            worksheet.write("D%s" % new_row, amount_total, bold)
            worksheet.write("E%s" % new_row, deposit_total, bold)
            worksheet.write("F%s" % new_row, total, bold)


BillReportXlsx('report.Driver Bata Accounts.xlsx', 'driver.bata.accounts.report')
