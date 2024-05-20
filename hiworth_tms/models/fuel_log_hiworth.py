import logging
import psycopg2
import time
from datetime import datetime

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp
import openerp.addons.product.product



class tms_picking(osv.osv):
    _inherit = 'tms.picking'
    _columns= {
        'vehicle_fuel_log_id': fields.many2one('fleet.vehicle.log.fuel', 'Fuel Log', states={'done':[('readonly', True)]}),
        'items_line': fields.many2one('sale.order.line', 'Items', states={'done':[('readonly', True)]}),
    }


