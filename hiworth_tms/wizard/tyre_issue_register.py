from openerp import fields, models, api

class TyreIssueRegisterWizard(models.TransientModel):
    _name = 'tyre.issue.register.wizard'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")


    @api.multi
    def button_print_tyre_issue_register(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,

        }

        return {
            'name': 'Tyre Issue Register Report',
            'type': 'ir.actions.report.xml',
            'report_name': "hiworth_tms.report_tyre_issue_register",

            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def get_details(self):
        for rec in self:
            tyre_list = self.env['retreading.tyre.line'].search([('fitting_date','>=',rec.date_from),('fitting_date','<=',rec.date_to)])
            return tyre_list