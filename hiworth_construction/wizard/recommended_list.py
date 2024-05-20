from openerp import models, fields, api


class RecommendedList(models.TransientModel):
	_name = 'recommended.list'
	
	@api.model
	def default_get(self, fields):
		res = super(RecommendedList, self).default_get(fields)
		print'blalalalalala', self._context
		active_model = self._context.get('active_model')
		print 'rrrrrrrrrrrrrrrrrrrrraaaaa', active_model
		active_ids = self._context.get('active_ids')
		print'clllllllaaaaaaaaaaaaaaaaaaaaa', active_ids
		purchase_order = self.env['purchase.comparison']
		print 'vuuuuuuuuuuuuuuuuuuuu', purchase_order
		list_prod = []
		if active_model == 'purchase.comparison':
			for active in active_ids:
				browse_purchase_order = purchase_order.browse(active)
				print 'vuuuuuuuuuuuuuuuuuuuu', purchase_order
				for purchase in browse_purchase_order:
					for products in purchase.comparison_line:
						print 'vuuuuuuuuuuuuuuuuuuuu', purchase_order
						max=products.rate1
						suppilier = products.res_id.partner_id1.id
						if max>products.rate2:
							max = products.rate2
							suppilier = products.res_id.partner_id2.id
						if max>products.rate3:
							max = products.rate3
							suppilier = products.res_id.partner_id3.id
						if max>products.rate4:
							max = products.rate4
							suppilier = products.res_id.partner_id4.id
						if max>products.rate5:
							max = products.rate5
							suppilier = products.res_id.partner_id5.id
						print "qqqqqqqqqqqqqqqqqqqqqqqqqqqqq", suppilier
						list_prod.append((0,0,{'supplier_id':suppilier,
											   'product_ids':[products.product_id.id]}))
			
			print "frrrrrrrrrrrrrrrrrrrrrrrrr", list_prod
			res.update({'recommeneded_list_line_ids': list_prod})
		return res
	
	recommeneded_list_line_ids=fields.One2many('recommended.list.line','recommended_list_id',"Products and Suppliers")
	
class RecommendedListLine(models.TransientModel):
	_name = 'recommended.list.line'
	
	supplier_id = fields.Many2one('res.partner','Supplier')
	product_ids = fields.Many2many('product.product',string="Products")
	recommended_list_id = fields.Many2one('recommended.list',string="Recommended List")
	
	
	
	
	
	
	
	
	
	
	