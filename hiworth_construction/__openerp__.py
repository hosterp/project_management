{
    'name': 'Hiworth Construction Management',
    'version': '1.0',
    'category': 'Project',
    'sequence': 21,
    'description': """ Project Cost Estimation """,
    'depends': ['mail','sale','project','mrp','purchase','document','hr','hiworth_accounting','hiworth_hr_attendance','auditlog','hiworth_tms',],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.csv',
        'security/hide_sale_manufacturing.xml',
        'data/tender_emd_data.xml',
        'data/defaultdata.xml',
        'wizard/recommended_list_views.xml',
        'wizard/view_stock_history_views.xml',
        'wizard/view_purchase_history_wizard_views.xml',
        'wizard/do_yo_want_to_save_wizard_views.xml',
        'wizard/stock_transfer_details.xml',
        'wizard/driver_bata_report.xml',
        'wizard/cleaner_bata_report.xml',
        'wizard/driver_bata_accounts_reports.xml',
        'wizard/bill_status_update_views.xml',



        'report/master_plan_report.xml',
        'report/planning_chart_report.xml',
        'report/alter_default_header_footer.xml',
        'report/project.xml',
        'report/task.xml',
        'report/material_request.xml',
        'report/location_wise_report.xml',
        'report/stock_report.xml',
        'report/common_report_alteration.xml',
        'report/project_report.xml',
        'report/bills_followup_report.xml',
       
        'views/construction_project_details_view.xml',
        'views/counstruction_menu_view.xml',
        'views/export_tree_view.xml',
         #'security/security.xml',
    
        'report/product_to_location_report.xml',
        'report/stock_move_report.xml',
        'report/activity_reports.xml',
        'report/contractor_invoices_report.xml',
        'report/task_report_wizarad.xml',
        'views/work_order_sequence.xml',
        'views/contractor_bill_sequence.xml',
        'views/fund_return.xml',
       
        'views/hiworth_invoice.xml',
        'views/hiworth_accounting_view.xml',
        
        
        'views/site_purchase.xml',
        'views/invoice_action_data.xml',
        
        'views/work_order.xml',
        
        'views/purchase_order_action_data.xml',
        'views/default_project_stages.xml',
        'views/activity_view.xml',
        
        
        'views/admin_saction_records.xml',
        
        'views/daily_progress_report.xml',
        'views/work_shedule.xml',
        'views/employee_activity.xml',
        'views/delay_report.xml',
        # 'views/progress_report.xml',
       
        
        'views/account_payment_schedule.xml',
       
        'views/material_request.xml',
        'views/project_stages.xml',
        'views/driver_daily_stmt.xml',
        'views/daily_statment_sequence.xml',
        'views/partner_daily_statement.xml',
        'report/driver_daily_report.xml',
        'report/partner_daily_report.xml',
        'report/material_procurement_report.xml',

        'report/report.xml',
        #'views/site_purchase.xml',
        'report/site_purchase_report.xml',
        'views/sequence.xml',
        'views/product_price_data.xml',
        'views/tendor_views.xml',
        'views/action_menu_hide.xml',
        'views/planning.xml',
        # 'views/planning_survey.xml',
        'views/finance_views.xml',
        'views/nextday_settlement.xml',
        'views/supervisor_payment_views.xml',
        'report/tender_security_report.xml',
        'report/hiworth_vehicle_status_view.xml',
        'report/goods_transfer_note_report.xml',
        'report/goods_receive_report.xml',
        # 'report/rent_vehicle_report.xml'

        'views/report_property_view.xml',
        'views/purchase_comparison.xml',
        'views/material_issue_slip_views.xml',
        'views/debit_note_supplier_views.xml',
        'views/goods_tranfer_note.xml',
        'views/labour_sheet_activities_views.xml',
'wizard/goods_recieve_report_wizard_views.xml',
        'wizard/labour_bata_report.xml',
        'wizard/labour_details_wizard_views.xml',
        'wizard/labour_bata_accounts_reports.xml',
        'report/daily_progress_report_views.xml',
        'wizard/rent_vehicle_reports_wizard_views.xml',
        'wizard/rent_machinery_statements_wizard_views.xml',
        'wizard/stock_report_location_wizard_views.xml',
        'wizard/project_costing_wizard_views.xml',
        'wizard/project_wizard_report_views.xml',
        'wizard/goods_transfer_note_report_wizard_views.xml',


    ],

    # 'qweb': [
    #     'static/src/xml/popup_notifications.xml',
    # ],

    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
