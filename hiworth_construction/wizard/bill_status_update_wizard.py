from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz


class BillStatusUpdate(models.TransientModel):
    _name = 'bill.status.update'

    current_status = fields.Many2one('current.status','Current Status')
    current_table = fields.Many2one('current.table','Current Table')
    Date = fields.Date('Date')
    update_status = fields.Many2one('current.status','Status Update')
    update_table = fields.Many2one('current.table','Table')
    remarks= fields.Text('Remarks')

    
    @api.model
    def default_get(self, default_fields):
      vals = super(BillStatusUpdate, self).default_get(default_fields)
      #context = self._context
      active_model = self._context.get('active_model')
      active_id = self._context.get('active_id')
      customer_follow_up = self.env['customer.invoice.follow.up']
      if active_model == 'customer.invoice.follow.up':
        browse_invoice_followup = customer_follow_up.browse(active_id)
        vals.update({
                      'current_status':browse_invoice_followup.current_status.id,
                      'current_table':browse_invoice_followup.current_table.id
          })

      
      
      
      return vals

    @api.multi
    def button_save(self):

      active_model = self._context.get('active_model')
      active_id = self._context.get('active_id')
      customer_follow_up = self.env['customer.invoice.follow.up']
      if active_model == 'customer.invoice.follow.up':
        browse_invoice_followup = customer_follow_up.browse(active_id)
        print 'browseeeeeeeeeeeeeeee',browse_invoice_followup
        browse_invoice_followup.write(vals={
                                              'current_status':self.current_status.id,
                                              'current_table':self.current_table.id
          })
        self.env['status.update.history'].create(vals={'Date':self.Date,

                                                        'update_status':self.update_status.id,
                                                        'update_table':self.update_table.id,
                                                        'remarks':self.remarks,
                                                        'customer_invoice_id':browse_invoice_followup.id})
        
        



class CurrentStatus(models.Model):

  _name = 'current.status'

  name = fields.Char("Status")


class CurrentTable(models.Model):

  _name = 'current.table'
  
  name = fields.Char("Table")