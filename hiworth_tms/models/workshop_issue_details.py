from openerp import models, fields, api, _


class FleetWorkshop(models.Model):
    _name = 'fleet.workshop'

    name = fields.Char("Name")

class WorkshopIssue(models.Model):
    _name = 'workshop.issue'

    @api.model
    def create(self, vals):
        vals.update({'name':self.env['ir.sequence'].next_by_code('workshop.issue.code')})
        res = super(WorkshopIssue, self).create(vals)
        return res

    name=fields.Char("Number")
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
    workshop_id = fields.Many2one('fleet.workshop',"Workshop")
    date_order = fields.Date("Date")
    project_id = fields.Many2one('project.project',"Project")
    issue_line_ids = fields.One2many('workshop.issue.line','workshop_id',"Item details")
    state = fields.Selection([('draft','Draft'),
                              ('confirm','Confirm')],default='draft')

    @api.multi
    def action_confirm(self):
        for rec in self:
            for line in rec.issue_line_ids:
                line.item_id.product_tmpl_id.write({'non_useable_qty':line.item_id.product_tmpl_id.useable_qty+ line.quantity,
                                    'useable_qty':line.item_id.product_tmpl_id.qty_available - (line.item_id.product_tmpl_id.useable_qty + line.quantity)})

            location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            stock = self.env['stock.picking'].create({
    
                'source_location_id': rec.project_id.location_id.id,
    
                'site': location.id,
                'order_date': rec.date_order,
                'account_id': rec.project_id.location_id.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
               
            })
            for req in rec.issue_line_ids:
                stock_move = self.env['stock.move'].create({
                    'location_id': rec.project_id.location_id.id,
                    'project_id': rec.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': rec.project_id.location_id.id}).qty_available,
                    'name': req.item_id.name,
                    'product_uom_qty': req.quantity,
                    'product_uom': req.unit_id.id,
                    'price_unit': 1,
                    'date': rec.date_order,
                    'date_expected': rec.date_order,
                    'account_id': rec.project_id.location_id.related_account.id,
                    'location_dest_id': location.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
            stock.action_done()
            rec.state = 'confirm'

class WorkshopIssueLine(models.Model):
    _name = 'workshop.issue.line'

    @api.depends('quantity','price')
    def compute_total(self):
        for rec in self:
            rec.total = rec.quantity * rec.price

    @api.onchange('item_id')
    def onchange_item_id(self):
        for rec in self:
            if rec.item_id:
                rec.unit_id = rec.item_id.uom_id.id
                rec.available_qty = rec.item_id.with_context(
                    {'location': rec.workshop_id.project_id.location_id.id}).qty_available

    @api.depends('quantity')
    def compute_rem_qty(self):
        for rec in self:
            rec.rem_qty = rec.available_qty - rec.quantity

    item_id = fields.Many2one('product.product',"Product")
    unit_id = fields.Many2one('product.uom',"Unit of Measure")
    available_qty = fields.Float("Available Quantity")
    quantity = fields.Float("Quantity")
    rem_qty = fields.Float("Remaining Quantity",compute='compute_rem_qty')
    price = fields.Float("Price")
    total = fields.Float("Total", compute='compute_total')
    workshop_id = fields.Many2one('workshop.issue',"Workshop")


class Product(models.Model):
    _inherit = 'product.product'

    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = super(Product, self)._product_available(cr, uid, ids, field_names=None, arg=False, context=None)

        for product in self.search(cr, uid,[('id','in',ids)], context=None):
            quant = self.pool.get('stock.quant').search(cr, uid,[('product_id','=',product)], context=None)

            total = sum(self.pool.get('stock.quant').browse(cr, uid,quant, context=None).mapped('qty'))

            res[product]['qty_available'] = total

        return res

    useable_qty = fields.Float("Usable Quantity")
    non_useable_qty = fields.Float("Non-Usable Quantity")

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    useable_qty = fields.Float("Usable Quantity")
    non_useable_qty = fields.Float("Non-Usable Quantity")

class ProductCategory(models.Model):
    _inherit = 'product.category'

    vehicle_type = fields.Selection([('tyre', "Tyre"), ('lub', 'Lub'), ('oil', "Oil"), ('fuel', 'Fuel'),('spare','Spare'),('battery','Battery')])