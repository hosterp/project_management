from openerp import fields, models, api
from datetime import datetime
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta


class ReportDieselVehicleDaily(models.TransientModel):
    _name = 'report.diesel.vehicle.daily'

    location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', 'Company')
    date_today = fields.Date('Date', required=True)
    project_id = fields.Many2one('project.project',"Project")
    product_id = fields.Many2one('product.product',"Fuel Type")
    defaults = {
        'date_today': datetime.now(),

    }

    @api.multi
    def generate_xls_report_daily(self):
        return self.env["report"].get_action(self, report_name='custom.diesel.vehicle.report.daily.xlsx')



