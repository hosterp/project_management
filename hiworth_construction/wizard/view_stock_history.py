from openerp import models, fields, api

class ViewStockHistory(models.TransientModel):


    _name = 'view.stock.history'



    @api.model
    def default_get(self,fields):
        res=super(ViewStockHistory,self).default_get(fields)
        
        active_model=self._context.get('active_model')
        
        active_ids=self._context.get('active_ids')
        
        purchase_order=self.env['purchase.comparison']
        purchase_order_line = self.env['purchase.order']
        site_purchase_model = self.env['site.purchase']
        
        list_prod=[]
        if active_model=='purchase.comparison':
            for active in active_ids:
                browse_purchase_order=purchase_order.browse(active)
                
                for purchase in browse_purchase_order:
                    for products in purchase.comparison_line:

                            
                            
                            list_prod.append(products.product_id.id)
            
            
            res.update({'products_id':[(6,0,list_prod)]})
        if active_model=='purchase.order':
            for active in active_ids:
                browse_purchase_order=purchase_order_line.browse(active)
                
                for purchase in browse_purchase_order:
                    for products in purchase.order_line:

                            
                            
                            list_prod.append(products.product_id.id)
            
            
            res.update({'products_id':[(6,0,list_prod)]})

        if active_model=='site.purchase':
            for active in active_ids:
                browse_site_purchase=site_purchase_model.browse(active)
                
                for sites in browse_site_purchase:
                    for products in sites.req_list:

                            
                            list_prod.append(products.item_id.id)
            
            
            res.update({'products_id':[(6,0,list_prod)]})

        return res




    products_id = fields.Many2many('product.product','stock_product_rel','stock_id','product_id',string='Products')
    

    


    @api.multi
    def stock_history_submit(self):
        location = self.env['stock.location'].search([('usage','=','internal')])
        return {
                'type':'ir.actions.act_window',
                'name':'Stock History',
                'res_model':'stock.history',
                'view_type':'form',
                'view_mode':'tree',
                'domain':"[('product_id','in',%s),('location_id','in',%s)]"%(self.products_id.ids,location.ids),
                'context':{'search_default_group_by_product':1,'search_default_group_by_location':1}
                
              }
