from openerp.exceptions import except_orm, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
import time
import datetime
#from datetime import datetime, timedelta
from datetime import date
#from openerp.osv import fields, osv
from openerp.tools.translate import _
#from openerp import SUPERUSER_ID
import openerp.addons.decimal_precision as dp
#from openerp.osv import fields, osv
from datetime import timedelta



class fleet_vehicle_odometer_update(models.Model):
    _name = 'fleet.vehicle.odometer.update'
    
    
    
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', states={'done':[('readonly', True)]})
    date = fields.Date('Date')
    fuel_old = fields.Float('Fuel Previous')
    fuel_new = fields.Float('Fuel New')
    odometer_old = fields.Float('Odometer Previous')
    odometer_new = fields.Float('Odometer New')
    remarks = fields.Text('Remarks')
    is_updated = fields.Boolean('Is Updated')
    
    
    @api.one 
    def update_vehicle(self):
        if self.odometer_new:
            obj=self.vehicle_id.write({'odometer' : self.odometer_new})
            self.write({'is_updated' : True})
        if self.fuel_new:
            obj2=self.vehicle_id.write({'fuel_odometer' : self.fuel_new})
            self.write({'is_updated' : True})

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    