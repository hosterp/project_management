from openerp import fields, models, api



class DoYouWantToSave(models.TransientModel):
	_name = 'do.you.want.to.save.wizard'
	
	
	
	@api.multi
	def action_submit(self):
		active_model = self._context.get('active_model')
		if active_model == 'site.purchase':
			return self.env['site.purchase'].browse(self._context.get('active_id'))
			#return super(SitePurchase).create(vals)