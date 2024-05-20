from openerp import fields, models, api
from datetime import datetime
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta


class ReportDieselVehicle(models.TransientModel):
    _name = 'report.diesel.vehicle'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', 'Company')
    date_today = fields.Date('Date')
    project_id = fields.Many2one('project.project', string="Project")
    product_id = fields.Many2one('product.product',"Product")
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
                              ('December', 'December')], 'Month', required=True)
    _defaults = {
        'date_today': datetime.today(),

    }

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 ' + self.month + ' ' + str(datetime.now().year)
            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)
            self.to_date = end_date

    @api.onchange('company_id')
    def onchange_field(self):
        if self.company_id.id != False:
            return {
                'domain': {
                    'account_id': [('company_id', '=', self.company_id.id), ('type', '=', 'view')],
                },
            }



    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='custom.diesel.vehicle.monthly.xlsx')