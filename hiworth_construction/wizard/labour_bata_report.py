from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz


class LabourBataReport(models.TransientModel):
    _name = 'labour.bata.report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', 'Company')

    partner_select = fields.Selection([('sub', 'Subcontractor Labour'),
                                       ('com', 'Company Labour')], 'Labour Type', default='com')
    project_id = fields.Many2one('project.project')
    labour_id = fields.Many2one('hr.employee',"Labour")
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
    sub_contractor_id = fields.Many2one('res.partner',string="Subcontractor",domain="[('labour_contractor','=',True)]")
    _defaults = {
        'date_today': datetime.today(),
        # 'from_date': '2017-04-01',
        # 'to_date': fields.Date.today(),
    }

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 ' + self.month + ' ' + str(datetime.now().year)
            print
            'ddddddddddddddddddd', date
            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)
            print
            'sssssssssssssssss', end_date
            self.to_date = end_date




    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='labour_bata_report.xlsx')


class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bill")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'size': 12})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True, 'align': 'center','size': 10})
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

        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:S', 10)
        partner_select = ''
        if invoices.partner_select == 'com':
            partner_select = "Company Labour"
        else:
            partner_select = "Subcontractor Labour : "+ invoices.sub_contractor_id.name
        worksheet.merge_range('A1:K1', 'BEGORRA INFRASTRUCTURE & DEVELOPERS PVT LTD', boldc)
        worksheet.merge_range('A2:K2', partner_select, boldc)
        worksheet.merge_range('A3:K3', 'PAYMENT FOR THE PERIOD OF %s TO %s'%(datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%d/%m/%Y"),datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%d/%m/%Y")) , boldc)
        worksheet.merge_range('A4:A5', 'Sl.NO', bold)
        worksheet.merge_range('B4:B5', 'Name', bold)

        worksheet.merge_range('C4:C5', 'ID No', bold)

        worksheet.write('D5', 'SITE', bold)
        worksheet.write('E5', 'DUTY/DAY', bold)
        worksheet.write('F5', 'RATE', bold)
        worksheet.write('G5', 'OT/HR', bold)
        worksheet.write('H5', 'OT RATE', bold)
        # worksheet.merge_range('A4:O5','',regular)
        worksheet.write('I5', 'SUB TOTAL', bold)
        worksheet.write('J5', 'TOTAL', bold)
        worksheet.write('K5','Remarks',bold)




        count = 0
        for rec in invoices:
            labour_total = 0
            labour_sub = 0
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")
            if rec.partner_select == 'com':
                if rec.labour_id:
                    first_row = new_row
                    if rec.partner_select == 'com':
                        labour_report = self.env['labour.activities.sheet'].search([('date','>=',date_from),('date','<=',date_to),('partner_select','=',rec.partner_select),('employee_id','=',rec.labour_id.id)])

                    labour_list = []
                    labour_dict = {}
                    for labour in labour_report:
                        if not labour.project_id.location_id in labour_dict.keys():
                            labour_dict.update({'location':labour.project_id.location_id.name,
                                                'day':labour.day,
                                                'rate':labour.rate,
                                                'ot':labour.over_time,
                                                'ot_rate':labour.ot_rate,
                                                'sub_total':labour.ot_amount+(labour.rate * labour.day),
                                                'total':labour.ot_amount+(labour.rate * labour.day),
                                                'remarks':labour.remarks})
                        else:
                            labour_dict['day'] = labour_dict['day'] + labour.day
                            labour_dict['ot'] = labour['ot'] + labour.over_time
                            labour_dict['ot_rate'] = labour.ot_rate
                            labour_dict['sub_total'] = labour['sub_total'] + (labour.rate * labour.day) + labour.ot_amount
                            labour_dict['total'] = labour_dict['sub_total']
                            labour_dict['remarks'] = labour_dict['remarks'] + labour.remarks
                    for key,val in labour_dict.items():
                        worksheet.write('A%s' % (new_row), count, regular)
                        if first_row == new_row:
                            worksheet.write('B%s' % (new_row), rec.labour_id.name, regular)
                        else:
                            worksheet.merge_range('B%s:B%s' % (first_row,new_row), rec.labour_id.name, regular)

                        worksheet.write('C%s' % (new_row), rec.labour_id.labour_id, regular)
                        worksheet.write('D%s' % (new_row), labour_dict['location'], regular)
                        worksheet.write('E%s' % (new_row), labour_dict['day'], regular)
                        worksheet.write('F%s' % (new_row), labour_dict['rate'], regular)
                        worksheet.write('G%s' % (new_row), labour_dict['ot'], regular)
                        worksheet.write('H%s' % (new_row), labour_dict['ot_rate'], regular)


                        worksheet.write('I%s' % (new_row), labour_dict['sub_total'], regular)

                        if first_row == new_row:
                            worksheet.write('J%s' % (new_row), labour_dict['total'], regular)
                        else:
                            worksheet.merge_range('J%s:J%s' % (first_row,new_row), labour_dict['total'], regular)
                        worksheet.write('K%s' % (new_row), labour_dict['remarks'], regular)


                    # worksheet.write('R%s' % (new_row), driver.remark, regular)
                    count += 1
                    new_row += 1
                    labour_total+=labour_dict['total']
                    labour_sub += labour_dict['sub_total']
                else:
                    labour_dict = {}
                    for labour_de in self.env['hr.employee'].search([('user_category','=','ylabour')],order='labour_id asc'):
                        labour_report = self.env['labour.activities.sheet'].search(
                            [('date', '>=', date_from), ('date', '<=', date_to),
                             ('partner_select', '=', rec.partner_select), ('employee_id', '=', labour_de.id)])

                        labour_list = []

                        labour_dict.update({labour_de.name:{}})
                        for labour in labour_report:
                            if not labour.project_id.location_id.name in labour_dict[labour_de.name].keys():
                                remarks =''
                                if labour.remarks:
                                    remarks += labour.remarks
                                labour_dict[labour_de.name].update({labour.project_id.location_id.name:{
                                                    'day': labour.day,
                                                    'rate': labour.rate,
                                                    'ot': labour.over_time,
                                                    'ot_rate': labour.ot_rate,
                                                    'sub_total': labour.ot_amount + (labour.rate * labour.day),
                                                    'total': labour.ot_amount + (labour.rate * labour.day),
                                                    'remarks':remarks}})
                            else:
                                remarks = ''
                                if labour.remarks:
                                    remarks += labour.remarks
                                labour_dict[labour_de.name][labour.project_id.location_id.name]['day'] = labour_dict[labour_de.name][labour.project_id.location_id.name]['day'] + labour.day
                                labour_dict[labour_de.name][labour.project_id.location_id.name]['ot'] = labour_dict[labour_de.name][labour.project_id.location_id.name]['ot'] + labour.over_time
                                labour_dict[labour_de.name][labour.project_id.location_id.name]['ot_rate'] = labour.ot_rate
                                labour_dict[labour_de.name][labour.project_id.location_id.name]['sub_total'] = labour_dict[labour_de.name][labour.project_id.location_id.name]['sub_total'] + (labour.rate * labour.day) + labour.ot_amount
                                labour_dict[labour_de.name][labour.project_id.location_id.name]['total'] = labour_dict[labour_de.name][labour.project_id.location_id.name]['sub_total']
                                labour_dict[labour_de.name][labour.project_id.location_id.name]['remarks'] = labour_dict[labour_de.name][labour.project_id.location_id.name]['remarks'] + ','+remarks
                    for lab in self.env['hr.employee'].search([('user_category','=','ylabour')],order='labour_id asc'):
                        first_row = new_row
                        lab_total = 0


                        for key,val in labour_dict[lab.name].items():


                            if first_row == new_row:
                                count += 1
                                worksheet.write('B%s' % (new_row), lab.name, regular)
                                worksheet.write('A%s' % (new_row), count, regular)
                                worksheet.write('C%s' % (new_row), lab.labour_id, regular)
                            else:
                                worksheet.merge_range('B%s:B%s' % (first_row,new_row), lab.name, regular)
                                worksheet.merge_range('A%s:A%s' % (first_row,new_row), count, regular)
                                worksheet.merge_range('C%s:C%s' % (first_row,new_row), lab.labour_id, regular)



                            worksheet.write('D%s' % (new_row), key, regular)
                            worksheet.write('E%s' % (new_row), labour_dict[lab.name][key]['day'], regular)
                            worksheet.write('F%s' % (new_row), labour_dict[lab.name][key]['rate'], regular)
                            worksheet.write('G%s' % (new_row), labour_dict[lab.name][key]['ot'], regular)

                            worksheet.write('H%s' % (new_row), labour_dict[lab.name][key]['ot_rate'], regular)

                            worksheet.write('I%s' % (new_row), labour_dict[lab.name][key]['sub_total'], regular)
                            subtotal = labour_dict[lab.name][key]['day'] * labour_dict[lab.name][key]['rate'] + \
                                       labour_dict[lab.name][key]['ot'] * labour_dict[lab.name][key]['ot_rate']

                            # worksheet.write('I%s' % (new_row), labour_dict[lab.name][key]['sub_total'], regular)
                            worksheet.write('I%s' % (new_row), subtotal, regular)
                            # lab_total +=labour_dict[lab.name][key]['total']
                            lab_total += subtotal
                            if first_row == new_row:
                                worksheet.write('J%s' % (new_row), lab_total, regular)
                            else:
                                worksheet.merge_range('J%s:J%s' % (first_row,new_row), lab_total, regular)
                            worksheet.write('K%s' % (new_row), labour_dict[lab.name][key]['remarks'], regular)

                            new_row += 1
                            labour_total += labour_dict[lab.name][key]['total']
                            labour_sub += labour_dict[lab.name][key]['sub_total']

                worksheet.merge_range("A%s:H%s"%(new_row,new_row),"Total",bold)
                worksheet.write('I%s' % (new_row), labour_sub, bold)
                worksheet.write('J%s' % (new_row), labour_total, bold)
            else:

                labour_dict = {}
                for labour_de in self.env['subcontractor.labour'].search([('contractor_id', '=', rec.sub_contractor_id.id)],
                                                                order='labour_id asc'):
                    labour_report = self.env['labour.activities.sheet'].search(
                        [('date', '>=', date_from), ('date', '<=', date_to),
                         ('partner_select', '=', rec.partner_select), ('labour_id', '=', labour_de.id)])

                    labour_list = []

                    labour_dict.update({labour_de.name: {}})
                    for labour in labour_report:
                        if not labour.project_id.location_id.name in labour_dict[labour_de.name].keys():
                            remarks = ''
                            if labour.remarks:
                                remarks += labour.remarks
                            labour_dict[labour_de.name].update({labour.project_id.location_id.name: {
                                'day': labour.day,
                                'rate': labour.rate,
                                'ot': labour.over_time,
                                'ot_rate': labour.ot_rate,
                                'sub_total': labour.ot_amount + (labour.rate * labour.day),
                                'total': labour.ot_amount + (labour.rate * labour.day),
                                'remarks': remarks}})
                        else:
                            remarks = ''
                            if labour.remarks:
                                remarks += labour.remarks
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['day'] = \
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['day'] + labour.day
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['ot'] = \
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['ot'] + labour.over_time
                            labour_dict[labour_de.name][labour.project_id.location_id.name][
                                'ot_rate'] = labour.ot_rate
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['sub_total'] = \
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['sub_total'] + (
                                        labour.rate * labour.day) + labour.ot_amount
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['total'] = \
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['sub_total']
                            labour_dict[labour_de.name][labour.project_id.location_id.name]['remarks'] = \
                            labour_dict[labour_de.name][labour.project_id.location_id.name][
                                'remarks'] + ',' + remarks

                for lab in self.env['subcontractor.labour'].search([('contractor_id', '=', rec.sub_contractor_id.id)],
                                                          order='labour_id asc'):
                    first_row = new_row
                    lab_total = 0
                    labour_sub = 0


                    for key, val in labour_dict[lab.name].items():

                        if first_row == new_row:
                            count += 1
                            worksheet.write('B%s' % (new_row), lab.name, regular)
                            worksheet.write('A%s' % (new_row), count, regular)
                            worksheet.write('C%s' % (new_row), lab.labour_id, regular)
                        else:
                            worksheet.merge_range('B%s:B%s' % (first_row, new_row), lab.name, regular)
                            worksheet.merge_range('A%s:A%s' % (first_row, new_row), count, regular)
                            worksheet.merge_range('C%s:C%s' % (first_row, new_row), lab.labour_id, regular)

                        worksheet.write('D%s' % (new_row), key, regular)
                        worksheet.write('E%s' % (new_row), labour_dict[lab.name][key]['day'], regular)
                        worksheet.write('F%s' % (new_row), labour_dict[lab.name][key]['rate'], regular)
                        worksheet.write('G%s' % (new_row), labour_dict[lab.name][key]['ot'], regular)

                        worksheet.write('H%s' % (new_row), labour_dict[lab.name][key]['ot_rate'], regular)

                        worksheet.write('I%s' % (new_row), labour_dict[lab.name][key]['sub_total'], regular)
                        lab_total += labour_dict[lab.name][key]['total']
                        if first_row == new_row:
                            worksheet.write('J%s' % (new_row), lab_total, regular)
                        else:
                            worksheet.merge_range('J%s:J%s' % (first_row, new_row), lab_total, regular)
                        worksheet.write('K%s' % (new_row), labour_dict[lab.name][key]['remarks'], regular)

                        new_row += 1
                        labour_total += labour_dict[lab.name][key]['total']
                        labour_sub += labour_dict[lab.name][key]['sub_total']

                worksheet.merge_range("A%s:H%s" % (new_row, new_row), "Total", bold)
                worksheet.write('I%s' % (new_row), labour_sub, bold)
                worksheet.write('J%s' % (new_row), labour_total, bold)



BillReportXlsx('report.labour_bata_report.xlsx', 'labour.bata.report')




