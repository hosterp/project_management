from openerp import models, fields, api
from datetime import datetime

class PurchaseComparison(models.Model):
    _name = 'purchase.comparison'
    _rec_name = 'number'
    _order = 'id desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'finance')]

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.brand_id = rec.vehicle_id.brand_id.id
                rec.model_id = rec.vehicle_id.model_id.id
                rec.chase_no = rec.vehicle_id.chase_no
                rec.engine_no = rec.vehicle_id.engine_no

    @api.onchange('mpr_id')
    def onchange_mpr_id(self):
        for rec in self:
            if rec.mpr_id:
                values = []
                rec.project_id = rec.mpr_id.project_id.id
                rec.vehicle_id=rec.mpr_id.vehicle_id.id
                rec.number = rec.mpr_id.name + "Comparison"
                for mpr_line in rec.mpr_id.req_list:
                    if mpr_line.is_comparison == False:
                        values.append((0,0,{'product_id':mpr_line.item_id.id,
                            'qty':mpr_line.quantity,
                            'uom':mpr_line.unit.id}))
                rec.comparison_line = values

    # @api.one
    # def button_request(self):
    #    

    # @api.one
    # def button_approve1(self):
    #     self.user_id1 = self.env.user.id
    #     self.state = 'validated1'


    @api.one
    def button_request(self):
        
        l=[]
        if self.total_amt1 != 0:
            l.append(self.total_amt1)
        if self.total_amt2 !=0:
            l.append(self.total_amt2)
        if self.total_amt3 !=0:
            l.append(self.total_amt3)
        if self.total_amt4 !=0:
            l.append(self.total_amt4)
        if self.total_amt5 !=0:
            l.append(self.total_amt5)
        
        
        if min(l) == self.total_amt1:
            self.partner_selected = self.partner_id1.id
        if min(l) == self.total_amt2:
            self.partner_selected = self.partner_id2.id
        if min(l) == self.total_amt3:
            self.partner_selected = self.partner_id3.id
        if min(l) == self.total_amt4:
            self.partner_selected = self.partner_id4.id
        if min(l) == self.total_amt5:
            self.partner_selected = self.partner_id5.id
        if self.mpr_id:
            self.mpr_id.write({'state':'processing'})
        self.requested_by = self.env.user.id
        self.requested_date = fields.datetime.now()
        self.state = 'requested'
        for line in self.comparison_line:
            if self.mpr_id:
                for good in self.mpr_id.req_list:
                    if line.product_id.id == good.item_id.id:
                        good.is_comparison = True

        
    @api.one
    def button_approve2(self):
        self.user_id2 = self.env.user.id
        self.approved_date = fields.datetime.now()
        if self.partner_select1:
            self.partner_selected = self.partner_id1.id
        if self.partner_select2:
            self.partner_selected = self.partner_id2.id
        if self.partner_select3:
            self.partner_selected = self.partner_id3.id
        if self.partner_select4:
            self.partner_selected = self.partner_id4.id
        for user in self.env['res.users'].search([]):
            if user.has_group('hiworth_construction.group_purchase_manager'):
                self.env['popup.notifications'].sudo().create({
                    'name': user.id,
                    'status': 'draft',
                    'message': 'You have a Purchase Comparison To Create Purchase',

                })
        self.state = 'validated2'


    @api.one
    def button_cancel(self):
        for rec in self:
            if rec.state == 'po':
                rec.state = 'validated2'
            elif rec.state == 'validated2':
                rec.state = 'finance'
            elif rec.state == 'requested':
                rec.state = 'draft'

            elif rec.state == 'finance':
                rec.state = 'requested'


    @api.one
    def button_po_create(self):
        list = []
        flag = 0

        vals = {
            'partner_id': self.partner_selected.id,
            'pricelist_id': self.partner_selected.property_product_pricelist_purchase.id,
            'minimum_planned_date': self.mpr_id.min_expected_date,
            'maximum_planned_date':self.mpr_id.max_expected_date,
            'project_id': self.project_id.id,
            'location_id': self.project_id.location_id.id,
            'account_id': self.partner_selected.property_account_payable.id,
            'mpr_id':self.mpr_id.id,
            'vehicle_id':self.vehicle_id.id,
            'model_id':self.model_id.id,
            'brand_id':self.brand_id.id,
        }
       
        for l in self.comparison_line:
            if l.approved:
                tax = []
                for taxes in l.tax_ids:
                    tax.append(taxes.id)
                l.product_id.taxes_id = [(6,0,l.tax_ids.ids)]
                dictionary = {
                    'product_id': l.product_id.id,
                    'name': l.product_id.name,
                    'required_qty': l.qty,
                    'product_uom': l.product_id.uom_id.id,
                    'price_unit': 0.0,
                    'account_id': self.env['account.account'].search([('name', '=', 'Purchase')]).id,
                    'taxes_id':[(6,0, tax)],
                }
                if self.partner_selected.id == self.partner_id1.id:
                    flag = 1
                    dictionary['expected_rate'] = l.rate1
                    dictionary['price_unit'] = l.rate1
                    l.product_id.standard_price = l.rate1

                    list.append((0, 0, dictionary))
                if self.partner_selected.id == self.partner_id2.id:
                    flag = 2
                    dictionary['expected_rate'] = l.rate2
                    dictionary['price_unit'] = l.rate2
                    l.product_id.standard_price = l.rate2
                    list.append((0, 0, dictionary))
                if self.partner_selected.id == self.partner_id3.id:
                    flag = 3
                    dictionary['expected_rate'] = l.rate3
                    dictionary['price_unit'] = l.rate3
                    l.product_id.standard_price = l.rate3
                    list.append((0, 0, dictionary))
                if self.partner_selected.id == self.partner_id4.id:
                    flag = 4
                    dictionary['expected_rate'] = l.rate4
                    dictionary['price_unit'] = l.rate4
                    l.product_id.standard_price = l.rate4
                    list.append((0, 0, dictionary))
                if self.partner_selected.id == self.partner_id5.id:
                    flag = 5
                    dictionary['expected_rate'] = l.rate5
                    dictionary['price_unit'] = l.rate5
                    l.product_id.standard_price = l.rate5
                    list.append((0, 0, dictionary))
                

    
        if flag == 1:
            vals.update({'payment_term_id':self.payment_term1.id,
                         'notes':str(self.remark) + " " +str(self.remark1) or '',
                         'packing_charge':self.p_n_f1,
                         'loading_charge':self.loading_charge1,
                         'transporting_charge':self.transport_cost1,
                         'round_off_amount':self.round_off_amt1})

                
        if flag == 2:
            vals.update({'payment_term_id': self.payment_term2.id,
                         'notes': str(self.remark) + " " + str(self.remark2) or '',
                         'packing_charge': self.p_n_f2,
                         'loading_charge': self.loading_charge2,
                         'transporting_charge': self.transport_cost2,
                         'round_off_amount':self.round_off_amt2})


                    
        if flag == 3:
            vals.update({'payment_term_id': self.payment_term3.id,
                         'notes': str(self.remark) + " " + str(self.remark3) or '',
                         'packing_charge': self.p_n_f3,
                         'loading_charge': self.loading_charge3,
                         'transporting_charge': self.transport_cost3,
                         'round_off_amount':self.round_off_amt3})
                    
        if flag == 4:
            vals.update({'payment_term_id': self.payment_term4.id,
                         'notes': str(self.remark) + " " + str(self.remark4) or '',
                         'packing_charge': self.p_n_f4,
                         'loading_charge': self.loading_charge4,
                         'transporting_charge': self.transport_cost4,
                         'round_off_amount':self.round_off_amt4})
        if flag == 5:
            vals.update({'payment_term_id': self.payment_term5.id,
                         'notes': str(self.remark) + " " + str(self.remark5) or '',
                         'packing_charge': self.p_n_f5,
                         'loading_charge': self.loading_charge5,
                         'transporting_charge': self.transport_cost5,
                         'round_off_amount':self.round_off_amt5})
        vals['order_line'] = list
        
        purchase_id = self.env['purchase.order'].create(vals)
        self.purchase_id = purchase_id.id
        self.state = 'po'
        self.mpr_id.state = 'purchase'
        for user in self.env['res.users'].search([]):
            if user.has_group('hiworth_construction.group_ceo'):
                self.env['popup.notifications'].sudo().create({
                    'name': user.id,
                    'status': 'draft',
                    'message': "You have a Purchase Order To Approve",

                })


    @api.multi
    def button_view_purchase(self):
        res = {
            'type': 'ir.actions.act_window',
            'name': 'Purchases',
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', '=', self.purchase_id.id)]
        }

        return res
    
    @api.multi
    def action_verify(self):
        for rec in self:
            rec.finance_verified_id = self.env.user.id
            rec.finance_verfied_date = fields.datetime.now()
            rec.state = 'finance'
            
    @api.multi
    def button_send_report(self):
        for rec in self:
            
            message = 'Hi, '+ self.env.user.name + " " + rec.remark + " against MPR NO : " + rec.mpr_id.name
            if rec.mpr_id and rec.mpr_id.project_manager:
                self.env['popup.notifications'].sudo().create({
                                                    'name':rec.mpr_id.project_manager.id,
                                                    'status':'draft',
                                                    'message':message,
                                                    
                                                    })
            if rec.mpr_id and rec.mpr_id.dgm_id:
                self.env['popup.notifications'].sudo().create({
                'name': rec.mpr_id.dgm_id.id,
                'status': 'draft',
                'message': message,
    
            })

            if rec.mpr_id and rec.mpr_id.planning_manager:
                self.env['popup.notifications'].sudo().create({
                    'name': rec.mpr_id.planning_manager.id,
                    'status': 'draft',
                    'message': message,
        
                })

            if rec.mpr_id and rec.create_uid:
                self.env['popup.notifications'].sudo().create({
                    'name': rec.create_uid.id,
                    'status': 'draft',
                    'message': message,
        
                })



    @api.one
    def get_total(self):
        for s in self:
            t1 = 0.0
            t2 = 0.0
            t3 = 0.0
            t4 = 0.0
            t5 = 0.0
            sub_total1 = 0
            sub_total2 = 0
            sub_total3 = 0
            sub_total4 = 0
            sub_total5 = 0

            for l in s.comparison_line:
                t1 += l.sub_total1
                t2 += l.sub_total2
                t3 += l.sub_total3
                t4 += l.sub_total4
                t5 += l.sub_total5
                sub_total1 += l.sub_total1 +( s.loading_charge1 * l.qty)+ (s.transport_cost1 * l.qty )+ (s.p_n_f1 * l.qty)
                sub_total2 += l.sub_total2+ (s.loading_charge2 * l.qty)+ (s.transport_cost2 * l.qty)+ (s.p_n_f2* l.qty)
                sub_total3 += l.sub_total3 + (s.loading_charge3  * l.qty)+( s.transport_cost3 * l.qty )+( s.p_n_f3 * l.qty)
                sub_total4 += l.sub_total4+ (s.loading_charge4 * l.qty) + (s.transport_cost5  * l.qty)+ (s.p_n_f4  * l.qty)
                sub_total5 += l.sub_total5+ s.loading_charge5* l.qty + s.transport_cost5* l.qty + s.p_n_f5* l.qty
                for taxes in l.tax_ids:

                    if taxes.tax_type == 'cgst' and not taxes.price_include:
                        s.tax_amount1 += l.rate1 * l.qty * taxes.amount
                        s.tax_amount2 += l.rate2 * l.qty * taxes.amount
                        s.tax_amount3 += l.rate3 * l.qty * taxes.amount
                        s.tax_amount4 += l.rate4 * l.qty * taxes.amount
                        s.tax_amount5 += l.rate5 * l.qty * taxes.amount

                    elif taxes.tax_type == 'sgst' and not taxes.price_include:
                        s.stax_amount1 += l.rate1 * l.qty * taxes.amount
                        s.stax_amount2 += l.rate2 * l.qty * taxes.amount
                        s.stax_amount3 += l.rate3 * l.qty * taxes.amount
                        s.stax_amount4 += l.rate4 * l.qty * taxes.amount
                        s.stax_amount5 += l.rate5 * l.qty * taxes.amount

                    elif taxes.tax_type == 'igst' and not taxes.price_include:
                        s.itax_amount1 += l.rate1 * l.qty * taxes.amount
                        s.itax_amount2 += l.rate2 * l.qty * taxes.amount
                        s.itax_amount3 += l.rate3 * l.qty * taxes.amount
                        s.itax_amount4 += l.rate4 * l.qty * taxes.amount
                        s.itax_amount5 += l.rate5 * l.qty * taxes.amount

            s.total_amt1 = sub_total1 + s.tax_amount1 + s.stax_amount1 + s.itax_amount1 - s.discount_amount1 + s.round_off_amt1
            s.total_amt2 = sub_total2 + s.tax_amount2 + s.stax_amount2 + s.itax_amount2 - s.discount_amount2 + s.round_off_amt2
            s.total_amt3 = sub_total3 + s.tax_amount3 + s.stax_amount3 + s.itax_amount3 - s.discount_amount3 + s.round_off_amt3
            s.total_amt4 = sub_total4 + s.tax_amount4 + s.stax_amount4 + s.itax_amount4 - s.discount_amount4 + s.round_off_amt4
            s.total_amt5 = sub_total5 + s.tax_amount5 + s.stax_amount5 + s.itax_amount5 - s.discount_amount5 + s.round_off_amt5


    @api.onchange('partner_select1')
    def onchange_partner_select(self):
        for rec in self:
            if rec.partner_select1:
                rec.partner_selected = rec.partner_id1.id
                rec.partner_select2 = False
                rec.partner_select3 = False


    @api.onchange('partner_select2')
    def onchange_partner_select2(self):
        for rec in self:

            if rec.partner_select2:
                rec.partner_selected = rec.partner_id2.id
                rec.partner_select1 = False
                rec.partner_select3 = False


    @api.onchange( 'partner_select3')
    def onchange_partner_select3(self):
        for rec in self:

            if rec.partner_select3:
                rec.partner_selected = rec.partner_id3.id
                rec.partner_select2 = False
                rec.partner_select1 = False

    project_id = fields.Many2one('project.project', 'Project')
    number = fields.Char('Purchase Comparison Number:')
    mpr_id = fields.Many2one('site.purchase',string="Material Requistion")
    date = fields.Datetime('Indent Date',default=lambda self: fields.datetime.now())
    partner_id1 = fields.Many2one('res.partner', 'Supplier')
    remark1 = fields.Char('Remark')
    partner_id2 = fields.Many2one('res.partner', 'Supplier')
    remark2 = fields.Char('Remark')
    partner_id3 = fields.Many2one('res.partner', 'Supplier')
    remark3 = fields.Char('Remark')
    partner_id4 = fields.Many2one('res.partner', 'Supplier')
    remark4 = fields.Char('Remark')
    partner_id5 = fields.Many2one('res.partner', 'Supplier')
    remark5 = fields.Char('Remark')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle No")
    model_id = fields.Many2one('fleet.vehicle.model', "Model")
    brand_id = fields.Many2one('fleet.vehicle.model.brand', "Brand")
    chase_no = fields.Char("Chase No")
    engine_no = fields.Char("Model No")
    state = fields.Selection([('draft', 'Draft'), ('requested', 'Under Finance'), ('finance','For Approval'),('validated2', 'Approved'),
                              ('po', 'Purchase Order')],default='draft')
    comparison_line = fields.One2many('purchase.comparison.line', 'res_id', 'Comparison Line')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
    approved_date = fields.Datetime('Approved Date' ,default=lambda self: fields.datetime.now())
    finance_verified_id = fields.Many2one('res.users',"Finance Verified By")
    finance_verfied_date = fields.Datetime("Finance Verified Date",default=lambda self: fields.datetime.now())
    requested_date = fields.Datetime("Requested Date",default=lambda self: fields.datetime.now())
    requested_by = fields.Many2one('res.users',"Requested By")
    mpr_approved_date=fields.Datetime('Purchase Manager Approved Date',related='mpr_id.approved_date')
    mpr_verified_date=fields.Datetime('Planning/P&M Verified Date',related='mpr_id.verified_date')
    mpr_approved_date1=fields.Datetime('GM Approved date',related='mpr_id.approved_date1')
    mpr_purchase_manager_id = fields.Many2one('res.users',"Purchase Manager",related='mpr_id.project_manager')
    mpr_planning_id = fields.Many2one('res.users',"Planning/P&M",related='mpr_id.planning_manager')
    mpr_gm = fields.Many2one('res.users',"General Manager",related='mpr_id.dgm_id')

    tax_id1 = fields.Many2one('account.tax', 'GST')
    # tax_id2 = fields.Many2one('account.tax', 'GST')
    # tax_id3 = fields.Many2one('account.tax', 'GST')
    # tax_id4 = fields.Many2one('account.tax', 'GST')
    # tax_id5 = fields.Many2one('account.tax', 'GST')

    p_n_f1 =fields.Float('P&F')
    p_n_f2 =fields.Float('P&F')
    p_n_f3 =fields.Float('P&F')
    p_n_f4 =fields.Float('P&F')
    p_n_f5 =fields.Float('P&F')

    loading_charge1 = fields.Float('Loading Charge')
    loading_charge2 = fields.Float('Loading Charge')
    loading_charge3 = fields.Float('Loading Charge')
    loading_charge4 = fields.Float('Loading Charge')
    loading_charge5 = fields.Float('Loading Charge')

    transport_cost1 = fields.Float('Transport Cost')
    transport_cost2 = fields.Float('Transport Cost')
    transport_cost3 = fields.Float('Transport Cost')
    transport_cost4 = fields.Float('Transport Cost')
    transport_cost5 = fields.Float('Transport Cost')

    delivery_period1 = fields.Char('Ready To Stock')
    delivery_period2 = fields.Char('Ready To Stock')
    delivery_period3 = fields.Char('Ready To Stock')
    delivery_period4 = fields.Char('Ready To Stock')
    delivery_period5 = fields.Char('Ready To Stock')

    payment_term1 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term2 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term3 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term4 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term5 = fields.Many2one('account.payment.term', 'Term Of Payment')
    
    
    tax_amount1 = fields.Float("CGST Amount",compute='get_total')
    tax_amount2 = fields.Float("CGST Amount",compute='get_total')
    tax_amount3 = fields.Float("CGST Amount",compute='get_total')
    tax_amount4 = fields.Float("CGST Amount",compute='get_total')
    tax_amount5 = fields.Float("CGST Amount",compute='get_total')

    stax_amount1 = fields.Float("SGST Amount", compute='get_total')
    stax_amount2 = fields.Float("SGST Amount", compute='get_total')
    stax_amount3 = fields.Float("SGST Amount", compute='get_total')
    stax_amount4 = fields.Float("SGST Amount", compute='get_total')
    stax_amount5 = fields.Float("SGST Amount", compute='get_total')

    itax_amount1 = fields.Float("IGST Amount", compute='get_total')
    itax_amount2 = fields.Float("IGST Amount", compute='get_total')
    itax_amount3 = fields.Float("IGST Amount", compute='get_total')
    itax_amount4 = fields.Float("IGST Amount", compute='get_total')
    itax_amount5 = fields.Float("IGST Amount", compute='get_total')

    discount_amount1 = fields.Float("Discount Amount")
    discount_amount2 = fields.Float("Discount Amount")
    discount_amount3 = fields.Float("Discount Amount")
    discount_amount4 = fields.Float("Discount Amount")
    discount_amount5 = fields.Float("Discount Amount")
    
    credit_balance1 = fields.Float("Credit Balance")
    credit_balance2 = fields.Float("Credit Balance")
    credit_balance3 = fields.Float("Credit Balance")
    credit_balance4 = fields.Float("Credit Balance")
    credit_balance5 = fields.Float("Credit Balance")

    round_off_amt1 = fields.Float("Round Off")
    round_off_amt2 = fields.Float("Round Off")
    round_off_amt3 = fields.Float("Round Off")
    round_off_amt4 = fields.Float("Round Off")
    round_off_amt5 = fields.Float("Round Off")
    

    total_amt5 = fields.Float('Total Amount', compute='get_total')
    total_amt4 = fields.Float('Total Amount', compute='get_total')
    total_amt3 = fields.Float('Total Amount', compute='get_total')
    total_amt2 = fields.Float('Total Amount', compute='get_total')
    total_amt1 = fields.Float('Total Amount', compute='get_total')

    partner_selected = fields.Many2one('res.partner', 'Vendor Selected')
    remark = fields.Text('Note')
    user_id1 = fields.Many2one('res.users', 'Approved By')
    user_id2 = fields.Many2one('res.users', 'Approved By')
    fund_available = fields.Boolean(string="Fund Available")
    fund_shortage = fields.Boolean(string="Fund Shortage")
    expected_date = fields.Date(string="Expected Date")
    partner_select1 = fields.Boolean("Partner1")
    partner_select2 = fields.Boolean("Partner1")
    partner_select3 = fields.Boolean("Partner1")
    partner_select4 = fields.Boolean("Partner1")

class PurchaseComparisonLine(models.Model):

    _name = 'purchase.comparison.line'

    

    @api.onchange('product_id')
    def onchange_product(self):
        self.uom = self.product_id.uom_id.id

    @api.one
    def get_total(self):
        for s in self:
            s.sub_total1 = s.rate1 * s.qty
            s.sub_total2 = s.rate2 * s.qty
            s.sub_total3 = s.rate3 * s.qty
            s.sub_total4 = s.rate4 * s.qty
            s.sub_total5 = s.rate5 * s.qty


    res_id = fields.Many2one('purchase.comparison', 'Purchase Comparison')
    product_id = fields.Many2one('product.product', 'Description')
    qty = fields.Float('Quantity')
    uom = fields.Many2one('product.uom', 'Unit')
    rate1 = fields.Float('Unit Rate')
    rate2 = fields.Float('Unit Rate')
    rate3 = fields.Float('Unit Rate')
    rate4 = fields.Float('Unit Rate')
    rate5 = fields.Float('Unit Rate')
    sub_total1 = fields.Float('Value', compute="get_total")
    sub_total2 = fields.Float('Value', compute="get_total")
    sub_total3 = fields.Float('Value', compute="get_total")
    sub_total4 = fields.Float('Value', compute="get_total")
    sub_total5 = fields.Float('Value', compute="get_total")
    approved = fields.Boolean(string="Approved",default=True)
    tax_ids = fields.Many2many('account.tax','comparison_line_account_tax_rel','comparison_line_id','tax_id','GST')


    