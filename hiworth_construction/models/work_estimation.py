from openerp import fields, models, api


class WorkType(models.Model):
    _name = 'work.type'

    name = fields.Char('Name')

class WorkEstimation(models.Model):
    _name = 'work.estimation'

    @api.depends('category_id')
    def compute_estimation_qty(self):
        for rec in self:
            master_data = self.env['project.task'].search([('project_id','=',rec.project_id.id),
                                                           ])
            for master in master_data:
               for task in master.task_line:
                   if task.category.id == rec.category_id.id:
                       rec.qty_estimate = task.qty
                       rec.rate   = task.rate

    # @api.depends('estimation_line_ids')
    # def compute_qty(self):
    #     for rec in self:
    #         total = 0
    #         for esti in rec.estimation_line_ids:
    #             total += esti.qty

    @api.depends('rate','qty')
    def compute_amount(self):
        for rec in self:
            rec.amount = rec.rate * rec.quantity

    @api.onchange('project_id')
    def onchange_project_id(self):
        for rec in self:
            item = []
            cate = []
            for line in rec.project_id.task_ids:
                for task_line in line.task_line:
                    item.append(task_line.name.id)
                    cate.append(task_line.category.id)
        return {'domain':{'work_id':[('id','in',item)],
                          'category_id':[('id','in',cate)]}}


    # @api.onchange('work_id')
    # def onchange_work_id(self):
    #     for rec in self:
    #         if rec.work_id:
    #             for line in rec.project_id.task_ids:
    #                 for task_line in line.task_line:
    #                     if rec.work_id == task_line.name:

    #                         rec.category_id = task_line.category.id

    @api.one
    def compute_category_id(self):
        for rec in self:
            if rec.category_id:

                for line in rec.project_id.task_ids:
                    for task_line in line.task_line:
                        if rec.category_id == task_line.category:

                            rec.work_id = task_line.name.id
                            rec.qty_estimate = task_line.qty
                            rec.rate = task_line.rate


    @api.onchange('estimation_line_ids')
    def compute_quantity(self):
        for rec in self:
            total = 0
            for line in rec.estimation_line_ids:
                total += line.qty
            rec.quantity = total
            if rec.quantity !=0 and rec.qty_estimate !=0:
                rec.perce_com = (rec.quantity/rec.qty_estimate)*100



    project_id = fields.Many2one('project.project',"Project")
    company_id = fields.Many2one('res.company',"Company")
    work_id = fields.Many2one('item.of.work',"Item of Work",compute='compute_category_id')
    category_id = fields.Many2one('task.category','Category')
    date_start = fields.Date("Start Date")

    completion_date = fields.Date("Completion Date")

    employee_id = fields.Many2one('hr.employee',"Employee")
    unit_id = fields.Many2one('product.uom',"Unit")
    qty_estimate = fields.Float('Estimate Quantity',compute='compute_category_id')
    estimation_line_ids = fields.One2many('work.estimation.line','line_id',"Lines")
    qty = fields.Float("Estimate Quantity")
    rate = fields.Float("Rate",compute='compute_category_id')
    quantity = fields.Float("Quantity",compute='compute_quantity')
    amount = fields.Float("Estimate Cost",compute='compute_amount')
    perce_com = fields.Float("% of Comleteion",compute='compute_amount')

class WorkEstimationLine(models.Model):
    _name = 'work.estimation.line'

    @api.one
    @api.depends('nos_x', 'length', 'breadth', 'depth')
    def _get_qty(self):
        nos_x = self.nos_x != 0 and self.nos_x or 1

        length = self.length != 0 and self.length or 1
        aw = self.breadth != 0 and self.breadth or 1
        ad = self.depth != 0 and self.depth or 1
        self.qty = nos_x * length * aw * ad


    date = fields.Date("Date")
    line_id = fields.Many2one('work.estimation', string="Work Estimation")
    name = fields.Char(string="Description")
    side = fields.Selection([('r', 'RHS'), ('l', 'LHS'), ('bs', 'BS')], string="Side")
    unit_id = fields.Many2one('product.uom',"Unit")
    chain_from = fields.Char('Chainage From')
    chain_to = fields.Char('Chainage To')
    nos_x = fields.Integer(string="Nos")

    length = fields.Float(string="Length")

    breadth = fields.Float(string="Breadth")

    depth = fields.Float(string="Depth")
    qty = fields.Float(string="Quantity", compute='_get_qty')



