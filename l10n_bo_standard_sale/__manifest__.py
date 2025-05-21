# -*- coding: utf-8 -*-
# Part of APPEX BOLIVIA SRL.

{
    'name': 'Registro de ventas estándar (BO).',
    'version': '17.0',
    'author' : 'APPEX BOLIVIA SRL.',
    'summary': 'Registro de ventas estándar (BO).',
    'description': """
        El Registro de Ventas Estándar permite el registro de documentos fiscales
    """,
    'depends': ['l10n_bo_bolivian_invoice'],
    'category': 'Accounting',
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',

        'data/l10n_bo_standard_sale.xml',
        
        'views/l10n_bo_standard_sale_line.xml',
        'views/l10n_bo_standard_sale.xml',
        'views/menuitem.xml',
        
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'website': 'https://www.appexbo.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}