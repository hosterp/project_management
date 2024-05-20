from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
from datetime import datetime,timedelta
import datetime
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp import SUPERUSER_ID
from lxml import etree


class Number2Words(object):


		def __init__(self):
			'''Initialise the class with useful data'''

			self.wordsDict = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven',
							  8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve', 13: 'thirteen',
							  14: 'fourteen', 15: 'fifteen', 16: 'sixteen', 17: 'seventeen',
							  18: 'eighteen', 19: 'nineteen', 20: 'twenty', 30: 'thirty', 40: 'forty',
							  50: 'fifty', 60: 'sixty', 70: 'seventy', 80: 'eighty', 90: 'ninty' }

			self.powerNameList = ['thousand', 'lac', 'crore']


		def convertNumberToWords(self, number):

			# Check if there is decimal in the number. If Yes process them as paisa part.
			formString = str(number)
			if formString.find('.') != -1:
				withoutDecimal, decimalPart = formString.split('.')

				paisaPart =  str(round(float(formString), 2)).split('.')[1]
				inPaisa = self._formulateDoubleDigitWords(paisaPart)

				formString, formNumber = str(withoutDecimal), int(withoutDecimal)
			else:
				# Process the number part without decimal separately
				formNumber = int(number)
				inPaisa = None

			if not formNumber:
				return 'zero'

			self._validateNumber(formString, formNumber)

			inRupees = self._convertNumberToWords(formString)

			if inPaisa:
				return '%s and %s paisa' % (inRupees.title(), inPaisa.title())
			else:
				return '%s' % inRupees.title()


		def _validateNumber(self, formString, formNumber):

			assert formString.isdigit()

			# Developed to provide words upto 999999999
			if formNumber > 999999999 or formNumber < 0:
				raise AssertionError('Out Of range')


		def _convertNumberToWords(self, formString):

			MSBs, hundredthPlace, teens = self._getGroupOfNumbers(formString)

			wordsList = self._convertGroupsToWords(MSBs, hundredthPlace, teens)

			return ' '.join(wordsList)


		def _getGroupOfNumbers(self, formString):

			hundredthPlace, teens = formString[-3:-2], formString[-2:]

			msbUnformattedList = list(formString[:-3])

			#---------------------------------------------------------------------#

			MSBs = []
			tempstr = ''
			for num in msbUnformattedList[::-1]:
				tempstr = '%s%s' % (num, tempstr)
				if len(tempstr) == 2:
					MSBs.insert(0, tempstr)
					tempstr = ''
			if tempstr:
				MSBs.insert(0, tempstr)

			#---------------------------------------------------------------------#

			return MSBs, hundredthPlace, teens


		def _convertGroupsToWords(self, MSBs, hundredthPlace, teens):

			wordList = []

			#---------------------------------------------------------------------#
			if teens:
				teens = int(teens)
				tensUnitsInWords = self._formulateDoubleDigitWords(teens)
				if tensUnitsInWords:
					wordList.insert(0, tensUnitsInWords)

			#---------------------------------------------------------------------#
			if hundredthPlace:
				hundredthPlace = int(hundredthPlace)
				if not hundredthPlace:
					# Might be zero. Ignore.
					pass
				else:
					hundredsInWords = '%s hundred' % self.wordsDict[hundredthPlace]
					wordList.insert(0, hundredsInWords)

			#---------------------------------------------------------------------#
			if MSBs:
				MSBs.reverse()

				for idx, item in enumerate(MSBs):
					inWords = self._formulateDoubleDigitWords(int(item))
					if inWords:
						inWordsWithDenomination = '%s %s' % (inWords, self.powerNameList[idx])
						wordList.insert(0, inWordsWithDenomination)

			#---------------------------------------------------------------------#
			return wordList


		def _formulateDoubleDigitWords(self, doubleDigit):

			if not int(doubleDigit):
				# Might be zero. Ignore.
				return None
			elif self.wordsDict.has_key(int(doubleDigit)):
				# Global dict has the key for this number
				tensInWords = self.wordsDict[int(doubleDigit)]
				return tensInWords
			else:
				doubleDigitStr = str(doubleDigit)
				tens, units = int(doubleDigitStr[0])*10, int(doubleDigitStr[1])
				tensUnitsInWords = '%s %s' % (self.wordsDict[tens], self.wordsDict[units])
				return tensUnitsInWords

class ResCompany(models.Model):
	_inherit = 'res.company'

	write_off_account_id = fields.Many2one('account.account', 'Default Write off Account')
	discount_account_id = fields.Many2one('account.account', 'Default Discount Account')
	gst_account_id = fields.Many2one('account.account', 'Default GST Account')

class mrp_bom_line(models.Model):
	_inherit = 'mrp.bom.line'

	@api.multi
	@api.depends('product_id','product_qty')
	def _compute_total_cost(self):
		for line in self:
			line.total_cost=line.product_id.standard_price*line.product_qty

	total_cost = fields.Float(compute='_compute_total_cost', store=True, string='Total Cost')


class mrp_bom(models.Model):
	_inherit = 'mrp.bom'

	@api.multi
	@api.depends('bom_line_ids')
	def _compute_bom_cost(self):

		for line in self:
			for bom_lines in line.bom_line_ids:
				line.bom_cost += bom_lines.product_id.standard_price*bom_lines.product_qty

	bom_cost = fields.Float(compute='_compute_bom_cost', store=True, string='BOM Cost')

	def create(self, cr, uid, vals, context=None):
			product_obj=self.pool.get('product.template').browse( cr, uid, [(vals['product_tmpl_id'])])
			bom_cost = 0.0
			for line in vals['bom_line_ids']:
				product_obj2=self.pool.get('product.product').browse( cr, uid, [(line[2]['product_id'])])
				bom_cost += product_obj2.standard_price*line[2]['product_qty']
			product_obj.write({'standard_price':bom_cost,'list_price':bom_cost})
			result = super(mrp_bom, self).create(cr, uid, vals, context=context)
			return result

class mrp_production(models.Model):
	_inherit = 'mrp.production'

	@api.multi
	@api.depends('bom_id')
	def _compute_estimated_cost(self):
		for line in self:
			for lines in line.bom_id:
				line.estimated_cost=lines.bom_cost

	estimated_cost = fields.Float(compute='_compute_estimated_cost', store=True, string='Estimated Cost')
	real_cost = fields.Float('Actual Host')

class task_category(models.Model):
	_name = 'task.category'

	@api.multi
	def name_get(self):
		def get_names(cat):
			""" Return the list [cat.name, cat.parent_id.name, ...] """
			res = []
			while cat:
				res.append(cat.name)
				cat = cat.parent_id
			return res

		return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if not context:
			context = {}
		if name:
			# Be sure name_search is symetric to name_get
			categories = name.split(' / ')
			parents = list(categories)
			child = parents.pop()
			domain = [('name', operator, child)]
			if parents:
				names_ids = self.name_search(cr, uid, ' / '.join(parents), args=args, operator='ilike', context=context, limit=limit)
				category_ids = [name_id[0] for name_id in names_ids]
				if operator in expression.NEGATIVE_TERM_OPERATORS:
					category_ids = self.search(cr, uid, [('id', 'not in', category_ids)])
					domain = expression.OR([[('parent_id', 'in', category_ids)], domain])
				else:
					domain = expression.AND([[('parent_id', 'in', category_ids)], domain])
				for i in range(1, len(categories)):
					domain = [[('name', operator, ' / '.join(categories[-1 - i:]))], domain]
					if operator in expression.NEGATIVE_TERM_OPERATORS:
						domain = expression.AND(domain)
					else:
						domain = expression.OR(domain)
			ids = self.search(cr, uid, expression.AND([domain, args]), limit=limit, context=context)
		else:
			ids = self.search(cr, uid, args, limit=limit, context=context)
		return self.name_get(cr, uid, ids, context)

	def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
		res = self.name_get(cr, uid, ids, context=context)
		return dict(res)

	name = fields.Char('name')
	seq = fields.Integer('sequence')
	task_ids = fields.One2many('project.task', 'categ_id')
	parent_id = fields.Many2one('task.category','Parent Category', select=True, ondelete='cascade')
	child_id = fields.One2many('task.category', 'parent_id', string='Child Categories')

class task(models.Model):
	_inherit = "project.task"

	@api.multi
	@api.depends('estimate_ids')
	def _compute_estimated_cost(self):
		for line in self:
			if line.estimate_ids:
				line.estimated_cost = 0.0
				for lines in line.estimate_ids:
					line.estimated_cost+=lines.estimated_cost_sum
			if line.task_line:
				cost = 0.0
				for val in line.task_line:
					cost += val.amt
				line.estimated_cost = cost
			 #   temp += lines.estimated_cost_sum
#         for temp in self:
#             pro_id = temp.project_id.id
#         pro_obj = self.env['project.project'].browse(pro_id)
#         pro_obj.write({'estimated_cost' : pro_obj.estimated_cost +temp.estimated_cost })

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1
		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			line_num = 1
			for line_rec in first_line_rec.project_id.task_ids:
				line_rec.line_no = line_num
				line_num += 1
			line_num = 1
			for line_rec in first_line_rec.project_id.extra_task_ids:
				line_rec.line_no = line_num
				line_num += 1
			line_num = 1
			for line_rec in first_line_rec.project_id.temp_tasks:
				line_rec.line_no = line_num
				line_num += 1

	line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
	estimated_cost = fields.Float(compute='_compute_estimated_cost', string='Estimated Cost')
	estimate_ids = fields.One2many('project.task.estimation', 'task_id', 'Estimation')
	manpower_usage_ids = fields.One2many('manpower.usage', 'usage_id', string='Manpower Usage')
	is_extra_work = fields.Boolean('Extra Work', default=False)
	is_work_estimation = fields.Boolean('Is Work Estimation', default=False)

	extra_id = fields.Many2one('project.project')
	partner_id = fields.Many2one(related='project_id.partner_id', string='Customer')
	usage_ids1 = fields.One2many('project.task.estimation','task_ids1',string='Items usage')
	state = fields.Selection([
			('draft', 'Draft'),
			('approved', 'Approved'),
			('inprogress', 'In Progress'),
			('completed', 'Completed')
		], default='draft')
	sub_categ_id = fields.Many2one('task.category', 'Sub Category')
	categ_id = fields.Many2one('task.category', 'Category')
	civil_contractor = fields.Many2one('res.partner', 'Civil Contractor', domain = [('contractor','=',True)])
	labour_report_ids = fields.One2many('project.labour.report', 'task_id')
	task_id2 = fields.Many2one('project.project', 'Project')
	task_line = fields.One2many('project.task.line','task_id')
	detailed_ids = fields.One2many("detailed.estimation.line", 'task_id', store=True)
	#
	#
	# resource_ids = fields.One2many('resource.details', 'task_id', store=True)
	# consumption_ids = fields.One2many('consumption.control', 'task_id', store=True)
	#
	# material_ids = fields.One2many('material.estimation', 'task_id', string="Material")
	# manpower_ids = fields.One2many('manpower.estimation', 'task_id', string='Manpower')


	@api.one
	def button_template(self):
		self.is_template = True

	@api.onchange('template_id')
	def onchange_template_id(self):
		if self.template_id:
			for val in self.template_id:
				l1 = []
				for est in val.task_line:
					l2 = []
					for detail in est.detailed_ids:
						l2.append((0, 0, {
											'name':detail.name,
											'nos_x':detail.nos_x,
											'length':detail.length,
											'breadth':detail.breadth,
											'depth':detail.depth
										}))
					# print '=======================l2=======================>',l2
					l3 = []
					for resource in est.resource_ids:
						l3.append((0, 0, {
											'resource_id':resource.resource_id.id,
											'qty':resource.qty,
										}))
					# print '===============================l3===========================>',l3
					l4 = []
					for cons in est.consumption_ids:
						l4.append((0, 0, {
											'resource_id':cons.resource_id.id,
											'estimated_qty':cons.estimated_qty,
											'uom_id':cons.uom_id.id,
										}))
					# print '===============================l4===========================>',l4
					l1.append((0, 0, {
										'name':est.name.id,
										'category':est.category.id,
										'unit':est.unit.id,
										'note':est.note,
										'detailed_ids':l2,
										'resource_ids':l3,
										'consumption_ids':l4,
									}))
				# print '==========================l1===========================>',l1
				self.name = val.name
				self.sub_categ_id = val.sub_categ_id.id or False
				self.categ_id = val.categ_id.id or False
				self.project_id = val.project_id.id or False
				self.civil_contractor = val.civil_contractor.id or False
				self.task_line = l1
				# print '==========================task_line===========================>',self.task_line


	@api.multi
	def task_approve(self):
		self.ensure_one()
		self.state = 'approved'

	@api.multi
	def start_task(self):
		self.ensure_one()
		self.state = 'inprogress'

	@api.multi
	def complete_task(self):
		self.ensure_one()
		self.state = 'completed'

	@api.multi
	def reset_task(self):
		self.ensure_one()
		self.state = 'draft'


class item_of_work(models.Model):
	_name = "item.of.work"

	name = fields.Char(string="Item of Work")

class ProjectTaskLine(models.Model):
	_name = "project.task.line"

	@api.multi
	@api.depends('detailed_ids')
	def _get_total_qty(self):
		for value in self:
			qty = 0.0
			for val in value.detailed_ids:
				qty += val.qty

			value.qty = qty


	@api.multi
	@api.depends('project_id','name')
	def _get_rate(self):
		for val in self:
			if val.name and val.project_id:
				data = self.env['main.data'].search([('name','=',val.name.id),('project_id','=',val.project_id.id)])
				if data:
					rate = 0.0
					for value in data:
						rate += value.amt
					val.rate = rate


	@api.one
	@api.depends('qty','rate')
	def _get_amt(self):
		if self.rate or self.qty:
			self.amt = self.rate * self.qty


	@api.onchange("name")
	def onchange_name(self):
		if self.name and self.task_id.project_id:
			self.resource_ids.unlink()
			self.consumption_ids.unlink()
			items = self.env['main.data'].search([('project_id','=',self.task_id.project_id.id),('name','=',self.name.id)])
			vals = []
			temp = []
			for item in items:
				for data in item.data_ids:
					vals.append((0, 0,{
								'task_line_id':self.id,
								'resource_id':data.item_id.id,
								'qty':data.qty,
							}))
					temp.append((0,0,{
								'consumption_id':self.id,
								'resource_id':data.item_id.id,
								'qty':data.qty,
								'uom_id':data.item_id.unit.id,
							}))

				ids = []
				for val in vals:
					ids.append(val[2]['resource_id'])

				for subdata in item.sub_ids:
					for sub in subdata.subdata_ids:
						if sub.item_id.id not in ids:
							vals.append((0, 0,{
									'task_line_id':self.id,
									'resource_id':sub.item_id.id,
									'qty':sub.qty,
									}))
							temp.append((0,0,{
								'consumption_id':self.id,
								'resource_id':sub.item_id.id,
								'qty':sub.qty,
								'uom_id':sub.item_id.unit.id,
							}))

			self.resource_ids = vals
			self.consumption_ids = temp


	task_id= fields.Many2one('project.task', string="Task")

	stmt_line = fields.Many2one('partner.daily.statement')
	name = fields.Many2one('item.of.work', string="Item of Work")
	category = fields.Many2one('task.category', string="Category")
	qty = fields.Float(string="Quantity", compute='_get_total_qty',digits=(6,5))
	unit = fields.Many2one('product.uom', string="Unit")
	rate = fields.Float(string="Rate")
	amt = fields.Float(string="Amount", compute='_get_amt')
	note = fields.Text(string="Description")

	project_id = fields.Many2one(related='task_id.project_id', string='Project')
	detailed_ids = fields.One2many("detailed.estimation.line", 'line_id', store=True)
	task_line_id = fields.Many2one('partner.daily.statement')

	resource_ids = fields.One2many('resource.details','task_line_id', store=True)
	consumption_ids = fields.One2many('consumption.control','consumption_id', store=True)

	material_ids = fields.One2many('material.estimation','material_id', string="Material")
	manpower_ids = fields.One2many('manpower.estimation', 'manpower_id', string='Manpower')
	costing_project_ids = fields.One2many('costing.project','project_task_line_id',"Costing Project")
	major_item = fields.Boolean("Major Item")


class ManpowerEstimation(models.Model):
	_name = "manpower.estimation"

	@api.multi
	@api.depends('qty','wage')
	def _compute_total(self):
		for line in self:
			line.total = line.qty * line.wage

	@api.multi
	@api.depends('manpower_id.task_id')
	def _compute_val(self):
		for line in self:
			for val in line.manpower_id:
				if val.task_id:
					line.estimate_id = val.task_id.id

	@api.multi
	@api.onchange('category_id')
	def onchange_category_id(self):
		for val in self:
			if val.category_id:
				val.wage = val.category_id.wage

	manpower_id = fields.Many2one('project.task.line')

	estimate_id = fields.Many2one('project.task', string="Estimation", compute='_compute_val')
	work_id = fields.Many2one(related='manpower_id.name', string='Item of Work')
	category_id = fields.Many2one('labour.category', string="Category")
	qty = fields.Float(string="Qty")
	wage = fields.Float(string='Wage')
	total = fields.Float(string="Total", compute='_compute_total')

	total_qty = fields.Float(string="Total Qty")
	account_id = fields.Many2one('account.account', string='Manpower')
	remarks = fields.Text(string="Remarks")
	task_id = fields.Many2one('project.task')

class MaterialEstimation(models.Model):
	_name = "material.estimation"


	@api.multi
	@api.depends('material_id.task_id')
	def _compute_val(self):
		for line in self:
			for val in line.material_id:
				if val.task_id:
					line.estimate_id = val.task_id.id

	material_id = fields.Many2one('project.task.line')

	estimate_id = fields.Many2one('project.task',string="Estimation", compute='_compute_val')
	work_id = fields.Many2one(related='material_id.name', string='Item of Work')

	item_id = fields.Many2one('product.product',string='Items')
	qty = fields.Float(string="Qty")
	rate = fields.Float(string="Rate")
	task_id = fields.Many2one('project.task')


class ManpowerUsage(models.Model):
	_name = "manpower.usage"

	usage_id = fields.Many2one('project.task')

	account_id = fields.Many2one('account.account', string='Manpower')
	estimated_qty = fields.Float(string="Estimated Qty")
	assigned_qty = fields.Float(string="Assigned Qty")

	@api.multi
	@api.onchange('account_id')
	def onchange_account_id(self):
		manpower = []
		for value in self.usage_id.manpower_ids:
			manpower.append(value.account_id.id)
		return {'domain':{'account_id':[('id','in',manpower)]}}

class project_labour_report(models.Model):
	_name = 'project.labour.report'
	_order = "date asc"

	@api.multi
	@api.depends('labour_detail_ids')
	def _compute_amount(self):
		for line in self:
			line.amount = 0.0
			for lines in line.labour_detail_ids:
				line.amount+=lines.amount

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1
		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			for line_rec in first_line_rec.project_id.labour_report_ids:
				line_rec.line_no = line_num
				line_num += 1

	line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
	name = fields.Text('Description')
	date = fields.Date('Date')
	amount = fields.Float(compute='_compute_amount', string='Amount')
	labour_detail_ids = fields.One2many('labour.details', 'detail_ids')
	task_id = fields.Many2one('project.task', 'Task')
	project_id = fields.Many2one('project.project', 'Project')

	_defaults = {
		'date': fields.Date.today(),
		}

class labour_details(models.Model):
	_name = 'labour.details'

	@api.multi
	@api.depends('product_id','rate','qty')
	def _compute_amount(self):
		for line in self:
			line.amount = line.rate * line.qty

	detail_ids = fields.Many2one('project.labour.report', 'Report')
	product_id = fields.Many2one('product.product', 'Product')
	rate = fields.Float(related='product_id.standard_price', string='Rate')
	qty = fields.Float('Nos')
	amount = fields.Float(compute='_compute_amount', string='Amount')

class category_items_estimation(models.Model):
	_name = 'category.items.estimation'

	@api.multi
	@api.depends('product_id','unit_price','qty')
	def _compute_amount(self):
		for line in self:
			line.amount = line.unit_price * line.qty

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1
		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			for line_rec in first_line_rec.project_id.categ_estimation_ids:
				line_rec.line_no = line_num
				line_num += 1

	line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
	name = fields.Char('Name')
	product_id = fields.Many2one('product.product', 'Product')
	unit_price = fields.Float(related='product_id.standard_price', string="Unit Price")
	uom = fields.Many2one(related='product_id.uom_id', string="Uom")
	qty = fields.Float('Qty')
	amount = fields.Float(compute='_compute_amount', string='Amount')
	project_id = fields.Many2one('project.project', 'Project')


class BillDetails(models.Model):
	_name = 'bill.details'

	project_id = fields.Many2one('project.project',"Project")
	name = fields.Char("Bill No")
	amt = fields.Float("Bill Amount")
	remarks = fields.Char("Remarks")
class VehicleCategoryCost(models.Model):
	_name = 'vehicle.category.cost'

	@api.depends('qty','rate')
	def compute_amt(self):
		for rec in self:
			rec.amount = rec.rate * rec.qty

	vehicle_type_id = fields.Many2one('vehicle.category.type',"Vehicle Category")
	unit_id = fields.Many2one('product.uom',"Unit")
	rate = fields.Float("Rate")
	qty = fields.Float("Quantity")
	amount = fields.Float("Amount",compute='compute_amt',store=True)
	costing_project_id = fields.Many2one('costing.project')

class LabourCostProject(models.Model):
	_name = 'labour.cost.project'

	@api.depends('qty', 'rate')
	def compute_amt(self):
		for rec in self:
			rec.amount = rec.rate * rec.qty

	category = fields.Selection(
		[('skilled', 'Skilled'), ('unskilled', 'Unskilled'), ('survey', "Survey"), ('union', "Union")], "Category")
	costing_project_id = fields.Many2one('costing.project')
	rate = fields.Float("Rate")
	qty = fields.Float("Quantity")
	amount = fields.Float("Amount", compute='compute_amt', store=True)

class MaterialCost(models.Model):
	_name = 'material.cost'

	@api.depends('qty','rate')
	def compute_amt(self):
		for rec in self:
			rec.amount = rec.rate * rec.qty

	@api.onchange('product_id')
	def onchange_product_id(self):
		for rec in self:
			rec.unit_id = rec.product_id.uom_id.id
			rec.rate = rec.product_id.standard_price

	product_id = fields.Many2one('product.product',"Product")
	unit_id = fields.Many2one('product.uom',"Unit")
	rate = fields.Float("Rate")
	qty = fields.Float("Quantity")
	amount = fields.Float("Amount",compute='compute_amt',store=True)
	costing_project_id = fields.Many2one('costing.project')

class CostingProject(models.Model):
	_name = 'costing.project'

	vehicle_category_cost_ids = fields.One2many('vehicle.category.cost','costing_project_id',"Equipment Cost")
	material_cost_ids = fields.One2many('material.cost', 'costing_project_id',"Material Cost")
	labour_cost_project_ids = fields.One2many('labour.cost.project','costing_project_id',"Labour Cost")
	project_task_line_id = fields.Many2one('project.task.line')

class GeneralExpenseProject(models.Model):
	_name = 'genral.expense.project'

	project_id = fields.Many2one('project.project')
	item = fields.Selection([('rent', "Rent"),
							 ('bank_guarantee', "Bank Guarantee Charges"),
							 ('survey', "Survey Expenses"),
							 ('general', "General Expenses")], "Category")
	rate = fields.Float("Rate")

class project(models.Model):
	_inherit = "project.project"

	@api.multi
	def set_open_project(self):
		self.state = 'open'

	@api.multi
	@api.depends('task_ids')
	def _compute_estimated_cost(self):
		for line in self:
			for lines in line.task_ids:
				line.estimated_cost+=lines.estimated_cost

	@api.multi
	@api.depends('extra_task_ids')
	def _compute_estimated_cost_extra(self):
		for line in self:
			for lines in line.extra_task_ids:
				line.estimated_cost_extra+=lines.estimated_cost

	@api.multi
	@api.depends('estimated_cost','estimated_cost_extra')
	def _compute_estimated_cost_total(self):
		for line in self:
			line.total_estimated_cost = line.estimated_cost + line.estimated_cost_extra

	@api.onchange('schedule_id')
	@api.multi
	def _compute_stage_total(self):
		if (not self.schedule_id):
			return
		amount = 0.0
		for line in self.schedule_id:
			amount+= line.amount
		line['stage_total'] =  amount

	@api.multi
	@api.onchange('categ_id')
	def onchange_task_ids(self):
		return {
			'domain': {
				'task_ids':[('categ_id','=', self.categ_id.id)]
			}
		}

	@api.one
	@api.depends('start_date','date_end')
	def _compute_duration(self):
		if self.start_date and self.date_end:
			fmt = '%Y-%m-%d'
			d1 = datetime.datetime.strptime(self.start_date, fmt)
			d2 = datetime.datetime.strptime(self.date_end, fmt)
			diff = str((d2-d1).days)
			self.duration = diff

	company_id = fields.Many2one('res.company', 'Company', required=True)
	estimated_cost = fields.Float(compute='_compute_estimated_cost', store=True, string='Estimated Cost')
	estimated_cost_extra = fields.Float(compute='_compute_estimated_cost_extra', store=True, string='Estimated Cost for Extra Work')
	total_estimated_cost = fields.Float(compute='_compute_estimated_cost_total', store=True, string='Total Estimated Cost')
	date_end = fields.Date('End Date')
	start_date = fields.Date('Start Date')
	task_ids = fields.One2many('project.task', 'project_id',
									domain=[('is_extra_work', '=', False)])
	extra_task_ids = fields.One2many('project.task', 'project_id', domain=[('is_extra_work','=', True)])
	stage_id = fields.One2many('project.stages', 'project_id', 'Project Status')
	stages_generated = fields.Boolean('Stages Generated', default=False)
	location_id = fields.Many2one('stock.location', 'Location', domain=[('usage','=','internal')])
	cent = fields.Float('Cent')
	building_sqf = fields.Float('Building in Sq. Ft')
	rate = fields.Float('Rate')
	total_value = fields.Float('Total Value')
	schedule_id = fields.One2many('project.schedule', 'project_id', 'Schedule')
	schedule_note = fields.Text('Note')
	remark1 = fields.Char('Remarks')
	acc_statement = fields.One2many('account.move.line','project_id', string='Account Statement',compute="_onchange_acc_statement")
	acc_balance = fields.Float(string='Balance',compute="_onchange_acc_statement")
	civil_contractor = fields.Many2one('res.partner', 'Civil Contractor')
	project_product_ids = fields.One2many('project.product', 'project_id')
	labour_report_ids = fields.One2many('project.labour.report', 'project_id')
	categ_id = fields.Many2one('task.category', 'Category')
	view_categ_estimation = fields.Boolean('View Category Wise Estimation', default=False)
	hide_tasks = fields.Boolean('Hide Tasks', default=False)
	temp_tasks = fields.One2many('project.task', 'task_id2', 'Tasks')
	categ_estimation_ids = fields.One2many('category.items.estimation', 'project_id', 'Category Estimation')
	directory_ids = fields.One2many('project.directory', 'project_id', 'Directory')

	project_no = fields.Char(string="Project Number")
	duration = fields.Integer(string="Duration", store=True, compute='_compute_duration')
	project_type = fields.Selection([('govt', 'Government'),('private', 'Private')], string='Project Type')
	is_govt = fields.Boolean('Is Govt', default=False)

	sub_data_line = fields.One2many('sub.data','project_id', string="Sub Data")
	pricelist_ids = fields.One2many('pricelist.pricelist', 'pricelist_id')
	data_line = fields.One2many('main.data', 'project_id', string="Data")
	quality_ids = fields.One2many('quality.control', 'project_id', string="Quality Control")
	mpr_no = fields.Integer('MPR.NO',digits=(12,6))
	po_no = fields.Integer('PO.NO')
	grr_no = fields.Integer('GRR.NO')
	gtn_no = fields.Integer('GTN.NO')
	mis_no = fields.Integer('MIS.NO')
	mrn_no = fields.Integer('MRN.NO')
	dbn_no = fields.Integer('DBN.NO')
	fuel_no = fields.Integer('Fuel No')
	project_name = fields.Char("Project Name (Full)")
	agrrement_no = fields.Char("Agreement No")
	agreement_date = fields.Date("Agreement Date")
	toc = fields.Date("Time of Completion")
	extend_time = fields.Date("Extend of Time If any")
	site_hand_date = fields.Date("Site Hand Over Date")
	gurantee_from = fields.Date("Gurantee Period From")
	gurantee_to = fields.Date("To")
	as_no = fields.Char("AS No")
	as_amt = fields.Float("AS Amount")
	ts_no = fields.Char("TS No")
	ts_amt = fields.Float("TS AMount")
	total_project_length = fields.Float("Total Project Length")
	no_culverts = fields.Float("No of Culverts")
	retaining_wall = fields.Float("Retaining Wall Length")
	remarks = fields.Text("Remarks")
	bill_details_ids = fields.One2many('bill.details','project_id',"Bill Details")
	general_expense_details_ids = fields.One2many('genral.expense.project','project_id',"General Expense Project")
	ts_approved_date = fields.Date("TS Approved")


	@api.model
	def default_get(self, vals):
		res = super(project, self).default_get(vals)
		prod_list = []
		prod_dict = {}
		prod = self.env['pricelist.master'].search([])
		for val in prod:
			prod_dict = {
						'pricelist_id':self.id,
						'item_id':val.id,
						'categ_id':val.categ_id.id,
						'unit':val.unit.id,
						'gst_percent':val.gst_percent,
						'margin_percent':val.margin_percent,
						'purchase_rate':val.purchase_rate,
						'sale_rate':val.sale_rate,
						}
			prod_list.append(prod_dict)

		res.update({'pricelist_ids': prod_list})

		return res


	@api.one
	@api.onchange('project_type')
	def onchange_project_type(self):
		if self.project_type:
			if self.project_type == 'govt':
				self.is_govt = True
			if self.project_type == 'private':
				self.is_govt = False
		else:
			self.is_govt = False

	# partner_id.property_account_receivable.balance


	@api.depends('partner_id')
	def _onchange_acc_statement(self):
		debit = 0.0
		credit = 0.0
		record = self.env['account.move.line'].search([('project_id','=',self.id),('account_id','=',self.partner_id.property_account_receivable.id)])
		self.acc_statement = record
		for rec in record:
			debit += rec.debit
			credit += rec.credit
		self.acc_balance = debit - credit

	_defaults = {
		'schedule_note': 'KVAT AND SERVICE TAX AS PER GOVT. RULES SHOULD BE PAID IN ADDITION TO THE ABOVE AMOUNT ALONG WITH EACH INSTALLMENT. ALL INSTALLMENTS SHOULD BE PAID IN ADVANCE BEFORE STARTING EACH WORK',
		'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
		}

	@api.multi
	def compute_estimated_cost(self):
		temp=0.0
		for line in self:
			for lines in line.task_ids:
				temp+=lines.estimated_cost
			line.estimated_cost=temp
			temp2=0.0
			for lines in line.extra_task_ids:
				temp2 += lines.estimated_cost
			line.estimated_cost_extra=temp2

	@api.multi
	def display_project_status(self):
		stage_lines = self.env['project.stages.line'].search([('id','!=',False)])
		stage = self.env['project.stages']
		for line in self:
			if line.stages_generated == False:
				for stage_line in stage_lines:
					values = {'stage_line_id': stage_line.id,
							  'state': 'no',
							  'project_id': line.id}
					stage_id = stage.create(values)
			if line.stages_generated == True:
				for stage_line in stage_lines:
					generated = False
					for stages in stage_line.stage_id:
						if stages.project_id.id == line.id:
							generated = True
					if generated ==  False:
						values = {'stage_line_id': stage_line.id,
								  'state': 'no',
								  'project_id': line.id}
						stage_id = stage.create(values)
						line.stages_generated = True
			line.stages_generated = True

	@api.multi
	def visible_category(self):
		for line in self:
			line.view_categ_estimation=True

	@api.multi
	def hide_category(self):
		for line in self:
			line.view_categ_estimation = False
			line.hide_tasks = False

	@api.multi
	def refresh_category(self):
		for line in self:
			if line.categ_id.id == False:
				raise osv.except_osv(('Warning!'), ('Please Select A Category'))
			if line.categ_id.id != False:
				line.hide_tasks = True
				categ_estimation_obj = self.env['category.items.estimation']
				categ_estimations = categ_estimation_obj.search([('id','!=',False)])
				for items in categ_estimations:
					items.unlink()
				temp_task_ids = self.env['project.task'].search([('task_id2','=',line.id)])
				for tasks2 in temp_task_ids:
					tasks2.task_id2 = False
				child_ids = []
				childs=self.env['task.category'].search([('parent_id','=',line.categ_id.id)])
				for child in childs:
					child_ids.append(child.id)
				if child_ids == []:
					child_ids.append(line.categ_id.id)
				task_ids = self.env['project.task'].search([('project_id','=',line.id),('categ_id','in',child_ids)])
				for lines in task_ids:
					lines.task_id2 = line.id
					for esimations in lines.estimate_ids:
						if categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)]).id != False:
							categ_obj = categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)])
							categ_obj.qty+=esimations.qty
						if categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)]).id == False:
							values = {'product_id':esimations.pro_id.id,
									'qty':esimations.qty,
									'project_id':line.id}
							categ_estimation_obj.create(values)

	@api.model
	def get_records(self, project_id):

		res = self.env['project.labour.report'].search([('project_id','=',project_id)])
		recordset = res.sorted(key=lambda r: r.date)
		return recordset

	def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
		res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		if view_type == 'form':
			doc = etree.XML(res['arch'])
			for sheet in doc.xpath("//sheet"):
				parent = sheet.getparent()
				index = parent.index(sheet)
				for child in sheet:
					parent.insert(index, child)
					index += 1
				parent.remove(sheet)
			res['arch'] = etree.tostring(doc)
		return res

class document_file(models.Model):
	_inherit = 'ir.attachment'

	ref_name = fields.Char('Description', size=100)
	stage_id = fields.Many2one('project.stages', 'Project Stage')

class project_attachment(models.Model):
	_name = 'project.attachment'
	_description = "Project Attachment"

	name = fields.Char('Name')
	binary_field = fields.Binary('File')
	filename = fields.Char('Filename')
	parent_id = fields.Many2one('document.directory', 'Directory')
	stage_id = fields.Many2one('project.stages', 'Project Stage')
	project_id = fields.Many2one(related='stage_id.project_id', string="Project")

class project_directory(models.Model):
	_name = 'project.directory'

	name = fields.Char('Name')
	project_id = fields.Many2one('project.project', 'Project')
	directory_id = fields.Many2one('document.directory', 'Directories')

	@api.multi
	def open_selected_directory(self):
		self.ensure_one()
		# Search for record belonging to the current staff
		record =  self.env['document.directory'].search([('id','=',self.directory_id.id)])
		context = self._context.copy()
		if record:
			res_id = record[0].id
		else:
			res_id = False
		# Return action to open the form view
		return {
			'name':'Directory Form view',
			'view_type': 'form',
			'view_mode':'form',
			'views' : [(False,'form')],
			'res_model':'document.directory',
			'view_id':'view_document_directory_form',
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'context':context,
		}
class document_directory(models.Model):
	_inherit = 'document.directory'

	@api.multi
	@api.depends('parent_id')
	def _compute_is_parent(self):
		for line in self:
			if line.parent_id.id == False:
				line.is_parent = True
			if line.parent_id.id != False:
				line.is_parent = False

	pro_attachment_ids = fields.One2many('project.attachment', 'parent_id', 'Attachments')
	is_parent = fields.Boolean(compute='_compute_is_parent', store=True, readonly=False, string="Parent")

class project_stages(models.Model):
	_name = 'project.stages'
	_order = "sequence, id"

	name = fields.Char('Name')
	sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
	project_id = fields.Many2one('project.project', 'Project')
	stage_line_id = fields.Many2one('project.stages.line', 'Stage')
	attachment_id = fields.One2many('project.attachment', 'stage_id', 'Attachments')
	state = fields.Selection([('no', 'No'),('yes', 'Yes')], 'Status',
									select=True, copy=False)
	seq = fields.Integer(related='stage_line_id.seq', store=True, string='Sequence')

	_defaults = {
		'state': 'no'}

class project_schedule(models.Model):
	_name = 'project.schedule'
	_order = "seq asc"

	name = fields.Char('Name')
	sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
	seq = fields.Integer('Seq')
	amount = fields.Float('Inst Amount')
	due_on = fields.Char('Due on')
	stage_total = fields.Float(compute='_compute_stage_total',  store=True, string='Stage Total')

	project_id = fields.Many2one('project.project', string='Project')


	@api.multi
	@api.depends('amount')
	def _compute_stage_total(self):
		for line in self:
			for lines in line.project_id.schedule_id:
				if lines.seq <= line.seq:
					line.stage_total += lines.amount

class project_stages_line(models.Model):
	_name = 'project.stages.line'
	_order = "seq asc"

	name = fields.Char('Status')
	seq = fields.Integer('Sequence')
	stage_id = fields.One2many('project.stages', 'stage_line_id', 'Stages')

class project_task_estimation(models.Model):

	_name = 'project.task.estimation'

	@api.multi
	@api.depends('pro_id','qty','unit_price')
	def _compute_estimated_cost_sum(self):

		for line in self:
			line.estimated_cost_sum = line.qty * line.unit_price

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1
		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			for line_rec in first_line_rec.task_id.estimate_ids:
				line_rec.line_no = line_num
				line_num += 1

	line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
	name = fields.Char('Description')
	task_id = fields.Many2one('project.task', 'Task')
	task_ids1 = fields.Many2one('project.task', 'Task')
	project_id = fields.Many2one(related='task_id.project_id', string="Project")
	pro_id =  fields.Many2one('product.product', 'Resource')
	qty = fields.Float('Qty', default=1)
	unit_price = fields.Float(related='pro_id.standard_price', string='Unit Price')
	uom = fields.Many2one(related='pro_id.uom_id',string='Uom')
	estimated_cost_sum =  fields.Float(compute='_compute_estimated_cost_sum', string='Estimated Cost')
	qty_used = fields.Float('Consumed Qty', default=0)
	qty_assigned = fields.Float(compute='_compute_qty_assigned', string='Assigned quantity')
	trigger_project_estimation_calc = fields.Integer(compute='_trigger_project_estimation_calc')
	invoiced_qty = fields.Float('Invoiced Qty', default=0.0)

	@api.model
	def create(self, vals):
		if 'task_id' in vals:
			vals['task_ids1'] = vals['task_id']
		result = super(project_task_estimation, self).create(vals)
		return result

	@api.multi
	@api.depends('qty')
	def _trigger_project_estimation_calc(self):
		# Retrive all product ids related to current project and delete from project_product table
		project_product_recs_ids = self.env['project.product'].search([('project_id','=',self[0].task_id.project_id.id)])._ids
		if project_product_recs_ids:
			sql = ('DELETE FROM project_product '
				'WHERE id in {}').format('('+', '.join(str(t) for t in project_product_recs_ids)+')')
			self.env.cr.execute(sql)
		project = self.env['project.project'].browse(self[0].task_id.project_id.id)
		project_product_list = []
		prod_dict = {}
		for task in project.task_ids:
			for estimate in task.estimate_ids:
				if estimate.pro_id not in prod_dict:
					prod_dict[estimate.pro_id] = estimate.qty
				else:
					prod_dict[estimate.pro_id] = prod_dict[estimate.pro_id]+estimate.qty
		for key, value in prod_dict.items():
			project_product_dict = {}
			project_product_dict['name'] = key.id
			project_product_dict['quantity'] = value
			project_product_dict['unit_price'] = key.standard_price
			project_product_dict['estimated_price'] = value*key.standard_price
			project_product_dict['project_id'] = project.id
			project_product_list.append(project_product_dict)
		for rec in project_product_list:
			self.env['project.product'].create(rec)

	@api.multi
	@api.depends('pro_id')
	def _compute_qty_assigned(self):
		for line in self:
			stock_picking = self.env['stock.picking'].search([('task_id','=',line.task_id.id),('state','=','done')])
			if not stock_picking:
				line.qty_assigned = 0
				return
			stock_picking = stock_picking[0]
			for move_line in stock_picking.move_lines:
				if move_line.product_id==line.pro_id:
					line.qty_assigned = move_line.product_uom_qty

	@api.onchange('qty_used')
	@api.multi
	def _restrict_qty_used(self):
		if self.qty_used>self.qty_assigned:
			self.qty_used=0
			return {
				'warning': {
					'title': 'Warning',
					'message': "Used quantity cannot be greater than assigned quantity."
				}
			}

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.model
	def hide_reconcile_entries(self):
		if self.env.ref('account.action_account_move_line_reconcile_prompt_values'):
			self.env.ref('account.action_account_move_line_reconcile_prompt_values').unlink()
		if self.env.ref('account.account_unreconcile_values'):
			self.env.ref('account.account_unreconcile_values').unlink()
		if self.env.ref('account.action_partner_reconcile_actino'):
			self.env.ref('account.action_partner_reconcile_actino').unlink()
		if self.env.ref('account.validate_account_move_line_values'):
			self.env.ref('account.validate_account_move_line_values').unlink()

	@api.multi
	def reconcile_entry(self):
		for line in self:
			line.reconcile_bool = True

	@api.multi
	def apply_reconcile_entry(self):
		for line in self:
			line.reconcile_bool = False

	@api.multi
	@api.depends('name')
	def _get_opposite_accounts_cash_bank(self):
		for temp in self:
			temp.opp_acc_cash_bank = ""
			for line in temp.move_id:
				for lines in line.line_id:
					if lines.id != temp.id:
						if lines.account_id.is_cash_bank == True:
							temp.opp_acc_cash_bank = lines.account_id.name + "," + temp.opp_acc_cash_bank

	@api.multi
	@api.depends('debit','credit')
	def get_balance(self):
		rec = self.env['account.move.line'].search([])
		for lines in self:
			balance = 0
			if lines.crusher_line == True:
				move_lines = rec.search([('crusher_line','=',True),('date','<=',lines.date),('id','<',lines.id)])
				for move in move_lines:
					if move.id != lines.id:
						balance += move.debit - move.credit
				lines.balance = balance + lines.debit - lines.credit
			if lines.fuel_line == True:
				move_lines = rec.search([('fuel_line','=',True),('date','<=',lines.date),('id','<',lines.id)])
				for move in move_lines:
					if move.id != lines.id:
						balance += move.debit - move.credit
				lines.balance = balance + lines.debit - lines.credit

	@api.multi
	@api.depends('tax_ids','amount')
	def _get_subtotal_crusher_report(self):
		for lines in self:
			taxi = 0
			taxe = 0
			for tax in lines.tax_ids:
				if tax.price_include == True:
					taxi = tax.amount
				if tax.price_include == False:
					taxe += tax.amount
			lines.tax_amount = (lines.amount)/(1+taxi)*(taxi+taxe)
			lines.sub_total = (lines.amount)/(1+taxi)

	description2 =  fields.Char('Description')
	project_id = fields.Many2one('project.project', 'Project')
	opp_acc_cash_bank = fields.Char(compute='_get_opposite_accounts_cash_bank', store=True, string='Account Opposite')
	vehicle_id = fields.Many2one('fleet.vehicle','Vehicle')
	driver_stmt_id = fields.Many2one('driver.daily.statement','Vehicle')
	is_crusher = fields.Boolean(related='account_id.is_crusher', store=True, string='Is Crusher')
	is_fuel_pump = fields.Boolean(related='account_id.is_fuel_pump', store=True, string='Is Fuel Pump')
	bill_no = fields.Char('Bill No')
	contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
	vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
	location_id = fields.Many2one('stock.location', 'Site Name')
	product_id = fields.Many2one('product.product', 'Material')
	qty = fields.Float('Qty')
	rate = fields.Float('Rate')
	amount = fields.Float('Amount')
	tax_ids = fields.Many2many('account.tax', string="GST")
	balance = fields.Float(compute="get_balance",string='Balance')
	driver_stmt_line_id = fields.Many2one('driver.daily.statement.line')
	partner_stmt_line_id = fields.Many2one('partner.daily.statement.line')
	rent_stmt_id = fields.Many2one('rent.vehicle.statement')
	diesel_pump_line_id = fields.Many2one('diesel.pump.line')
	mach_fuel_collection_id = fields.Many2one('machinery.fuel.collection')
	round_off = fields.Float('Round Off')
	sub_total = fields.Float('Sub Total',compute="_get_subtotal_crusher_report")
	tax_amount = fields.Float('Tax Amount',compute="_get_subtotal_crusher_report")

class account_voucher(models.Model):
	_inherit = 'account.voucher'

	description =  fields.Char('Description')

	def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
		'''
		Return a dict to be use to create the first account move line of given voucher.
		:param voucher_id: Id of voucher what we are creating account_move.
		:param move_id: Id of account move where this line will be added.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: mapping between fieldname and value of account move line to create
		:rtype: dict
		'''
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		debit = credit = 0.0
		# TODO: is there any other alternative then the voucher type ??
		# ANSWER: We can have payment and receipt "In Advance".
		# TODO: Make this logic available.
		# -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
		if voucher.type in ('purchase', 'payment'):
			credit = voucher.paid_amount_in_company_currency
		elif voucher.type in ('sale', 'receipt'):
			debit = voucher.paid_amount_in_company_currency
		if debit < 0: credit = -debit; debit = 0.0
		if credit < 0: debit = -credit; credit = 0.0
		sign = debit - credit < 0 and -1 or 1
		#set the first line of the voucher
		move_line = {
				'name': voucher.name or '/',
				'debit': debit,
				'credit': credit,
				'account_id': voucher.account_id.id,
				'move_id': move_id,
				'journal_id': voucher.journal_id.id,
				'period_id': voucher.period_id.id,
				'partner_id': voucher.partner_id.id,
				'currency_id': company_currency != current_currency and  current_currency or False,
				'amount_currency': (sign * abs(voucher.amount) # amount < 0 for refunds
					if company_currency != current_currency else 0.0),
				'date': voucher.date,
				'date_maturity': voucher.date_due,
				'description2': voucher.description
			}
		return move_line

	def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
		'''
		Set a dict to be use to create the writeoff move line.
		:param voucher_id: Id of voucher what we are creating account_move.
		:param line_total: Amount remaining to be allocated on lines.
		:param move_id: Id of account move where this line will be added.
		:param name: Description of account move line.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: mapping between fieldname and value of account move line to create
		:rtype: dict
		'''
		currency_obj = self.pool.get('res.currency')
		move_line = {}
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id
		if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
			diff = line_total
			account_id = False
			write_off_name = ''
			if voucher.payment_option == 'with_writeoff':
				account_id = voucher.writeoff_acc_id.id
				write_off_name = voucher.comment
			elif voucher.partner_id:
				if voucher.type in ('sale', 'receipt'):
					account_id = voucher.partner_id.property_account_receivable.id
				else:
					account_id = voucher.partner_id.property_account_payable.id
			else:
				# fallback on account of voucher
				account_id = voucher.account_id.id
			sign = voucher.type == 'payment' and -1 or 1
			move_line = {
				'name': write_off_name or name,
				'account_id': account_id,
				'move_id': move_id,
				'partner_id': voucher.partner_id.id,
				'date': voucher.date,
				'credit': diff > 0 and diff or 0.0,
				'debit': diff < 0 and -diff or 0.0,
				'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or 0.0,
				'currency_id': company_currency <> current_currency and current_currency or False,
				'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
				'description2': voucher.description
			}
		return move_line

	def action_move_line_create(self, cr, uid, ids, context=None):
		'''
		Confirm the vouchers given in ids and create the journal entries for each of them
		'''
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for voucher in self.browse(cr, uid, ids, context=context):
			local_context = dict(context, force_company=voucher.journal_id.company_id.id)
			if voucher.move_id:
				continue
			company_currency = self._get_company_currency(cr, uid, voucher.id, context)
			current_currency = self._get_current_currency(cr, uid, voucher.id, context)
			# we select the context to use accordingly if it's a multicurrency case or not
			context = self._sel_context(cr, uid, voucher.id, context)
			# But for the operations made by _convert_amount, we always need to give the date in the context
			ctx = context.copy()
			ctx.update({'date': voucher.date})
			# Create the account move record.
			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
			# Get the name of the account_move just created
			name = move_pool.browse(cr, uid, move_id, context=context).name
			# Create the first line of the voucher
			move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
			move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
			line_total = move_line_brw.debit - move_line_brw.credit
			rec_list_ids = []
			if voucher.type == 'sale':
				line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
			elif voucher.type == 'purchase':
				line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
			# Create one move line per voucher line where amount is not 0.0
			line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

			# Create the writeoff line if needed
			ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
			if ml_writeoff:
				move_line_pool.create(cr, uid, ml_writeoff, local_context)
			# We post the voucher.
			self.write(cr, uid, [voucher.id], {
				'move_id': move_id,
				'state': 'posted',
				'number': name,
			})
			if voucher.journal_id.entry_posted:
				move_pool.post(cr, uid, [move_id], context={})
			# We automatically reconcile the account move lines.
			reconcile = False
			for rec_ids in rec_list_ids:
				if len(rec_ids) >= 2:
					reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
		return True


	def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
		'''
		Create one account move line, on the given account move, per voucher line where amount is not 0.0.
		It returns Tuple with tot_line what is total of difference between debit and credit and
		a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

		:param voucher_id: Voucher id what we are working with
		:param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
		:param move_id: Account move wher those lines will be joined.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
		:rtype: tuple(float, list of int)
		'''
		if context is None:
			context = {}
		move_line_obj = self.pool.get('account.move.line')
		currency_obj = self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		tot_line = line_total
		rec_lst_ids = []
		date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
		ctx = context.copy()
		ctx.update({'date': date})
		voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
		voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
		ctx.update({
			'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
			'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
		prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
		for line in voucher.line_ids:
			#create one move line per voucher line where amount is not 0.0
			# AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
			if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
				continue
			# convert the amount set on the voucher line into the currency of the voucher's company
			# this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
			amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
			# if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
			# currency rate difference
			if line.amount == line.amount_unreconciled:
				if not line.move_line_id:
					raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
				sign = line.type =='dr' and -1 or 1
				currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
			else:
				currency_rate_difference = 0.0
			move_line = {
				'journal_id': voucher.journal_id.id,
				'period_id': voucher.period_id.id,
				'name': line.name or '/',
				'account_id': line.account_id.id,
				'move_id': move_id,
				'partner_id': voucher.partner_id.id,
				'currency_id': line.move_line_id and (company_currency != line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
				'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
				'quantity': 1,
				'credit': 0.0,
				'debit': 0.0,
				'date': voucher.date,
				'description2': voucher.description
			}
			if amount < 0:
				amount = -amount
				if line.type == 'dr':
					line.type = 'cr'
				else:
					line.type = 'dr'
			if (line.type=='dr'):
				tot_line += amount
				move_line['debit'] = amount
			else:
				tot_line -= amount
				move_line['credit'] = amount
			if voucher.tax_id and voucher.type in ('sale', 'purchase'):
				move_line.update({
					'account_tax_id': voucher.tax_id.id,
				})
			# compute the amount in foreign currency
			foreign_currency_diff = 0.0
			amount_currency = False
			if line.move_line_id:
				# We want to set it on the account move line as soon as the original line had a foreign currency
				if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
					# we compute the amount in that foreign currency.
					if line.move_line_id.currency_id.id == current_currency:
						# if the voucher and the voucher line share the same currency, there is no computation to do
						sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
						amount_currency = sign * (line.amount)
					else:
						# if the rate is specified on the voucher, it will be used thanks to the special keys in the context
						# otherwise we use the rates of the system
						amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
				if line.amount == line.amount_unreconciled:
					foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)
			move_line['amount_currency'] = amount_currency
			voucher_line = move_line_obj.create(cr, uid, move_line)
			rec_ids = [voucher_line, line.move_line_id.id]
			if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
				# Change difference entry in company currency
				exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
				new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
				move_line_obj.create(cr, uid, exch_lines[1], context)
				rec_ids.append(new_id)
			if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
				# Change difference entry in voucher currency
				move_line_foreign_currency = {
					'journal_id': line.voucher_id.journal_id.id,
					'period_id': line.voucher_id.period_id.id,
					'name': _('change')+': '+(line.name or '/'),
					'account_id': line.account_id.id,
					'move_id': move_id,
					'partner_id': line.voucher_id.partner_id.id,
					'currency_id': line.move_line_id.currency_id.id,
					'amount_currency': (-1 if line.type == 'cr' else 1) * foreign_currency_diff,
					'quantity': 1,
					'credit': 0.0,
					'debit': 0.0,
					'date': line.voucher_id.date,
				}
				new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
				rec_ids.append(new_id)
			if line.move_line_id.id:
				rec_lst_ids.append(rec_ids)
		return (tot_line, rec_lst_ids)

class purchase_item_category(models.Model):
	_name = 'purchase.item.category'

	name = fields.Char('Name')
	account_id = fields.Many2one('account.account','Related Account')

class TermsCondition(models.Model):
	_name = 'terms.condition'

	terms_id = fields.Many2one('purchase.order')
	term = fields.Char("Terms")
	condition = fields.Char("Conditions")


class purchase_order(models.Model):
	_inherit = 'purchase.order'
	_order = 'id desc'

	terms_ids = fields.One2many('terms.condition', 'terms_id')

	@api.model
	def _needaction_domain_get(self):
		return [('state', '=', 'draft')]



	READONLY_STATES = {
		'confirmed': [('readonly', True)],
		'approved': [('readonly', True)],
		'done': [('readonly', True)]
	}

	def create(self, cr, uid, vals, context=None):
		if vals.get('name', '/') == '/':
			project = self.pool.get('project.project').browse(cr,uid,vals['project_id']).project_no
			self.pool.get('project.project').browse(cr,uid,vals['project_id']).po_no +=1
			po_no=str(self.pool.get('project.project').browse(cr,uid,vals['project_id']).po_no).zfill(4)
			mpr = self.pool.get('site.purchase').browse(cr,uid,vals['mpr_id'])
			# date_year = '/'+str(datetime.datetime.today().year) + '-' + str((datetime.datetime.today() + timedelta(days=365)).year)
			date_year = '/' + str(datetime.datetime.today().year)
			project_name = str(project.split('/')[0])
        	vals['name'] = str(project_name) + '/'+ 'S&P/' + po_no + date_year
        # if mpr.vehicle_purchase != True:
			# 	vals['name'] = project + '/'+ 'CIVIL/' +  'PO' + po_no + date_year
			# else:
			# 	vals['name'] = project + '/' + 'MECH/' + 'PO' + po_no + date_year
		context = dict(context or {}, mail_create_nolog=True)
		order = super(purchase_order, self).create(cr, uid, vals, context=context)
		self.message_post(cr, uid, [order], body=_("RFQ created"), context=context)
		return order

	@api.multi
	@api.depends('name')
	def _count_invoices(self):
		for line in self:
			line.invoice_count = 0
			invoice_ids = self.env['hiworth.invoice'].search([('origin','=',line.name)])
			line.invoice_count = len(invoice_ids)

	@api.model
	def _default_currency(self):
		journal = self._default_journal()
		return journal.currency or journal.company_id.currency_id

	@api.model
	def _default_journal(self):
		inv_type = ['purchase']
		company_id = self._context.get('company_id', self.env.user.company_id.id)
		domain = [
			('type', 'in', inv_type),
			('company_id', '=', company_id),
		]
		return self.env['account.journal'].search(domain, limit=1)

	@api.onchange('date_order')
	def onchage_dateorder(self):
		if self.date_order:
			self.minimum_planned_date = self.date_order

	@api.multi
	@api.depends('order_line','round_off_amount','discount_amount')
	def compute_gst(self):
		for rec in self:
			rec.sgst_tax = 0.0
			rec.cgst_tax = 0.0
			rec.igst_tax = 0.0
			if rec.order_line:
				for line in rec.order_line:
					rec.sgst_tax += line.sgst_tax
					rec.cgst_tax += line.cgst_tax
					rec.igst_tax += line.igst_tax
			rec.amount_total2 = round(rec.sgst_tax + rec.cgst_tax +rec.igst_tax+rec.amount_untaxed + rec.packing_charge + rec.loading_charge + rec.transporting_charge+rec.round_off_amount - rec.discount_amount, 2)
			rec.amount_tax = rec.sgst_tax + rec.cgst_tax + rec.igst_tax
			if rec.amount_total2 == 0.0:
				rec.amount_total2 =rec.amount_total



	@api.model
	def _default_write_off_account(self):
		return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).write_off_account_id

	@api.model
	def _default_discount_account(self):
		return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).discount_account_id

	@api.onchange('account_id')
	def onchange_account(self):
		account_ids = []
		account_ids = [account.id for account in self.env['account.account'].search([('company_id','=',self.company_id.id)])]
		return {
				'domain': {
					'account_id': [('id','in',account_ids)]


				}
			}


	@api.depends('amount_total')
	def compute_total_unit_price(self):
		for rec in self:
			quanity = rec.order_line and sum(rec.order_line.mapped('required_qty'))
			print 'quantitttttttttttttty',quanity
			if quanity==0:
				quanity=1
				#rec.total_unit_price =1
			if rec.amount_total == 0.0:
				rec.total_unit_price = 1
			else:
				rec.total_unit_price = rec.amount_total / quanity

	@api.onchange('mpr_id')
	def onchange_mpr_id(self):
		for rec in self:
			if rec.mpr_id:
				values = []
				rec.project_id = rec.mpr_id.project_id.id
				for mpr_line in rec.mpr_id.req_list:
					expected_rate=self.env['purchase.order.line'].search([('product_id','=',mpr_line.item_id.id)] ,limit =1).expected_rate
					values.append((0,0,{'product_id':mpr_line.item_id.id,
										'name':mpr_line.desc,
										'required_qty':mpr_line.quantity,
										'product_uom':mpr_line.unit.id,
										'expected_rate':expected_rate,
										'account_id':mpr_line.item_id.property_account_expense.id,
										'state':rec.state,
										'order_id':rec.id,
						}))
				rec.order_line = values



	@api.depends('order_line')
	def compute_items_list(self):
		for rec in self:
			items = ''
			for line in rec.order_line:
				items += line.product_id.name + ','
			rec.items_list = items

	@api.depends('order_line')
	def compute_items_quantity(self):
		for rec in self:
			quantity = 0
			for line in rec.order_line:
				quantity += line.product_qty
			rec.total_items_quantity = quantity

	@api.onchange('vehicle_id')
	def onchange_vehicle_id(self):
		for rec in self:
			if rec.vehicle_id:
				rec.brand_id = rec.vehicle_id.brand_id.id
				rec.model_id = rec.vehicle_id.model_id.id
				rec.chase_no = rec.vehicle_id.chase_no
				rec.engine_no = rec.vehicle_id.engine_no


	STATE_SELECTION = [
		('draft', 'Waiting'),
		('sent', 'RFQ'),
		('bid', 'Bid Received'),
		('confirmed', 'Approved'),
		('approved', 'Order Placed'),
		('except_picking', 'Shipping Exception'),
		('except_invoice', 'Invoice Exception'),
		('done', 'Received'),
		('paid', 'Paid'),
		('cancel', 'Cancelled')
	]
	request_id = fields.Many2one('site.purchase', 'Request')
	state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
								  help="The status of the purchase order or the quotation request. "
									   "A request for quotation is a purchase order in a 'Draft' status. "
									   "Then the order has to be confirmed by the user, the status switch "
									   "to 'Confirmed'. Then the supplier must confirm the order to change "
									   "the status to 'Approved'. When the purchase order is paid and "
									   "received, the status becomes 'Done'. If a cancel action occurs in "
									   "the invoice or in the receipt of goods, the status becomes "
									   "in exception.",
								  select=True, copy=False)
	journal_id2 = fields.Many2one('account.journal', string='Journal',
		default=_default_journal, states=READONLY_STATES,
		domain="[('type', '=', 'purchase')]")
	partner_id = fields.Many2one('res.partner', 'Supplier', required=False, states=READONLY_STATES,
			change_default=True, track_visibility='always')
	invoice_created = fields.Boolean('Invoice Created', default=False)
	invoice_count = fields.Integer(compute='_count_invoices', string='Invoice Nos')
	order_line = fields.One2many('purchase.order.line', 'order_id', 'Order Lines',
									  states=READONLY_STATES,
									  copy=True)
	currency_id = fields.Many2one('res.currency', string='Currency',
		required=True, readonly=True, states={'draft': [('readonly', False)]},
		default=_default_currency, track_visibility='always')
	is_requisition = fields.Boolean('Is Requisition', default = True)
	requisition_id = fields.Many2one('purchase.order', 'Purchase Requisition')
	account_id = fields.Many2one('account.account', 'Account', states=READONLY_STATES)
	sgst_tax = fields.Float(compute="compute_gst", store=True, string="SGST Amount")
	cgst_tax = fields.Float(compute="compute_gst", store=True, string="CGST Amount")
	igst_tax = fields.Float(compute="compute_gst", store=True, string="IGST Amount")
	amount_total2 = fields.Float(compute="compute_gst", string='Total', store=True, help="The total amount")
	invoice_date = fields.Date('Invoice Date')
	round_off_amount = fields.Float('Round off Amount (+/-)', states=READONLY_STATES)
	round_off_account = fields.Many2one('account.account', 'Write off Account', states=READONLY_STATES,
	 default=_default_write_off_account)
	discount_amount = fields.Float('Discount Amount', states=READONLY_STATES)
	discount_account = fields.Many2one('account.account', 'Discount Account', states=READONLY_STATES,
	 default=_default_discount_account)
	order_line = fields.One2many('purchase.order.line', 'order_id', 'Order Lines',
						readonly=False, copy=True)
	maximum_planned_date = fields.Date('Maximum Expected Date')
	location_id = fields.Many2one('stock.location', domain=[('usage','=','internal')])
	pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=False, states=READONLY_STATES, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities.")
	project_id = fields.Many2one('project.project', string="Project", required=True)
	mpr_id = fields.Many2one('site.purchase', string="Material Procurement Requistion")
	total_unit_price = fields.Float(string="Unit Price", compute='compute_total_unit_price')
	price_bool = fields.Boolean("Price")
	price_char = fields.Char("Price",default="Price Inclusive of all Taxes")
	# transport_bool = fields.Boolean("Transportation")
	# transport_char = fields.Char("Transportation")
	warranty_bool = fields.Boolean('Warranty')
	warranty_char = fields.Char('Warranty')
	# service_bool = fields.Boolean("Service")
	# service_char = fields.Char("Service")
	# tyres_bool = fields.Boolean('Tyres')
	# tyres_char = fields.Char('Tyres')
	# accessory_bool = fields.Boolean('Accessory')
	# accessory_char = fields.Char('Accessory')
	# permenent_reg_bool = fields.Boolean('Permenent Reg')
	# permenent_reg_char = fields.Char('Permenent Reg')
	# fastag_bool = fields.Boolean('Fastag')
	# fastag_char = fields.Char('Fastag')
	delivery_bool = fields.Boolean("Delivery")
	delivery_char = fields.Char("Delivery",default="Immediate")
	machine_bool = fields.Char("Machine")
	machine_char = fields.Char("Machine")
	payment_bool = fields.Boolean("Payment")
	payment_char = fields.Char("Payment",default="Through Bank Transfer Credit")
	freight_bool = fields.Boolean("Freight")
	freight_char = fields.Char("Freight",default="Extra")
	q_number = fields.Char("Q No")
	q_date = fields.Date("Q Date",default=fields.Date.today())
	items_list = fields.Char(string="Items",compute='compute_items_list')
	total_items_quantity = fields.Char(string="Total Quantity",compute='compute_items_quantity')
	packing_charge = fields.Float(string="Packing Charge")
	loading_charge = fields.Float(string="Loading Charge")
	transporting_charge = fields.Float(string="Freight Charge")
	vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle No")
	model_id = fields.Many2one('fleet.vehicle.model', "Model")
	brand_id = fields.Many2one('fleet.vehicle.model.brand', "Brand")
	chase_no = fields.Char("Chase No")
	engine_no = fields.Char("Model No")
	received_qty = fields.Float("Received Quantity")
	rejected_qty = fields.Float("Rejected Quantity")



	@api.multi
	def wkf_confirm_order(self):
		res = super(purchase_order, self).wkf_confirm_order()
		for rec in self:
			if rec.mpr_id:
				rec.mpr_id.write({'state':'confirm_purchase'})

		return res

	def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
		res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		if view_type == 'form':
			doc = etree.XML(res['arch'])
			for sheet in doc.xpath("//sheet"):
				parent = sheet.getparent()
				index = parent.index(sheet)
				for child in sheet:
					parent.insert(index, child)
					index += 1
				parent.remove(sheet)
			res['arch'] = etree.tostring(doc)
		return res

	def wkf_send_rfq(self, cr, uid, ids, context=None):
		'''
		This function opens a window to compose an email, with the edi purchase template message loaded by default
		'''
		if not context:
			context= {}
		ir_model_data = self.pool.get('ir.model.data')
		try:
			if context.get('send_rfq', False):
				template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase15')[1]
			else:
				template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase_done2')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx = dict(context)
		ctx.update({
			'default_model': 'purchase.order',
			'default_res_id': ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
		})
		return {
			'name': _('Compose Email'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form_id, 'form')],
			'view_id': compose_form_id,
			'target': 'new',
			'context': ctx,
		}

	def picking_done(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'shipped':1,'state':'done'}, context=context)
		# Do check on related procurements:
		proc_obj = self.pool.get("procurement.order")
		po_lines = []
		for po in self.browse(cr, uid, ids, context=context):
			po_lines += [x.id for x in po.order_line if x.state != 'cancel']
		if po_lines:
			procs = proc_obj.search(cr, uid, [('purchase_line_id', 'in', po_lines)], context=context)
			if procs:
				proc_obj.check(cr, uid, procs, context=context)
		self.message_post(cr, uid, ids, body=_("Products received"), context=context)
		return True

	@api.multi
	def create_invoice(self):
		'''
		This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
		'''
		if not self.partner_ref:
			raise osv.except_osv(_('Warning!'),
						_('You must enter a Invoice Number'))
		invoice_line = self.env['hiworth.invoice.line2']
		invoice = self.env['hiworth.invoice']
		now = datetime.datetime.now()
		for line in self:
			values1 = {
						'is_purchase_bill': True,
						'partner_id': line.partner_id.id,
						'purchase_order_date':line.date_order,
						'origin': line.name,
						'name': self.partner_ref,
						'journal_id': line.journal_id2.id,
						'account_id': line.account_id.id,
						'date_invoice': line.invoice_date,
						'round_off_amount': line.round_off_amount,
						'round_off_account': line.round_off_account.id,
						'discount_amount': line.discount_amount,
						'discount_account': line.discount_account.id,
						'purchase_order_id': line.id,
						}
			invoice_id = invoice.create(values1)
			for lines in line.order_line:
				taxes_ids = []
				taxes_ids = [tax.id for tax in lines.taxes_id]
				values2={
						'product_id': lines.product_id.id,
						'name': lines.product_id.name,
						'price_unit': lines.price_unit,
						'uos_id': lines.product_uom.id,
						'quantity': lines.product_qty,
						'price_subtotal':lines.price_subtotal,
						'task_id': lines.task_id.id,
						'location_id': lines.location_id.id,
						'invoice_id': invoice_id.id,
						'account_id': lines.account_id.id,
						'tax_ids':  [(6, 0, taxes_ids)]
						}
				invoice_line_id = invoice_line.create(values2)
			invoice_id.action_for_approval()
			line.invoice_created = True


	@api.multi
	def _amount_in_words(self,amount_total2):
		wGenerator = Number2Words()
		if amount_total2 >= 0.0:
			amount_to_text = wGenerator.convertNumberToWords(amount_total2) + ' Only'
			return amount_to_text

	@api.multi
	def invoice_open(self):
		self.ensure_one()
		# Search for record belonging to the current staff
		record =  self.env['hiworth.invoice'].search([('origin','=',self.name)])

		context = self._context.copy()
		context['type2'] = 'out'
		#context['default_name'] = self.id
		if record:
			res_id = record[0].id
		else:
			res_id = False
		# Return action to open the form view
		return {
			'name':'Invoice view',
			'view_type': 'form',
			'view_mode':'form',
			'views' : [(False,'form')],
			'res_model':'hiworth.invoice',
			'view_id':'hiworth_invoice_form',
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'context':context,
		}

	@api.multi
	def button_approve(self):
		for rec in self:
			rec.state = 'confirmed'
			for user in self.env['res.users'].search([]):
				if user.has_group('hiworth_construction.group_purchase_manager'):
					self.env['popup.notifications'].sudo().create({
						'name': user.id,
						'status': 'draft',
						'message': 'You have a Purchase Order To Confirm',

					})


	@api.multi
	def button_send_report(self):
		for rec in self:
			message = 'Hi, ' + self.env.user.name + " " + rec.notes + " against Purchase Order NO " + rec.name
			if rec.mpr_id and rec.mpr_id.project_manager:
				self.env['popup.notifications'].sudo().create({
					'name': rec.mpr_id.project_manager.id,
					'status': 'draft',
					'message': message,

				})
			if rec.mpr_id and rec.mpr_id.dgm_id:
				self.env['popup.notifications'].sudo().create({
					'name': rec.mpr_id.dgm_id.id,
					'status': 'draft',
					'message': message,

				})

   

	def view_invoice(self, cr, uid, ids, context=None):
		'''
		This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
		'''
		context = dict(context or {})
		mod_obj = self.pool.get('ir.model.data')
		wizard_obj = self.pool.get('purchase.order.line_invoice')
		inv_ids = []
		for po in self.browse(cr, uid, ids, context=context):
			if po.invoice_method == 'manual':
				if not po.invoice_ids:
					context.update({'active_ids' :  [line.id for line in po.order_line if line.state != 'cancel']})
					wizard_obj.makeInvoices(cr, uid, [], context=context)
		for po in self.browse(cr, uid, ids, context=context):
			inv_ids+= [invoice.id for invoice in po.invoice_ids]
			invoice = self.pool.get('account.invoice').search(cr, uid, [('purchase_id','=',po.id)])
			if self.pool.get('account.invoice').browse(cr, uid, invoice).not_visible == True:
				for line in self.pool.get('account.invoice').browse(cr, uid, invoice).invoice_line:
					line.quantity = line.purchase_line_id.product_qty
					line.price_unit = line.purchase_line_id.price_unit
				self.pool.get('account.invoice').browse(cr, uid, invoice).not_visible = False
				self.pool.get('account.invoice').browse(cr, uid, invoice).number = po.partner_ref
				self.pool.get('account.invoice').browse(cr, uid, invoice).date_invoice = po.invoice_date
		res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
		res_id = res and res[1] or False
		return {
			'name': _('Supplier Invoices'),
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': [res_id],
			'res_model': 'account.invoice',
			'context': "{'type':'in_invoice', 'journal_type': 'purchase'}",
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			'res_id': inv_ids and inv_ids[0] or False,
		}

class invoice_attachment(models.Model):
	_name = "invoice.attachment"

	@api.onchange('parent_id')
	def _onchange_attachment_selection(self):
		res={}
		attachment_ids = []
		if self.parent_id.id != False and self.invoice_id.project_id.id != False:
			attachment_ids = [attachment.id for attachment in self.env['project.attachment'].search([('parent_id','=',self.parent_id.id),('project_id','=',self.invoice_id.project_id.id)])]
			return {
				'domain': {
					'attachment_id': [('id','in',attachment_ids)]
				}
			}
		if self.parent_id.id != False and self.invoice_id.project_id.id == False:
			attachment_ids = [attachment.id for attachment in self.env['project.attachment'].search([('parent_id','=',self.parent_id.id)])]
			return {
				'domain': {
					'attachment_id': [('id','in',attachment_ids)]
				}
			}
		else:
			return res

	name = fields.Char('Name')
	attachment_id = fields.Many2one('project.attachment', 'Attachments')
	filename = fields.Char(related='attachment_id.filename', string='Filename')
	binary_field = fields.Binary(related='attachment_id.binary_field', string="File")
	invoice_id = fields.Many2one('account.invoice', 'Invoice')
	parent_id = fields.Many2one('document.directory', 'Directory')

class account_invoice(models.Model):
	_inherit = "account.invoice"
	_rec_name = 'prime_invoice'

	@api.onchange('project_id')
	def _onchange_task_selection(self):
		if self.is_contractor_bill == True:
			return {
				'domain': {
					'task_id': [('project_id','=',self.project_id.id)]
				}
			}

	@api.onchange('is_contractor_bill')
	def _onchange_contractor_selection(self):
		if self.is_contractor_bill == True:
			return {
				'domain': {
					'partner_id': [('contractor','=',True)]
				}
			}

	@api.multi
	@api.depends('task_id')
	def _visible_prevoius_bills(self):
		for line in self:
			if line.task_id.id != False:
				line.visible_previous_bill = True

	@api.multi
	@api.depends('amount_total','residual')
	def _compute_balance(self):
		for line in self:
			if line.state == 'draft':
				line.balance2 = line.amount_total
			if line.state != 'draft':
				line.balance2 = line.residual

	@api.multi
	@api.depends('prevous_bills')
	def _compute_prevoius_balance(self):
		for line in self:
			for lines in line.prevous_bills:
				line.previous_balance+=lines.balance2

	@api.multi
	@api.depends('previous_balance','amount_total','residual')
	def _compute_net_total(self):
		for line in self:
			if line.residual == 0.0:
				line.net_total = line.previous_balance + line.amount_total
			else:
				line.net_total = line.previous_balance + line.residual

	state = fields.Selection([
			('draft','Draft'),
			('proforma','Pro-forma'),
			('proforma2','Pro-forma'),
			('open','Waiting for Approval'),
			('approve','Approved'),
			('paid','Paid'),
			('cancel','Cancelled'),
		], string='Status', index=True, readonly=True, default='draft',
		track_visibility='onchange', copy=False,
		help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
			 " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
			 " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
			 " * The 'Approved' status is used when the Invoice approved for Payment.\n"
			 " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
			 " * The 'Cancelled' status is used when user cancel invoice.")
	project_id = fields.Many2one('project.project', 'Project')
	customer_id = fields.Many2one(related='project_id.partner_id', string="Client")
	is_contractor_bill = fields.Boolean('Contractor Bill', default=False)
	task_id = fields.Many2one('project.task', 'Task')
	prevous_bills = fields.One2many('account.invoice', 'invoice_id5', 'Previous Invoices')
	invoice_id5 = fields.Many2one('account.invoice', 'Invoices')
	visible_previous_bill = fields.Boolean(compute='_visible_prevoius_bills', store=True, string="Visible Prevoius Bill", default=False)
	visible_bills = fields.Boolean('Visible', default=False)
	balance2 = fields.Float(compute='_compute_balance', string="Balance Of Not Validated")
	previous_balance = fields.Float(compute='_compute_prevoius_balance', string="Previous Balance")
	net_total = fields.Float(compute='_compute_net_total', string="Net Total")
	attachment_ids = fields.One2many('invoice.attachment', 'invoice_id', 'Attachments')
	task_related = fields.Boolean('Related To Task')
	agreed_amount = fields.Float(related='task_id.estimated_cost', string="Agreement Amount")
	type_id = fields.Selection([('Arch','Architectural'),('Struc','Structural'),('Super','Supervision')],string="Type")
	prime_invoice = fields.Char('Prime Invoice')
	account_invoice_ids = fields.Many2one('account.invoice','Invoice no')
	district = fields.Char('District')
	person = fields.Char('Person Incharge',compute='select_person')
	total_tender_amount = fields.Float('Tender Amount',compute='compute_tender_amount')
	balance_amount = fields.Float('Balance Amount',readonly=True)
	contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
	statusline_ids = fields.One2many('customer.invoice.follow.up','account_invoice_ids', 'Status')
	purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
	not_visible =  fields.Boolean('Visible', default=False)

	def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
		res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		if view_type == 'form':
			doc = etree.XML(res['arch'])
			for sheet in doc.xpath("//sheet"):
				parent = sheet.getparent()
				index = parent.index(sheet)
				for child in sheet:
					parent.insert(index, child)
					index += 1
				parent.remove(sheet)
			res['arch'] = etree.tostring(doc)
		return res

	@api.onchange('project_id')
	def onchange_datas(self):
		if self.project_id:
			self.district = self.project_id.district
			self.contractor_id = self.project_id.contractor_id.id

	@api.multi
	@api.depends('account_invoice_ids')
	def select_person(self):
		for person in self:
			person.person = self.env['customer.invoice.follow.up'].search([('account_invoice_ids', '=',person.account_invoice_ids.id)]).person
			person.balance_amount=self.env['customer.invoice.follow.up'].search([('account_invoice_ids', '=',person.account_invoice_ids.id)]).balance_amount

	@api.multi
	@api.depends('project_id')
	def compute_tender_amount(self):
		for tender in self:
			tender.total_tender_amount = self.env['hiworth.tender'].search([('id', '=',tender.project_id.tender_id.id)]).apac

	@api.multi
	def refresh_prevoius_bills(self):
		for line in self:
			invoice_objs = self.env['account.invoice'].search([('task_id','=',line.task_id.id)])
			for invoice in invoice_objs:
				invoice.invoice_id5 = False
			for invoices in invoice_objs:
				if invoices.id != line.id:
					invoices.invoice_id5 = line.id
			line.visible_bills = True

	@api.multi
	def hide_prevoius_bills(self):
		for line in self:
			line.visible_bills = False

	@api.multi
	def invoice_approve(self):
		for line in self:
			line.state = 'approve'

	@api.multi
	def action_invoice_sent(self):
		""" Open a window to compose an email, with the edi invoice template
			message loaded by default
		"""
		assert len(self) == 1, 'This option should only be used for a single id at a time.'
		template = self.env.ref('hiworth_construction.email_template_edi_invoice23', False)
		compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
#         print 'template=====================23423423234====', template
		ctx = dict(
			default_model='account.invoice',
			default_res_id=self.id,
			default_use_template=bool(template),
			default_template_id=template.id,
			default_composition_mode='comment',
			mark_invoice_as_sent=True,
		)
		return {
			'name': _('Compose Email'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form.id, 'form')],
			'view_id': compose_form.id,
			'target': 'new',
			'context': ctx,
		}

class account_invoice_line(models.Model):
	_inherit = 'account.invoice.line'

	total_assigned_qty = fields.Float('Assigned Qty')
	discount_amt = fields.Float('Cash Discount')
	net_total = fields.Float('Net Total')

	@api.multi
	def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
			partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
			company_id=None, task_related=False,task_id=False):
		context = self._context
		company_id = company_id if company_id is not None else context.get('company_id', False)
		self = self.with_context(company_id=company_id, force_company=company_id)
		if not partner_id:
			raise except_orm(_('No Partner Defined!'), _("You must first select a partner!"))
		values = {}
		part = self.env['res.partner'].browse(partner_id)
		fpos = self.env['account.fiscal.position'].browse(fposition_id)
		if part.lang:
			self = self.with_context(lang=part.lang)
		product = self.env['product.product'].browse(product)
		values['name'] = product.partner_ref
		if type in ('out_invoice', 'out_refund'):
			account = product.property_account_income or product.categ_id.property_account_income_categ
		else:
			account = product.property_account_expense or product.categ_id.property_account_expense_categ
		account = fpos.map_account(account)
		if account:
			values['account_id'] = account.id
		if type in ('out_invoice', 'out_refund'):
			taxes = product.taxes_id or account.tax_ids
			if product.description_sale:
				values['name'] += '\n' + product.description_sale
		else:
			taxes = product.supplier_taxes_id or account.tax_ids
			if product.description_purchase:
				values['name'] += '\n' + product.description_purchase
		fp_taxes = fpos.map_tax(taxes)
		values['invoice_line_tax_id'] = fp_taxes.ids
		if type in ('in_invoice', 'in_refund'):
			if price_unit and price_unit != product.standard_price:
				values['price_unit'] = price_unit
			else:
				values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.standard_price, taxes, fp_taxes.ids)
		else:
			values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.lst_price, taxes, fp_taxes.ids)
		values['uos_id'] = product.uom_id.id
		if uom_id:
			uom = self.env['product.uom'].browse(uom_id)
			if product.uom_id.category_id.id == uom.category_id.id:
				values['uos_id'] = uom_id
		domain = {'uos_id': [('category_id', '=', product.uom_id.category_id.id)]}
		company = self.env['res.company'].browse(company_id)
		currency = self.env['res.currency'].browse(currency_id)
		if company and currency:
			if company.currency_id != currency:
				values['price_unit'] = values['price_unit'] * currency.rate
			if values['uos_id'] and values['uos_id'] != product.uom_id.id:
				values['price_unit'] = self.env['product.uom']._compute_price(
					product.uom_id.id, values['price_unit'], values['uos_id'])
		product_ids = []
		if task_related == True:
			estimation = self.env['project.task.estimation'].search([('task_id','=',task_id),('pro_id','=',product.id)])
			values['total_assigned_qty']=estimation.qty
			values['quantity']=0.0
			if task_id == False:
				raise osv.except_osv(_('Warning!'),
						_('Please enter a task or uncheck "Related to task Field"'))
			if task_id != False:
				product_ids = [estimate.pro_id.id for estimate in self.env['project.task'].search([('id','=',task_id)]).estimate_ids]
				return {'value': values, 'domain': {'product_id': [('id','in',product_ids)]}}
		if not product:
			if type in ('in_invoice', 'in_refund'):
				return {'value': {}, 'domain': {'uos_id': []}}
			else:
				return {'value': {'price_unit': 0.0}, 'domain': {'uos_id': []}}

		return {'value': values, 'domain': domain,}

	@api.model
	def create(self,vals):
		if 'invoice_id' in vals:
			task_id = self.env['account.invoice'].browse(vals['invoice_id']).task_id
			product_id = self.env['product.product'].browse(vals['product_id'])
			estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',product_id.id)],limit=1)
			if vals['quantity'] != 0.0:
				estimation.write({'invoiced_qty': estimation.invoiced_qty+vals['quantity']})
			vals['total_assigned_qty']=estimation.qty
			return super(account_invoice_line, self).create(vals)
		return super(account_invoice_line, self).create(vals)

class product_cost_table(models.Model):
	_name = "product.cost.table"

	_order = "date desc"

	name = fields.Char('name')
	product_id = fields.Many2one('product.template', 'Product')
	date = fields.Date('Date')
	standard_price = fields.Float('Cost')
	purchase_id = fields.Char('Reference')
	remarks = fields.Char('Remarks' ,size=200)
	qty = fields.Float('Quantity')
	location_id = fields.Many2one('stock.location','Location')

class product_template(models.Model):

	_inherit = "product.template"



	# def create(self, cr, uid, vals, context=None):
	# 	return super(product_template, self).create( cr, uid, vals, context=None)
		# if not vals.get('default_code',False):
		# 	if vals.get('categ_id',False):
		# 		category = self.env['product.category'].browse(vals.get('categ_id',False))
		# 		category.product_sequence +=1
		# 		code = category.product_category_code + '-'+str(category.product_sequence)
		# 	vals.update({'default_code':code})
		#  res

	# def create(self, cr, uid, vals, context=None):
	# 	''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
	# 	product_template_id = super(product_template, self).create(cr, uid, vals, context=context)
	# 	if not context or "create_product_product" not in context:
	# 		self.create_variant_ids(cr, uid, [product_template_id], context=context)
	# 	self._set_standard_price(cr, uid, product_template_id, vals.get('standard_price', 0.0), context=context)
	#
	# 	# TODO: this is needed to set given values to first variant after creation
	# 	# these fields should be moved to product as lead to confusion
	# 	related_vals = {}
	# 	if vals.get('ean13'):
	# 		related_vals['ean13'] = vals['ean13']
	# 	if vals.get('default_code'):
	# 		related_vals['default_code'] = vals['default_code']
	# 	if related_vals:
	# 		self.write(cr, uid, product_template_id, related_vals, context=context)
	#
	# 	return product_template_id

	# @api.multi
	# def write(self, vals):
	# 	print "ggggggggggggggggggggggggggggg",vals
	# 	res = super(product_template, self).write(vals)
	# 	for rec in self:
	# 		return res
	# 	# code = ''
	# 	# if vals:
	# 	# 	for rec in self:
	# 	# 		print "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",rec.default_code
	# 	# 		if rec.default_code ==False:
	# 	# 			# if vals.get('categ_id', False) or rec.categ_id:
	# 	# 			# 	if vals.get('categ_id', False):
	# 	# 			# 		category = self.env['product.category'].browse(vals.get('categ_id', False))
	# 	# 			# 	else:
	# 	# 			# 		category = rec.categ_id
	# 	# 			# 	category.product_sequence += 1
	# 	# 			# 	code = category.product_category_code + '-' + str(category.product_sequence)
	# 	# 			vals.update({'default_code': code})




	@api.multi
	@api.depends('standard_price','qty_available')
	def _compute_inventory_value(self):
		for line in self:
			line.inventory_value = line.standard_price * line.qty_available

	@api.multi
	@api.depends('name')
	def _compute_total_in_qty(self):
		cr = self._cr
		uid = self._uid
		context = self._context
		user = self.pool.get('res.users').browse(cr, uid, uid, context)
		warehouse = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', user.company_id.id)], limit=1, context=context)
		loc_id = self.env['stock.warehouse'].search([('id','=',warehouse[0])]).lot_stock_id
		for line in self:
			line.qty_in = 0.0
			moves = self.env['stock.move'].search([('location_dest_id','=',loc_id.id),('product_id','=',line.id),('state','=','done')])
			for move in moves:
				line.qty_in += move.product_uom_qty

	show_cost_variation = fields.Boolean('Show Cost Variations', default=False)
	cost_table_id = fields.One2many('product.cost.table','product_id', 'Cost Variations')
	old_price = fields.Float('Old Price')
	inventory_value = fields.Float(compute='_compute_inventory_value', string="Inventory Value")
	temp_remain = fields.Float('Qty')
	process_ok = fields.Boolean('Process')
	qty_in = fields.Float(compute='_compute_total_in_qty', string="Qty IN")
	allocation_no = fields.Char('Allocation No')
	product_categ = fields.Many2one('pricelist.master', string="Product Category")
	total_receipts = fields.Float(string="Total Receipts")


	@api.multi
	def show_cost_variation2(self):
		for line in self:
			line.show_cost_variation = True

	@api.multi
	def hide_cost_variation(self):
		for line in self:
			line.show_cost_variation = False

	# @api.multi
	# def unlink(self):
	# 	return super(product_template, self).unlink()


class Product(models.Model):
	_inherit = 'product.product'

	def name_get(self, cr, user, ids, context=None):
		if context is None:
			context = {}
		if isinstance(ids, (int, long)):
			ids = [ids]
		if not len(ids):
			return []

		def _name_get(d):
			name = d.get('name', '')
			code = context.get('display_default_code', True) and d.get('default_code', False) or False
			if code:
				name = '[%s] %s' % (code, name)
			return (d['id'], name)

		partner_id = context.get('partner_id', False)
		if partner_id:
			partner_ids = [partner_id, self.pool['res.partner'].browse(cr, user, partner_id,
																	   context=context).commercial_partner_id.id]
		else:
			partner_ids = []

		# all user don't have access to seller and partner
		# check access and use superuser
		self.check_access_rights(cr, user, "read")
		self.check_access_rule(cr, user, ids, "read", context=context)

		result = []
		for product in self.browse(cr, SUPERUSER_ID, ids, context=context):
			variant = ", ".join([v.name for v in product.attribute_value_ids])
			name = variant and "%s (%s)" % (product.name, variant) or product.name
			sellers = []
			if partner_ids:
				sellers = filter(lambda x: x.name.id in partner_ids, product.seller_ids)
			if sellers:
				for s in sellers:
					seller_variant = s.product_name and (
							variant and "%s (%s)" % (s.product_name, variant) or s.product_name
					) or False
					mydict = {
						'id': product.id,
						 'name': seller_variant or name,
						'default_code': s.product_code or product.default_code,
					}
					result.append(_name_get(mydict))
			else:
				mydict = {
					'id': product.id,
					 'name': name,
					'default_code': product.default_code,
				}
				result.append(_name_get(mydict))
		return result

	@api.model
	def create(self, vals):
		if not vals.get('default_code', False):
			if vals.get('product_tmpl_id',False):
				templa = self.env['product.template'].browse(vals.get('product_tmpl_id',False))
				templa.categ_id.product_sequence +=1
				code = str(templa.categ_id.product_category_code) + '-'+str(templa.categ_id.product_sequence)
				vals.update({'default_code':code,
							 'type':'product'})
		res = super(Product, self).create(vals)
		return res

	@api.multi
	def write(self, vals):
		for rec in self:
			if not rec.default_code:
				categ = vals.get('categ_id') and vals.get('categ_id') or rec.categ_id.id
				if categ:
					category = self.env['product.category'].browse(categ)
					category.product_sequence += 1
					code = category.product_category_code or '' + '-' + str(category.product_sequence)
					vals.update({'type':'product','default_code': code})
		res = super(Product, self).write(vals)

		return res

class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'

	def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
			partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
			name=False, price_unit=False, state='draft', context=None):
		"""
		onchange handler of product_id.
		"""
		if context is None:
			context = {}
		res = {'value': {'expected_rate': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
		if not product_id:
			if not uom_id:
				uom_id = self.default_get(cr, uid, ['product_uom'], context=context).get('product_uom', False)
				res['value']['product_uom'] = uom_id
			return res
		product_product = self.pool.get('product.product')
		product_uom = self.pool.get('product.uom')
		res_partner = self.pool.get('res.partner')
		product_pricelist = self.pool.get('product.pricelist')
		account_fiscal_position = self.pool.get('account.fiscal.position')
		account_tax = self.pool.get('account.tax')
		context_partner = context.copy()
		if partner_id:
			lang = res_partner.browse(cr, uid, partner_id).lang
			context_partner.update( {'lang': lang, 'partner_id': partner_id} )
		product = product_product.browse(cr, uid, product_id, context=context_partner)
		#call name_get() with partner in the context to eventually match name and description in the seller_ids field
		if not name or not uom_id:
			# The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
			dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
			if product.description_purchase:
				name += '\n' + product.description_purchase
			res['value'].update({'name': name})
		# - set a domain on product_uom
		res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}
		# - check that uom and product uom belong to the same category
		product_uom_po_id = product.uom_po_id.id
		if not uom_id:
			uom_id = product_uom_po_id
		if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
			if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
				res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
			uom_id = product_uom_po_id
		res['value'].update({'product_uom': uom_id})
		# - determine product_qty and date_planned based on seller info
		if not date_order:
			date_order = fields.datetime.now()
		supplierinfo = False
		precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
		for supplier in product.seller_ids:
			if partner_id and (supplier.name.id == partner_id):
				supplierinfo = supplier
				if supplierinfo.product_uom.id != uom_id:
					res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
				min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
				if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
					if qty:
						res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
					qty = min_qty
		dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		qty = qty or False
		res['value'].update({'date_planned': date_planned or dt})
		if qty:
			res['value'].update({'product_qty': qty})

		price = price_unit
		if price_unit is False or price_unit is None:
			if pricelist_id:
				date_order_str = datetime.datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
				price = product_pricelist.price_get(cr, uid, [pricelist_id],
						product.id, qty or False, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
			else:
				price = product.standard_price
		if uid == SUPERUSER_ID:
			company_id = self.pool['res.users'].browse(cr, uid, [uid]).company_id.id
			taxes = product.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id)
		else:
			taxes = product.supplier_taxes_id
		fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
		taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes, context=context)
		price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, product.supplier_taxes_id, taxes_ids)
		res['value'].update({'expected_rate': price, 'taxes_id': taxes_ids})
		return res

	@api.multi
	@api.depends('price_subtotal','taxes_id','product_id','required_qty','expected_rate')
	def compute_gst_tax(self):
		for line in self:
			line.gst_tax=0.0
			line.igst_tax=0.0
			taxi = 0
			taxe = 0
			if line.taxes_id:
				for tax in line.taxes_id:
					if tax.child_ids:
						for child in tax.child_ids:
							if child.price_include == True:
								taxi += child.amount
							else:
								taxe += child.amount
							if child.tax_type == 'sgst':
								line.sgst_tax += line.price_subtotal*child.amount
							if child.tax_type == 'cgst':
								line.cgst_tax += line.price_subtotal*child.amount
							if child.tax_type == 'igst':
								line.igst_tax += line.price_subtotal*child.amount
					else:
						if tax.price_include == True:
								taxi += tax.amount
						else:
							taxe += tax.amount
						if tax.tax_type == 'cgst':
							line.cgst_tax += line.price_subtotal*tax.amount
						if tax.tax_type == 'sgst':
							line.sgst_tax += line.price_subtotal*tax.amount
						if tax.tax_type == 'igst':
							line.igst_tax += line.price_subtotal*tax.amount
			line.tax_amount = line.price_subtotal*(taxe+taxi)
			line.total = line.price_subtotal + line.tax_amount

	pro_old_price = fields.Float(related='product_id.standard_price', store=True, string='Previous Unit Price')
	task_id = fields.Many2one('project.task', 'Task')
	location_id = fields.Many2one(related='task_id.project_id.location_id', store=True, string='Location')
	account_id = fields.Many2one('account.account', 'Account', domain=[('type', 'not in', ['view', 'closed', 'consolidation'])])
	date_planned = fields.Date('Scheduled Date', required=False, select=True)
	checked_qty = fields.Boolean('Is Checked Arrived Qty', default=False)
	gst_tax = fields.Float(compute='compute_gst_tax', string="GST Tax")
	igst_tax = fields.Float(compute='compute_gst_tax', string="IGST Tax")
	cgst_tax = fields.Float(compute='compute_gst_tax', string="CGST Tax")
	sgst_tax = fields.Float(compute='compute_gst_tax', string="SGST Tax")
	site_purchase_id = fields.Many2one('site.purchase')
	required_qty = fields.Float('Qty')
	expected_rate = fields.Float('Rate')
	tax_amount = fields.Float(compute='compute_gst_tax', string='Tax Amount')
	total = fields.Float(compute='compute_gst_tax', string='Total')
	price_unit = fields.Float('Unit Price', required=False, digits_compute= dp.get_precision('Product Price'))
	product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=False)
	received_qty = fields.Float("Rejected Quantity")
	po_name = fields.Char('Order No',related ='order_id.name')
	supplier_id = fields.Many2one(string ="Supplier",related ="order_id.partner_id")
	project_id = fields.Many2one(string="project",related ="order_id.project_id")
	order_date = fields.Datetime(string="Date",related = "order_id.date_order")
	destination_id = fields.Many2one(string="Destination",related ="order_id.location_id")
	amount_total = fields.Float(string = 'total',related ="order_id.amount_total2")

	@api.multi
	def get_sgst(self,order_line):
		for rec in order_line:
			for tax in rec.taxes_id:
				if tax.tax_type == 'sgst':
					return rec.tax_amount
				if tax.tax_type == 'gst':
					return rec.tax_amount/2
				return 0

	@api.multi
	def get_cgst(self, order_line):
		for rec in order_line:
			for tax in rec.taxes_id:
				if tax.tax_type == 'cgst':
					return rec.tax_amount
				if tax.tax_type == 'gst':
					return rec.tax_amount / 2
				return 0

	@api.multi
	def get_igst(self, order_line):
		for rec in order_line:
			for tax in rec.taxes_id:
				if tax.tax_type == 'igst':
					return rec.tax_amount
				return 0
class stock_history(models.Model):
	_inherit = 'stock.history'

	uom_id = fields.Many2one(related='product_id.uom_id', string="Unit")
	quantity  =fields.Float('Product Quantity',digits=(6,3))


class res_partner(models.Model):
	_inherit = 'res.partner'

	@api.multi
	@api.depends('project_ids')
	def _count_projects(self):
		for line in self:
			line.project_count = 0
			for lines in line.project_ids:
				line.project_count+=1

	@api.one
	@api.onchange('project_ids')
	def onchange_project_ids(self):
		if self.project_ids:
			for line in self.project_ids:
				if line.project_type == 'govt':
					self.is_govt = True
				if line.project_type == 'private':
					self.is_private = True

	@api.one
	@api.onchange('is_govt','is_private')
	def onchange_type(self):
		if self.is_govt == True and self.is_private == True:
			self.project_type = 'both'
		elif self.is_govt == True and self.is_private == False:
			self.project_type = 'govt'
		elif self.is_govt == False and self.is_private == True:
			self.project_type = 'pvt'
		else:
			self.project_type = False

	family_ids = fields.One2many('res.partner.family','family_id')
	tin_no = fields.Char('GST NO', size=20)
	diesel_pump_bool = fields.Boolean(default=False)
	crusher_bool = fields.Boolean(default=False)
	cleaners_bool = fields.Boolean(default=False)
	sp_code = fields.Char('Supplier Code', size=20)
	attachment_id = fields.One2many('ir.attachment', 'partner_id', 'Attachments')
	guardian = fields.Char('guardian')
	kara = fields.Char('Kara')
	desam = fields.Char('Desam')
	village = fields.Char('Village')
	Municipality = fields.Char('Name of Municipality')
	taluk = fields.Char('Taluk')
	dist = fields.Char('District')
	age = fields.Integer('Age')
	post = fields.Char('Post')
	stage_id = fields.Many2one('project.stages', 'Customer Status')
	project_ids = fields.One2many('project.project', 'partner_id', 'Projects')
	project_count = fields.Integer(compute='_count_projects', store=True, string='No of Projects')
	contractor = fields.Boolean('Contractor')
	account_receivable = fields.Many2one(related='property_account_receivable', string='Account Receivable', store=True)
	account_payable = fields.Many2one(related='property_account_receivable', string='Account Payable', store=True)
	tds_applicable = fields.Boolean(default=False,string='TDS Applicable')
	tender_contractor = fields.Boolean("Tender Contractor")
	shipping_location = fields.Boolean("Shipping Location" ,default=False)

class stock_picking(models.Model):
	_inherit="stock.picking"

	_order = 'date desc'

	@api.multi
	def unlink(self):
		#on picking deletion, cancel its move then unlink them too
		move_obj = self.env['stock.move']
#         context = context or {}
		for pick in self:
			move_ids = [move.id for move in pick.move_lines]
			move_obj.action_cancel()
			move_obj.unlink()
			packs = self.env['stock.pack.operation'].search([('picking_id','=',pick.id)])
			for pack in packs:
				pack.unlink()
		return super(stock_picking, self).unlink()

	@api.onchange('picking_type_id')
	def onchange_picking_type(self):
		if self.picking_type_id:
			self.source_location_id = self.picking_type_id.default_location_dest_id.id

	@api.multi
	@api.depends('move_lines')
	def _compute_is_stock_receipts(self):
		cr = self._cr
		uid = self._uid
		context = self._context
		user = self.pool.get('res.users').browse(cr, uid, uid, context)
		warehouse = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', user.company_id.id)], limit=1, context=context)
		loc_id = self.env['stock.warehouse'].search([('id','=',warehouse[0])]).lot_stock_id
		for line in self:
			is_stock_reciept = False
			for move in line.move_lines:
				is_stock_reciept = False
				if move.location_dest_id.id == loc_id.id:
					is_stock_reciept = True
			line.is_stock_reciept = is_stock_reciept

	@api.multi
	@api.depends('move_lines')
	def _compute_inventory_value(self):

		for line in self:
			for lines in line.move_lines:
				line.inventory_value+=lines.inventory_value

	def _state_get(self, cr, uid, ids, field_name, arg, context=None):
		'''The state of a picking depends on the state of its related stock.move
			draft: the picking has no line or any one of the lines is draft
			done, draft, cancel: all lines are done / draft / cancel
			confirmed, waiting, assigned, partially_available depends on move_type (all at once or partial)
		'''
		res = {}
		for pick in self.browse(cr, uid, ids, context=context):
			if (not pick.move_lines) or any([x.state == 'draft' for x in pick.move_lines]):
				res[pick.id] = 'draft'
				continue
			if all([x.state == 'cancel' for x in pick.move_lines]):
				res[pick.id] = 'cancel'
				continue
			if all([x.state in ('cancel', 'done') for x in pick.move_lines]):
				res[pick.id] = 'done'
				continue
			order = {'confirmed': 0, 'waiting': 1, 'assigned': 2}
			order_inv = {0: 'confirmed', 1: 'waiting', 2: 'assigned'}
			lst = [order[x.state] for x in pick.move_lines if x.state not in ('cancel', 'done')]
			if pick.move_type == 'one':
				res[pick.id] = order_inv[min(lst)]
			else:
				#we are in the case of partial delivery, so if all move are assigned, picking
				#should be assign too, else if one of the move is assigned, or partially available, picking should be
				#in partially available state, otherwise, picking is in waiting or confirmed state
				res[pick.id] = order_inv[max(lst)]
				if not all(x == 2 for x in lst):
					if any(x == 2 for x in lst):
						res[pick.id] = 'partially_available'
					else:
						#if all moves aren't assigned, check if we have one product partially available
						for move in pick.move_lines:
							if move.partially_available:
								res[pick.id] = 'partially_available'
								break
		if 'assigned' in res.values():
			res[ids[0]] = 'approve'
		return res

	def _get_pickings(self, cr, uid, ids, context=None):
		res = set()
		for move in self.browse(cr, uid, ids, context=context):
			if move.picking_id:
				res.add(move.picking_id.id)
		return list(res)

	@api.model
	def _default_journal(self):
		return self.env['account.journal'].search([('name','=','Stock Journal')], limit=1)
	@api.model
	def _default_source(self):
		return self.env['stock.location'].search([('name','=','Stock')], limit=1)

	@api.model
	def get_default_partner(self):
		return self.env['res.users'].browse(self.env.uid).partner_id

	@api.onchange('source_location_id')
	def onchange_source(self):
		if self.source_location_id:
			self.account_id = self.source_location_id.related_account.id

	source_location_id = fields.Many2one('stock.location', 'Source Location',default=_default_source)
	journal_id = fields.Many2one('account.journal',string='Journal', default=_default_journal)
	account_id = fields.Many2one('account.account', 'Account')
	min_date = fields.Datetime(default=lambda self: fields.datetime.now(), states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, string='Scheduled Date', select=1, help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.", track_visibility='onchange')
	task_id = fields.Many2one('project.task', string="Related task")
	is_task_related = fields.Boolean('Related to task')
	is_other_move = fields.Boolean('Other Move')
	is_eng_request = fields.Boolean('Engineer Request')
	is_stock_reciept = fields.Boolean(compute='_compute_is_stock_receipts', store=True, string='Stock Receipt', default=False)
	inventory_value = fields.Float(compute='_compute_inventory_value', string='Inventory Value')
	changed_to_allocation = fields.Boolean('Changed To Allocation', default=False)
	request_user = fields.Many2one('res.users', 'Requested By')
	is_purchase = fields.Boolean('Is From Purchase', default=False)
	purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
	picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=False)
	partner_id = fields.Many2one('res.partner', 'Partner', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=get_default_partner)
	returned_move_ids = fields.One2many('stock.move','returned_id', string="Returned Products")
	project_id = fields.Many2one('project.project',string="Project")
	request_id = fields.Many2one('site.purchase', 'Request')

	_columns = {
		'state': old_fields.function(_state_get, type="selection", copy=False,
			store={
					'stock.picking': (lambda self, cr, uid, ids, ctx: ids, ['move_type'], 20),
					'stock.move': (_get_pickings, ['state', 'picking_id', 'partially_available'], 20)},
			selection=[
				('draft', 'Draft'),
				('cancel', 'Cancelled'),
				('waiting', 'Waiting Another Operation'),
				('confirmed', 'Waiting Availability'),
				('partially_available', 'Partially Available'),
				('approve', 'Waiting for approval'),
				('assigned', 'Ready to Transfer'),
				('done', 'Transferred'),
				('partial_returned', 'Partially Returned'),
				('returned', 'Returned'),
				], string='Status', readonly=True, select=True, track_visibility='onchange',
			help="""
				* Draft: not confirmed yet and will not be scheduled until confirmed\n
				* Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
				* Waiting Availability: still waiting for the availability of products\n
				* Partially Available: some products are available and reserved\n
				* Ready to Transfer: products reserved, simply waiting for confirmation.\n
				* Transferred: has been processed, can't be modified or cancelled anymore\n
				* Cancelled: has been cancelled, can't be confirmed anymore"""
		),
	}

	_defaults = {
		'request_user': lambda self, cr, uid, ctx=None: uid,
		}

	@api.multi
	def approve_picking(self):
		sql = ('UPDATE stock_picking '
				'SET state={} '
				'WHERE id={}').format('\'assigned\'', self[0].id)
		self.env.cr.execute(sql)

	@api.multi
	def set_to_draft(self):
		sql = ('UPDATE stock_picking '
				'SET state={} '
				'WHERE id={}').format('\'draft\'', self[0].id)
		self.env.cr.execute(sql)
		sql = ('UPDATE stock_move '
				'SET state={} '
				'WHERE picking_id={}').format('\'draft\'', self[0].id)
		self.env.cr.execute(sql)

	def action_confirm(self, cr, uid, ids, context=None):
		todo = []
		todo_force_assign = []
		for picking in self.browse(cr, uid, ids, context=context):
			if picking.location_id.usage in ('supplier', 'inventory', 'production'):
				todo_force_assign.append(picking.id)
			for r in picking.move_lines:
				if r.state == 'draft':
					todo.append(r.id)
			if picking.is_eng_request == True:
				picking.changed_to_allocation = True
		if len(todo):
			self.pool.get('stock.move').action_confirm(cr, uid, todo, context=context)
		if todo_force_assign:
			self.force_assign(cr, uid, todo_force_assign, context=context)
		allow = True
		for line in self.browse(cr, uid, ids[0], context=context).move_lines:
			if line.allow_to_request == False:
				allow = False
		if allow == False:
			raise osv.except_osv(_('Warning!'),
						_('You cannot request until the extra demand for products are approved.'))
		return True

	@api.model
	def get_move_line(self, picking_id):
		return self.env['stock.picking'].browse(picking_id).move_lines

	def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
		res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		if view_type == 'form':
			doc = etree.XML(res['arch'])
			for sheet in doc.xpath("//sheet"):
				parent = sheet.getparent()
				index = parent.index(sheet)
				for child in sheet:
					parent.insert(index, child)
					index += 1
				parent.remove(sheet)
			res['arch'] = etree.tostring(doc)
		return res

	@api.multi
	def open_purchase_order(self):
		self.ensure_one()
		record =  self.env['purchase.order'].search([('name','=',self.origin)])
		context = self._context.copy()
		if record:
			res_id = record[0].id
		else:
			res_id = False
		return {
			'name':'Purchase Order view',
			'view_type': 'form',
			'view_mode':'form',
			'views' : [(False,'form')],
			'res_model':'purchase.order',
			'view_id':'purchase_order_form_changed',
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'context':context,
		}

	# @api.multi
	# def action_account_move_create(self):
	#   move = self.env['account.move']
	#   move_line = self.env['account.move.line']
	#   for line in self:
	#       values = {
	#           'journal_id': self.journal_id.id,
	#           'date': self.min_date,
	#           }
	#       move_id = move.create(values)
	#       inventory_value = 0
	#       name = ""
	#       move_list = []
	#       for lines in line.move_lines:
	#           entry_list = filter(lambda x: x['account_id'] == lines.account_id.id, move_list)
	#           if len(entry_list) == 0:
	#               move_list.append({'account_id':lines.account_id.id, 'debit': lines.inventory_value, 'credit': 0, 'move_id': move_id.id, 'name': 'Stock Movement ' + lines.product_id.categ_id.name,})
	#           if len(entry_list) != 0:
	#                               a = move_list.index(entry_list[0])
	#                               move_list[a]['debit'] += lines.inventory_value
	#                               move_list[a]['credit'] += 0
	#                               if lines.product_id.categ_id.name not in move_list[a]['name']:
	#                                   move_list[a]['name'] += ', ' + lines.product_id.categ_id.name
	#           entry_list = filter(lambda x: x['account_id'] == line.account_id.id, move_list)
	#           if len(entry_list) == 0:
	#               move_list.append({'account_id':line.account_id.id, 'debit': 0, 'credit': lines.inventory_value, 'move_id': move_id.id, 'name': 'Stock Movement ' + lines.product_id.categ_id.name,})
	#           if len(entry_list) != 0:
	#                               a = move_list.index(entry_list[0])
	#                               move_list[a]['debit'] += 0
	#                               move_list[a]['credit'] += lines.inventory_value
	#                               if lines.product_id.categ_id.name not in move_list[a]['name']:
	#                                   move_list[a]['name'] += ', ' + lines.product_id.categ_id.name
	#       for entry_line in move_list:
	#           line_id = move_line.create(entry_line)
	#       move_id.button_validate()

	@api.cr_uid_ids_context
	def do_enter_transfer_details(self, cr, uid, picking, context=None):
		for line in self.pool.get('stock.picking').browse(cr, uid, picking):
			if not line.date_done:
				raise osv.except_osv(('Warning!'), ('Please Enter Date of Transfer'))
		if not context:
			context = {}
		else:
			context = context.copy()
		context.update({
			'active_model': self._name,
			'active_ids': picking,
			'active_id': len(picking) and picking[0] or False
		})

		created_id = self.pool['stock.transfer_details'].create(cr, uid, {'picking_id': len(picking) and picking[0] or False}, context)
		return self.pool['stock.transfer_details'].wizard_view(cr, uid, created_id, context)

class stock_move(models.Model):
	_inherit="stock.move"
	extra_quantity = 0

	@api.onchange('product_id','location_id','product_uom_qty')
	def onchange_pro_id(self):
		if self.product_id:
			self.location_id = self.picking_id.source_location_id.id
			self.product_uom = self.product_id.uom_id.id
			self.name = self.product_id.name
			product = self.env['product.product'].search([('id','=',self.product_id.id)])
			self.available_qty = product.with_context({'location' : self.picking_id.source_location_id.id}).qty_available
			if self.product_id.product_tmpl_id.track_product == True:
				if self.product_uom_qty > self.available_qty:
					self.product_uom_qty = self.available_qty
					return {
								'warning': {
									'title': 'Warning',
									'message': "Not Much Available Qty For This Product"
								}
							}
				qty = 0
				price_unit = 0
				if self.product_id and self.location_id and self.product_uom_qty:
					qty = self.product_uom_qty
					rec = self.env['product.price.data'].search([('site_id','=',self.location_id.id),('product_id','=',self.product_id.id)], order='date asc')
					for val in rec:
						if qty != 0:
							if qty <= val.qty:
								price_unit += qty * val.rate
								qty = 0
							else:
								price_unit += val.qty * val.rate
								qty = qty - val.qty
					self.price_unit = price_unit/self.product_uom_qty
			else:
				self.price_unit = self.product_id.standard_price

	def _default_location_destination(self, cr, uid, context=None):
		pass

	def _default_destination_address(self, cr, uid, context=None):
		return False

	def _default_group_id(self, cr, uid, context=None):
		context = context or {}
		if context.get('default_picking_id', False):
			picking = self.pool.get('stock.picking').browse(cr, uid, context['default_picking_id'], context=context)
			return picking.group_id.id
		return False

	_defaults = {
		'location_dest_id': _default_location_destination,
		'partner_id': _default_destination_address,
		'state': 'draft',
		'priority': '1',
		'product_uom_qty': 1.0,
		'scrapped': False,

		'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.move', context=c),

		'procure_method': 'make_to_stock',
		'propagate': True,
		'partially_available': False,
		'group_id': _default_group_id,
	}

	@api.onchange('project_id','task_id')
	def _onchange_project(self):
		product_ids = []
		task_ids = []
		domain = {}
		if self.project_id and not self.task_id:
			for estimation in self.env['project.task.estimation'].search([('project_id','=',self.project_id.id)]):
				if estimation.pro_id.id not in product_ids:
					product_ids.append(estimation.pro_id.id)
			domain['product_id'] = [('id','in',product_ids)]
		if self.project_id.id:
			self.location_dest_id = self.project_id.location_id
			task_ids = [task.id for task in self.env['project.task'].search([('project_id','=',self.project_id.id)])]
			domain['task_id'] = [('id','in',task_ids)]
		return {
			'domain': domain
		}

	@api.onchange('task_id')
	def _onchange_product_selection(self):
		if self.task_id.id != False:
			product_ids = [estimate.pro_id.id for estimate in self.task_id.estimate_ids]
			self.location_dest_id = self.task_id.project_id.location_id
			return {
				'domain': {
					'product_id': [('id','in',product_ids)]
				},
			}

	@api.onchange('product_uom_qty')
	def _onchange_product_uom_qty(self):
		super(stock_move, self).onchange_quantity(self.product_id.id, self.product_uom_qty, self.product_uom, self.product_uos)
		estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
		if not len(estimate):
			return
		if (estimate[0].qty - self.product_uom_qty)<0:
			stock_move.extra_quantity = (self.product_uom_qty-estimate[0].qty)
			self.product_uom_qty = estimate[0].qty
			self.is_request_more_btn_visible = True
			return {
				'warning': {
					'title': 'Warning',
					'message': "Quantity cannot be greater than the quantity assigned for the task. Please increase the quantity from the task."
				}
			}

	@api.onchange('location_dest_id')
	def onchange_location_dest_id(self):
		if self.location_dest_id:
			self.account_id = self.location_dest_id.related_account

	@api.multi
	@api.depends('product_id','product_uom_qty','price_unit')
	def _compute_inventory_value(self):
		for line in self:
			line.inventory_value = line.price_unit * line.product_uom_qty

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1
		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			for line_rec in first_line_rec.picking_id.move_lines:
				line_rec.line_no = line_num
				line_num += 1

	line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
	is_request_more_btn_visible = fields.Boolean(default=False)
	is_task_related = fields.Boolean(related='picking_id.is_task_related', string='Related to task')
	task_id = fields.Many2one('project.task', string="Related Task")
	inventory_value = fields.Float(compute='_compute_inventory_value', string='Inventory Value')
	available_qty = fields.Float(string='Available Qty')
	allow_to_request = fields.Boolean('Allow To Request', default=True)
	project_id = fields.Many2one('project.project', string="Related Project")
	asset_account_id = fields.Many2one('account.account', string='Asset Account')
	account_id = fields.Many2one('account.account', string='Account')
	is_purchase = fields.Boolean(related='picking_id.is_purchase', store=True)
	partner_stmt_id = fields.Many2one('partner.daily.statement')
	mach_collection_id = fields.Many2one('machinery.fuel.collection')
	mach_allocation_id = fields.Many2one('machinery.fuel.allocation')
	fuel_transfer_id = fields.Many2one('partner.fuel.transfer')
	returned_id = fields.Many2one('stock.picking','Returned Product')
	returned_qty = fields.Float(string="Returned Qty")

	@api.multi
	def unlink(self):
		for move in self:
			quants = self.env['stock.quant'].search([('reservation_id','=', move.id)])
			for quant in move.quant_ids:
				quant.qty = 0.0
			move.state = 'draft'
			move.product_id.product_tmpl_id.qty_available = move.product_id.product_tmpl_id.qty_available - move.product_uom_qty
			if move.picking_id:
				packs = self.env['stock.pack.operation'].search([('picking_id','=',move.picking_id.id)])
				for pack in packs:
					pack.unlink()
			return  super(stock_move, move).unlink()

	@api.multi
	def generate_prchase_order(self):
		self.ensure_one()
		view_id = self.env.ref('hiworth_construction.purchase_order_form_changed').id
		context = self._context.copy()

		order_obj = self.env['purchase.order']
		order_line_obj = self.env['purchase.order.line']
		price_list = self.env['product.pricelist'].search([('name','=','Default Purchase Pricelist')])

		order_values = {'origin': self.picking_id.name,
						'date_order': self.date,
						 'location_id': self.location_id.id,
						'state': 'draft',
						'minimum_planned_date': self.picking_id.min_date,
						'pricelist_id': price_list.id,
				   }
		order_id = order_obj.create(order_values)
		order_line_values = {'product_id': self.product_id.id,
							 'name': self.product_id.name,
							  'price_unit': self.product_id.standard_price,
							  'product_qty': self.product_uom_qty,
							  'date_planned': self.picking_id.min_date,
							  'order_id': order_id.id }
		line_id = order_line_obj.create(order_line_values)
		context = {'related_usage': False,}
		return {
			'name':'Purchase Requisition',
			'view_type':'form',
			'view_mode':'tree',
			'views' : [(view_id, 'form')],
			'res_model':'purchase.order',
			'view_id':view_id,
			'type':'ir.actions.act_window',
			'res_id':order_id.id,
			'context':context,
			}

	@api.multi
	def request_more_task_qty(self):
		return {
			'type': 'ir.actions.act_window',
			'id': 'test_id_act',
			'res_model': 'estimate.quantity.extra.request',
			'views': [[self.env.ref("hiworth_construction.estimate_quantity_extra_request_popup").id, "form"]],
			'target': 'new',
			'name': 'Send extra request',
			'context': {
				'default_task_id': self.picking_id.task_id.id,
				'default_product_id': self.product_id.id,
				'default_materialrequest_id': self.picking_id.id,
				'default_quantity': stock_move.extra_quantity,
				'default_date': fields.Datetime.now(),
				'default_move_id': self.id
			}
		}

class EstimateQuantityExtraRequest(models.Model):
	_name='estimate.quantity.extra.request'

	task_id = fields.Many2one('project.task', 'Task')
	product_id = fields.Many2one('product.product', 'Product')
	materialrequest_id  = fields.Many2one('stock.picking')
	quantity = fields.Float(string="Quantity")
	date = fields.Date()
	move_id = fields.Many2one('stock.move', 'Stock Move')

	state = fields.Selection([
		('draft', 'Draft'),
		('rejected', 'Rejected'),
		('approved', 'Approved'),
		],default='draft')

	@api.multi
	def extra_request_approve(self):
		self.ensure_one()
		estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
		if estimate:
			estimate[0].qty = estimate[0].qty+self.quantity
		self.state = 'approved'
		self.move_id.allow_to_request = True

	@api.multi
	def extra_request_reject(self):
		self.ensure_one()
		self.state = 'rejected'

	@api.multi
	def write(self,vals):
		if self.move_id.id != False:
			self.move_id.is_request_more_btn_visible = False
			self.move_id.allow_to_request = False
		super(EstimateQuantityExtraRequest, self).write(vals)
		return True

class res_groups(models.Model):
	_inherit = 'res.groups'

	company_group = fields.Boolean('Company Group')


class product_category(models.Model):
	_inherit = 'product.category'

	stock_account_id = fields.Many2one('account.account', 'Asset Account', domain=[('type','not in', ['view','consolidation', 'closed'])])


# class stock_return_picking(models.TransientModel):
#   _inherit = 'stock.return.picking'
#
#   def _create_returns(self, cr, uid, ids, context=None):
#       res,res1 = super(stock_return_picking, self)._create_returns(cr, uid, ids, context=None)
#       return res,res1

class SubData(models.Model):
	_name = 'sub.data'

	name = fields.Many2one('name.of.work', string="Name of Work")
	categ_id = fields.Many2one('task.category', string="Category")
	note = fields.Text(string="Description")
	unit = fields.Many2one('product.uom', string="Unit")
	amt = fields.Float(string="Amount", compute="_compute_amt")

	project_id = fields.Many2one('project.project', string="Project")
	project_id2 = fields.Many2one(related='sub_id.project_id', string='Project')
	subdata_ids = fields.One2many('sub.data.line', 'subdata_id')
	sub_id = fields.Many2one('main.data', string="Data")


	@api.multi
	@api.onchange('name')
	def onchange_name(self):
		datas = []
		res = {}
		for value in self:
			if value.name:
				data = self.env['sub.data.master'].search([('name','=',value.name.id)],limit=1)
				self.note = data.note or ''
				self.unit = data.unit.id or False
				self.categ_id = data.categ_id.id or False
				self.amt = data.amt or 0.0
				for val in data.subdata_ids:
					res = {
							'item_id':val.item_id.id or False,
							'qty':val.qty or 0.0,
							'unit':val.unit.id or False,
							}
					datas.append(res)
				value.subdata_ids = datas

	@api.one
	@api.depends('subdata_ids.amt')
	def _compute_amt(self):
		amt = 0.0
		for val in self.subdata_ids:
			amt += val.amt

		self.amt = amt


class SubDataLine(models.Model):
	_name = 'sub.data.line'

	subdata_id = fields.Many2one('sub.data', string="Sub Data")

	item_id = fields.Many2one('pricelist.master', string="Items")
	qty = fields.Float(string="Quantity")
	unit = fields.Many2one('product.uom', string="Unit")
	rate = fields.Float(string="Item Rate", compute="_compute_rate")
	amt = fields.Float(string="Amount", compute="_compute_amt")


	@api.one
	@api.depends('subdata_id')
	def _compute_rate(self):
		if self.item_id and self.subdata_id.project_id:
			price = self.env['pricelist.pricelist'].search([('pricelist_id','=',self.subdata_id.project_id.id),('item_id','=',self.item_id.id)])
			self.rate = price.sale_rate

		if self.item_id and self.subdata_id.project_id2:
			price = self.env['pricelist.pricelist'].search([('pricelist_id','=',self.subdata_id.project_id2.id),('item_id','=',self.item_id.id)])
			self.rate = price.sale_rate


	@api.one
	@api.depends('qty','rate')
	def _compute_amt(self):
		if self.qty and self.rate:
			self.amt = self.rate * self.qty


class PricelistMaster(models.Model):
	_name = 'pricelist.master'
	_rec_name = 'item_id'


	@api.one
	@api.depends('purchase_rate','gst_percent','margin_percent')
	def _compute_sale_rate(self):
		self.sale_rate = self.purchase_rate + (self.purchase_rate * (self.gst_percent/100)) + (self.purchase_rate * (self.margin_percent/100))

	item_id = fields.Char(string="Item Name")
	categ_id = fields.Many2one('task.category', string="Category")
	purchase_rate = fields.Float(string="Purchase Price")
	gst_percent = fields.Float(string="GST %")
	unit = fields.Many2one('product.uom', string="Unit")
	margin_percent = fields.Float(string="Margin %")
	sale_rate = fields.Float(string="Sale Price", compute="_compute_sale_rate")


class Pricelist(models.Model):
	_name = 'pricelist.pricelist'
	_rec_name = 'item_id'


	@api.one
	@api.depends('purchase_rate','gst_percent','margin_percent')
	def _compute_sale_rate(self):
		self.sale_rate = self.purchase_rate + (self.purchase_rate * (self.gst_percent/100)) + (self.purchase_rate * (self.margin_percent/100))


	pricelist_id = fields.Many2one('project.project', string="Project")

	item_id = fields.Many2one('pricelist.master', string="Item Name")
	categ_id = fields.Many2one('task.category', string="Category")
	purchase_rate = fields.Float(string="Purchase Price")
	gst_percent = fields.Float(string="GST %")
	unit = fields.Many2one('product.uom', string="Unit")
	margin_percent = fields.Float(string="Margin %")
	sale_rate = fields.Float(string="Sale Price", compute='_compute_sale_rate')


class product_template(models.Model):
	_inherit = "product.template"

	gst_percent = fields.Float(string="GST %(Sale)")
	margin_percent = fields.Float(string="Margin %")
	part_no = fields.Char('PartNo/Specification')


class name_of_work(models.Model):
	_name = "name.of.work"


	name = fields.Char(string="Name of Work")


class MainData(models.Model):
	_name = 'main.data'

	@api.multi
	@api.depends('data_ids','sub_ids')
	def _compute_amt(self):
		data_tot = 0.0
		sub_tot = 0.0
		for value in self:
			if value.data_ids:
				for val in value.data_ids:
					data_tot += val.amt
			if value.sub_ids:
				for val in value.sub_ids:
					sub_tot += val.amt
			value.amt = data_tot + sub_tot


	name = fields.Many2one('item.of.work', string="Name of Work")
	categ_id = fields.Many2one('task.category', string="Category")
	note = fields.Text(string="Description")
	unit = fields.Many2one('product.uom', string="Unit")
	amt = fields.Float(string="Amount", compute='_compute_amt')

	project_id = fields.Many2one('project.project', string="Project")
	data_ids = fields.One2many('main.data.line', 'data_id', string="Data Info")
	sub_ids = fields.One2many('sub.data', 'sub_id', string="Sub Data")

	# boq_id =fields.Many2one('boq.quotation.master')

	@api.onchange('name')
	def onchange_name(self):
		datas = []
		res = {}
		sub = []
		dict1 = {}
		line = {}
		if self.name:
			data = self.env['main.data.master'].search([('name','=',self.name.id)])
			self.note = data.note or ''
			self.unit = data.unit.id or False
			self.categ_id = data.categ_id.id or False
			self.amt = data.amt or 0.0
			if data.data_ids:
				for val in data.data_ids:
					res = {
							'item_id':val.item_id.id or False,
							'qty':val.qty or 0.0,
							'unit':val.unit.id or False,
							}
					datas.append(res)

				self.data_ids = datas

			if data.sub_ids:
				for value in data.sub_ids:
					sub_line = []
					for val in value.subdata_ids:
						line = {
								'item_id':val.item_id.id or False,
								'qty':val.qty or 0.0,
								'unit':val.unit.id or False,
							}
						sub_line.append(line)

					dict1 = {
							'name':value.name.id,
							'categ_id':value.categ_id.id,
							'note':value.note,
							'unit':value.unit.id,
							'subdata_ids':sub_line,
							}
					sub.append(dict1)

				self.sub_ids = sub

class MainDataLine(models.Model):
	_name = 'main.data.line'

	@api.one
	@api.depends('qty','rate')
	def _compute_amt(self):
		if self.qty and self.rate:
			self.amt = self.rate * self.qty


	@api.one
	@api.depends('data_id.project_id')
	def _compute_rate(self):
		if self.item_id and self.data_id.project_id:
			price = self.env['pricelist.pricelist'].search([('pricelist_id','=',self.data_id.project_id.id),('item_id','=',self.item_id.id)])
			self.rate = price.sale_rate


	data_id = fields.Many2one('main.data', string="Data")

	item_id = fields.Many2one('pricelist.master', string="Items")
	qty = fields.Float(string="Quantity")
	unit = fields.Many2one('product.uom', string="Unit")
	rate = fields.Float(string="Item Rate", compute='_compute_rate')
	amt = fields.Float(string="Amount", compute='_compute_amt')


class MainDataMaster(models.Model):
	_name = 'main.data.master'

	name = fields.Many2one('item.of.work', string="Name of Work")
	categ_id = fields.Many2one('task.category', string="Category")
	note = fields.Text(string="Description")
	unit = fields.Many2one('product.uom', string="Unit")
	amt = fields.Float(string="Amount")

	data_ids = fields.One2many('main.data.line.master', 'data_id', string="Data Info")
	sub_ids = fields.One2many('sub.data.master', 'sub_id', string="Sub Data")


class MainDataLineMaster(models.Model):
	_name = 'main.data.line.master'

	data_id = fields.Many2one('main.data.master', string="Data")

	item_id = fields.Many2one('pricelist.master', string="Items")
	qty = fields.Float(string="Quantity")
	unit = fields.Many2one('product.uom', string="Unit")
	rate = fields.Float(string="Item Rate")
	amt = fields.Float(string="Amount")

class SubDataMaster(models.Model):
	_name = 'sub.data.master'

	name = fields.Many2one('name.of.work', string="Name of Work")
	categ_id = fields.Many2one('task.category', string="Category")
	note = fields.Text(string="Description")
	unit = fields.Many2one('product.uom', string="Unit")
	amt = fields.Float(string="Amount")
	subdata_ids = fields.One2many('sub.data.line.master', 'subdata_id')
	sub_id = fields.Many2one('main.data.master', string="Data")


	@api.onchange('name')
	def onchange_name(self):
		datas = []
		res = {}
		if self.name:
			data = self.env['sub.data.master'].search([('name','=',self.name.id)],limit=1)
			self.note = data.note or ''
			self.unit = data.unit.id or False
			self.categ_id = data.categ_id.id or False
			self.amt = data.amt or 0.0
			for val in data.subdata_ids:
				res = {
						'item_id':val.item_id.id or False,
						'qty':val.qty or 0.0,
						'unit':val.unit.id or False,
						}
				datas.append(res)
			self.subdata_ids = datas

class SubDataLineMaster(models.Model):
	_name = 'sub.data.line.master'

	subdata_id = fields.Many2one('sub.data.master', string="Sub Data")
	item_id = fields.Many2one('pricelist.master', string="Items")
	qty = fields.Float(string="Quantity")
	unit = fields.Many2one('product.uom', string="Unit")
	rate = fields.Float(string="Item Rate")
	amt = fields.Float(string="Amount")

class EstimateQuantityExtraRequest(models.Model):
	_name='estimate.quantity.extra.request'

	task_id = fields.Many2one('project.task', 'Task')
	product_id = fields.Many2one('product.product', 'Product')
	materialrequest_id  = fields.Many2one('stock.picking')
	quantity = fields.Float(string="Quantity")
	date = fields.Date()
	move_id = fields.Many2one('stock.move', 'Stock Move')
	state = fields.Selection([
		('draft', 'Draft'),
		('rejected', 'Rejected'),
		('approved', 'Approved'),
		],default='draft')

	@api.multi
	def extra_request_approve(self):
		self.ensure_one()
		estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
		if estimate:
			estimate[0].qty = estimate[0].qty+self.quantity
		self.state = 'approved'
		self.move_id.allow_to_request = True

	@api.multi
	def extra_request_reject(self):
		self.ensure_one()
		self.state = 'rejected'

	@api.multi
	def write(self,vals):
		if self.move_id.id != False:
			self.move_id.is_request_more_btn_visible = False
			self.move_id.allow_to_request = False
		super(EstimateQuantityExtraRequest, self).write(vals)
		return True


class QualityControl(models.Model):
	_name = 'quality.control'

	project_id = fields.Many2one('project.project', string="Project")

	name = fields.Char(string="Description")
	checked = fields.Boolean(string="Checked")

class DetailedEstimationLine(models.Model):
	_name = "detailed.estimation.line"
	_rec_name = "name"

	@api.one
	@api.depends('nos_x', 'length', 'breadth', 'depth','nos_1','nos_2')
	def _get_qty(self):
		nos_x = self.nos_x != 0 and self.nos_x or 1
		nos_1 = self.nos_1 != 0 and self.nos_1 or 1
		nos_2 = self.nos_2 != 0 and self.nos_2 or 1
		length = self.length != 0 and self.length or 1
		aw = self.aw != 0 and self.aw or 1
		ad = self.ad != 0 and self.ad or 1
		self.qty = nos_x * length * aw * ad * nos_1 * nos_2


	@api.onchange('w1', 'w2')
	def onchange_w1_w2(self):
		if self.w1:
			self.aw = self.w1
			self.breadth = self.w1
		if self.w2:
			self.aw = self.w2
			self.breadth = self.w2
		if self.w1 and self.w2:
			self.aw = (self.w1 + self.w2)/2
			self.breadth = "("+str(self.w1)+"+"+str(self.w2)+")/2"

	@api.onchange('d1', 'd2')
	def onchange_d1_d2(self):
		if self.d1:
			self.ad = self.d1
			self.depth = self.d1
		if self.d2:
			self.ad = self.d2
			self.depth = self.d2
		if self.d1 and self.d2:
			self.ad = (self.d1 + self.d2)/2
			self.depth = "("+str(self.d1)+"+"+str(self.d2)+")/2"

	line_id = fields.Many2one('project.task.line')
	name = fields.Char(string="Description")
	side = fields.Selection([('r', 'RHS'), ('l', 'LHS'), ('bs', 'BS')],string="Side")
	chain_from = fields.Char('Chainage From')
	chain_to = fields.Char('Chainage To')
	nos_x = fields.Float(string="Nos1",digits=(6,5))
	nos_1 = fields.Float(string="Nos2",digits=(6,5))
	nos_2 = fields.Float(string="Nos3",digits=(6,5))
	length = fields.Float(string="L",digits=(6,5))
	w1 = fields.Float(string="W1",digits=(6,5))
	w2 = fields.Float(string="W2",digits=(6,5))
	aw = fields.Float(string="Avg W",digits=(6,5))
	breadth = fields.Char(string="W",digits=(6,5))
	d1 = fields.Float(string="D1",digits=(6,5))
	d2 = fields.Float(string="D2",digits=(6,5))
	ad = fields.Float(string="Avg D",digits=(6,5))
	depth = fields.Char(string="D",digits=(6,5))
	qty = fields.Float(string="Quantity", compute='_get_qty',digits=(6,5))
	task_id = fields.Many2one(string="Task")

class ResourceDetails(models.Model):
	_name = "resource.details"


	def compute_available(self):
		for rec in self:
			if rec.resource_id:
				rec.available_qty = rec.resource_id.with_context({'location_id':rec.project_id.location_id.id}).qty_available
				rec.balance_qty = rec.total_used_qty - rec.available_qty

	@api.one
	@api.depends('qty')
	def _compute_qty(self):
		if self.qty and self.task_line_id.qty:
			self.tot_qty = self.qty * self.task_line_id.qty

	@api.one
	def unlink(self):
		return super(ResourceDetails, self).unlink()

	task_line_id = fields.Many2one('project.task.line')
	resource_id = fields.Many2one('product.product', string="Resource")
	qty = fields.Float(string="Quantity")
	total_used_qty = fields.Float("Total Purchase")
	tot_qty = fields.Float(string="Total Quantity", compute='_compute_qty')
	task_id = fields.Many2one('project.task')
	project_id = fields.Many2one('project.project')
	is_editable = fields.Boolean("Is editable",default=False)
	available_qty = fields.Float("Available Quantity",compute='compute_available')
	balance_qty = fields.Float("Issued Quantity",compute='compute_available')

	@api.multi
	def action_product(self):
		for rec in self:
			stock_inventory = self.env['stock.inventory'].search([('date', '<=', fields.Datetime.now()),
																  ('location_id', '=',
																   rec.project_id.location_id.id),('state','=','done')])
			for inv in stock_inventory:
				for line in inv.line_ids:
					self.create({'resource_id':line.product_id.id,
								 'project_id':rec.project_id.id})



class ConsumptionControl(models.Model):
	_name = "consumption.control"

	@api.one
	@api.depends('qty', 'consumption_id.qty')
	def _compute_estimated_qty(self):
		if self.qty and self.consumption_id.qty:
			self.estimated_qty = self.qty * self.consumption_id.qty

	consumption_id = fields.Many2one('project.task.line')

	resource_id = fields.Many2one('pricelist.master', string="Resource")
	qty = fields.Float(string="Quantity")
	estimated_qty = fields.Float(string="Estimated Qty", compute='_compute_estimated_qty')
	uom_id = fields.Many2one('product.uom', string="Unit")
	alotted_qty = fields.Float(string="Alloted Qty")
	consumed_qty = fields.Float(string="Consumed Qty")
	task_id = fields.Many2one('project.task')


class task(models.Model):
	_inherit = "project.task"

	@api.multi
	@api.depends('estimate_ids')
	def _compute_estimated_cost(self):

		for line in self:
			if line.estimate_ids:
				line.estimated_cost = 0.0
				for lines in line.estimate_ids:
					line.estimated_cost += lines.estimated_cost_sum
			if line.task_line:
				cost = 0.0
				for val in line.task_line:
					cost += val.amt
				line.estimated_cost = cost

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1

		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			line_num = 1
			for line_rec in first_line_rec.project_id.task_ids:
				line_rec.line_no = line_num
				line_num += 1
			line_num = 1
			for line_rec in first_line_rec.project_id.extra_task_ids:
				line_rec.line_no = line_num
				line_num += 1
			line_num = 1
			for line_rec in first_line_rec.project_id.temp_tasks:
				line_rec.line_no = line_num
				line_num += 1

class product_product(models.Model):
	_inherit='product.product'

	product_categ = fields.Many2one(related='product_tmpl_id.product_categ', string="Product Category", store=True)
	part_no = fields.Char('Part No/Specification')

class QuotationQuotation(models.Model):
	_name = "quotation.quotation"

	@api.one
	@api.depends('line_ids')
	def _compute_value(self):
		amt = 0.0
		for v in self.line_ids:
			amt += v.amt
		self.value = amt

	@api.multi
	# @api.depends('bom_id')
	def _compute_estimated_cost(self):
		print "-+_+_=-=-+=-+-="
		# for line in self:
		#   for lines in line.bom_id:
		#       line.estimated_cost = lines.bom_cost

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1
		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			for line_rec in first_line_rec.project_id.categ_estimation_ids:
				line_rec.line_no = line_num
				line_num += 1

	template_id = fields.Many2one('quotation.quotation',string="Template")
	is_template = fields.Boolean(string="Is Template")
	line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No', readonly=False, default=False)
	estimated_cost = fields.Float(compute='_compute_estimated_cost', string='Estimated Cost')
	estimate_ids = fields.One2many('project.task.estimation', 'task_id', 'Estimation')
	manpower_usage_ids = fields.One2many('manpower.usage', 'usage_id', string='Manpower Usage')
	is_extra_work = fields.Boolean('Extra Work', default=False)
	extra_id = fields.Many2one('project.project')
	partner_id = fields.Many2one(related='project_id.partner_id', string='Customer')
	usage_ids1 = fields.One2many('project.task.estimation', 'task_ids1', string='Items usage')
	state = fields.Selection([
		('draft', 'Draft'),
		('approved', 'Approved'),
		('inprogress', 'In Progress'),
		('completed', 'Completed')
	], default='draft')
	sub_categ_id = fields.Many2one('task.category', 'Sub Category')
	categ_id = fields.Many2one('task.category', 'Category')
	civil_contractor = fields.Many2one('res.partner', 'Civil Contractor', domain=[('contractor', '=', True)])
	labour_report_ids = fields.One2many('project.labour.report', 'task_id')
	task_id2 = fields.Many2one('project.project', 'Project')
	task_line = fields.One2many('project.task.line', 'task_id', store=True)
	name = fields.Char(string="Name of Quotation")
	project_id = fields.Many2one('project.project', string="Name of Project")
	value = fields.Float(string="Value", compute="_compute_value")
	date = fields.Date(string="Date", default=fields.Date.today())

	partner_id = fields.Many2one('res.partner',string="Customer")
	street = fields.Char(string='Street')
	street2 = fields.Char(string='Street2')
	post = fields.Char(string='Post')
	city = fields.Char(string='City')
	state_id = fields.Many2one('res.country.state', string='State')
	zip = fields.Char(string='Zip')

	msg = fields.Html(string="Welcome Message")
	terms = fields.Html(string="Terms & Conditions")

	line_ids = fields.One2many('quotation.line','line_id', string="Quotation Details", store=True)
	@api.one
	def button_template(self):
		self.is_template = True

	@api.onchange('template_id')
	def onchange_template_id(self):
		if self.template_id:
			for val in self.template_id:
				l1 = []
				for est in val.task_line:
					l2 = []
					for detail in est.detailed_ids:
						l2.append((0, 0, {
							'name': detail.name,
							'nos_x': detail.nos_x,
							'length': detail.length,
							'breadth': detail.breadth,
							'depth': detail.depth
						}))
					l3 = []
					for resource in est.resource_ids:
						l3.append((0, 0, {
							'resource_id': resource.resource_id.id,
							'qty': resource.qty,
						}))
					l4 = []
					for cons in est.consumption_ids:
						l4.append((0, 0, {
							'resource_id': cons.resource_id.id,
							'estimated_qty': cons.estimated_qty,
							'uom_id': cons.uom_id.id,
						}))
					l1.append((0, 0, {
						'name': est.name.id,
						'category': est.category.id,
						'unit': est.unit.id,
						'note': est.note,
						'detailed_ids': l2,
						'resource_ids': l3,
						'consumption_ids': l4,
					}))
				self.name = val.name
				self.sub_categ_id = val.sub_categ_id.id or False
				self.categ_id = val.categ_id.id or False
				self.project_id = val.project_id.id or False
				self.civil_contractor = val.civil_contractor.id or False
				self.task_line = l1

	@api.multi
	def task_approve(self):
		self.ensure_one()
		self.state = 'approved'

	@api.multi
	def start_task(self):
		self.ensure_one()
		self.state = 'inprogress'

	@api.multi
	def complete_task(self):
		self.ensure_one()
		self.state = 'completed'

	@api.multi
	def reset_task(self):
		self.ensure_one()
		self.state = 'draft'



class ManpowerUsage(models.Model):
	_name = "manpower.usage"

	usage_id = fields.Many2one('project.task')

	account_id = fields.Many2one('account.account', string='Manpower')
	estimated_qty = fields.Float(string="Estimated Qty")
	assigned_qty = fields.Float(string="Assigned Qty")

	@api.multi
	@api.onchange('account_id')
	def onchange_account_id(self):
		manpower = []
		for value in self.usage_id.manpower_ids:
			manpower.append(value.account_id.id)
		return {'domain':{'account_id':[('id','in',manpower)]}}

class ResPartnerFamily(models.Model):
	_name = 'res.partner.family'

	family_id = fields.Many2one('res.partner')

	name = fields.Char(string="Name")
	relation = fields.Char(string="Relation")
	dob = fields.Date(string="DOB")
	# name = fields.Char(string="")

class QuotationLine(models.Model):
	_name = "quotation.line"
	_rec_name = "name_of_work"

	@api.multi
	@api.depends('detail_ids')
	def _compute_amt(self):
		for value in self:
			amt = 0.0
			for val in value.detail_ids:
				amt += val.amt
			value.amt = amt

	line_id = fields.Many2one('quotation.quotation')

	name_of_work = fields.Char(string="Name of Work")
	amt = fields.Float(string="Amount", compute="_compute_amt")
	estimate_id = fields.Many2one('project.task',string="Estimate")
	project_id = fields.Many2one(related='line_id.project_id')

	detail_ids = fields.One2many('quotation.items.line','detail_id', store=True)

class QuotationItemsLine(models.Model):
	_name = "quotation.items.line"
	_rec_name = "item_of_work"

	@api.one
	@api.depends('rate','qty')
	def _compute_amt(self):
		self.amt = self.rate * self.qty

	detail_id = fields.Many2one('quotation.line')
	item_of_work = fields.Many2one('project.task.line',string="Items of Work")
	desc = fields.Text(string="Description")
	qty = fields.Float(string="Quantity")
	uom_id = fields.Many2one('product.uom', string="Units")
	rate = fields.Float(string="Rate")
	amt = fields.Float(string="Amount", compute="_compute_amt")

	@api.onchange("item_of_work")
	def onchange_item_of_work(self):
		if self.detail_id.estimate_id and self.detail_id.project_id:
			items = self.env['project.task.line'].search([('task_id','=',self.detail_id.estimate_id.id),('task_id.project_id','=',self.detail_id.project_id.id)])
			ids = []
			for val in items:
				ids.append(val.id)
			if self.item_of_work:
				self.desc = self.item_of_work.note
				self.qty = self.item_of_work.qty
				self.uom_id = self.item_of_work.unit.id
				self.rate = self.item_of_work.rate
			return {'domain': {'item_of_work': [('id','in', ids)]}}


class stock_inventory(osv.osv):
	_inherit = "stock.inventory"

	@api.multi
	def action_done(self):
		res = super(stock_inventory, self).action_done()
		for rec in self:
			for inventory_line in rec.line_ids:
				inventory_line.product_id.total_receipts += inventory_line.product_qty
		return res

	@api.multi
	def action_update(self):
		for rec in self:
			for inventory_line in rec.line_ids:
				inventory_line.product_id.total_receipts += inventory_line.product_qty


class stock_inventory_line(osv.osv):
	_inherit = "stock.inventory.line"

	_defaults = {
		'product_qty': 0,
		'product_uom_id': False
	}

	# Should be left out in next version
	def on_change_product_id(self, cr, uid, ids, product, uom, theoretical_qty, context=None):
		""" Changes UoM
		@param location_id: Location id
		@param product: Changed product_id
		@param uom: UoM product
		@return:  Dictionary of changed values
		"""

		obj_product = self.pool.get('product.product').browse(cr, uid, product, context=context)
		return {'value': {'product_uom_id': uom or obj_product.uom_id.id}}


