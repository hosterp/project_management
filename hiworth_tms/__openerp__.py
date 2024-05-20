# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'TMS Extension',
    'version': '1.0',
    'category': 'Tools',
    'description': """
The module adds the possibility to display data from OpenERP in Google Spreadsheets in real time.
=================================================================================================
""",
    'author': 'Hiworth',
    'website': 'http://www.hiworthsolutions.com',
    'depends': ['fleet','stock','stock_account','web','report_xlsx','im_chat'],
    'data' : [
        'security/tms_security.xml',
        'security/ir.model.access.csv',
        'report/tyre_purchase_register_report.xml',
        'report/tyre_issue_register_report.xml',
        'report/tyre_removal_register_report.xml',
        'wizard/vehicle_diesel_report_wizard_daily_views.xml',
        'wizard/vehicle_diesel_report_wizard_monthly_views.xml',
        'wizard/tyre_purchase_register_views.xml',
        'wizard/tyre_issue_register_views.xml',
        'wizard/tyre_removal_register_views.xml',
        'wizard/vehicle_maintenance_wizard_views.xml',
        'views/vehicle_odometer_update_view.xml',
        'views/vehicle_details_view.xml',
   #     'hiworth_tms_view.xml',
        'views/hiworth_tms_view2.xml',
        'views/hiworth_tms_menu.xml',
        'views/hiworth_fleet.xml',
        'views/machinery_fuel.xml',
        'views/my_widget.xml',
        'views/workshop_issue_details_views.xml',
        'views/workshop_return_details_view.xml',
        'views/vehicle_tyre_views.xml',
        'report/route_mapping_report.xml',
        'report/vehicle_report.xml',
        'report/diesel_tanker_report.xml',
        'report/monthly_utilization_report.xml',
        'report/vehicle_utilization_report.xml',
        'report/daily_utilization_report.xml',
        'report/daily_monthly_service_report.xml',
        'data/vehicle_category_data.xml',
        'security/hide_sale_pos.xml',
        'views/km_details_config_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
