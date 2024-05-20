from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from openerp.osv import osv
from datetime import datetime,timedelta
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning as UserError
from lxml import etree
from dateutil import tz
from pytz import timezone

class ItemProduct(models.Model):
    _name = 'item.product'

    name = fields.Char('Name')


class AccountJournal(models.Model):
    _inherit = 'account.move'

    driver_stmt_id = fields.Many2one('driver.daily.statement')
    partner_stmt_id = fields.Many2one('partner.daily.statement')
    rent_vehicle_stmt = fields.Many2one('rent.vehicle.statement')
    fleet_emi = fields.Many2one('fleet.emi')


class CashTransferLimit(models.Model):
    _name = 'cash.transfer.limit'

    name = fields.Many2one('hr.employee','Employee')
    cash_limit = fields.Float('Cash Transfer Limit Per Day',required=True)

class CashConfirmTransfer(models.Model):
    _name = 'cash.confirm.transfer'
    _order = 'id desc'

    @api.multi
    def get_visibility(self):
        if self.user_id:
            if self.user_id.id == self.env.user.employee_id.id:
                self.visibility2 = True
            else:
                self.visibility2 = False

    @api.multi
    @api.depends('user_id')
    def compute_to_user(self):
        for rec in self:
            rec.transfer_to_user = self.env['res.users'].search([('employee_id','=',rec.user_id.id)], limit=1).id

    @api.multi
    @api.depends('name')
    def compute_from_user(self):
        for rec in self:
            rec.transfer_from_user = self.env['res.users'].search([('employee_id','=',rec.name.id)], limit=1).id
    # rec = fields.Many2one('driver.daily.statement')
    date = fields.Date(default=fields.Date.today, string="Date")
    name = fields.Many2one('hr.employee')
    state = fields.Selection([('pending','Pending'),('accepted','Accepted')],default='pending')
    amount = fields.Float('Amount')
    user_id = fields.Many2one('hr.employee')
    admin = fields.Many2one('res.users')
    driver_stmt_id = fields.Many2one('driver.daily.statement')
    visibility2 = fields.Boolean(default=False,compute='get_visibility')
    transfer_to_user = fields.Many2one('res.users', compute='compute_to_user', store=True, string='Receiver')
    transfer_from_user = fields.Many2one('res.users', compute='compute_from_user', store=True, string='Sender')



    @api.multi
    def accept_cash(self):
        if len(self.env['driver.daily.statement'].search([('date','=',self.date),('driver_name','=',self.user_id.id)])) == 0 and len(self.env['partner.daily.statement'].sudo().search([('date','=',self.date),('employee_id','=',self.user_id.id)])) == 0:
            raise osv.except_osv(_('Error!'),_("Please open a Daily Statement for accepting this transfer."))
        # if len(self.env['partner.daily.statement'].sudo().search([('date','=',self.date)])) == 0:
        # 	raise osv.except_osv(_('Error!'),_("Please open a Daily Statement for accepting this transfer."))
        move = self.env['account.move']
        move_line = self.env['account.move.line']
        journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
        if not journal:
            raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
        if len(journal) > 1:
            raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))

        for rec in self:
            driver_stmt_id = self.env['driver.daily.statement'].sudo().search([('id','=',rec.driver_stmt_id.id)])
            values = {
                    'journal_id': journal.id,
                    'date': self.date,
                    }
            move_id = move.create(values)
            values = {
                    'account_id': rec.name.petty_cash_account.id,
                    # 'vehicle_id':driver_stmt_id.vehicle_no.id  if driver_stmt_id and rec.name.user_category == 'driver' or rec.name.user_category == 'eicher_driver' else False,
                    # 'driver_stmt_id':rec.driver_stmt_id.id if self.driver_stmt_id else False,
                    'name': 'narration',
                    'debit': 0,
                    'credit': rec.amount,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values)
            values2 = {
                    'account_id': rec.user_id.petty_cash_account.id,
                    'name': 'narration',
                    'debit': rec.amount,
                    'credit': 0,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values2)
            rec.state = 'accepted'

class FuelTransfer(models.TransientModel):
    _name = 'fuel.transfer'

    rec = fields.Many2one('driver.daily.statement')
    date = fields.Date(default=fields.Date.today, string="Date")
    name = fields.Many2one('hr.employee')
    amount = fields.Float('Amount')
    user_id = fields.Many2one('hr.employee')


    @api.multi
    def transfer_fuel(self):
        self.env['fuel.confirm.transfer'].sudo().create({
            'date':self.date,
            'name':self.name.id,
            'amount':self.amount,
            'user_id':self.user_id.id,
            'state':'pending',
            'driver_stmt_id':self.rec.id,
            'admin':1})
        return True


class FuelConfirmTransfer(models.Model):
    _name = 'fuel.confirm.transfer'
    _order = 'id desc'

    @api.multi
    def get_visibility(self):
        if self.user_id:
            if self.user_id.id == self.env.user.employee_id.id:
                self.visibility2 = True
            else:
                self.visibility2 = False

    @api.multi
    @api.depends('user_id')
    def compute_to_user(self):
        for rec in self:
            rec.transfer_to_user = self.env['res.users'].search([('employee_id','=',rec.user_id.id)], limit=1).id


    @api.multi
    @api.depends('name')
    def compute_from_user(self):
        for rec in self:
            rec.transfer_from_user = self.env['res.users'].search([('employee_id','=',rec.name.id)], limit=1).id

    date = fields.Date(default=fields.Date.today, string="Date")
    name = fields.Many2one('hr.employee')
    state = fields.Selection([('pending','Pending'),('accepted','Accepted')],default='pending')
    amount = fields.Float('Amount')
    user_id = fields.Many2one('hr.employee')
    admin = fields.Many2one('res.users')
    driver_stmt_id = fields.Many2one('driver.daily.statement')
    visibility2 = fields.Boolean(default=False, compute='get_visibility')
    transfer_to_user = fields.Many2one('res.users', compute='compute_to_user', store=True, string='Receiver')
    transfer_from_user = fields.Many2one('res.users', compute='compute_from_user', store=True, string='Sender')


class CashTransfer(models.TransientModel):
    _name = 'cash.transfer'

    rec = fields.Many2one('driver.daily.statement')
    date = fields.Date(default=fields.Date.today, string="Date")
    name = fields.Many2one('hr.employee')
    amount = fields.Float('Amount')
    user_id = fields.Many2one('hr.employee')

    @api.multi
    def transfer_amount(self):
        # records = self.env['cash.confirm.transfer'].search([('date','=',self.date),('name','=',self.name.id)])
        # amount = 0
        # limit_amount = 0
        # if records:
        # 	for line in records:
        # 		amount += line.amount
        # limit = self.env['cash.transfer.limit'].search([('name','=',self.name.id)])
        # if limit:
        # 	limit_amount = limit.cash_limit
        # else:
        # 	raise except_orm(_('Warning'),
        # 					 _('Please Set An Amount Transfer Limit'))
        # if limit_amount < amount or (amount + self.amount) > limit_amount:
        # 	raise except_orm(_('Warning'),
        # 					 _('Amount Exceeds Limit..Please Check'))
        # else:
        self.env['cash.confirm.transfer'].sudo().create({
                                                      'date':self.date,
                                                      'name':self.name.id,
                                                      'amount':self.amount,
                                                      'user_id':self.user_id.id,
                                                      'state':'pending',
                                                      'driver_stmt_id':self.rec.id,
                                                      'admin':1})
                                                    # 'transfer_from_user':self.env['res.users'].search[('employee_id','=',self.name.id)].id,
                                                      # 'transfer_to_user':self.env['res.users'].search[('employee_id','=',self.name.id)].id
        return True



class DieselPump(models.Model):
    _name = 'diesel.pump'

    name = fields.Char('Pump Name', required=True)

class DieselPumpLine(models.Model):
    _name = 'diesel.pump.line'
    _order = 'id desc'




    @api.multi
    def action_confirm(self):
        litre = 0
        for litre_lines in self:
            if litre_lines.vehicle_id:
                litre_lines.vehicle_id.mileage = litre_lines.close_km
            if litre_lines.diesel_mode == 'pump':
                litre += litre_lines.litre
                if litre_lines.vehicle_id.tanker_bool == True:
                    location = litre_lines.vehicle_id.location_id
                else:
                    location = litre_lines.project_id.location_id
                self.env['fuel.report'].sudo().create({
                    'date': litre_lines.date,
                    'diesel_pump': litre_lines.diesel_pump.id,
                    # 'vehicle_owner': litre_lines.vehicle_no.owner.id,
                    'vehicle_no': litre_lines.vehicle_id.id,
                    'item_char': litre_lines.fuel_product_id.name,
                    'qty': litre_lines.litre,
                    'rate': litre_lines.per_litre,
                    'amount': litre_lines.total_litre_amount,
                    'diesel_pump_id': litre_lines.id,
                })
                values = {'Date': litre_lines.date,
                          'supplier_id':litre_lines.diesel_pump.id,
                          'invoice_no':litre_lines.pump_bill_no,
                          'project_id':litre_lines.project_id.id,
                          'project_location_id':location.id,
                        'own_vehicle':True,
                          'without_po':True,
                        'vehicle_id':litre_lines.vehicle_id.id,
                          'goods_recieve_report_line_ids':[(0,0,{'item_id':litre_lines.fuel_product_id.id,
                                                                 'desc':litre_lines.fuel_product_id.name,
                                                                 'unit_id':litre_lines.fuel_product_id.uom_id.id,
                                                                 'po_quantity':litre_lines.litre,
                                                                 'quantity_accept':litre_lines.litre,
                                                                 'rate':litre_lines.per_litre,
                                                                 'remarks':litre_lines.remark})]
                          }
                grr = self.env['goods.recieve.report'].create(values)

                litre_lines.goods_receive_id = grr.id
                date = datetime.strptime(litre_lines.date, "%Y-%m-%d")
                date = date + timedelta(seconds=2)
                if litre_lines.vehicle_id.tanker_bool == False:
                    values = {'date': date,

                          'project_id': litre_lines.project_id.id,
                          'source_location_id': location.id,
                          'is_receive':False,
                          'vehicle_id': litre_lines.vehicle_id.id,
                          'material_issue_slip_lines_ids': [(0, 0, {'item_id': litre_lines.fuel_product_id.id,
                                                                    'desc': litre_lines.fuel_product_id.name,
                                                                    'unit_id': litre_lines.fuel_product_id.uom_id.id,
                                                                    'quantity': litre_lines.litre,
                                                                    'req_qty': litre_lines.litre,
                                                                    'rate': litre_lines.fuel_product_id.standard_price,
                                                                    'remarks': litre_lines.remark})]
                          }
                    material_issue_slip = self.env['material.issue.slip'].create(values)
                    litre_lines.material_issue_slip_id = material_issue_slip.id

            if litre_lines.diesel_mode == 'tanker':
                # date = datetime.strptime(litre_lines.date, "%Y-%m-%d").strftime("%Y-%m-%d")
                # date = date + ' '+ datetime.strptime(litre_lines.create_date, "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
                date = datetime.strptime(litre_lines.date, "%Y-%m-%d").strftime("%Y-%m-%d")
                date_time = datetime.strptime(litre_lines.new_time, "%H:%M:%S").strftime("%H:%M:%S")
                date = date + ' ' + date_time
                from_zone = tz.gettz('UTC')
                to_zone = tz.gettz('Asia/Kolkata')
                # from_zone = tz.tzutc()
                # to_zone = tz.tzlocal()
                utc = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                utc = utc.replace(tzinfo=to_zone)
                central = utc.astimezone(from_zone)

                date = central.strftime("%Y-%m-%d %H:%M:%S")
                if litre_lines.stock_balance < litre_lines.total_diesel:
                    location_id = self.env['stock.location'].search([('usage', '=', 'supplier')],limit=1)
                    qty = litre_lines.total_diesel - litre_lines.stock_balance
                    stock_move = self.env['stock.move'].create({
                        'location_id': location_id.id,
                        'project_id': litre_lines.project_id.id,
                        'product_id': litre_lines.fuel_product_id.id,
                        'available_qty': litre_lines.fuel_product_id.with_context(
                            {'location': location_id.id}).qty_available,
                        'name': litre_lines.fuel_product_id.name,
                        'date': litre_lines.date,
                        'date_expected': litre_lines.date,
                        'product_uom_qty': qty,
                        'product_uom': litre_lines.fuel_product_id.uom_id.id,
                        'price_unit': litre_lines.fuel_product_id.standard_price,
                        'account_id': litre_lines.diesel_tanker.location_id.related_account.id,
                        'location_dest_id': litre_lines.diesel_tanker.location_id.id,

                    })
                    stock_move.action_done()

                litre_lines.diesel_tanker.write({'capacity':litre_lines.closing_reading})
                litre += litre_lines.total_diesel
                values = {'date': date,

                          'project_id': litre_lines.project_id.id,
                          'source_location_id': litre_lines.diesel_tanker.location_id.id,
                          'is_receive':False,
                          'employee_id':litre_lines.receiver_id.id,
                          'vehicle_id': litre_lines.vehicle_id.id,
                          'material_issue_slip_lines_ids': [(0, 0, {'item_id': litre_lines.fuel_product_id.id,
                                                                    'desc': litre_lines.fuel_product_id.name,
                                                                    'unit_id': litre_lines.fuel_product_id.uom_id.id,
                                                                    'quantity': litre_lines.total_diesel,
                                                                    'req_qty': litre_lines.total_diesel,
                                                                    'rate': litre_lines.fuel_product_id.standard_price,
                                                                    'remarks': litre_lines.remark})]
                          }
                material_issue_slip = self.env['material.issue.slip'].create(values)
                litre_lines.material_issue_slip_id = material_issue_slip.id


            litre_lines.state= 'confirm'

    @api.depends('opening_reading', 'closing_reading')
    def compute_total_diesel(self):
        for rec in self:
            rec.total_diesel = rec.closing_reading - rec.opening_reading

    @api.depends('start_km', 'close_km')
    def comute_run_km(self):
        for rec in self:
            rec.running_km = rec.close_km - rec.start_km

    @api.depends('diesel_tanker')
    def compute_diesel_reading(self):
        for rec in self:
            rec.opening_reading = rec.diesel_tanker.capacity

    @api.onchange('diesel_mode')
    def onchnage_diesel_mode(self):
        for rec in self:
            if rec.diesel_mode == 'tanker':
                rec.diesel_pump = False
                rec.litre = 0
            else:
                rec.diesel_tanker = False
                rec.closing_reading = 0

    @api.depends('diesel_tanker', 'new_time')
    def compute_stock_balance(self):
        for rec in self:
            if rec.date:
                # date = datetime.strptime(rec.date, "%Y-%m-%d").strftime("%Y-%m-%d")
                # if not rec.create_date:
                #
                #     new_date = datetime.strptime(rec.new_time,"%H:%M:%S")
                # else:
                #     new_date = datetime.strptime(rec.create_date,"%Y-%m-%d %H:%M:%S")
                # date = date + ' ' + new_date.strftime("%H:%M:%S")
                date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                stock_history = self.env['stock.history'].search(
                    [('location_id', '=', rec.diesel_tanker.location_id.id),
                     ('product_id', '=', rec.fuel_product_id.id), ('date', '<', date)])
                # available = 0
                # for hist in stock_history:
                #
                #     available += hist.quantity
                # rec.stock_balance = available
                rec.stock_balance = sum(stock_history.mapped('quantity'))

    @api.depends('diesel_tanker', 'new_time')
    def compute_new_stock_balance(self):
        for rec in self:
            if rec.date:
            #     date = datetime.strptime(rec.date, "%Y-%m-%d").strftime("%Y-%m-%d")
            #     if rec.new_time:
            #
            #         new_date = datetime.strptime(rec.new_time, "%H:%M:%S")
            #     else:
            #         new_date = datetime.strptime(rec.create_date, "%Y-%m-%d %H:%M:%S")
            #     date = date + ' ' + new_date.strftime("%H:%M:%S")
            #     from_zone = tz.gettz('UTC')
            #     to_zone = tz.gettz('Asia/Kolkata')
            #     # from_zone = tz.tzutc()
            #     # to_zone = tz.tzlocal()
            #     utc = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            #     utc = utc.replace(tzinfo=to_zone)
            #     central = utc.astimezone(from_zone)
            #     date = central.strftime("%Y-%m-%d %H:%M:%S")
                date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                stock_history = self.env['stock.history'].search(
                    [('location_id', '=', rec.diesel_tanker.location_id.id),
                     ('product_id', '=', rec.fuel_product_id.id), ('date', '<', date)])
                # available = 0
                # for hist in stock_history:
                #     available += hist.quantity
                # rec.new_stock_balance = available
                rec.new_stock_balance = sum(stock_history.mapped('quantity'))

    @api.depends('vehicle_id')
    def compute_prereading(self):
        for rec in self:
            rec.start_km = rec.vehicle_id.mileage

    @api.depends('running_km', 'total_diesel','litre')
    def compute_mileage(self):
        for rec in self:
            if rec.running_km > 0:
                if rec.diesel_mode == 'pump':
                    if rec.vehicle_id.machinery != True:
                        rec.mileage = rec.running_km/rec.litre
                    else:
                        rec.mileage = rec.litre/rec.running_km
                if rec.diesel_mode == 'tanker':

                    if rec.vehicle_id.machinery != True:
                        if rec.total_diesel !=0 :
                            rec.mileage = rec.running_km / rec.total_diesel
                    else:
                        rec.mileage = rec.total_diesel/rec.running_km

    @api.onchange('rent_vehicle')
    def onchange_rent_vehicle(self):
        for rec in self:
            rec.own_vehicle = False
            rec.vehicle_id = False

    @api.onchange('own_vehicle')
    def onchange_own_vehicle(self):
        for rec in self:
            rec.rent_vehicle = False
            rec.rent_vehicle_id = False
            rec.rent_vehicle_partner_id = False

    @api.onchange('rent_vehicle_partner_id')
    def onchnage_vehicle_owner_id(self):
        for rec in self:
            vehicle = self.env['fleet.vehicle'].search(['|','|',('rent_vehicle','=',True),('is_rent_mach','=',True),('other','=',True),('vehicle_under','=',rec.rent_vehicle_partner_id.id)])
            domain ={'domain':{'rent_vehicle_id':[('id','in',vehicle.ids)]}}
        return domain

    @api.onchange('cash_purchase')
    def onchange_cash_purchase(self):
        for rec in self:
            rec.diesel_mode='pump'

    own_vehicle = fields.Boolean("Own Vehicle")
    rent_vehicle = fields.Boolean("Rent Vehicle")
    rent_vehicle_partner_id = fields.Many2one('res.partner',"Rent Vehicle Owner",domain="[('is_rent_mach_owner','=',True)]")
    rent_vehicle_id = fields.Many2one('fleet.vehicle',domain="['|','|',('rent_vehicle','=',True),('is_rent_mach','=',True),('other','=',True)]",string="Rent Vehicle No")
    name = fields.Char("Diesel entry Number")
    line_id = fields.Many2one('driver.statement.line')
    line_id2 = fields.Many2one('driver.daily.statement')
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle No",domain="['|','|',('vehicle_ok','=',True),('machinery','=',True),('other','=',True)]")
    date = fields.Date("Date")
    diesel_pump = fields.Many2one('res.partner','Diesel Pump')
    diesel_mode = fields.Selection([
                                    ('pump','Diesel Pump'),
                                    ('tanker','Diesel Tanker')],'Received From')
    diesel_tanker= fields.Many2one('fleet.vehicle','Tanker No.')
    stock_balance = fields.Float("Stock Balance", compute='compute_stock_balance', store=True)
    new_stock_balance = fields.Float("Stock Balance", compute='compute_new_stock_balance',store=True )
    opening_reading = fields.Float('Opening Reading',compute='compute_diesel_reading',store=True)
    closing_reading = fields.Float('Closing Reading')
    total_diesel = fields.Float('Issued Qty' ,compute='compute_total_diesel',store=True)
    diesel_start_reading = fields.Float('Reading at the Time of diesel filling')
    filling_time = fields.Char('Time')
    litre = fields.Float('Received Qty')
    per_litre = fields.Float('Rate Per Litre')
    fuel_product_id = fields.Many2one('product.product',"Fuel Type")
    total_litre_amount = fields.Float('Total Litre Amount', compute='compute_total_diesel_amount',digits=(6,2), store=True)
    # odometer = fields.Float('Odometer Reading')
    is_full_tank = fields.Boolean('Is Full Tank')

    pump_bill_no = fields.Char('Bill No.')
    fuel_item = fields.Many2one('product.product', 'Fuel Item')
    project_id = fields.Many2one('project.project',"Project Name")
    state = fields.Selection([('draft','Draft'),
                              ('confirm','Confirm')],default='draft')
    remark = fields.Char("Remark")

    indent_no = fields.Char("Indent No")
    start_km = fields.Float("Pre Reading",compute='compute_prereading',store=True)
    close_km = fields.Float("Current Reading")
    running_km = fields.Float("Running Km",compute='comute_run_km', digits=(6,2))
    mileage = fields.Float("Mileage", compute='compute_mileage',digits=(6,2))
    goods_receive_id = fields.Many2one('goods.recieve.report',"GRR NO")
    material_issue_slip_id = fields.Many2one('material.issue.slip','MRN NO')
    receiver_id = fields.Many2one('hr.employee',"Receiver")
    cash_purchase = fields.Boolean("Cash Purchase")
    new_time = fields.Char("Filling Time")

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.material_issue_slip_id:
                rec.material_issue_slip_id.action_cancel()
            if rec.goods_receive_id:
                rec.goods_receive_id.action_cancel()
            if rec.vehicle_id:
                rec.vehicle_id.mileage = rec.start_km
            if rec.diesel_tanker:
                rec.diesel_tanker.capacity = rec.opening_reading
        return super(DieselPumpLine, self).unlink()

    @api.model
    def create(self, vals):

        res = super(DieselPumpLine, self).create(vals)
        if res.project_id:
            res.project_id.fuel_no +=1
        # no = str(res.project_id.fuel_no).zfill(3)
        # res.name=str("Fuel/"+no)
        # no = datetime.today().strftime("%Y-%m-%d")+"/"+str(res.id)
        res.name = "Fuel/" + str(res.id)
        res.action_confirm()
        return res


    @api.multi
    def number_change(self):
        # self.search([], order='id asc')
        for rec in self:
            if rec.material_issue_slip_id and rec.filling_time:
                print "ffffffffffffffffffffffffffffffff",rec.filling_time

                date = datetime.strptime(rec.date, "%Y-%m-%d").strftime("%Y-%m-%d")

                new_date = datetime.strptime(rec.create_date, "%Y-%m-%d %H:%M:%S")
                date = date + ' ' + new_date.strftime("%H:%M:%S")
                rec.goods_receive_id.picking_id.date = date
                for line in rec.goods_receive_id.goods_recieve_report_line_ids:
                    line.move_id.date = date
                    line.move_id.date_expected = date
        return True

    @api.multi
    def write(self,vals):
        for rec in self:
            if vals.get('fuel_product_id'):
                if rec.goods_receive_id:
                    for goods in rec.goods_receive_id.goods_recieve_report_line_ids:
                        goods.write({'item_id':vals.get('fuel_product_id')})
                    if rec.material_issue_slip_id:
                        for material in rec.material_issue_slip_id.material_issue_slip_lines_ids:
                            material.write({'item_id': vals.get('fuel_product_id')})
            if vals.get('litre'):
                if rec.goods_receive_id:
                    for goods in rec.goods_receive_id.goods_recieve_report_line_ids:
                        goods.write({'quantity_accept':vals.get('litre'),
                                     'po_quantity':vals.get('litre')})

            if vals.get('total_diesel'):

                if rec.material_issue_slip_id:
                    for material in rec.material_issue_slip_id.material_issue_slip_lines_ids:
                        material.write({'req_qty': vals.get('total_diesel')})

            if vals.get('new_time'):
                date = datetime.strptime(rec.date, "%Y-%m-%d").strftime("%Y-%m-%d")
                date_time = datetime.strptime(vals.get('new_time'), "%H:%M:%S").strftime("%H:%M:%S")
                date = date + ' ' + date_time
                from_zone = tz.gettz('UTC')
                to_zone = tz.gettz('Asia/Kolkata')
                # from_zone = tz.tzutc()
                # to_zone = tz.tzlocal()
                utc = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                utc = utc.replace(tzinfo=to_zone)
                central = utc.astimezone(from_zone)
                print "hhhhhhhhhhhhhhhhhhhhh",central,type(central)
                central = central.strftime("%Y-%m-%d %H:%M:%S")
                # central = datetime.strptime(central.strftime("%d-%m-%Y %H:%M:%S"), '%d-%m-%Y %H:%M:%S').strftime(
                #     "%d-%m-%Y %H:%M:%S")

                if rec.goods_receive_id:
                    rec.goods_receive_id.write({'Date': central})
                    for goods_line in rec.goods_receive_id.goods_recieve_report_line_ids:
                        goods_line.move_id.date = central
                        goods_line.move_id.date_expected = central
                        for quant_line in goods_line.move_id.quant_ids:
                            quant_line.write({'in_date': central})
                            print "huuuuuuuuuuuuuuuuuuuuuuuuu"
                if rec.material_issue_slip_id:
                    rec.material_issue_slip_id.write({'date': central})
            if vals.get('date'):
                date = datetime.strptime(vals.get('date'), "%Y-%m-%d").strftime("%Y-%m-%d")
                date = date + ' ' + datetime.strptime(rec.create_date, "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")

                if rec.goods_receive_id:
                    rec.goods_receive_id.write({'Date': vals.get('date')})
                if rec.material_issue_slip_id:
                    rec.material_issue_slip_id.write({'date': date})

        return super(DieselPumpLine, self).write(vals)

    @api.depends('litre','per_litre')
    def compute_total_diesel_amount(self):
        for rec in self:
            rec.total_litre_amount = rec.litre * rec.per_litre

class DriverDailyStatement(models.Model):
    _name = 'driver.daily.statement'
    _order = 'date desc'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(DriverDailyStatement, self).fields_view_get(
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


    @api.multi
    def get_date(self,date):
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
        return str(date.day)+str('/')+str(date.month)+str('/')+str(date.year)

    @api.model
    def default_get(self, default_fields):
        vals = super(DriverDailyStatement, self).default_get(default_fields)

        vals.update({'user_id' :self.env.user.id,
                            })
        return vals

    @api.onchange('vehicle_no','theoretical_close_km')
    def onchange_vehicle_no(self):
        if self.vehicle_no:
            self.start_km = self.vehicle_no.odometer
            # self.actual_close_km = self.theoretical_close_km

    @api.multi
    @api.depends('start_km','actual_close_km')
    def compute_closing_km(self):
        for rec in self:
            rec.running_km = rec.actual_close_km - rec.start_km

    @api.multi
    @api.depends('start_time','end_time')
    def compute_hrs_worked(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                hrs_worked = datetime.strptime(rec.end_time,"%Y-%m-%d %H:%M:%S") - datetime.strptime(rec.start_time,"%Y-%m-%d %H:%M:%S")

                rec.hrs_worked = str(hrs_worked)

    @api.multi
    @api.depends('driver_name','date')
    def compute_name(self):
        for rec in self:
            if rec.driver_name and rec.date:
                date = datetime.strptime(rec.date, "%Y-%m-%d")
                rec.name = rec.driver_name.name+' '+str(date.day)+ str('-')+str(date.month)+ str('-') + str(date.year)

    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
        'cancelled': [('readonly', True)],
    }

    @api.onchange('rent_vehicle')
    def onchange_rent_vehicle(self):
        for rec in self:
            rec.own_vehicle = False
            rec.vehicle_id = False

    @api.onchange('own_vehicle')
    def onchange_own_vehicle(self):
        for rec in self:
            rec.rent_vehicle = False
            rec.rent_vehicle_id = False
            rec.rent_vehicle_partner_id = False

    @api.onchange('rent_vehicle_partner_id')
    def onchnage_vehicle_owner_id(self):
        for rec in self:
            vehicle = self.env['fleet.vehicle'].search(
                ['|', '|', ('rent_vehicle', '=', True), ('is_rent_mach', '=', True), ('other', '=', True),
                 ('vehicle_under', '=', rec.rent_vehicle_partner_id.id)])
            domain = {'domain': {'rent_vehicle_id': [('id', 'in', vehicle.ids)]}}
        return domain

    name = fields.Char(compute='compute_name', string='Name')
    driver_name = fields.Many2one('hr.employee', 'Name',)
    vehicle_no = fields.Many2one('fleet.vehicle','Daily Statement Of Vehicle No:', states=READONLY_STATES,domain="['|','|',('machinery','=',True),('vehicle_ok','=',True),('other','=',True)]")
    date = fields.Date('Date',default=fields.Date.today, states=READONLY_STATES)
    driver_stmt_line = fields.One2many('driver.daily.statement.line','line_id')
    cleaners_name = fields.Many2one('hr.employee','Cleaner Name')


    project_id = fields.Many2one('project.project',string="Project")

    state = fields.Selection([('draft','draft'),('confirmed','Confirmed'),('cancelled','Cancelled')],default='draft')


    start_km = fields.Float('Starting Km')

    actual_close_km = fields.Float('Closing Km')
    odometer = fields.Float('Meter Reading', states=READONLY_STATES)
    remark = fields.Text('Remarks', states=READONLY_STATES)
    running_km = fields.Float('Running Km',compute="compute_closing_km")

    approved_by = fields.Many2one('hr.employee','Approved By')
    sign = fields.Binary('Sign')
    cleaner_bata = fields.Float('Cleaner Bata')

    reference = fields.Char('Reference No:')
    user_id = fields.Many2one('res.users','User')
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    hrs_worked = fields.Char(string="Hrs Worked",compute='compute_hrs_worked')
    idle_hrs = fields.Float(string="IDLE Hrs")
    bd_hrs = fields.Float(string="B/D Hrs")
    ot_time = fields.Float("Over Time time")
    ot_rate = fields.Float("Over Time Bata")
    ot_amt = fields.Float("Over time Amount",compute='compute_amount')
    deposit = fields.Float("Food Allowance")
    driver_bata = fields.Float("Driver Bata")
    trip_sheet_no = fields.Char("Trip Sheet No")
    own_vehicle = fields.Boolean("Own Vehicle")
    rent_vehicle = fields.Boolean("Rent Vehicle")
    rent_vehicle_partner_id = fields.Many2one('res.partner', "Rent Vehicle Owner",
                                              domain="[('is_rent_mach_owner','=',True)]")
    rent_vehicle_id = fields.Many2one('fleet.vehicle',
                                      domain="['|','|',('rent_vehicle','=',True),('is_rent_mach','=',True),('other','=',True)]",
                                      string="Rent Vehicle No")
    full_day = fields.Boolean("Full Day")
    half_day = fields.Boolean("Half Day")
    rent_driver = fields.Char("Driver Name")
    rent_cleaner = fields.Char("Rent Cleaner")

    @api.constrains('date')
    def _check_date(self):
        for record in self:
            selected_date = fields.Date.from_string(record.date)
            today = fields.Date.from_string(fields.Date.today())

            if selected_date < today:
                raise ValidationError("You cannot select a date in the past. Please verify the date.")

            if selected_date > (today + timedelta(days=3)):
                raise ValidationError("You cannot update the record after three days from the selected date.")

    @api.depends('ot_rate','ot_time')
    def compute_amount(self):
            for rec in self:
                rec.ot_amt = rec.ot_time * rec.ot_rate


    @api.model
    def create(self, vals):
        dom = []
        vehicle = False
        if vals.get('vehicle_no'):
            dom.append(('vehicle_no','=',vals['vehicle_no']))
            vehicle = self.env['fleet.vehicle'].browse(vals['vehicle_no'])
        if vals.get('date'):
            dom.append(('date','=',vals['date']))
        if vals.get('driver_name'):
            dom.append(('driver_name','=',vals['driver_name']))
        if vals.get('rent_vehicle_id'):
            dom.append(('rent_vehicle_id','=',vals['rent_vehicle_id']))
            vehicle = self.env['fleet.vehicle'].browse(vals['rent_vehicle_id'])
        if vals.get('rent_driver'):
            dom.append(('rent_driver', '=', vals['rent_driver']))


        driver_daily = self.env['driver.daily.statement'].search(dom)
        if not vals.get('vehicle_no') and not vals.get('rent_vehicle_id'):
            raise except_orm(_('Warning'),
                             _("Please Enter Vehicle No"))

        if driver_daily:
            raise except_orm(_('Warning'),
                             _('Already created daily statement for vehicle %s on %s'%(vals['vehicle_no'] or vals['rent_vehicle_id'],vals['date'])))
        result = super(DriverDailyStatement, self).create(vals)
        if result.reference == False:
            result.reference = self.env['ir.sequence'].next_by_code('driver.daily.statement') or '/'

        if not self.env.user.has_group("hiworth_hr_attendance.group_labour"):
            date = datetime.now() - timedelta(days=3)
            if datetime.strptime(result['date'],"%Y-%m-%d") < date:
                raise except_orm(_('Warning'),
                             _("You Don't have access to create daily statement for 3 days Back"))
        return result

    @api.multi
    def write(self, vals):
        if vals.get('vehicle_no'):
            self.start_km =self.env['fleet.vehicle'].browse(vals.get('vehicle_no')).odometer
            driver_daily = self.env['driver.daily.statement'].search(
                [('vehicle_no', '=', vals['vehicle_no']), ('date', '=', self.date),('driver_name','=',self.driver_name.id)])
            if len(driver_daily)>1:
                raise except_orm(_('Warning'),
                                 _('Already created daily statement for vehicle %s on %s' % (
                                 vals['vehicle_no'], self.date)))

        return super(DriverDailyStatement, self).write(vals)


    @api.multi
    def approve_entry(self):

        self.state = 'approved'

        self.approved_by = self.env.user.employee_id.id
        self.sign = self.env.user.employee_id.sign


    @api.multi
    def validate_entry(self):
        if self.start_km != 0 or self.actual_close_km != 0:
            if self.own_vehicle:
                if (float(self.actual_close_km) - float(self.start_km)) != 0:
                    self.env['vehicle.meter'].create({'date': self.date,
                                                      'vehicle_id': self.vehicle_no.id,
                                                      'start_value': self.start_km,
                                                      'end_value': self.actual_close_km,
                                                      })
                self.vehicle_no.odometer=self.actual_close_km
            if self.rent_vehicle_id:
                self.rent_vehicle_id.odometer = self.actual_close_km
        self.state = 'confirmed'

    @api.multi
    def set_draft(self):
        self.state = 'draft'

    @api.multi
    def cancel_entry(self):

        self.state = 'cancelled'


class DriverDailyStatementLine(models.Model):
    _name = 'driver.daily.statement.line'

    @api.onchange('qty')
    def onchange_qty_rate(self):
        if self.qty == 0:
            self.total = 0
        else:
            if self.total != 0 and self.rate != 0 and self.qty != round((self.total / self.rate),2):
                self.qty = 0.0
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': "For Entering value to Qty field, Rate or Total should be Zero"
                        }
                    }
            if self.qty != 0 and self.rate != 0:
                if self.rate*self.qty != self.total:
                    pass
                if self.total == 0.0:
                    self.total = round((self.qty * self.rate),2)
            if self.total != 0 and self.qty != 0:
                if self.rate == 0.0:
                    self.rate = round((self.total / self.qty),2)


    @api.onchange('rate')
    def onchange_rate_total(self):
        if self.rate == 0:
            self.total = 0
        else:
            if self.total != 0 and self.qty != 0 and self.rate != round((self.total / self.qty),2):
                self.rate = 0.0
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': "For Entering value to Rate field, Qty or Total should be Zero."
                        }
                    }
            if self.qty != 0 and self.rate != 0:
                if self.rate*self.qty != self.total:
                    pass
                if self.total == 0.0:
                    self.total = round((self.qty * self.rate),2)
            if self.total != 0 and self.rate != 0:
                if self.qty == 0.0:
                    self.qty = round((self.total / self.rate),2)

    @api.onchange('total')
    def onchange_qty_total(self):
        if self.total != 0:
            if self.rate*self.qty != self.total:
                if self.rate != 0 and self.qty != 0:
                    self.total = self.rate*self.qty
                    # self.total = 0.0
                    # return {
                    # 	'warning': {
                    # 		'title': 'Warning',
                    # 		'message': "For Entering value to Total field, Qty or Rate should be Zero."
                    # 		}
                    # 	}
                elif self.rate == 0 and self.qty != 0:
                    self.rate = round((self.total / self.qty),2)
                elif self.qty == 0 and self.rate != 0:
                    self.qty = round((self.total / self.rate),2)
                else:
                    pass


    @api.onchange('start_km','end_km')
    def _onchange_end_km(self):
        if self.end_km and self.start_km:
            self.rent = (self.end_km - self.start_km) * self.line_id.vehicle_no.rate_per_km

        if self.end_km and self.start_km and self.end_km <= self.start_km:
            self.end_km = 0

            return {
            'warning': {
                'title': 'Warning',
                'message': "End KM Should be greater than starting KM."
                }
            }
    @api.multi
    @api.depends('start_km','end_km')
    def compute_total(self):
        for rec in self:
            rec.total_km = rec.end_km-rec.start_km

    @api.onchange('rent')
    def onchange_total_km(self):
        if self.total_km:
            self.driver_betha = self.rent*self.env['fleet.vehicle'].sudo().browse(self.env.context.get('vehicle_no')).trip_commission/100

    @api.onchange('driver_betha')
    def onchange_driver_betha(self):
        if self.driver_betha < self.rent*self.env['fleet.vehicle'].sudo().browse(self.env.context.get('vehicle_no')).trip_commission/100:
            self.driver_betha = self.rent*self.env['fleet.vehicle'].sudo().browse(self.env.context.get('vehicle_no')).trip_commission/100
            return {
            'warning': {
                'title': 'Warning',
                'message': "Driver Betha cannot be less than the minimum value."
                }
            }


    invoice_date = fields.Date("Date")
    line_id = fields.Many2one('driver.daily.statement', delegate=True)
    # stmt_id = fields.Many2one('driver.daily.statement')
    particulars = fields.Char('Particulars')
    from_id2 = fields.Many2one('res.partner','From')
    location_id = fields.Many2one('stock.location','From Location', domain=[('usage','=','internal')])
    to_id2 = fields.Many2one('stock.location','To', domain=[('usage','=','internal')])
    project_id = fields.Many2one('project.project',"Project")

    item_expense2 = fields.Many2one('product.product','Item')
    qty = fields.Float('Qty')
    rate = fields.Float(string = 'Rate',store=True)
    total = fields.Float(string = 'Total')

    payment = fields.Float('Payment')
    voucher_no = fields.Char('Voucher No')
    tax_ids = fields.Many2many('account.tax',string="Tax")
    # trip = fields.Float('Trip/Km')

    remarks  = fields.Char('Remarks')
    start_km = fields.Float('Start KM')
    end_km = fields.Float('End KM')
    driver_betha = fields.Float('Driver Amount')


    total_km = fields.Float(compute='compute_total', store=True, string='Total Km')
    rejection_remarks  = fields.Text('Reason for Rejection')

    employee_id = fields.Many2one('hr.employee', 'Employee')
    date = fields.Date(related="line_id.date")
    bata_cleaner = fields.Float('Cleaner Bata')
    bata_driver = fields.Float('Driver Bata')
    km_deposit = fields.Float('Deposit/Km')

#
# class Fleetvehicle(models.Model):
#     _inherit = 'fleet.vehicle'
#
#     tanker_stock_balance = fields.Float(string="Stock Balance")
