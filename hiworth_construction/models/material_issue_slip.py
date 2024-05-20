from openerp import fields, models, api
from datetime import datetime
from openerp.exceptions import Warning as UserError,ValidationError
from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
from openerp.exceptions import except_orm, ValidationError
import openerp.addons.decimal_precision as dp


class MaterialIssueSlip(models.Model):
    _name = 'material.issue.slip'
    _order = 'date desc'




    @api.onchange('project_id')
    def onchange_project(self):
        for rec in self:
            if rec.project_id:
                rec.source_location_id = rec.project_id.location_id
        return {'domain':{'goods_receive_report_id':[('project_id','=',rec.project_id.id)]}}

    @api.depends('material_issue_slip_lines_ids')
    def compute_item_list(self):
        for rec in self:
            item = ''
            for lines in rec.material_issue_slip_lines_ids:
                item += lines.item_id.name + ','
            rec.item_list = item

    @api.depends('material_issue_slip_lines_ids')
    def compute_item_qty(self):
        for rec in self:
            quantity = 0
            for lines in rec.material_issue_slip_lines_ids:
                quantity += lines.quantity
            rec.total_quantity = quantity


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.project_id and rec.is_receive:
                rec.project_id.mis_no -= 1
                if rec.picking_id:
                    for move in rec.picking_id.move_lines:
                        for quant in move.quant_ids:
                            quant.with_context({'force_unlink':True}).unlink()
                        move.unlink()
            if not rec.is_receive and rec.project_id:
                rec.project_id.mrn_no -= 1
                if rec.picking_id:
                    for move in rec.picking_id.move_lines:
                        for quant in move.quant_ids:
                            quant.with_context({'force_unlink':True}).unlink()
                        move.unlink()

        return super(MaterialIssueSlip, self).unlink()

    @api.multi
    def write(self, vals):
        for rec in self:
            location = self.env['stock.location'].search([('usage','=','inventory')],limit=1)
            if vals.get('date'):
                rec.picking_id.order_date = vals.get('date')
                for line in rec.material_issue_slip_lines_ids:
                    line.move_id.date = vals.get('date')
                    line.move_id.date_expected = vals.get('date')
                    for quant in line.move_id.quant_ids:
                        quant.in_date = vals.get('date')
            if vals.get('material_issue_slip_lines_ids'):
                for li in vals.get('material_issue_slip_lines_ids'):
                    
                    if  li[0]==1:
                        line_id = self.env['material.issue.slip.line'].browse(li[1])
                        if li[2].get('req_qty')>=0:
                            line_id.move_id.product_uom_qty = li[2].get('req_qty')
                            for quant in line_id.move_id.quant_ids:
                                if quant.qty <0:

                                    quant.qty = - li[2].get('req_qty')
                                else:
                                    quant.qty = li[2].get('req_qty')
                        if line_id.req_qty == 0 and li[2].get('req_qty')>0:
                            line_id.move_id.product_uom_qty = li[2].get('req_qty')
                            quant_id1 = self.env['stock.quant'].create({'product_id':line_id.item_id.id,
                                                                      'qty': - li[2].get('req_qty'),
                                                                      'location_id':rec.source_location_id.id,
                                                                      'in_date':rec.date})
                            quant_id2 = self.env['stock.quant'].create({'product_id': line_id.item_id.id,
                                                                       'qty':  li[2].get('req_qty'),
                                                                       'location_id': line_id.move_id.location_dest_id.id,
                                                                       'in_date': rec.date})
                            line_id.move_id.quant_ids = [(6,0,[quant_id1.id,quant_id2.id])]

                        if li[2].get('item_id'):
                            line_id.move_id.product_id = li[2].get('item_id')
                            for quant in line_id.move_id.quant_ids:
                                    quant.product_id = li[2].get('item_id')    
                    if li[0] == 2:

                        line_id = self.env['material.issue.slip.line'].browse(li[1])
                        for quant in line_id.move_id.quant_ids:
                            quant.with_context({'force_unlink':True}).unlink()
                        line_id.move_id.unlink()


                    if li[0]==0:
                        
                        stock_move = self.env['stock.move'].create({
                            'location_id': rec.source_location_id.id,
                            'project_id': rec.project_id.id,
                            'product_id': li[2]['item_id'],
                            'available_qty': self.env['product.product'].browse(li[2]['item_id']).qty_available,
                            'name': li[2]['desc'],
                            'date': rec.date,
                            'date_expected': rec.date,
                            'product_uom_qty': li[2]['req_qty'],
                            'product_uom': self.env['product.product'].browse(li[2]['item_id']).uom_id.id,
                            'price_unit': li[2]['rate'],
                            'account_id': rec.source_location_id.related_account.id,
                            'location_dest_id': location.id,
                            'picking_id': rec.picking_id.id,
                            
                        })
                       

                        stock_move.action_done()
                        li[2].update({'move_id':stock_move.id})
           
        return super(MaterialIssueSlip, self).write(vals)

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.brand_id = rec.vehicle_id.brand_id.id
                rec.model_id = rec.vehicle_id.model_id.id
                rec.chase_no = rec.vehicle_id.chase_no
                rec.engine_no = rec.vehicle_id.engine_no


    name = fields.Char('Name')
    date = fields.Datetime('Date', default=lambda self: fields.datetime.now())
    project_id = fields.Many2one('project.project','Project')
    employee_id = fields.Many2one('hr.employee', 'Supervisor')
    partner_id = fields.Many2one('res.partner',"Sub Contracor")
    source_location_id = fields.Many2one('stock.location',"Source Location")
    location_id = fields.Many2one('stock.location',"Location")
    material_issue_slip_lines_ids = fields.One2many('material.issue.slip.line','material_issue_slip_id',string="Item List")
    state = fields.Selection([('draft','Draft'),
                              ('cancel','Cancel')],default='draft',String="Status")

    user_id = fields.Many2one('res.users',"Users")
    store_manager_id = fields.Many2one('res.users',"Supervisor")
    is_debit_note = fields.Boolean("Is a Debit Note",default=False)
    is_receive = fields.Boolean("Receive")
    item_list = fields.Char(string="Items", compute='compute_item_list')
    total_quantity = fields.Char(string="Quantity", compute='compute_item_qty')
    own_vehicle = fields.Boolean(string="Own Vehicle",default=False)
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle No")
    model_id = fields.Many2one('fleet.vehicle.model',"Model")
    brand_id = fields.Many2one('fleet.vehicle.model.brand',"Brand")
    chase_no = fields.Char("Chase No")
    engine_no = fields.Char("Model No")
    picking_id = fields.Many2one('stock.picking',"Stock Picking")
    goods_receive_report_id = fields.Many2one('goods.recieve.report',"GRR No")



    @api.onchange('goods_receive_report_id')
    def onchange_grr_id(self):
        for rec in self:
            val_list =[]

            if rec.goods_receive_report_id:
                for line in rec.goods_receive_report_id.goods_recieve_report_line_ids:
                    rate = 0
                    if line.quantity_accept != 0:
                        rate = line.total_amount/line.quantity_accept

                    values = {'item_id':line.item_id.id,
                              'desc':line.desc,
                              'unit_id':line.unit_id.id,
                              'rate':rate,
                              }
                    val_list.append((0,0,values))
            rec.material_issue_slip_lines_ids = val_list




    @api.multi
    def action_cancel(self):
        for rec in self:
            for line in rec.material_issue_slip_lines_ids:
                line.write({'req_qty':0})
                line.move_id.write({'product_uom_qty':0})
                for quant in line.move_id.quant_ids:
                    quant.write({'qty':0})
            rec.state = 'cancel'

    @api.multi
    def action_receive(self):
        for rec in self:
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            location = self.env['stock.location'].search([('usage','=','inventory')],limit=1)


            stock = self.env['stock.picking'].create({

                'source_location_id': location.id,

                'site': rec.source_location_id.id,
                'order_date': rec.date,
                'account_id': rec.source_location_id.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })


            for req in rec.material_issue_slip_lines_ids:
                stock_history = self.env['stock.history'].search(
                    [('date', '<=', rec.date), ('location_id', '=', rec.source_location_id.id),('product_id','=',req.item_id.id)])
                available = 0
                for hist in stock_history:
                    available += hist.quantity
                stock_move = self.env['stock.move'].create({
                    'location_id': location.id,
                    'project_id': rec.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': available,
                    'name': req.desc,
                    'date': rec.date,
                    'date_expected': rec.date,
                    'product_uom_qty': req.req_qty,
                    'product_uom': req.unit_id.id,
                    'price_unit': 1,
                    'account_id': rec.source_location_id.related_account.id,
                    'location_dest_id': rec.source_location_id.id,
                    'picking_id':stock.id
                })
                stock_move.action_done()
                req.move_id = stock_move.id
            stock.action_done()
            rec.picking_id = stock.id


    @api.multi
    def compute_avilable_quantity(self):
        print "satatrtttttttttttttttttttt"
        for record in self:
            for rec in record.material_issue_slip_lines_ids:
                print "fffffffffffffffffffffffffff"
                stock_history = self.env['stock.history'].search(
                    [('date', '<=', rec.date), ('location_id', '=', rec.material_issue_slip_id.source_location_id.id),
                     ('product_id', '=', rec.item_id.id)])
                available = 0
                for hist in stock_history:
                    available += hist.quantity
                rec.stock = available
                if rec.stock < rec.req_qty:
                    rec.req_qty = rec.stock
    @api.multi
    def button_request(self):
        for res in self.search([]):

            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            stock = self.env['stock.picking'].create({

                'source_location_id': res.source_location_id.id,

                'site': location.id,
                'order_date': res.date,
                'account_id': res.source_location_id.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': res.project_id.id,
            })
            for req in res.material_issue_slip_lines_ids:
                req.compute_stock_balance()
                stock_move = self.env['stock.move'].create({
                    'location_id': res.source_location_id.id,
                    'project_id': res.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': res.source_location_id.id}).qty_available,
                    'name': req.desc,
                    'product_uom_qty': req.req_qty,
                    'product_uom': req.unit_id.id,
                    'price_unit': 1,
                    'date': res.date,
                    'date_expected': res.date,
                    'account_id': res.source_location_id.related_account.id,
                    'location_dest_id': location.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                req.move_id = stock_move.id
            stock.action_done()
            res.picking_id = stock.id

    @api.model
    def create(self,vals):
        res =super(MaterialIssueSlip, self).create(vals)
        location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
        if res.is_receive == False:
            res.project_id.mis_no+=1
            mis_no=str(res.project_id.mis_no).zfill(3) + '/'+str(datetime.now().year)
            res.name = 'MRN/'+mis_no
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            stock = self.env['stock.picking'].create({

                'source_location_id': res.source_location_id.id,

                'site': location.id,
                'order_date': res.date,
                'account_id': res.source_location_id.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': res.project_id.id,
            })
            for req in res.material_issue_slip_lines_ids:
                stock_move = self.env['stock.move'].create({
                    'location_id': res.source_location_id.id,
                    'project_id': res.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': res.source_location_id.id}).qty_available,
                    'name': req.desc,
                    'product_uom_qty': req.req_qty,
                    'product_uom': req.unit_id.id,
                    'price_unit': 1,
                    'date': res.date,
                    'date_expected':res.date,
                    'account_id': res.source_location_id.related_account.id,
                    'location_dest_id': location.id,
                    'picking_id':stock.id,
                    
                })
                stock_move.action_done()
                req.move_id = stock_move.id
            stock.action_done()
            res.picking_id = stock.id

        else:
            res.project_id.mrn_no+=1
            mrn_no=str(res.project_id.mrn_no).zfill(3)  +'/'+str(datetime.now().year)
            res.name = 'MRN/'+mrn_no
            res.action_receive()
            
        if res.vehicle_id:
            for line in res.material_issue_slip_lines_ids:
                self.env['fleet.issue.details'].create({'name':res.vehicle_id.id,
                                                        'date':res.date,
                                                        'mrn_no':res.id,
                                                        'item_id':line.item_id.id,
                                                        'qty':line.req_qty,
                                                        'rate':line.rate,
                                                        'amount':line.req_qty * line.rate})
        return res
    # @api.constrains('quantity_rec','po_quantity')
    # def constraints_quantity(self):
    #     if self.po_quantity < self.quantity_rec:
    #         raise ValidationError(_('Received Quantity cannot be greater than PO Quantity.'))
    #
    #     return res


    @api.multi
    def action_debit_note(self):
        for rec in self:
            if  rec.is_debit_note == True:
                if rec.employee_id:
                    partner = rec.employee_id.user_id.partner_id.id
                else:
                    partner = rec.partner_id.id
                source_location = self.env['stock.location'].search([('usage','=','inventory')],limit=1)
                values = {'employee_id':partner,
                          'location_id':rec.source_location_id.id,
                          'date':rec.date,
                          'source_location_id':source_location.id,
                          'is_material_request':True,
                          'material_requst_id':rec.id,

                          }

                value_list=[]
                for material in rec.material_issue_slip_lines_ids:
                    value_list.append((0,0,{
                                            'date':rec.date,
                                            'grr_number':rec.grr_no_id.id,
                                            'item_id':material.item_id.id,
                                            'desc':material.item_id.name,
                                            'unit_id':material.unit_id.id,
                                            'quantity':material.req_qty,
                                            'rate':material.rate + (material.rate * 0.03),

                        }))
                values.update({'debit_note_supplier_lines_ids':value_list})


                debit_note = self.env['debit.note.supplier'].create(values)

                

class MaterialIssuelipLine(models.Model):
    _name = 'material.issue.slip.line'


    @api.constrains('req_qty')
    def check_available_quantity(self):
        for rec in self:
            if rec.stock<rec.req_qty and not rec.material_issue_slip_id.is_receive:
                raise ValidationError(_(
                    "Available Quantity of selected product %s is %s"%(rec.item_id.name,rec.stock)))


    @api.depends('item_id')
    def compute_stock_balance(self):
        for rec in self:
            if rec.item_id:
                stock_history = self.env['stock.history'].search(
                    [ ('location_id', '=', rec.material_issue_slip_id.source_location_id.id),
                     ('product_id', '=', rec.item_id.id),('date', '<', rec.material_issue_slip_id.date)])
                available = 0
                for hist in stock_history:
                    available += hist.quantity
                rec.stock = available

    @api.onchange('item_id')
    def onchange_date(self):
        for rec in self:
            if rec.material_issue_slip_id.date:
                rec.date = rec.material_issue_slip_id.date
            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.unit_id = rec.item_id.uom_id.id
                rec.rate = rec.item_id.standard_price




    @api.onchange('project_id')
    def onchange_product(self):
        for rec in self:
            if rec.material_issue_slip_id.project_id:
                rec.project_id = rec.material_issue_slip_id.project_id
                


    @api.depends('quantity','req_qty')
    def compute_rem_qty(self):
        for rec in self:
            rec.rem_qty =  rec.stock - rec.req_qty


    @api.depends('quantity','rate')
    def compute_amount(self):
        for rec in self:
            rec.amount = rec.quantity * rec.rate
            if rec.material_issue_slip_id.state == 'receive':
                rec.amount = rec.req_qty * rec.rate



    item_id = fields.Many2one('product.product',string="Material Code")
    stock = fields.Float(string="Stock Balance",compute='compute_stock_balance',digits=(6,3))
    quantity = fields.Float(string="Requested Quantity")
    unit_id = fields.Many2one('product.uom')
    desc = fields.Char(string="Material Name")
    remarks = fields.Text(string="Remarks")
    material_issue_slip_id = fields.Many2one('material.issue.slip',string="Material Issue Slip")
    date = fields.Date('Date')
    project_id = fields.Many2one('project.project')

    rate = fields.Float('Rate',digits=(6,3))
    amount = fields.Float('Amount',compute='compute_amount',digits=(6,3))
    req_qty = fields.Float('Received Quantity',digits=(6,3))
    rem_qty = fields.Float('Remaining Quantity',compute='compute_rem_qty',digits=(6,3))
    mrn_no = fields.Char(string='MRN NO',related = "material_issue_slip_id.name")
    date_export =  fields.Datetime('Date',related = "material_issue_slip_id.date")
    project_id_export = fields.Many2one(string="Project" ,related = "material_issue_slip_id.project_id")
    source_location_id = fields.Many2one(string="Project Store" ,related = "material_issue_slip_id.source_location_id")
    employee_id = fields.Many2one(string="Reciever" ,related = "material_issue_slip_id.employee_id")
    location_id = fields.Many2one(string="Chainage" ,related = "material_issue_slip_id.location_id")
    move_id = fields.Many2one('stock.move',"Stock Move")
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle",related = "material_issue_slip_id.vehicle_id")
    partner_daily_statement_id = fields.Many2one('partner.daily.statement',"Partner Daily Statement")