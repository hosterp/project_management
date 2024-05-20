from openerp import fields, models, api,_
from datetime import date,datetime
from openerp.exceptions import except_orm,ValidationError
from openerp.osv import fields as osv
import openerp.addons.decimal_precision as dp
from lxml import etree

import re
class GoodsTransferDummy(models.Model):

    _name = 'goods.transfer.dummy'

    @api.constrains('qty')
    def check_stock_balance(self):
        for rec in self:
            if rec.stock_balance<rec.qty and rec.transfer_list_id.goods_transfer_bool == False:
                raise ValidationError(_(
                "Available Quantity of selected product %s is %s" % (
                rec.item_id.name, rec.stock_balance)))


    @api.depends('item_id')
    def compute_stock_balance(self):
        for rec in self:
            if rec.item_id:
                stock_history = self.env['stock.history'].search(
                    [('date', '<', rec.transfer_list_id.date), ('location_id', '=', rec.transfer_list_id.site_from.id),
                     ('product_id', '=', rec.item_id.id)])
                available = 0
                for hist in stock_history:
                    available += hist.quantity
                rec.stock_balance = available

    @api.onchange('item_id')
    def onchange_item_id(self):
        for rec in self:
            rec.desc = rec.item_id.name
            rec.specs = rec.item_id.part_no
            rec.rate = rec.item_id.standard_price
            rec.unit_id = rec.item_id.uom_id.id

                # rec.stock_balance = rec.item_id.with_context({'location' : rec.transfer_list_id.site_from.id}).qty_available

    @api.one
    def get_total(self):
        for s in self :
            s.value= s.rate * s.qty

    item_id = fields.Many2one('product.product', 'Material Code')
    desc = fields.Char('Material Name')
    specs = fields.Char('Specification')
    unit_id = fields.Many2one('product.uom',"Unit")
    qty = fields.Float('Qty',digits=(6,3))
    rate = fields.Float('Rate',digits=(6,3))
    value = fields.Float('Value',compute='get_total',digits=(6,3))
    remarks = fields.Char('Remarks')
    transfer_list_id = fields.Many2one('goods.transfer.note.in')
    transfer_recieve_id = fields.Many2one('goods.recieve.report')
    stock_balance = fields.Float('Stock Balance',compute='compute_stock_balance',digits=(6,3))
    date = fields.Datetime("Date",related='transfer_list_id.date')
    rece_date = fields.Date("Received Date",related='transfer_list_id.rece_date')
    gtn_no = fields.Char("GTN No",related='transfer_list_id.gtn_no')
    from_project_id = fields.Many2one('project.project',"From Project",related='transfer_list_id.project_id')
    to_project_id = fields.Many2one('project.project',"To Project",related='transfer_list_id.to_project_id')
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle",related='transfer_list_id.vehicle_id')
    current_project_id = fields.Many2one('project.project','Current Project',related='transfer_list_id.current_project_id')
    move_id = fields.Many2one('stock.move',"Stock Move")
    


class GoodsTransferNoteIn(models.Model):
    _name = 'goods.transfer.note.in'
    _rec_name = 'gtn_no'
    _order = 'date desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    
    @api.model
    def create(self, vals):
        #res = super(GoodsTransferNoteIn,self).create(fields)

        if vals.get('gtn_no',False) == False:
            project = self.env['project.project'].browse(vals['project_id'])
            project.gtn_no+=1
            gtn_no=str(project.gtn_no).zfill(3)
            vals.update({'gtn_no' :'GTN - ' + gtn_no + '/'+ str(datetime.now().year)})

        res = super(GoodsTransferNoteIn,self).create(vals)
        return res

    @api.multi
    def unlink(self):
        journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
        location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
        for rec in self:
            if rec.goods_transfer_bool == True and rec.state == 'recieve':
                for material_issue in rec.transfer_list_ids:
                    stock = self.env['stock.picking'].create({

                        'source_location_id': rec.site_to.id,

                        'site': rec.site_from.id,
                        'order_date': rec.date,
                        'account_id': rec.site_from.related_account.id,
                        'supervisor_id': self.env.user.employee_id.id,
                        'is_purchase': False,
                        'journal_id': journal_id.id,
                        'project_id': rec.project_id.id,
                    })
                    stock_move = self.env['stock.move'].create({
                        'location_id': rec.site_to.id,
                        'project_id': rec.project_id.id,
                        'product_id': material_issue.item_id.id,
                        'available_qty': material_issue.item_id.with_context(
                            {'location': rec.site_from.id}).qty_available,
                        'name': material_issue.desc,
                        'date': rec.date,
                        'date_expected': rec.date,
                        'product_uom_qty': material_issue.qty,
                        'product_uom': material_issue.item_id.uom_id.id,
                        'price_unit': material_issue.rate,
                        'account_id': rec.site_from.related_account.id,
                        'location_dest_id': location.id,
                        'picking_id': stock.id
                    })
                    stock_move.action_done()
                    stock.action_done()
            if rec.goods_transfer_bool == False and rec.state == 'transfer':
                for material_issue in rec.transfer_list_ids:
                    stock = self.env['stock.picking'].create({

                        'source_location_id': location.id,

                        'site': rec.site_from.id,
                        'order_date': rec.rece_date,
                        'account_id': rec.site_from.related_account.id,
                        'supervisor_id': self.env.user.employee_id.id,
                        'is_purchase': False,
                        'journal_id': journal_id.id,
                        'project_id': rec.project_id.id,
                    })
                    stock_move = self.env['stock.move'].create({
                        'location_id': location.id,
                        'project_id': rec.project_id.id,
                        'product_id': material_issue.item_id.id,
                        'available_qty': material_issue.item_id.with_context(
                            {'location': rec.site_from.id}).qty_available,
                        'name': material_issue.desc,
                        'date': rec.rece_date,
                        'date_expected': rec.rece_date,
                        'product_uom_qty': material_issue.qty,
                        'product_uom': material_issue.item_id.uom_id.id,
                        'price_unit': material_issue.rate,
                        'account_id': rec.site_from.related_account.id,
                        'location_dest_id': rec.site_from.id,
                        'picking_id': stock.id
                    })
                    stock_move.action_done()
                    stock.action_done()

        return super(GoodsTransferNoteIn, self).unlink()
    
    # @api.model
    # def create(self,vals):
    #     print "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww",vals,vals.get('name')
    #     if vals.get('name', False) == False: 
    #         project = self.env['project.project'].browse(vals['project_id']).name
    #         vals.update({'name': 'MRN' +  str(self.env['ir.sequence'].next_by_code('mrn.code'))})
    #     res =super(MaterialIssueSlip, self).create(vals)

    @api.depends('transfer_list_ids')
    def compute_item_list(self):
        for rec in self:
            item = ''
            for lines in rec.transfer_list_ids:
                item += lines.item_id.name + ','
            rec.item_list = item

    @api.depends('transfer_list_ids')
    def compute_item_qty(self):
        for rec in self:
            quantity = 0
            for lines in rec.transfer_list_ids:
                quantity += lines.qty
            rec.total_quantity = quantity
    
    @api.onchange('project_id')
    def onchange_project_location(self):
        for rec in self:
            if rec.project_id:
                rec.site_from = rec.project_id.location_id
            if not rec.goods_transfer_bool:
                rec.current_project_id = rec.project_id.id
                

    @api.onchange('to_project_id')
    def onchange_project_to_location(self):
        for rec in self:
            if rec.to_project_id:
                rec.site_to = rec.to_project_id.location_id
            if rec.goods_transfer_bool:
                rec.current_project_id = rec.to_project_id.id

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.brand_id = rec.vehicle_id.brand_id.id
                rec.model_id = rec.vehicle_id.model_id.id
                rec.chase_no = rec.vehicle_id.chase_no
                rec.engine_no = rec.vehicle_id.engine_no


    project_id = fields.Many2one('project.project', 'Project',track_visibility='onchange')
    to_project_id = fields.Many2one('project.project', 'To Project',track_visibility='onchange')
    site_from = fields.Many2one('stock.location', 'From',track_visibility='onchange')
    site_to = fields.Many2one('stock.location', 'To',track_visibility='onchange')
    gtn_no = fields.Char('GTN NO',track_visibility='onchange')
    date = fields.Datetime('Date',default=lambda self: fields.datetime.now())
    rece_date = fields.Date('Recieved Date', )
    transfer_list_ids = fields.One2many('goods.transfer.dummy','transfer_list_id',track_visibility='onchange')
    user_created = fields.Many2one('res.users', 'Prepared by')
    project_manager = fields.Many2one('res.users', 'Project Manager')
    purchase_manager = fields.Many2one('res.users', 'Purchase Manager')
    dgm_id = fields.Many2one('res.users', 'GM')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Requested'),
                              ('approved1', 'Approved By GM'),
                              ('transfer', 'Transferred'),
                              ('recieve', 'Recieved'),
                              ('approved', 'Approved By PM'),
                              ('cancel', 'Cancelled')], default="draft", string="Status")
    goods_transfer_bool = fields.Boolean('Goods transfer',default="True" )
    user_id = fields.Many2one('res.users',string="Issuer",track_visibility='onchange')
    store_manager_id = fields.Many2one('res.users',"Receiver")
    transfer_gtn_id = fields.Many2one('goods.transfer.note.in',"Transfer ")
    item_list = fields.Char(string="Items", compute='compute_item_list')
    total_quantity = fields.Char(string="Quantity", compute='compute_item_qty')
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
    model_id = fields.Many2one('fleet.vehicle.model', "Model")
    brand_id = fields.Many2one('fleet.vehicle.model.brand', "Brand")
    chase_no = fields.Char("Chase No")
    engine_no = fields.Char("Model No")
    own_vehicle = fields.Boolean(string="Own Vehicle",default=False)
    vehicle_no = fields.Char("Vehicle No")
    current_project_id = fields.Many2one('project.project','Current Project')
    picking_id = fields.Many2one('stock.picking',"Picking")

    @api.multi
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    @api.multi
    def action_cancel(self):
        for rec in self:
            for line in rec.transfer_list_ids:
                line.write({'qty': 0})
                line.move_id.write({'product_uom_qty': 0})
                for quant in line.move_id.quant_ids:
                    quant.write({'qty': 0})
            rec.state = 'cancel'
    

    

    @api.multi
    def set_draft(self):
        self.state = 'draft'
        self.request_not_in_draft = False
    @api.multi
    def confirm_purchase(self):
            self.user_created = self.env.user.id
            self.state = 'confirm'
            self.request_not_in_draft = True

    @api.multi
    def approve_purchase1(self):
        self.project_manager = self.env.user.id
        self.state = 'approved1'

    @api.multi
    def button_transfer(self):
        for rec in self.search([]):
            if rec.state == 'transfer':


                journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
                location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
                stock = self.env['stock.picking'].create({

                    'source_location_id': rec.site_from.id,

                    'site': rec.site_to.id,
                    'order_date': rec.date,
                    'account_id': rec.site_to.related_account.id,
                    'supervisor_id': self.env.user.employee_id.id,
                    'is_purchase': False,
                    'journal_id': journal_id.id,

                })
                for req in rec.transfer_list_ids:
                    stock_move = self.env['stock.move'].create({
                        'location_id': rec.site_from.id,

                        'product_id': req.item_id.id,
                        'available_qty': req.item_id.with_context(
                            {'location': rec.site_to.id}).qty_available,
                        'name': req.desc,
                        'date': rec.date,
                        'date_expected': rec.date,
                        'product_uom_qty': req.qty,
                        'product_uom': req.item_id.uom_id.id,
                        'price_unit': req.rate,
                        'account_id': rec.site_to.related_account.id,
                        'location_dest_id': location.id,
                        'picking_id': stock.id
                    })
                    stock_move.action_done()
                    req.move_id = stock_move.id
                stock.action_done()

                rec.picking_id = stock.id
            if rec.state == 'recieve':
                journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
                location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
                stock = self.env['stock.picking'].create({

                    'source_location_id': location.id,

                    'site': rec.site_to.id,
                    'order_date': rec.rece_date,
                    'account_id': rec.site_to.related_account.id,
                    'supervisor_id': self.env.user.employee_id.id,
                    'is_purchase': False,
                    'journal_id': journal_id.id,

                })
                for req in rec.transfer_list_ids:
                    stock_move = self.env['stock.move'].create({
                        'location_id': location.id,

                        'product_id': req.item_id.id,
                        'available_qty': req.item_id.with_context(
                            {'location': rec.site_to.id}).qty_available,
                        'name': req.desc,
                        'date': rec.rece_date,
                        'date_expected': rec.rece_date,
                        'product_uom_qty': req.qty,
                        'product_uom': req.item_id.uom_id.id,
                        'price_unit': req.rate,
                        'account_id': rec.site_to.related_account.id,
                        'location_dest_id': rec.site_to.id,
                        'picking_id': stock.id
                    })
                    stock_move.action_done()
                    req.move_id = stock_move.id
                stock.action_done()
                rec.picking_id = stock.id


    @api.multi
    def action_transfer(self):
        for rec in self:

            line_vals = []
            for line in rec.transfer_list_ids:
                line_vals.append((0,0,{'item_id':line.item_id.id,
                                       'desc':line.desc,
                                       'specs':line.specs,
                                       'unit_id':line.unit_id.id,
                                       'qty':line.qty,
                                       'rate':line.rate,
                                    }))
            vals = {
                'user_id': rec.user_id.id,
                'store_manager_id': rec.store_manager_id.id,
                'project_id': rec.project_id.id,
                'current_project_id':rec.to_project_id.id,
                'to_project_id': rec.to_project_id.id,
                'site_from': rec.site_from.id,
                'site_to': rec.site_to.id,
                'vehicle_id': rec.vehicle_id.id,
                'model_id': rec.model_id.id,
                'brand_id': rec.brand_id.id,
                'chase_no': rec.chase_no,
                'engine_no': rec.engine_no,
                'goods_transfer_bool': True,
                'transfer_list_ids': line_vals,
                'state':'transfer',
                'transfer_gtn_id':rec.id,
            }
            transfer_list_id = self.env['goods.transfer.note.in'].create(vals)


            rec.transfer_gtn_id = transfer_list_id.id


            # journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            # location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            # stock = self.env['stock.picking'].create({
            #
            #     'source_location_id': rec.site_from.id,
            #
            #     'site': rec.site_to.id,
            #     'order_date': rec.date,
            #     'account_id': rec.site_to.related_account.id,
            #     'supervisor_id': self.env.user.employee_id.id,
            #     'is_purchase': False,
            #     'journal_id': journal_id.id,
            #
            # })
            # for req in rec.transfer_list_ids:
            #     stock_move = self.env['stock.move'].create({
            #         'location_id': rec.site_from.id,
            #
            #         'product_id': req.item_id.id,
            #         'available_qty': req.item_id.with_context(
            #             {'location': rec.site_to.id}).qty_available,
            #         'name': req.desc,
            #         'date': rec.date,
            #         'date_expected': rec.date,
            #         'product_uom_qty': req.qty,
            #         'product_uom': req.item_id.uom_id.id,
            #         'price_unit': req.rate,
            #         'account_id': rec.site_to.related_account.id,
            #         'location_dest_id': location.id,
            #         'picking_id': stock.id
            #     })
            #     stock_move.action_done()
            #     req.move_id = stock_move.id
            # stock.action_done()
            #
            # rec.picking_id = stock.id
            rec.state = 'transfer'
        # self.purchase_manager = self.env.user.id
    @api.multi
    def approve_purchase3(self):
        for rec in self:
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])

            stock = self.env['stock.picking'].create({
        
                'source_location_id': rec.site_from.id,
        
                'site': rec.site_to.id,
                'order_date': rec.rece_date,
                'account_id': rec.site_to.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
        
            })
            for req in rec.transfer_list_ids:
                stock_move = self.env['stock.move'].create( {
                    'location_id': rec.site_from.id,
            
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': rec.site_to.id}).qty_available,
                    'name': req.desc,
                    'date':rec.rece_date,
                    'date_expected': rec.rece_date,
                    'product_uom_qty': req.qty,
                    'product_uom': req.item_id.uom_id.id,
                    'price_unit': req.rate,
                    'account_id': rec.site_to.related_account.id,
                    'location_dest_id': rec.site_to.id,
                    'picking_id':stock.id
                })
                stock_move.action_done()
                req.move_id = stock_move.id
            stock.action_done()
            rec.picking_id = stock.id
            rec.state = 'recieve'
            for line in rec.transfer_list_ids:
                for rec_line in rec.transfer_gtn_id.transfer_list_ids:
                    if rec_line.item_id.id == line.item_id.id:
                        rec_line.qty = line.qty
            rec.transfer_gtn_id.state = 'recieve'
        # self.dgm_id = self.env.user.id

    @api.multi
    def cancel_process(self):
        self.state = 'cancel'

    @api.multi
    def goods_transfer_report(self):

        transfer_list=[]
        for rec in self:
            for tlist in rec.transfer_list_ids:

                transfer_dict={
                            'item_id':tlist.item_id.name,
                            'desc':tlist.desc,
                            'specs':tlist.specs,
                            'qty':tlist.qty,
                            'rate':tlist.rate,
                            'value':tlist.value,
                            'remarks':tlist.remarks,

                            }
                transfer_list.append(transfer_dict)

        return transfer_list
        
class GoodsRecieveReport(models.Model):

    _name = "goods.recieve.report"
    _rec_name = 'grr_no'
    _order = 'id desc,invoice_date desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    @api.constrains('vehicle_no')
    def check_license_plate_format(self):
        for rec in self:

            phoneNumRegex = re.compile(r'[A-Z]{2}[-][0-9]{1,2}[-]([A-Z]{1,2}[-][0-9]{4})')

            if rec.vehicle_no:
                mo = phoneNumRegex.search(rec.vehicle_no)

                if not mo:
                    raise except_orm(_('Warning'),
                                     _('Please Enter REG No in this format KL-01-XX-XXXX or KL-01-X-XXXX'))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(GoodsRecieveReport, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            # Check if user is in group that allow creation
            has_my_group = self.env.user.has_group('hiworth_hr_attendance.group_admin')
            if not has_my_group:
                root = etree.fromstring(res['arch'])
                root.set('edit', 'false')
                res['arch'] = etree.tostring(root)
        return res

    @api.model
    def create(self,vals):
        if vals.get('grr_no',False)==False:
            project = self.env['project.project'].browse(vals['project_id'])
            last_grr_no = self.env['goods.recieve.report'].search([], limit=1).grr_no
            if last_grr_no:
                new_grr_no = int(last_grr_no.split('/')[1])+1
                grr_no = str(new_grr_no).zfill(4)
                vals['grr_no'] = 'GRR/'  + grr_no + "/"+  str(datetime.now().year)
            else:
                new_grr_no = 0
                grr_no = str(new_grr_no).zfill(4)
                vals['grr_no'] = 'GRR/' + grr_no + "/" + str(datetime.now().year)

            vals['project_id'] = project.id
            supplier =self.env['res.partner'].browse(vals['supplier_id'])
            if supplier and supplier.is_fuel_station:
                vehicle = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
                if vehicle and vehicle.tanker_bool:
                    vals['project_location_id'] = vehicle.location_id.id
            else:
                vals['project_location_id'] = project.location_id.id
            location_id = self.env['stock.location'].search([('usage', '=', 'supplier')],order='id asc' ,limit=1)
            vals['supplier_location_id'] = location_id.id

        self.sudo(self.env.user.id)
        self.env['res.partner'].sudo(self.env.user.id)


        order = super(GoodsRecieveReport, self).create(vals)

        order.project_id = project.id
        journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
        # location_id = self.env['stock.location'].search([('usage','=','supplier')])
        # order.supplier_location_id = location_id.id
        for rec in order:
            stock = self.env['stock.picking'].create({

                'source_location_id': rec.supplier_location_id.id,

                'site': rec.project_location_id.id,
                'order_date': rec.Date,
                'account_id': rec.project_location_id.related_account.id,
                'supervisor_id': rec.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })
            for line in rec.goods_recieve_report_line_ids:
                line.item_id.sudo().write({
                    'standard_price':line.rate
                    })
                # line.item_id.taxes_id = [(6,0,line.tax_ids.ids)]
                stock_move = self.env['stock.move'].create({
                    'location_id': rec.supplier_location_id.id,
                    'project_id': rec.project_id.id,
                    'product_id': line.item_id.id,
                    'available_qty': line.item_id.with_context(
                        {'location': rec.supplier_location_id.id}).qty_available,
                    'name': line.desc,
                    'date':rec.Date,
                    'date_expected': rec.Date,
                    'product_uom_qty': line.quantity_accept,
                    'product_uom': line.item_id.uom_id.id,
                    'price_unit': line.rate,
                    'account_id': rec.project_location_id.related_account.id,
                    'location_dest_id': rec.project_location_id.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                line.move_id = stock_move.id
            stock.action_done()
            rec.picking_id = stock.id
            flag=0
            if order.purchase_id:
                for goods in order.goods_recieve_report_line_ids:
                    for order_line in order.purchase_id.order_line:
                        if goods.item_id.id == order_line.product_id.id:
                            order_line.received_qty = order_line.received_qty  + goods.quantity_accept
                            if order_line.received_qty == order_line.required_qty:
                                flag = 1
                            else:
                                flag = 0
            if flag == 1:
                order.mpr_id.state='received'
                order.purchase_id.state='done'
        if order.vehicle_id:
            for line in order.goods_recieve_report_line_ids:
                self.env['fleet.receipt.details'].create({'name':order.vehicle_id.id,
                                                        'date':order.Date,
                                                        'grr_no':order.id,
                                                        'item_id':line.item_id.id,
                                                        'qty':line.quantity_accept,
                                                        'rate':line.rate,
                                                        'tax_ids':[(6,0,line.tax_ids.ids)],
                                                        'amount':line.total_amount})
        
        return order


    @api.multi
    def write(self, vals):
        date = self.Date
        self.sudo(self.env.user.id)
        for rec in self:
            flag=0
            if vals.get('project_location_id'):
                rec.picking_id.location_dest_id = vals.get('project_location_id')
                for line in rec.goods_recieve_report_line_ids:
                    line.move_id.location_dest_id = vals.get('project_location_id')

                    for quant in line.move_id.quant_ids:
                        quant.location_id = vals.get('project_location_id')
            if vals.get('Date'):
                rec.picking_id.order_date = vals.get('Date')
                for line in rec.goods_recieve_report_line_ids:
                    line.move_id.date = vals.get('Date')
                    line.move_id.date_expected = vals.get('Date')
                    for quant in line.move_id.quant_ids:
                        quant.in_date = vals.get('Date')
            if vals.get('goods_recieve_report_line_ids'):
                for li in vals.get('goods_recieve_report_line_ids'):
                    if li[0] == 1:
                        line_id = self.env['goods.recieve.report.line'].browse(li[1])
                        if li[2].get('quantity_accept')>=0:
                            line_id.move_id.product_uom_qty = li[2].get('quantity_accept')

                            for quant in line_id.move_id.quant_ids:
                                quant.qty = li[2].get('quantity_accept')
                            if self.purchase_id:
                                for order_line in self.purchase_id.order_line:
                                    if line_id.item_id.id == order_line.product_id.id:
                                        order_line.received_qty = order_line.received_qty - line_id.quantity_accept + li[2].get('quantity_accept')
                        if line_id.quantity_accept == 0 and li[2].get('quantity_accept')>0:
                            line_id.move_id.product_uom_qty = li[2].get('quantity_accept')
                            quant_id = self.env['stock.quant'].create({'product_id':line_id.item_id.id,
                                                                      'qty': li[2].get('quantity_accept'),
                                                                      'location_id':rec.project_location_id.id,
                                                                      'in_date':rec.Date})
                            line_id.move_id.quant_ids = [(6,0,[quant_id.id])]
                            if self.purchase_id:
                                for order_line in self.purchase_id.order_line:
                                    if line_id.item_id.id == order_line.product_id.id:
                                        order_line.received_qty = order_line.received_qty - line_id.quantity_accept + li[2].get('quantity_accept')
                        if li[2].get('item_id'):
                            line_id.move_id.product_id = li[2].get('item_id')
                            for quant in line_id.move_id.quant_ids:
                                    quant.product_id = li[2].get('item_id')
                    if li[0]==0:
                        stock_move = rec.env['stock.move'].create({
                        'location_id': rec.supplier_location_id.id,
                        'project_id': rec.project_id.id,
                        'product_id': li[2]['item_id'],
                        'available_qty': self.env['product.product'].browse(li[2]['item_id']).with_context(
                            {'location': rec.supplier_location_id.id}).qty_available,
                        'name': 'kkkk',
                        'date':rec.Date,
                        'date_expected': rec.Date,
                        'product_uom_qty': li[2]['quantity_accept'],
                        'product_uom': li[2]['unit_id'],
                        'price_unit':li[2]['rate'],
                        'account_id': rec.project_location_id.related_account.id,
                        'location_dest_id': rec.project_location_id.id,
                        'picking_id': rec.picking_id.id
                        })
                        stock_move.action_done()
                        li[2].update({'move_id':stock_move.id})
                        if self.purchase_id:
                            for order_line in self.purchase_id.order_line:
                                if li[2]['item_id'] == order_line.product_id.id:
                                    order_line.received_qty = order_line.received_qty + li[2].get('quantity_accept')
                                    if order_line.required_qty == order_line.received_qty:
                                        flag = 0
                                    else:
                                        flag = 1
                            if flag == 1:
                                rec.purchase_id.state = 'done'
                                rec.mpr_id.state = 'received'
                    if li[0]==2:
                        line_id = self.env['goods.recieve.report.line'].browse(li[1])
                        if self.purchase_id:
                            for order_line in self.purchase_id.order_line:
                                if line_id.item_id.id == order_line.product_id.id:
                                    order_line.received_qty = order_line.received_qty - line_id.quantity_accept
                                    if order_line.required_qty == order_line.received_qty:
                                        flag = 0
                                    else:
                                        flag = 1
                                if flag == 1:
                                    rec.purchase_id.state = 'approved'
                                    rec.mpr_id.state = 'confirm_purchase'
                        for quant in line_id.move_id.quant_ids:
                            quant.with_context({'force_unlink':True}).unlink()
                        line_id.move_id.unlink()

        res= super(GoodsRecieveReport, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.picking_id:
                for move in rec.picking_id.move_lines:
                    for quant in move.quant_ids:
                        quant.with_context({'force_unlink':True}).unlink()
                    move.unlink()
            if rec.purchase_id:
                rec.purchase_id.state = 'draft'
        return super(GoodsRecieveReport, self).unlink()

    @api.onchange('supplier_id')
    def onchange_supplier(self):
        for rec in self:
            if rec.supplier_id:
                rec.supplier_location_id = self.env['stock.location'].search([('usage','=','supplier')],limit=1).id
    

    # @api.onchange('project_id')
    # def onchange_project(self):
    #     for rec in self:
    #         if rec.project_id:
    #             # rec.project_location_id = rec.project_id.location_id.id
    #             rec.supplier_location_id = self.env['stock.location'].search([('usage','=','supplier')],limit=1).id


    @api.onchange('purchase_id')
    def onchange_purchase(self):
        for rec in self:
            if rec.purchase_id:
                values = []
                rem_qty = 0
                rec.supplier_id = rec.purchase_id.sudo().partner_id.sudo().id
                for po_lines in rec.purchase_id.order_line:
                    rec.mpr_id = rec.purchase_id.mpr_id.id
                    rem_qty = po_lines.required_qty - po_lines.received_qty


                    values.append((0,0,{'item_id':po_lines.product_id.id,
                                        'desc':po_lines.name,
                                        'po_quantity':rem_qty,
                                        'tax_ids':[(6,0,po_lines.taxes_id.ids)],
                                        'rate':po_lines.expected_rate,
                                        }))
                rec.goods_recieve_report_line_ids = values


    @api.onchange('mpr_id')
    def onchange_material_procurement(self):
        for rec in self:
            if rec.mpr_id:
                p_order=self.env['purchase.order'].search([('mpr_id','=',rec.mpr_id.id)])
                rec.project_id = rec.mpr_id.project_id.id
                rec.vehicle_id = rec.mpr_id.vehicle_id.id



    
    @api.multi
    def picking_create(self):
        values = {}
        for goods_receive in self:
            stock=False
            picking_ids = goods_receive.purchase_id.picking_ids.ids
            for picking in picking_ids:
                if self.env['stock.picking'].browse(picking).state == 'approve':
                    stock = self.env['stock.picking'].browse(picking)
                    stock.action_confirm()
                    stock.sudo().action_assign()
                    stock.sudo().state = 'assigned'
                    stock.date_done = goods_receive.Date
                    stock.sudo().do_enter_transfer_details()
                    created_id = self.env['stock.transfer_details'].create({
                     	'picking_id': len(stock) and stock.id or False})
                    for req in goods_receive.goods_recieve_report_line_ids:
                        values = ({
                     		'product_id': req.item_id.id,
                     		'price_unit':req.rate,
                    		'quantity': req.quantity_accept,
                     		'product_uom_id': req.item_id.uom_id.id,
                    		'sourceloc_id': goods_receive.supplier_location_id.id,
                     		'destinationloc_id': goods_receive.project_location_id.id,
                     		'transfer_id': created_id.id
                     	})
                        transfer_details = self.env['stock.transfer_details_items'].create(values)
                    created_id.sudo().do_detailed_transfer()

                    stock.write({'project_id':goods_receive.project_id.id})
                    stock.action_done()
                if stock:
                    goods_receive.picking_id = stock.id
            
            
    @api.depends('goods_recieve_report_line_ids')
    def compute_item_list(self):
        for rec in self:
            item = ''
            for lines in  rec.goods_recieve_report_line_ids:
                item += lines.item_id.name + ','
            rec.item_list = item

    @api.depends('goods_recieve_report_line_ids')
    def compute_item_qty(self):
        for rec in self:
            quantity = 0
            for lines in rec.goods_recieve_report_line_ids:
                quantity += lines.quantity_accept
            rec.total_quantity = quantity

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.brand_id = rec.vehicle_id.brand_id.id
                rec.model_id = rec.vehicle_id.model_id.id
                rec.chase_no = rec.vehicle_id.chase_no
                rec.engine_no = rec.vehicle_id.engine_no


    @api.constrains('invoice_no')
    def check_invoice_no(self):
        for rec in self:
            if len(self.search([('supplier_id','=',rec.supplier_id.id),('invoice_no','=',rec.invoice_no)]))>1:
                raise ValidationError(_('Supplier invoice number already exists for this supplier.'))

    @api.onchange('rent_vehicle_owner_id')
    def onchnage_vehicle_owner_id(self):
        for rec in self:
            vehicle = self.env['fleet.vehicle'].search(
                ['|', '|', ('rent_vehicle', '=', True), ('is_rent_mach', '=', True), ('other', '=', True),
                 ('vehicle_under', '=', rec.rent_vehicle_owner_id.id)])
            domain = {'domain': {'rent_vehicle_id': [('id', 'in', vehicle.ids)]}}
        return domain

    @api.onchange('own_vehicle')
    def onchange_own_vehicle(self):
        for rec in self:
            rec.rent_vehicle = False
            rec.rent_vehicle_id = False
            rec.rent_vehicle_owner_id = False

    @api.onchange('rent_vehicle')
    def onchange_rent_vehicle(self):
        for rec in self:
            rec.own_vehicle = False
            rec.vehicle_id = False

    @api.onchange('supplier_vehicle')
    def onchange_supplier_vehicle(self):
        for rec in self:
            rec.own_vehicle = False
            rec.rent_vehicle = False

    project_id = fields.Many2one('project.project', 'Project',track_visibility='onchange')
    supplier_id = fields.Many2one('res.partner','Supplier',track_visibility='onchange', domain="[('supplier','=',True)]")
    supplier_location_id = fields.Many2one('stock.location','Location',track_visibility='onchange')
    project_location_id = fields.Many2one('stock.location','Project Location',track_visibility='onchange')
    mpr_id = fields.Many2one('site.purchase',"MPR No")
    purchase_id = fields.Many2one('purchase.order','PO No')
    po_no = fields.Char('P.O.No')
    grr_no = fields.Char('GRR No',track_visibility='onchange')
    Date = fields.Date('Date' , default=lambda self: fields.datetime.now())
    picking_id = fields.Many2one('stock.picking',"Picking")
    invoice_no = fields.Char(string="Supplier Invoice Number")
    goods_recieve_report_line_ids = fields.One2many('goods.recieve.report.line','goods_recieve_report_id')
    item_list = fields.Char(string="Items",compute='compute_item_list')
    total_quantity = fields.Char(string="Quantity",compute='compute_item_qty')
    own_vehicle = fields.Boolean(string="Own Vehicle",default=False)
    rent_vehicle = fields.Boolean(string="Rent Vehicle",default=False)
    supplier_vehicle = fields.Boolean(string="Supplier Vehicle",default=False)
    vehicle_no = fields.Char(string="Supplier Vehicle No")
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle No",domain="['|','|',('vehicle_ok','=',True),('machinery','=',True),('other','=',True)]")
    rent_vehicle_id = fields.Many2one('fleet.vehicle',"Rent Vehicle No",domain="['|','|',('rent_vehicle','=',True),('is_rent_mach','=',True),('other','=',True)]")
    rent_vehicle_owner_id = fields.Many2one('res.partner',"Rent Vehicle Owner",domain="[('is_rent_mach_owner','=',True)]")
    without_po = fields.Boolean("without PO",default=False)
    model_id = fields.Many2one('fleet.vehicle.model', "Model")
    brand_id = fields.Many2one('fleet.vehicle.model.brand', "Brand")
    chase_no = fields.Char("Chase No")
    engine_no = fields.Char("Model No")
    invoice_date = fields.Date("Invoice Date",default=lambda self: fields.datetime.today())
    mr_slip = fields.Char("MR Slip")
    state = fields.Selection([('draft', 'Draft'),
                              ('approved','Approved By PM'),
                              ('cancel', 'Cancel')],default='draft', string="State")


    @api.multi
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    @api.multi
    def action_cancel(self):
        for rec in self:
            if rec.purchase_id:
                flag=1
                for order_line in rec.purchase_id.order_line:
                    if line_id.item_id.id == order_line.product_id.id:
                        order_line.received_qty = order_line.received_qty - line_id.quantity_accept
                        if order_line.required_qty == order_line.received_qty:
                            flag=0
                        else:
                            flag=1
                if flag==1:
                    rec.purchase_id.state = 'approved'
                    rec.mpr_id.state = 'confirm_purchase'
            for line in rec.goods_recieve_report_line_ids:
                line.write({'quantity_accept': 0})
                line.move_id.write({'product_uom_qty': 0})
                for quant in line.move_id.quant_ids:
                    quant.write({'qty': 0})

            rec.state = 'cancel'





    @api.multi
    def action_done(self):
        journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
        # location_id = self.env['stock.location'].search([('usage','=','supplier')])
        # order.supplier_location_id = location_id.id
        for rec in self:
            stock = self.env['stock.picking'].create({

                'source_location_id': rec.supplier_location_id.id,

                'site': rec.project_location_id.id,
                'order_date': rec.Date,
                'account_id': rec.project_location_id.related_account.id,
                'supervisor_id': rec.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })
            for line in rec.goods_recieve_report_line_ids:
                stock_move = self.env['stock.move'].create({
                    'location_id': rec.supplier_location_id.id,
                    'project_id': rec.project_id.id,
                    'product_id': line.item_id.id,
                    'available_qty': line.item_id.with_context(
                        {'location': rec.supplier_location_id.id}).qty_available,
                    'name': line.desc,
                    'date': rec.Date,
                    'date_expected': rec.Date,
                    'product_uom_qty': line.quantity_accept,
                    'product_uom': line.item_id.uom_id.id,
                    'price_unit': line.rate,
                    'account_id': rec.project_location_id.related_account.id,
                    'location_dest_id': rec.project_location_id.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                line.move_id = stock_move.id
            stock.action_done()
            rec.picking_id = stock.id
    
    @api.multi
    def action_return(self):
        for goods_receive in self:
            stock = self.env['stock.picking'].create({
                'request_id': self.mpr_id.id,
                'source_location_id': goods_receive.project_location_id.id,
                'partner_id': goods_receive.supplier_id.id,
                'site': goods_receive.project_location_id.id,
                'order_date': self.Date,
                'account_id': goods_receive.supplier_id.property_account_payable.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': True,
                'project_id': goods_receive.project_id.id,
                })
        for req in goods_receive.goods_recieve_report_line_ids:
            if req.quantity_reject != 0.0:
                stock_move = self.env['stock.move'].create({
                'location_id': goods_receive.project_location_id.id,
                'project_id': goods_receive.project_id.id,
                'product_id': req.item_id.id,
                'available_qty': req.item_id.with_context(
                    {'location': goods_receive.project_location_id.id}).qty_available,
                'name': req.desc,
                    'date':req.goods_recieve_report_id.Date,
                    'date_expected': req.goods_recieve_report_id.Date,
                'product_uom_qty': req.quantity_reject,
                'product_uom': req.item_id.uom_id.id,
                'price_unit': req.rate,
                'account_id': goods_receive.supplier_id.property_account_payable.id,
                'location_dest_id': goods_receive.supplier_location_id.id,
                'picking-id':stock.id
            })
                stock_move.action_done()
        stock.action_done()
    
    
class GoodsRecieveReportLine(models.Model):

    _name = "goods.recieve.report.line"
    
    
    @api.onchange('item_id')
    def onchange_item_id(self):
        for rec in self:
            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.unit_id = rec.item_id.uom_id.id



    @api.constrains('quantity_accept','po_quantity')
    def constraints_quantity(self):

        if self.goods_recieve_report_id.without_po == False:
            if self.po_quantity < self.quantity_accept:
                raise ValidationError(_('Received Quantity cannot be greater than PO Quantity.'))
    

    @api.one
    @api.depends('quantity_accept','rate','tax_ids')
    def compute_total_amount(self):
        for rec in self:
            tax = 0
            cgst = 0
            sgst = 0
            igst = 0
            for taxes in rec.tax_ids:
                if taxes.tax_type == 'cgst':
                    cgst+=taxes.amount
                if taxes.tax_type == 'sgst':
                    sgst+=taxes.amount
                if taxes.tax_type == 'igst':
                    igst+=taxes.amount

                if taxes.price_include:
                    tax += (.5 + taxes.amount)
                else:
                    tax = 1
            if tax == 0:
                tax = 1
            rec.sub_total = (rec.rate / tax) * rec.quantity_accept
            rec.cgst_amount = rec.sub_total * cgst
            rec.sgst_amount = rec.sub_total *sgst
            rec.igst_amount = rec.sub_total *igst
            rec.total_amount = rec.sub_total + rec.cgst_amount + rec.sgst_amount + rec.igst_amount + rec.tcs_amount + rec.round_off_amount


    item_id = fields.Many2one('product.product', 'Material Code')
    desc = fields.Char('Material Name')
    specs = fields.Char('Specification')
    unit_id = fields.Many2one('product.uom',string="Unit")
    quantity_rec = fields.Float('Quantity Received',digits=(6,3))
    quantity_accept = fields.Float('Quantity Accepted',digits=(6,3))
    quantity_reject = fields.Float('Quantity Rejected',digits=(6,3))
    rate = fields.Float('Price',digits=(6,3))
    remarks = fields.Char('Remarks')
    goods_recieve_report_id = fields.Many2one('goods.recieve.report',string="Goods Recieve Report")
    date = fields.Date(string="Date",related = 'goods_recieve_report_id.Date')
    po_quantity = fields.Float(string='PO Quantity',digits=(6,3))
    received = fields.Boolean(string="Received",default=False)
    grr_no = fields.Char('GRR.No.',related = 'goods_recieve_report_id.grr_no')
    mpr_id = fields.Many2one(string='MPR.No.',related = 'goods_recieve_report_id.mpr_id')
    purchase_id = fields.Many2one(string='PO.No.',related = 'goods_recieve_report_id.purchase_id')
    supplier_id = fields.Many2one(string='Supplier',related = 'goods_recieve_report_id.supplier_id')
    supplier_location_id = fields.Many2one(string='Supplier Store',related = 'goods_recieve_report_id.supplier_location_id')
    invoice_no = fields.Char('Supplier Invoive Number',related = 'goods_recieve_report_id.invoice_no')
    project_id = fields.Many2one(string='Project Name',related = 'goods_recieve_report_id.project_id')
    project_location_id = fields.Many2one(string='Project Name',related = 'goods_recieve_report_id.project_location_id')
    tax_ids = fields.Many2many('account.tax','goods_receive_report_line_account_tax_rel','goods_receive_report_line_id','tax_id',"Taxes")
    sub_total = fields.Float("Subtotal",compute='compute_total_amount')
    cgst_amount = fields.Float("CGST Amount",compute='compute_total_amount')
    sgst_amount = fields.Float("SGST Amount",compute='compute_total_amount')
    igst_amount = fields.Float("IGST Amount",compute='compute_total_amount')
    tcs_amount = fields.Float("TCS Amount")
    total_amount = fields.Float("Total Amount",compute='compute_total_amount')
    vehicle_id = fields.Many2one(string='Own Vehicle .No.',related = 'goods_recieve_report_id.vehicle_id')
    vehicle_no = fields.Char("Vehicle No", related='goods_recieve_report_id.vehicle_no')
    mr_slip_no  =fields.Char("MR Slip No", related='goods_recieve_report_id.mr_slip')
    invoice_date = fields.Date("Invoice Date",related='goods_recieve_report_id.invoice_date')
    move_id = fields.Many2one('stock.move',"Stock Move")
    round_off_amount = fields.Float("Round OFF Amount")
    