# -*- coding: utf-8 -*-
# Part of APPEX BOLIVIA SRL.

{
    'name': 'AppexBo Facturación boliviana.',
    'version': '17.0',
    'author' : 'APPEX BOLIVIA SRL.',
    'summary': 'Facturacion electronica / computarizada',
    'description': """
        Facturacion boliviana electronica / computarizada
    """,
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_bo', 
        'base_address_extended'
    ],
    'category': 'Accounting',
    'demo': [],
    
    'external_dependencies': {
        'python': [
            'signxml', # => v2.10.1
            'qrcode'
        ]
    },
    'data': [
        
        # SECURITY
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        
        #DATA
        'data/l10n_bo_wsdl_service.xml',
        'data/l10n_bo_catalog.xml',
        'data/res.country.state.csv',
        'data/res.city.csv',
        'data/res.municipality.csv',
        
        #REPORTS
        'reports/paper_formats.xml',
        'reports/layout.xml',
        'reports/purchase_sale.xml',
        'reports/comercial_export.xml',
        'reports/purchase_sale_roll.xml',
        'reports/credit_debit_note.xml',
        'reports/ir_actions_report.xml',
        'reports/ice.xml',
        'reports/cero_rate.xml',
        
        

        #TEMPLATES
        'templates/mail_templates.xml',
        'templates/ir_cron.xml',
        

        #SEQUENCES


        #VIEWS
        'views/l10n_bo_wsdl_service.xml',
        'views/l10n_bo_wsdl_operation_service.xml',
        'views/res_company.xml',
        'views/l10n_bo_certificate.xml',
        'views/l10n_bo_branch_office.xml',
        'views/l10n_bo_pos.xml',
        'views/account_journal.xml',
        'views/account_move_base.xml',
        'views/l10n_bo_catalog.xml',
        'views/uom_uom.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/res_currency.xml',
        'views/res_partner.xml',
        'views/l10n_bo_cancellation_reason.xml',
        'views/l10n_bo_global_discount.xml',
        'views/l10n_bo_line_discount.xml',
        'views/significant_event.xml',
        'views/l10n_bo_cufd.xml',
        'views/l10n_bo_package.xml',
        #'views/cost_expenses.xml',
        
        'views/menu.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook': '',
    'assets': {},
    'license': 'OPL-1',
    'website': 'https://www.appexbo.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores']
}
