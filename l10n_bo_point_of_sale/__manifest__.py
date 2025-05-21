# -*- coding: utf-8 -*-

{
    'name': 'Punto de venta (BO).',
    'version': '17.0',
    'author' : 'APPEX BOLIVIA SRL.',
    'summary': 'Facturacion con punto de venta',
    'description': """
        Facturacion boliviana electronica / computarizada, integrado con punto de venta
    """,
    'depends': [
        'l10n_bo_bolivian_invoice',
        'point_of_sale',
    ],
    'category': 'Accounting',
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/l10n_bo_pos.xml',
        'views/pos_config.xml',
        'views/pos_payment_method.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'l10n_bo_point_of_sale/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'website': 'https://www.appexbo.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores']
}
