# -*- coding: utf-8 -*-
{
    'name': "subscription_tekniq",

    'summary': "Tekniq Subscription customization",

    'description': """
    """,

    'author': "Tekniq",
    'website': "https://www.tekniq.vn",

    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['subscription_oca', 'loyalty'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_pricelist_views.xml',
        'views/sale_order_views.xml',
        'wizard/sale_make_invoice_advance_views.xml',
        'views/loyalty_reward_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

