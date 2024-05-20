from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from datetime import datetime
from datetime import datetime
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta

class InventoryDepartment(models.Model):
    _name = 'inventory.department'

    name = fields.Many2one('product.product','Product')
    date = fields.Date('Date')
    location_id = fields.Many2one('stock.location','Location')
    qty = fields.Float('Quantity')
    rate = fields.Float('Rate')
    inventory_value = fields.Float('Inventory Value')
    department = fields.Selection([('general','General'),
                                   ('vehicle','Vehicle'),
                                   ('telecom','Telecom'),
                                   ('interlocks','Interlocks'),
                                   ('workshop','Workshop')],string="Department")
    site_purchase_id = fields.Many2one('site.purchase')





class SitePurchasegroup(models.Model):
    _name = 'site.purchase.group'

    @api.multi
    def merge_orders(self):
        site_requests = self.env.context.get('active_ids')
        record = []
        supplier = False
        for request in site_requests:
            site_record = self.env['site.purchase'].search([('id','=',request)])
            if site_record:
                if site_record.state != 'approved2':
                    raise except_orm(_('Warning'),_('Site Requests Must Be In Draft State.Please Check..!!'))
                if not site_record.expected_supplier:
                    raise except_orm(_('Warning'),_('One of the site requests not have supplier.Please configure..!!'))
                if supplier == False:
                    supplier = site_record.expected_supplier.id
                elif supplier != site_record.expected_supplier.id:
                    raise except_orm(_('Warning'),_('Supplers are different..!!'))

                line_record = {
                    'product_id':site_record.item_id.id,
                    'product_qty':site_record.quantity,
                    'name':site_record.item_id.name,
                    'site_purchase_id':site_record.id,
                    'product_uom':site_record.unit.id,
                    'pro_old_price':site_record.item_id.standard_price,
                    'unit_price':site_record.item_id.standard_price,
                    'price_unit':site_record.item_id.standard_price,
                    'location_id':False,
                    'account_id':site_record.item_id.categ_id.stock_account_id.id,
                    'state':'draft'
                    }
                record.append((0, False, line_record ))


        view_ref = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_form')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Purchase Order'),
           'res_model': 'purchase.order',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'current',
           'context': {'default_partner_id':supplier,'default_order_line':record,'default_date_order':fields.Date.today(),'default_state':'draft'}
       }

        return res


class SitePurchase(models.Model):
    _name = 'site.purchase'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    # _track = {
 #        'state': {
 #            'hiworth_construction.mt_order_sent': lambda self, cr, uid, obj, ctx=None: obj.state in ['confirm'],
 #            #'sale.mt_order_sent': lambda self, cr, uid, obj, ctx=None: obj.state in ['sent']
 #        },
 #    }
    _order = 'id desc'

    @api.onchange('quantity')
    def onchange_quantity_rate(self):
        if self.quantity == 0:
            self.estimated_amt = 0
        else:
            if self.estimated_amt != 0 and self.rate != 0 and self.quantity != round((self.estimated_amt / self.rate),
                                                                                     2):
                self.quantity = 0.0
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': "For Entering value to quantity field, Rate or estimated_amt should be Zero"
                    }
                }
            if self.quantity != 0 and self.rate != 0:
                if self.rate * self.quantity != self.estimated_amt:
                    pass
                if self.estimated_amt == 0.0:
                    self.estimated_amt = round((self.quantity * self.rate), 2)
            if self.estimated_amt != 0 and self.quantity != 0:
                if self.rate == 0.0:
                    self.rate = round((self.estimated_amt / self.quantity), 2)

    @api.onchange('rate')
    def onchange_rate_estimated_amt(self):
        if self.rate == 0:
            self.estimated_amt = 0
        else:
            if self.estimated_amt != 0 and self.quantity != 0 and self.rate != round(
                    (self.estimated_amt / self.quantity), 2):
                self.rate = 0.0
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': "For Entering value to Rate field, quantity or estimated_amt should be Zero."
                    }
                }
            if self.quantity != 0 and self.rate != 0:
                if self.rate * self.quantity != self.estimated_amt:
                    pass
                if self.estimated_amt == 0.0:
                    self.estimated_amt = round((self.quantity * self.rate), 2)
            if self.estimated_amt != 0 and self.rate != 0:
                if self.quantity == 0.0:
                    self.quantity = round((self.estimated_amt / self.rate), 2)

    @api.onchange('estimated_amt')
    def onchange_qty_estimated_amt(self):
        if self.estimated_amt != 0:
            if self.rate * self.quantity != self.estimated_amt:
                if self.rate != 0 and self.quantity != 0:
                    self.estimated_amt = 0.0
                    return {
                        'warning': {
                            'title': 'Warning',
                            'message': "For Entering value to estimated_amt field, quantity or Rate should be Zero."
                        }
                    }
                elif self.rate == 0 and self.quantity != 0:
                    self.rate = round((self.estimated_amt / self.quantity), 2)
                elif self.quantity == 0 and self.rate != 0:
                    self.quantity = round((self.estimated_amt / self.rate), 2)
                else:
                    pass

    @api.onchange('item_id')
    def onchange_product_id(self):

        if self.item_id:
            self.unit = self.item_id.uom_id.id
            self.desc = self.item_id.name

    @api.onchange('min_expected_date', 'max_expected_date')
    def onchange_min_expected_date1(self):
        current_date = datetime.now().date()
        if self.min_expected_date and (self.min_expected_date < str(current_date)):
            self.min_expected_date = False
        # raise except_orm(_('Warning'), ('Expected date should not be lesser than current date..'))

        if self.max_expected_date and (self.max_expected_date < str(current_date)):
            self.max_expected_date = False

    @api.model
    def default_get(self, default_fields):
        vals = super(SitePurchase, self).default_get(default_fields)
        user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if user:
            vals.update({'responsible': user.id})
            if user.employee_id or user.id == 1:
                vals.update({'supervisor_id': user.employee_id.id if user.id != 1 else self.env['hr.employee'].search(
                    [('id', '=', 1)]).id})

        return vals



    @api.multi
    @api.depends('tax_ids', 'received_total')
    def get_tax_amount(self):
        for lines in self:
            # if lines.state == 'processing':
            # 	flag1 = 0
            # 	flag2 = 0
            # 	for p in self.env['purchase.order'].search([('request_id', '=', lines.id)]):
            # 		if p:
            # 			if p.state != 'done':
            # 				flag1 = 1
            # 	for s in self.env['stock.picking'].search([('request_id', '=', lines.id)]):
            # 		if s:
            # 			if s.state != 'done':
            # 				flag2 = 1
            # 	if flag1 == 0 and flag2 == 0:
            # 		lines.state = 'received'
            taxi = 0
            taxe = 0
            for tax in lines.tax_ids:
                if tax.price_include == True:
                    taxi = tax.amount
                if tax.price_include == False:
                    taxe += tax.amount
            lines.tax_amount = (lines.received_total) / (1 + taxi) * (taxi + taxe)
            lines.sub_total = (lines.received_total) / (1 + taxi)
            lines.total_amount = lines.tax_amount + lines.sub_total

    @api.multi
    @api.depends('received_qty', 'received_rate')
    def get_received_total(self):
        for rec in self:
            rec.received_total = rec.received_qty * rec.received_rate


    @api.depends('req_list')
    def compute_items_list(self):
        for rec in self:
            items = ''
            for list in rec.req_list:
                items += list.item_id.name + ','
            rec.items_char = items


    @api.depends('req_list')
    def compute_total_quantity(self):
        for rec in self:
            quantity = 0
            for list in rec.req_list:
                quantity +=list.quantity
            rec.total_qunatity = quantity


    name = fields.Char('MPR No', readonly=True,track_visibility='onchange')
    supervisor_id = fields.Many2one('hr.employee', 'User',track_visibility='onchange')
    responsible = fields.Many2one('res.users', 'Responsible', readonly=True)
    order_date = fields.Datetime('Order Date', readonly=False, default=lambda self: fields.datetime.now())
    min_expected_date = fields.Date('Minimum Expected Date', required=True,default=lambda self: fields.datetime.now().date())
    max_expected_date = fields.Date('Maximum Expected Date',default=lambda self: fields.datetime.now().date())
    received_date = fields.Date('Received Date')
    item_id = fields.Many2one('product.product', 'Item')
    quantity = fields.Float('Quantity')
    unit = fields.Many2one('product.uom', 'Unit')
    req_list = fields.One2many('request.item.list', 'req_list_line', 'Req List')
    request_not_in_draft = fields.Boolean('flag')
    storekeeper_purchase = fields.Boolean('Store Keeper Purchase')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Requested'),
                              ('approved1', 'Approved By PM'),
                              ('verified','Planning/P&M'),
                              ('approved2', 'Approved By GM'),
                              ('processing', 'Under Comparison'),
                              ('purchase', 'Under Purchase'),
                              ('confirm_purchase','Order Placed'),
                              ('received','Received'),
                              ('cancel', 'Cancelled')], default="draft", string="Status")
    status = fields.Char(string="Status")
    site_id = fields.Many2one('partner.daily.statement')
    desc = fields.Char('Description')
    site = fields.Many2one('stock.location', 'Location')
    received_qty = fields.Float('Received Qty')
    received_rate = fields.Float('Received Rate')
    received_total = fields.Float(compute='get_received_total', string='Amount')
    general_purchase = fields.Boolean(default=False)
    vehicle_purchase = fields.Boolean(default=False)
    telecom_purchase = fields.Boolean(default=False)
    interlocks_purchase = fields.Boolean(default=False)
    workshop_purchase = fields.Boolean(default=False)
    bitumen_purchase = fields.Boolean(default=False)
    # expected_supplier = fields.Many2one('res.partner','Supplier')
    rate = fields.Float('Rate')
    estimated_amt = fields.Float('Estimated Amount')
    purchase_manager = fields.Many2one('res.users', 'Purchase Manager')
    sign_general_manager = fields.Binary('Sign')
    project_manager = fields.Many2one('res.users', 'Project Manager')
    dgm_id = fields.Many2one('res.users', 'GM')
    planning_manager = fields.Many2one('res.users', 'Planning/P&M Manager')
    sign_purchase_manager = fields.Binary('Sign')
    invoice_no = fields.Char('Invoice No.')
    invoice_date = fields.Date('Invoice Date')
    stock_move_id = fields.Many2one('stock.move', 'Stock Move')
    account_move_id = fields.Many2one('account.move', 'Journal Entry')
    tax_ids = fields.Many2many('account.tax', string="Tax")
    tax_amount = fields.Float('Tax Amount', compute="get_tax_amount")
    sub_total = fields.Float('Sub Total', compute="get_tax_amount")
    total_amount = fields.Float('Total', compute="get_tax_amount")
    bitumen_agent = fields.Many2one('res.partner', 'Agent')
    vehicle_agent = fields.Many2one('res.partner', 'Vehicle Agent')
    bank_id = fields.Many2one('res.partner.bank', 'Bank')
    doc_no = fields.Char('Doc No.')
    project_id = fields.Many2one('project.project', 'Project', required=True)
    req_no = fields.Char('Req No')
    remarks = fields.Text(string="Remarks",required=True)
    user_category = fields.Selection([('admin', 'Super User'),
                                      ('project_manager', 'Project Manager'),
                                      ('supervisor', 'Supervisor(Civil)'),
                                      ('DGM', 'DGM'),
                                      ], string='User Category', required=True, default='supervisor')
    ppf_dept = fields.Char('Department')
    approved_date=fields.Datetime('Approved Date',default=lambda self: fields.datetime.now())
    verified_date=fields.Datetime('Verified Date',default=lambda self: fields.datetime.now())
    approved_date1=fields.Datetime('Approved date',default=lambda self: fields.datetime.now())
    items_char = fields.Char(string="Item List",compute='compute_items_list')
    total_qunatity = fields.Float(string="Total quantity",compute='compute_total_quantity')
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
    brand_id = fields.Many2one('fleet.vehicle.model.brand',string="Brand")
    model_id = fields.Many2one('fleet.vehicle.model',string="Model")
    chase_no = fields.Char("Chase No")
    engine_no = fields.Char("Engine No")
    decalration = fields.Boolean("Read and Understood below message")




    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.site = self.project_id.location_id.id

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.brand_id = rec.vehicle_id.brand_id.id
                rec.model_id = rec.vehicle_id.model_id.id
                rec.chase_no = rec.vehicle_id.chase_no
                rec.engine_no = rec.vehicle_id.engine_no

    @api.multi
    def cancel_process(self):
        if self.state == 'confirm':
            self.state = 'draft'
        if self.state == 'approved1':
            self.state = 'confirm'
        if self.state  == 'verified':
            self.state = 'approved1'
        if self.state == 'approved2':
            self.state = 'verified'


    @api.multi
    def set_draft(self):
        self.state = 'draft'
        self.request_not_in_draft = False



    @api.cr_uid_ids_context
    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification', subtype=None,
                     parent_id=False, attachments=None, context=None, content_subtype='html', **kwargs):
        """ Overrides mail_thread message_post so that we can set the date of last action field when
            a new message is posted on the issue.
        """
        if context is None:
            context = {}
        res = super(SitePurchase, self).message_post(cr, uid, thread_id, body=body, subject=subject, type=type,
                                                      subtype=subtype, parent_id=parent_id, attachments=attachments,
                                                      context=context, content_subtype=content_subtype, **kwargs)
        if thread_id and subtype:
            self.write(cr, uid, thread_id, {'status': 'Explanantion needed'}, context=context)
        return res

    @api.multi
    def confirm_purchase(self):
        if not self.env.user.partner_id.email:
            self.env.user.partner_id.email = self.env.user.login
        if len(self.req_list):
            self.state = 'confirm'
            self.request_not_in_draft = True
            if self.supervisor_id.user_id and self.supervisor_id.user_id.partner_id:
                message_followers = []
                message_followers.extend(self.message_follower_ids.ids)
                message_followers.append(self.supervisor_id.user_id.partner_id.id)

                self.message_follower_ids = [(6,0,message_followers)]

            users_list = self.env['res.users'].search([])


            for user in users_list:
                if user.has_group('hiworth_construction.project_manager') and user.employee_id.loc_id.id == self.site.id:
                    self.env['popup.notifications'].sudo().create({
                        'name': user.id,
                        'status': 'draft',
                        'message': "You have a material request to approve from" + ' ' + self.supervisor_id.name})

        else:
            raise except_orm(_('Warning'), ('The Request items must be filled..'))

    @api.multi
    def view_moves(self):

        res = {
            'type': 'ir.actions.act_window',
            'name': _('Site To Site Transfer'),
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'view_id': view_id,
            'target': 'current',
            'domain': [('request_id','=',self.id)]
            # 'context': {'default_partner_id': supplier, 'default_order_line': record,
            # 			'default_date_order': fields.Date.today(), 'default_state': 'draft'}
        }

        return res

    @api.multi
    def view_purchases(self):

        res = {
            'type': 'ir.actions.act_window',
            'name': _('Site Purchases'),
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'view_id': view_id,
            'target': 'current',
            'domain': [('request_id', '=', self.id)]
            # 'context': {'default_partner_id': supplier, 'default_order_line': record,
            # 			'default_date_order': fields.Date.today(), 'default_state': 'draft'}
        }

        return res

    @api.multi
    def generate_po_stock(self):
        for rec in self.search([]):
            if rec.project_id.name == 'BIDPL/CENTRAL WORKSHOP':
                rec.name = rec.name.replace('S','')
            if rec.project_id.name == 'CENTRAL STORE':
                rec.name = rec.name.replace('W','')

    @api.multi
    def approve_purchase1(self):
        if not self.env.user.partner_id.email:
            self.env.user.partner_id.email = self.env.user.login
        self.project_manager = self.env.user.id
        self.state = 'approved1'
        # self.user_category = 'DGM'
        message_followers = []
        message_followers.extend(self.message_follower_ids.ids)
        message_followers.append(self.project_manager.partner_id.id)
        self.message_follower_ids = [(6, 0, message_followers)]
        self.approved_date = fields.datetime.now()
        # self.env['popup.notifications'].sudo().create({
        # 	'name': self.project_id.user_id.id,
        # 	'status': 'draft',
        # 	'message': "You have a material request to approve from" + ' ' + self.supervisor_id.name
        # })

        users_list = self.env['res.users'].search([])
        users_list = self.env['res.users'].search([])

        for user in users_list:
            if user.has_group('hiworth_construction.group_plannig_user') and not self.vehicle_purchase:
                self.env['popup.notifications'].sudo().create({
                    'name': user.id,
                    'status': 'draft',
                    'message': "You have a material request to approve from" + ' ' + self.supervisor_id.name})

            if user.has_group('hiworth_construction.group_plannig_user_plant_mac') and self.vehicle_purchase:
                self.env['popup.notifications'].sudo().create({
                    'name': user.id,
                    'status': 'draft',
                    'message': "You have a material request to approve from" + ' ' + self.supervisor_id.name})


    @api.multi
    def verified_planning(self):
        if not self.env.user.partner_id.email:
            self.env.user.partner_id.email = self.env.user.login
        self.state = 'verified'
        self.planning_manager = self.env.user.id
        self.verified_date = fields.datetime.now()
        message_followers = []
        message_followers.extend(self.message_follower_ids.ids)
        message_followers.append(self.planning_manager.partner_id.id)
        self.message_follower_ids = [(6, 0, message_followers)]
        users_list = self.env['res.users'].search([])

        for user in users_list:
            if user.has_group('hiworth_construction.group_general_manager') and not self.vehicle_purchase:

                self.env['popup.notifications'].sudo().create({
                    'name': user.id,
                    'status': 'draft',
                    'message': "You have a material request to approve from" + ' ' + self.supervisor_id.name})

            if user.has_group('hiworth_construction.group_plant_mach_gm') and self.vehicle_purchase:
                self.env['popup.notifications'].sudo().create({
                    'name': user.id,
                    'status': 'draft',
                    'message': "You have a material request to approve from" + ' ' + self.supervisor_id.name})

    @api.multi
    def approve_purchase2(self):
        if not self.env.user.partner_id.email:
            self.env.user.partner_id.email = self.env.user.login
        self.state = 'approved2'
        self.dgm_id = self.env.user.id
        self.approved_date1 = fields.datetime.now()
        message_followers = []
        message_followers.extend(self.message_follower_ids.ids)
        message_followers.append(self.dgm_id.partner_id.id)
        self.message_follower_ids = [(6, 0, message_followers)]

        users_list = self.env['res.users'].search([])

        for user in users_list:
            if user.has_group('hiworth_construction.group_purchase_manager'):
                self.env['popup.notifications'].sudo().create({
                    'name': user.id,
                    'status': 'draft',
                    'message': "You have to create comparison for the material request from" + ' ' + self.supervisor_id.name})



    @api.multi
    def view_invoices(self):
        record = self.env['hiworth.invoice'].search([('site_purchase_id', '=', self.id)])

        if record:
            res_id = record[0].id
        else:
            res_id = False
        res = {
            'name': 'Supplier Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hiworth.invoice',
            'domain': [('line_id', '=', self.id)],
            'res_id': res_id,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('hiworth_construction.hiworth_invoice_form').id,
            'context': {'default_inv_type': 'out', 'type2': 'out'},

        }

        return res

    @api.model
    def create(self, vals):

        if vals.get('supervisor_id') == False:
            user = self.env['res.users'].sudo().search([('id', '=', self.env.user.id)])
            if user:
                if user.employee_id or user.id == 1:
                    vals['supervisor_id'] = user.employee_id.id if user.id != 1 else self.env['hr.employee'].search(
                        [('id', '=', 1)]).id
                else:
                    raise except_orm(_('Warning'), _('User have To Be Linked With Employee.'))

        if vals.get('site') == False:
            if vals.get('site_id'):
                vals['site'] = self.env['partner.daily.statement'].search(
                    [('id', '=', vals['site_id'])]).location_ids.id

        result = super(SitePurchase, self).create(vals)
        if result.name == False:

            result.project_id.mpr_no +=1
            barcode =result.project_id.location_id.loc_barcode
            if result.project_id.name == 'CENTRAL STORE':
                barcode = 'CS'
            if result.project_id.name == 'BIDPL/CENTRAL WORKSHOP':
                barcode = 'CW'

            result.name = str('MPR-') +str(barcode) +  str(result.project_id.mpr_no).zfill(3)  + '/' + str(datetime.now().year)
            if len(self.env['site.purchase'].search([('name','=',result.name)]))>1:
                raise except_orm(_('Warning'), _('MPR NO Already Exists'))
            result.order_date = fields.Datetime.now()
            for rec in result.req_list:
                if rec.requested_quantity == 0:
                    raise except_orm(_('Warning'), _('Requested quantity must be greater than zero'))

        #result.message_post(body=_('%s created')%result.supervisor_id.name)`
        # self.env['mail.alias'].write([project_rec.alias_id.id], {'alias_parent_thread_id': project_id, 'alias_defaults': {'project_id': project_id}}, context)
        # my_val = self.env['site.purchase'].search([('id','=',2)])
        # my_val.message_post(body="TEXT")
        return result

    @api.multi
    def write(self,vals):
        res = super(SitePurchase, self).write(vals)
        if len(self.env['site.purchase'].search([('name', '=', self.name)])) > 1:
            raise except_orm(_('Warning'), _('MPR NO Already Exists'))
        return res



class Request_Item_list(models.Model):
    _name = 'request.item.list'

    @api.onchange('requested_quantity')
    def onchange_requested_quantity(self):
        if self.requested_quantity:
            self.quantity = self.requested_quantity




    @api.onchange('item_id')
    def onchange_item_id(self):
        for rec in self:
            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.part_no_spec = rec.item_id.part_no
                rec.unit = rec.item_id.uom_id.id
                # rec.available_quantity = 0.0

    @api.depends('item_id')
    def compute_available(self):
        for rec in self:
            if rec.item_id:

                stock_history = self.env['stock.history'].search(
                    [('date', '<', rec.req_list_line.order_date), ('location_id', '=', rec.req_list_line.site.id),
                     ('product_id', '=', rec.item_id.id)])
                available = 0
                for hist in stock_history:
                    available += hist.quantity

                rec.available_quantity = available


    req_list_line = fields.Many2one('site.purchase')
    item_id = fields.Many2one('product.product','Material Code')
    available_quantity = fields.Float('Available Quantity',compute='compute_available',digits_compute=dp.get_precision('Product Unit of Measure'))
    requested_quantity = fields.Float('Required Quantity',digits_compute=dp.get_precision('Product Unit of Measure'))
    quantity = fields.Float('Approved Quantity',digits_compute=dp.get_precision('Product Unit of Measure'))
    remarks = fields.Text('Remarks')
    unit = fields.Many2one('product.uom','Unit')
    rate = fields.Float('Rate')
    expected_supplier = fields.Many2one('res.partner', 'Supplier',domain=[('supplier','=',True)])
    location_id = fields.Many2one('stock.location', 'From')
    stock_type = fields.Selection([('company_stock', 'Company Stock'), ('supplier_stock', 'Supplier Stock')])
    estimated_amt = fields.Float('Estimated Amount', compute="get_estimate_amt")
    desc = fields.Char('Material Name')
    request_not_in_draft = fields.Boolean('flag', related="req_list_line.request_not_in_draft")
    part_no_spec = fields.Char('PartNo/Specification')
    user_id = fields.Many2one(string='User',related="req_list_line.supervisor_id")
    project_id = fields.Many2one(string ='Project',related="req_list_line.project_id")
    location_id = fields.Many2one(string ='Location',related="req_list_line.site")
    order_date = fields.Datetime('Order Date',related="req_list_line.order_date")
    min_expected_date = fields.Date('Minimum Expected Date',related="req_list_line.min_expected_date")
    max_expected_date = fields.Date('Maximum Expected Date',related="req_list_line.max_expected_date")
    name = fields.Char('MPR.No',related="req_list_line.name")
    is_comparison = fields.Boolean("Is comparison",default=False)



    @api.one
    def get_estimate_amt(self):
        for s in self:
            s.estimated_amt = s.quantity * s.rate

    # @api.onchange('stock_type')
    # def onchange_stock_type(self):
    # 	if self.stock_type == 'company_stock':
    # 		self.expected_supplier = 82



class BcplAccountDetails(models.Model):
    _name = 'bcpl.account.details'


    item = fields.Char('Item')
    invoice_no = fields.Integer('Invoice No')
    doc = fields.Integer('Doc')
    order_date = fields.Date('Order Date')
    supplier = fields.Many2one('res.partner','Supplier')
    site_name = fields.Char('Site Name')
    qty = fields.Integer('Qty')
    rate = fields.Float('Rate')
    amount = fields.Float('Amount',compute= 'onchange_amount')
    agent = fields.Char('Agent')
    vehicle_no = fields.Char('Vehicle No')
    date = fields.Date('Date')
    bank = fields.Char('Bank')
    total_amount = fields.Float('Toatal Amount')


    @api.onchange('qty','rate')
    def onchange_amount(self):
        self.amount = self.qty*self.rate

class SitePurchaseReport(models.TransientModel):

    _name = 'site.purchase.report'

    requested_site_id = fields.Many2one('stock.location', 'Requested Site')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    project_id = fields.Many2one('project.project', 'Project')
    report_type = fields.Selection([('transfer', 'Goods Transfer Report'), ('receive', 'Goods Receive Report')])

    @api.multi
    def print_report(self):
        datas = {
            'model': 'hr.contribution.register',
            'form': self.read()[0],
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_construction.report_site_purchase_template',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def print_report_html(self):
        datas = {
            'model': 'hr.contribution.register',
            'form': self.read()[0],
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_construction.report_site_purchase_template',
            'datas': datas,
            'report_type': 'qweb-html'
        }

class ReportSitePurchasTemplate(models.AbstractModel):

    _name = 'report.hiworth_construction.report_site_purchase_template'

    @api.model
    def render_html(self, docids, data=None):
        this = self.env['site.purchase.report'].browse(docids)
        if this:
            datas = []
            site = []
            domain = []
            if this.date_from:
                domain.append(('order_date', '>=', str(this.date_from) + " 00:01:01"))
            if this.date_to:
                domain.append(('order_date', '<=', str(this.date_to) + " 23:59:59"))
            if this.requested_site_id.id:
                domain.append(('site', '=', this.requested_site_id.id))
            if this.project_id.id:
                domain.append(('project_id', '=', this.project_id.id))
            if this.report_type == 'receive':
                domain.append(('state', '=', 'received'))
            for sp in self.env['site.purchase'].search(domain):
                if sp.site.id in site:
                    for d in datas:
                        if d['site_id'] == sp.site.id:
                            for i in sp.req_list:
                                if this.report_type == 'receive':
                                    if i.stock_type == 'supplier_stock':
                                        order_line = self.env['purchase.order.line'].search([('site_purchase_id', '=', sp.id), ('product_id', '=', i.item_id.id)])
                                        d['lines'].append({
                                            'location_id': i.location_id.name,
                                            'unit': i.unit.name,
                                            'supplier': i.expected_supplier.name or '',
                                            'po': order_line.order_id.name or '',
                                            'item_id': i.item_id.name,
                                            'default_code': i.item_id.default_code,
                                            'accepted_quantity': order_line.product_qty,
                                            'received_quantity': order_line.required_qty,
                                            'rejected_qty': order_line.required_qty - order_line.product_qty,
                                            'rate': i.rate,
                                            'estimated_amount': i.estimated_amt,
                                            'remarks': i.remarks,
                                        })
                                if this.report_type == 'transfer':
                                    if i.stock_type == 'company_stock':
                                        d['lines'].append({
                                            'location_id': i.location_id.name or '',
                                            'unit': i.unit.name or '',
                                            'item_id': i.item_id.name or '',
                                            'default_code': i.item_id.default_code or '',
                                            'requested_quantity': i.requested_quantity or '',
                                            'quantity': i.quantity or '',
                                            'rate': i.rate or '',
                                            'estimated_amount': i.estimated_amt or '',
                                            'remarks': i.remarks or '',
                                        })
                else:
                    s = {
                        'site': sp.site.name,
                        'site_id': sp.site.id,
                        'lines': [],
                        'grr': sp.name,
                        'project': sp.project_id.name,
                        'approved_by1': sp.purchase_manager.name or '',
                        'approved_by2': sp.dgm_id.name or '',
                        'approved_by3': sp.project_manager.name or ''
                    }
                    for i in sp.req_list:
                        if this.report_type == 'receive':
                            if i.stock_type == 'supplier_stock':
                                order_line = self.env['purchase.order.line'].search(
                                    [('site_purchase_id', '=', sp.id), ('product_id', '=', i.item_id.id)])
                                s['lines'].append({
                                    'location_id': i.location_id.name,
                                    'unit': i.unit.name,
                                    'supplier': i.expected_supplier.name or '',
                                    'po': order_line.order_id.name or '',
                                    'item_id': i.item_id.name,
                                    'default_code': i.item_id.default_code,
                                    'accepted_quantity': order_line.product_qty,
                                    'received_quantity': order_line.required_qty,
                                    'rejected_qty': order_line.required_qty - order_line.product_qty,
                                    'rate': i.rate,
                                    'estimated_amount': i.estimated_amt,
                                    'remarks': i.remarks,
                                })
                        if this.report_type == 'transfer':
                            if i.stock_type == 'company_stock':
                                s['lines'].append({
                                    'location_id': i.location_id.name or '',
                                    'unit': i.unit.name or '',
                                    'item_id': i.item_id.name or '',
                                    'default_code': i.item_id.default_code or '',
                                    'requested_quantity': i.requested_quantity or '',
                                    'quantity': i.quantity or '',
                                    'rate': i.rate or '',
                                    'estimated_amount': i.estimated_amt or '',
                                    'remarks': i.remarks or '',
                                })
                    if s['lines']:
                        datas.append(s)
                        site.append(sp.site.id)
            record = {
                'type': this.report_type,
                'data': datas
            }
            docargs = {
                'doc_ids': this.id,
                'doc_model': 'site.purchase',
                'docs': record,
            }

            return self.env['report'].render('hiworth_construction.report_site_purchase_template', docargs)