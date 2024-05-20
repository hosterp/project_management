from openerp import models, fields, api, _

class KmDetailsConfig(models.Model):
    _name = 'km.details.config'


    # @api.model
    # def create(self,vals):
    #     res = super(KmDetailsConfig, self).create(vals)
    #     base_url = self.env['ir.config_parameter'].get_param('web.base.url')
    #     base_url += '/web#id=%d&view_type=form&model=%s' % (res.id, res._name)
    #     user_list = []
    #     for user in self.env['res.users'].search([]):
    #         if user.has_group('hiworth_construction.group_ceo'):
    #             user_list.append(user.id)
    #     session_user = []
    #     session_user.extend(user_list)
    #     session_user.append(self.env.user.id)
    #     session = self.env['im_chat.session'].create({'user_ids': [(6, 0, session_user)]})
    #     for us in user_list:
    #         self.env['im_chat.message'].create({'from_id': self.env.user.id,
    #                                             'to_is': us,
    #                                             'to_id': session.id,
    #                                             'message': 'Please Approve the KM%s' % (base_url)})
    #     return res
    @api.onchange('supplier_id','from_location_id')
    def onchange_supplier_id(self):
        for rec in self:
            if rec.supplier_id:
                rec.name = rec.supplier_id.name
            if rec.from_location_id:
                rec.name = rec.from_location_id.name

    name = fields.Char("Name")
    supplier_id = fields.Many2one('res.partner',"Supplier Name",domain="[('supplier','=',True)]")
    from_location_id = fields.Many2one('stock.location',"From Location Name",domain="[('usage','=','internal')]")
    location_id = fields.Many2one('stock.location',"Location Name",domain="[('usage','=','internal')]")
    km = fields.Float("KM")
    with_effect = fields.Date("With Effect From")
    state = fields.Selection([('draft','For Approval'),('confirm','Approved')],default='draft')

    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'


    @api.multi
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'