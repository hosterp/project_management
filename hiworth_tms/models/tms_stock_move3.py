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



class fleet_vehicle_log_fuel(models.Model):
	_inherit = 'fleet.vehicle.log.fuel'
	
	
	def on_change_fuel_new(self, cr, uid, ids, vehicle_id, context=None):
		data={}
		if vehicle_id:
			#print 'test=00000000000000000', vehicle_id, self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id)
			data['gasoil_id'] = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id).gasoil_id
			
		return {'value' : data}
	
	def on_change_liter_new(self, cr, uid, ids, liter, price_per_liter, fuel_old, context=None):
		data={}
		if liter and price_per_liter:
			data['total_price'] = liter*price_per_liter
		if liter:
			data['fuel_expected'] = liter+fuel_old
		  #  data['qty_stock'] = gasoil.qty_available or 0.0
		return {'value' : data}
	def on_change_total_new(self, cr, uid, ids, total_price, price_per_liter, context=None):
		data={}    
		if total_price and price_per_liter:
			data['liter'] = total_price/price_per_liter
		  #  data['qty_stock'] = gasoil.qty_available or 0.0
		return {'value' : data}

	@api.onchange('vendor_id')
	def onchange_vendor(self):
		if self.vendor_id:
			self.account_id = self.vendor_id.property_account_payable
	@api.onchange('vehicle_id')
	def onchange_vehicle(self):
		if self.vehicle_id:
			self.owner = self.vehicle_id.owner
			self.manager = self.vehicle_id.manager
			self.driver_id = self.vehicle_id.hr_driver_id
			self.gasoil_id = self.vehicle_id.gasoil_id
	
	
	tms_picking_id2 = fields.Many2one('stock.picking', 'Delivery Orders', store=True)
	payment_type = fields.Selection([('cash', 'Cash'),('bank', 'Bank'),('card', 'Card'),
									  ('nature', 'Other')], 'Type of Payment')
	fuel_old = fields.Float('Old Fuel Meter Approximated', readonly=False, states={'done':[('readonly', True)]})
	fuel_expected = fields.Float('Expected Fuel Meter', readonly=False, states={'done':[('readonly', True)]})  
	purchaser_id = fields.Many2one('res.partner', 'Purchaser', domain="[('employee','=',True)]")
	vehicle_id2 = fields.Many2one('fleet.vehicle','Vehicle', domain="[('vehicle_ok','=','True')]",readonly=False) 
	total_price = fields.Float('Price total (HT)', digits_compute=dp.get_precision('account'), help='price HT internal + Price HT external')  
	account_id = fields.Many2one('account.account', 'Account')
	journal_id = fields.Many2one('account.journal', 'Journal')
	expense_account_id = fields.Many2one('account.account', 'Expense Account')
	state = fields.Selection([
            ('info', 'Info'),
            ('draft', 'Draft'),
            #('confirmed', u'Traitement'),
            ('assigned', 'Assigned'),
            ('free', 'Free'),
            ('done', 'Done'),
            ('cancel', 'Cancel')
            ], 'State', readonly=True)
	owner = fields.Many2one('res.partner', 'Owner')
	manager = fields.Many2one('res.partner','Manager')
	date_order = fields.Date('Date Order')
	# 'cistern_id': fields.many2one('stock.location', required=False, domain=[('cistern_ok','=',True)], states={'done':[('readonly', True)]})
	# 'attendant_id': fields.many2one('hr.employee', u'Pompiste', required=False, readonly=False, domain=[('attendant_ok','=',True)], help=u"Pompiste effectuant l'approvisionnement du carburant.", states={'done':[('readonly', True)]})
	# 'category_i fields.many2one('fleet.vehicle.category', 'Category', states={'done':[('readonly', True)]})

	_defaults = {
		 'vehicle_id': False
		 }
	

	@api.multi
	def action_confirm(self):
		for rec in self:
			move = self.env['account.move']
			move_line = self.env['account.move.line']
			print 'test============', rec.journal_id.id, rec.date_order
			values = {'journal_id': rec.journal_id.id,
					  'date': rec.date_order,
					  'state':'draft'
					  }
			move_id = move.create(values)
			values2 = {
						'account_id': rec.account_id.id,
						'debit': rec.amount,
						'credit': 0,
						'name': 'Fuel Voucher',
						'move_id': move_id.id,
						'state':'draft'

					}
			line_id = move_line.create(values2)
			
			values3 = {
						'account_id': rec.expense_account_id.id,
						'credit': rec.amount,
						'debit': 0,
						'name': 'Fuel Voucher',
						'move_id': move_id.id,
						'state':'draft'

						}
			line_id = move_line.create(values3)
			move_id.button_validate()
			rec.state = 'done'
				
	
	


# 
# class stock_move(models.Model):
#     _inherit = 'stock.move'
#     
#     
#     date_expected = fields.Datetime('Expected Date', states={'done': [('readonly', True)]}, required=True, select=True, help="Scheduled date for the processing of this move")
# 
#     _defaults = {
#         'date_expected': False
#         }
	
class res_partner(models.Model):
	_inherit = 'res.partner'

	
	
	 
	is_fuel_station  = fields.Boolean('Fuel Station', help="Check this option if a fuel station")
	veh_owner = fields.Boolean(default=False)
	