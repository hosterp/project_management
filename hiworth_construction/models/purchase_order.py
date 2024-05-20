# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare

class purchase_order(osv.osv):
	_inherit = 'purchase.order'

	def onchange_dest_address_id(self, cr, uid, ids, address_id, context=None):
		if not address_id:
			return {}
		address = self.pool.get('res.partner')
		values = {}
		supplier = address.browse(cr, uid, address_id, context=context)
		if supplier:
			location_id = supplier.property_stock_customer.id
			values.update({'location_id': location_id})
		return {'value':values}

	def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
		partner = self.pool.get('res.partner')
		if not partner_id:
			return {'value': {
				'fiscal_position': False,
				'payment_term_id': False,
				}}

		company_id = context.get('company_id') or self.pool.get('res.users')._get_company(cr, uid, context=context)
		if not company_id:
			raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
		fp = self.pool['account.fiscal.position'].get_fiscal_position(cr, uid, company_id, partner_id, context=context)
		supplier_address = partner.address_get(cr, uid, [partner_id], ['default'], context=context)
		supplier = partner.browse(cr, uid, partner_id, context=context)
		return {'value': {
			'pricelist_id': supplier.property_product_pricelist_purchase.id,
			'fiscal_position': fp or supplier.property_account_position and supplier.property_account_position.id,
			'payment_term_id': supplier.property_supplier_payment_term.id or False,
			'account_id': supplier.property_account_payable.id,
			}}

	def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, group_id, context=None):
		''' prepare the stock move data from the PO line. This function returns a list of dictionary ready to be used in stock.move's create()'''
		product_uom = self.pool.get('product.uom')
		
		if order_line.expected_rate != 0:
			price_unit = order_line.expected_rate
		else:
			price_unit = order_line.price_unit
		if order_line.taxes_id:
			taxes = self.pool['account.tax'].compute_all(cr, uid, order_line.taxes_id, price_unit, 1.0,
															 order_line.product_id, order.partner_id)
			price_unit = taxes['total']
		if order_line.product_uom.id != order_line.product_id.uom_id.id:
			price_unit *= order_line.product_uom.factor / order_line.product_id.uom_id.factor
		if order.currency_id.id != order.company_id.currency_id.id:
			# we don't round the price_unit, as we may want to store the standard price with more digits than allowed by the currency
			price_unit = self.pool.get('res.currency').compute(cr, uid, order.currency_id.id, order.company_id.currency_id.id, price_unit, round=False, context=context)
		res = []
		if order.location_id.usage == 'customer':
			name = order_line.product_id.with_context(dict(context or {}, lang=order.dest_address_id.lang)).display_name
		else:
			name = order_line.name or ''
		move_template = {
			'name': name,
			'product_id': order_line.product_id.id,
			'product_uom': order_line.product_uom.id,
			'product_uos': order_line.product_uom.id,
			'date': order.date_order,
			'date_expected': fields.date.date_to_datetime(self, cr, uid, order_line.date_planned, context),
			'location_id': order.partner_id.property_stock_supplier.id,
			'location_dest_id': order.location_id.id,
			'picking_id': picking_id,
			'partner_id': order.dest_address_id.id,
			'move_dest_id': False,
			'state': 'draft',
			'purchase_line_id': order_line.id,
			'company_id': order.company_id.id,
			'price_unit': price_unit,
			'picking_type_id': order.picking_type_id.id,
			'group_id': group_id,
			'procurement_id': False,
			'origin': order.name,
			'route_ids': order.picking_type_id.warehouse_id and [(6, 0, [x.id for x in order.picking_type_id.warehouse_id.route_ids])] or [],
			'warehouse_id':order.picking_type_id.warehouse_id.id,
			'invoice_state': order.invoice_method == 'picking' and '2binvoiced' or 'none',
		}
		if order_line.required_qty != 0:
			diff_quantity = order_line.required_qty
		else:
			diff_quantity = order_line.product_qty
		for procurement in order_line.procurement_ids:
			procurement_qty = product_uom._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, to_uom_id=order_line.product_uom.id)
			tmp = move_template.copy()
			tmp.update({
				'product_uom_qty': min(procurement_qty, diff_quantity),
				'product_uos_qty': min(procurement_qty, diff_quantity),
				'move_dest_id': procurement.move_dest_id.id,  #move destination is same as procurement destination
				'group_id': procurement.group_id.id or group_id,  #move group is same as group of procurements if it exists, otherwise take another group
				'procurement_id': procurement.id,
				'invoice_state': procurement.rule_id.invoice_state or (procurement.location_id and procurement.location_id.usage == 'customer' and procurement.invoice_state=='2binvoiced' and '2binvoiced') or (order.invoice_method == 'picking' and '2binvoiced') or 'none', #dropship case takes from sale
				'propagate': procurement.rule_id.propagate,
			})
			diff_quantity -= min(procurement_qty, diff_quantity)
			res.append(tmp)
		#if the order line has a bigger quantity than the procurement it was for (manually changed or minimal quantity), then
		#split the future stock move in two because the route followed may be different.
		if float_compare(diff_quantity, 0.0, precision_rounding=order_line.product_uom.rounding) > 0:
			move_template['product_uom_qty'] = diff_quantity
			move_template['product_uos_qty'] = diff_quantity
			res.append(move_template)
		return res

 
	def action_picking_create(self, cr, uid, ids, context=None):
		print 'test=========================1'
		for order in self.browse(cr, uid, ids):
			picking_vals = {
				'picking_type_id': order.picking_type_id.id,
				'partner_id': order.partner_id.id,
				'date': order.date_order,
				'origin': order.name,
				# 'account_id': order.account_id.id,
				'is_purchase': True,
				'purchase_id': order.id,
				'source_location_id': order.picking_type_id.default_location_src_id.id,
			}
			picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
			print 'test========================2', picking_id
			self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
		return picking_id

	

	def action_invoice_create(self, cr, uid, ids, context=None):
		print 'test=============================1'
		"""Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
		:param ids: list of ids of purchase orders.
		:return: ID of created invoice.
		:rtype: int
		"""
		context = dict(context or {})
		inv_obj = self.pool.get('account.invoice')
		inv_line_obj = self.pool.get('account.invoice.line')
		res = False
		uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
		for order in self.browse(cr, uid, ids, context=context):
			context.pop('force_company', None)
			if order.company_id.id != uid_company_id:
				#if the company of the document is different than the current user company, force the company in the context
				#then re-do a browse to read the property fields for the good company.
				context['force_company'] = order.company_id.id
				order = self.browse(cr, uid, order.id, context=context)
			# generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
			inv_lines = []
			for po_line in order.order_line:
				if po_line.state == 'cancel':
					continue
				acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
				inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
				inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
				inv_lines.append(inv_line_id)
				po_line.write({'invoice_lines': [(4, inv_line_id)]})
			# get invoice data and create invoice
			inv_data = self._prepare_invoice(cr, uid, order, inv_lines, context=context)
			inv_id = inv_obj.create(cr, uid, inv_data, context=context)
			# compute the invoice
			inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)
			#To make invoice Deactive Before Reception
			self.pool.get('account.invoice').write(cr, uid, inv_id, {'not_visible': True, 'purchase_id':order.id})
			inv = self.pool.get('account.invoice').browse(cr, uid, inv_id)
			# Link this new invoice to related purchase order
			order.write({'invoice_ids': [(4, inv_id)]})
			res = inv_id
		return res
	
	

# class ReportSitePurchasTemplate(models.AbstractModel):
#
# 	_name = 'report.hiworth_construction.report_site_purchase_template'
#
# 	@api.model
# 	def render_html(self, docids, data=None):
# 		if data.get('form'):
# 			datas = []
# 			site = []
# 			domain = []
# 			if data['form']['date_from']:
# 				domain.append(('order_date', '>=', str(data['form']['date_from']) + " 00:01:01"))
# 			if data['form']['date_to']:
# 				domain.append(('order_date', '<=', str(data['form']['date_to']) + " 23:59:59"))
# 			if data['form']['requested_site_id']:
# 				domain.append(('site', '<=', data['form']['requested_site_id'][0]))
# 			if data['form']['project_id']:
# 				domain.append(('project_id', '<=', data['form']['project_id'][0]))
# 			for sp in self.env['site.purchase'].search(domain):
# 				if sp.site.id in site:
# 					for d in datas:
# 						if d['site_id'] == sp.site.id:
# 							for i in sp.req_list:
# 								if i.stock_type == 'company_stock':
# 									d['lines'].append({
# 										'location_id': i.location_id.name,
# 										'unit': i.unit.name,
# 										'item_id': i.item_id.name,
# 										'default_code': i.item_id.default_code,
# 										'requested_quantity': i.requested_quantity,
# 										'quantity': i.quantity,
# 										'rate': i.rate,
# 										'estimated_amount': i.estimated_amt,
# 										'remarks': i.remarks,
# 									})
# 				else:
# 					s = {'site': sp.site.name, 'site_id': sp.site.id, 'lines': [], 'project': sp.project_id.name, 'approved_by': sp.purchase_manager.name or ''}
# 					for i in sp.req_list:
# 						if i.stock_type == 'company_stock':
# 							s['lines'].append({
# 								'location_id': i.location_id.name or '',
# 								'unit': i.unit.name or '',
# 								'item_id': i.item_id.name or '',
# 								'default_code': i.item_id.default_code or '',
# 								'requested_quantity': i.requested_quantity or '',
# 								'quantity': i.quantity or '',
# 								'rate': i.rate or '',
# 								'estimated_amount': i.estimated_amt or '',
# 								'remarks': i.remarks or '',
# 							})
# 					if s['lines']:
# 						datas.append(s)
# 						site.append(sp.site.id)
# 			docargs = {
# 				'doc_ids': data['form']['id'],
# 				'doc_model': 'site.purchase',
# 				'docs': datas,
# 			}
#
#         	return self.env['report'].render('hiworth_construction.report_site_purchase_template', docargs)