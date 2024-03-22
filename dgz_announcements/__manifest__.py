# -*- coding: utf-8 -*-
{
    'name': "DGZ ANNOUNCEMENT ",
    'version': '16.0.1',
    'author': 'Digitz/Vishnu',
    'summary': 'Announcements for users',
    'depends': ['base'],
    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/main.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dgz_announcements/static/src/js/main.js',],
    },


}
