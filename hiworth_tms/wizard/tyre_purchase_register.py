from openerp import fields, models, api

class TyrePurchaseRegisterWizard(models.TransientModel):
    _name = 'tyre.purchase.register.wizard'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")


    @api.multi
    def button_print_tyre_purchase_register(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,

        }

        return {
            'name': 'Tyre Purchase Register Report',
            'type': 'ir.actions.report.xml',
            'report_name': "hiworth_tms.report_tyre_purchase_register",

            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def get_details(self):
        for rec in self:
            tyre_list = self.env['vehicle.tyre'].search([('purchase_date','>=',rec.date_from),('purchase_date','<=',rec.date_to)])
            return tyre_list