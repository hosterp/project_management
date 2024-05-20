from openerp import fields, models, api, _
from datetime import datetime
import datetime
from openerp.osv import osv


class ProductTemplateNew(models.Model):
	_inherit = 'product.template'

	fuel_ok = fields.Boolean('Is Fuel')
	track_product = fields.Boolean('Track Product')


class MachineryFuelCollection(models.Model):
	_name = 'machinery.fuel.collection'

	collection_id = fields.Many2one('partner.daily.statement')
	date = fields.Date('Date')
	pump_id = fields.Many2one('res.partner','Diesel Pump', domain=[('diesel_pump_bool','=',True)])
	quantity = fields.Float('Quantity')
	uom_id = fields.Many2one('product.uom','Unit', related="product_id.uom_id")
	# per_litre = fields.Float('Per Litre Amount')
	amount_per_unit = fields.Float('Amount Per Unit')
	total_amount = fields.Float('Total Amount')
	site_id = fields.Many2one('stock.location', string="Site", domain=[('usage','=','internal')])
	supervisor_id = fields.Many2one('hr.employee', string="Supervisor", readonly="1")
	product_id = fields.Many2one('product.product', string="Fuel Type", domain=[('fuel_ok','=','True')])
	state = fields.Selection([('draft','Draft'),('approved','Approved'),('reconcile','Reconciled')], default="draft", string="Status")
	stock_move_id = fields.Many2one('stock.move')
	account_move_id = fields.Many2one('account.move')
	pump_bill_no = fields.Char('Bill No.')
	

	_defaults = {
		'date': date.today()
		}

	@api.model
	def create(self,vals):
		result = super(MachineryFuelCollection, self).create(vals)
		self.env['fuel.report'].sudo().create({
								'date':result.date,
								'item_char':result.product_id.name,
								'qty':result.quantity,
								'diesel_pump':result.pump_id.id,
								'rate':result.amount_per_unit,
								'amount':result.total_amount,
								'machinery_pump_id':result.id,
								})

		location =  self.env['stock.location'].search([('usage','=', 'supplier')], limit=1)
					
		stock_move = self.env['stock.move'].create({'name':result.product_id.id,
												'product_id':result.product_id.id,
												'product_uom_qty':result.quantity,
												'product_uom':result.uom_id.id,
												'location_id':location.id,
												'location_dest_id':result.site_id.id,
												'price_unit': result.amount_per_unit,
												'partner_stmt_id': result.collection_id.id,
												'mach_collection_id': result.id
												})
		stock_move.action_done()
		return result

	@api.multi
	def write(self,vals):
		result = super(MachineryFuelCollection, self).write(vals)
		fuel_report = self.env['fuel.report'].search([('machinery_pump_id','=',self.id)])
		location = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
		if fuel_report:
			if vals.get('date'):
				fuel_report.write({'date':vals['date']})
			if vals.get('pump_id'):
				fuel_report.write({'diesel_pump':vals['pump_id']})
			if vals.get('quantity'):
				fuel_report.write({'qty':vals['quantity']})
			if vals.get('amount_per_unit'):
				fuel_report.write({'rate':vals['amount_per_unit']})
			if vals.get('total_amount'):
				fuel_report.write({'amount':vals['total_amount']})
			if vals.get('product_id'):
				fuel_report.write({'item_char':self.env['product.product'].search([('id','=',vals['product_id'])]).name})

		stock_move = self.env['stock.move'].search([('mach_collection_id','=',self.id)])
		stock_move.unlink()
		print "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq",self.product_id,self.uom_id
		if result:
			stock_move = self.env['stock.move'].create({'name':vals.get('product_id') and self.env['product.product'].search([('id','=',vals['product_id'])]).name or self.product_id.name,
													'product_id':vals.get('product_id') and vals.get('product_id') or self.product_id.id,
													'product_uom_qty':vals.get('quantity') and vals.get('quantity') or self.quantity,
													'product_uom':vals.get('uom_id') and vals.get('uom_id') or self.uom_id.id,
													'location_id':location and location.id or False,
													'location_dest_id':vals.get('site_id') and vals.get('site_id') or self.site_id.id,
													'price_unit': vals.get('amount_per_unit') and vals.get('amount_per_unit') or self.amount_per_unit,
													'partner_stmt_id': vals.get('collection_id') and vals.get('collection_id') or False,
													'mach_collection_id': self.id
													})
			stock_move.action_done()
		return result



	@api.model
	def default_get(self, default_fields):
		vals = super(MachineryFuelCollection, self).default_get(default_fields)
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		if user:
			if user.employee_id:
				vals.update({'supervisor_id' : user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		return vals


	@api.onchange('quantity')
	def onchange_quantity(self):
		if self.quantity == 0:
			self.total_amount = 0
		else:
			if self.total_amount != 0 and self.amount_per_unit != 0 and self.quantity != round((self.total_amount / self.amount_per_unit),2):
				self.quantity = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Quantity field, Rate or Total should be Zero"
						}
					}	
			if self.quantity != 0 and self.amount_per_unit != 0:
				if self.amount_per_unit*self.quantity != self.total_amount:
					pass
				if self.total_amount == 0.0:
					self.total_amount = round((self.quantity * self.amount_per_unit),2)
			if self.total_amount != 0 and self.quantity != 0:
				if self.amount_per_unit == 0.0:
					self.amount_per_unit = round((self.total_amount / self.quantity),2)	


	@api.onchange('amount_per_unit')
	def onchange_amount_per_unit(self):
		if self.amount_per_unit == 0:
			self.total_amount = 0
		else:
			if self.total_amount != 0 and self.quantity != 0 and self.amount_per_unit != round((self.total_amount / self.quantity),2):
				self.amount_per_unit = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Rate field, Quantity or Total should be Zero."
						}
					}
			if self.quantity != 0 and self.amount_per_unit != 0:
				if self.amount_per_unit*self.quantity != self.total_amount:
					pass
				if self.total_amount == 0.0:
					self.total_amount = round((self.quantity * self.amount_per_unit),2)
			if self.total_amount != 0 and self.amount_per_unit != 0:
				if self.quantity == 0.0:
					self.quantity = round((self.total_amount / self.amount_per_unit),2)		
			


	@api.onchange('total_amount')
	def onchange_total_amount(self):
		if self.total_amount != 0:
			if self.amount_per_unit*self.quantity != self.total_amount:
				if self.amount_per_unit != 0 and self.quantity != 0:
					self.total_amount = 0.0
					return {
						'warning': {
							'title': 'Warning',
							'message': "For Entering value to Total field, Quantity or Rate should be Zero."
							}
						}
				elif self.amount_per_unit == 0 and self.quantity != 0:
					self.amount_per_unit = round((self.total_amount / self.quantity),2)
				elif self.quantity == 0 and self.amount_per_unit != 0:
					self.quantity = round((self.total_amount / self.amount_per_unit),2)				
				else:
					pass


	# @api.onchange('amount_per_unit', 'total_amount','quantity')
	# def onchange_amount(self):
	# 	if self.amount_per_unit != 0 and self.total_amount == 0:
	# 		self.total_amount = self.amount_per_unit * self.quantity
	# 	elif self.amount_per_unit == 0 and self.total_amount != 0 and self.quantity != 0:
	# 		self.amount_per_unit = self.total_amount / self.quantity
	# 	else:
	# 		self.total_amount = self.amount_per_unit * self.quantity


	@api.multi
	def button_reconcile(self):
		print 'gvjugffg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
		location =  self.env['stock.location'].search([('usage','=', 'supplier')], limit=1)
		
		stock_move = self.env['stock.move'].search([('id','=', self.stock_move_id.id)])
		if stock_move.product_uom_qty != self.quantity:
			stock_move.unlink()
			stock_move = self.env['stock.move'].create({'name':self.product_id.id,
								'product_id':self.product_id.id,
								'product_uom_qty':self.quantity,
								'product_uom':self.uom_id.id,
								'location_id':location.id,
								'location_dest_id':self.site_id.id,
								# 'picking_id': 1
								# 'picking_id': self.id
								})
			stock_move.action_done()
			print 'g-------------------------------------'
			
		move_line = self.env['account.move.line']
		journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
		if not journal:
			raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
		if len(journal) > 1:
			raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
		print 'hhhh---------------------------------------'
		values = {
				'journal_id': journal.id,
				'date': self.date,
				# 'partner_stmt_id':self.id,
				}
		move_id = self.env['account.move'].search([('id','=', self.account_move_id.id)])
		move_id.button_cancel()
		move_id.write(values)
		print '1--------------------------------------------'
		values1 = {
				'account_id': self.pump_id.property_account_payable.id,
				'name': 'Fuel Purchase',
				'debit': 0,
				'state': 'valid',
				'journal_id': journal.id,
				'period_id': move_id.period_id.id,
				'credit': self.total_amount,
				'move_id': move_id.id,
				}
		move_id.line_id[0].write(values1)
		values2 = {
				'account_id': self.site_id.related_account.id,
				'name': 'Fuel Purchase',
				'state': 'valid',
				'journal_id': journal.id,
				'period_id': move_id.period_id.id,
				'debit': self.total_amount,
				'credit': 0,
				'move_id': move_id.id,
				}
		move_id.line_id[1].write(values2)
		move_id.state = 'posted'
		self.state = 'reconcile'
		self.stock_move_id = stock_move.id
		self.account_move_id = move_id.id




class MachineryFuelAllocation(models.Model):
	_name = 'machinery.fuel.allocation'

	allocation_id = fields.Many2one('partner.daily.statement')
	date = fields.Date('Date')
	machinery_id = fields.Many2one('fleet.vehicle','Machinery', domain=[('machinery','=',True)])
	uom_id = fields.Many2one('product.uom','Unit', related="product_id.uom_id")
	available_quantity = fields.Float('Available Quantity', compute="_get_available_qty", store=True)
	current_quantity = fields.Float('Current Quantity', compute="_get_current_qty", store=True)
	quantity = fields.Float('Quantity')
	amount_per_unit = fields.Float('Amount Per Unit', compute="get_amount", store=True)
	total_amount = fields.Float('Total Amount', compute="get_amount", store=True)
	site_id = fields.Many2one('stock.location', string="Site", domain=[('usage','=','internal')])
	supervisor_id = fields.Many2one('hr.employee', string="Supervisor", readonly="1")
	product_id = fields.Many2one('product.product', string="Fuel Type", domain=[('fuel_ok','=','True')])
	state = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('reconcile','Reconciled')], default="draft", string="Status")
	stock_move_id = fields.Many2one('stock.move')
	account_move_id = fields.Many2one('account.move')


	_defaults = {
		'date': date.today()
		}

	@api.multi
	@api.depends('product_id','quantity')
	def _get_current_qty(self):
		for record in self:
			record.current_quantity = record.available_quantity - record.quantity

	@api.multi
	@api.depends('product_id','site_id')
	def _get_available_qty(self):
		for record in self:
			if record.site_id:
				product = self.env['product.product'].search([('id','=',record.product_id.id)])
				record.available_quantity = product.with_context({'location' : record.site_id.id}).qty_available
				print 'qty----------------------------------------------------', product.with_context({'location' : record.site_id.id}).qty_available



	# @api.multi
	# @api.depends('quantity','site_id','machinery_id')
	# def _compute_amts(self):
	# 	for record in self:
	# 		move = self.env['stock.move'].search([('mach_allocation_id','=',record.id)], limit=1)
	# 		record.total_amount = self.env['stock.history'].search([('move_id','=',move.id)], limit=1).inventory_value
	# 		if record.quantity:
	# 			record.amount_per_unit = (record.total_amount)/record.quantity


	@api.multi
	@api.depends('quantity')
	def get_amount(self):
		for record in self:
			amt = 0
			quantity = record.quantity
			quants = self.env['stock.quant'].search([('product_id','=', record.product_id.id),('location_id','=', record.site_id.id)], order="in_date asc")
			for quant_id in quants:
				print 'quant_id----------------------------------', quant_id.qty, quantity
				if quantity > 0:
					if quant_id.qty >= quantity:
						if quant_id.qty != 0:
							amt += (quant_id.inventory_value/quant_id.qty) * quantity
							quantity = quantity - quant_id.qty
							print 'amt11-----------------------------------', amt
					else:
						amt += quant_id.inventory_value
						quantity = quantity - quant_id.qty
						print 'amt22-----------------------------------', amt

			record.total_amount = amt
			if record.quantity != 0:
				record.amount_per_unit = amt/record.quantity


	@api.model
	def default_get(self, default_fields):
		vals = super(MachineryFuelAllocation, self).default_get(default_fields)
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		if user:
			if user.employee_id:
				vals.update({'supervisor_id' : user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		return vals



	@api.multi
	def button_reconcile(self):
		print 'gvjugffg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
		location =  self.env['stock.location'].search([('name','=', 'Product Consumed'),('usage','=', 'inventory')], limit=1)
		
		stock_move = self.env['stock.move'].search([('id','=', self.stock_move_id.id)])
		if stock_move.product_uom_qty != self.quantity:
			stock_move.unlink()
			stock_move = self.env['stock.move'].create({'name':self.product_id.id,
														'product_id':self.product_id.id,
														'product_uom_qty':self.quantity,
														'product_uom':self.uom_id.id,
														'location_id':self.site_id.id,
														'location_dest_id':location.id,
														# 'picking_id': 1
														# 'picking_id': self.id
														})
			stock_move.action_done()
			print 'g-------------------------------------'
		move_line = self.env['account.move.line']
		journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
		if not journal:
			raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
		if len(journal) > 1:
			raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
		print 'hhhh---------------------------------------'
		values = {
				'journal_id': journal.id,
				'date': self.date,
				# 'partner_stmt_id':self.id,
				}
		move_id = self.env['account.move'].search([('id','=', self.account_move_id.id)])
		move_id.button_cancel()
		move_id.write(values)
		print '1--------------------------------------------'
		values1 = {
				'account_id': self.site_id.related_account.id,
				'name': 'Fuel Allocation',
				'debit': 0,
				'state': 'valid',
				'journal_id': journal.id,
				'period_id': move_id.period_id.id,
				'credit': self.total_amount,
				'move_id': move_id.id,
				}
		move_id.line_id[0].write(values1)
		values2 = {
				'account_id': self.machinery_id.related_account.id,
				'name': 'Fuel Allocation',
				'state': 'valid',
				'journal_id': journal.id,
				'period_id': move_id.period_id.id,
				'debit': self.total_amount,
				'credit': 0,
				'move_id': move_id.id,
				}
		move_id.line_id[1].write(values1)
		move_id.state = 'posted'
		self.state = 'reconcile'
		self.stock_move_id = stock_move.id
		self.account_move_id = move_id.id
