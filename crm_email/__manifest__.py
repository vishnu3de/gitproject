{
    'name': 'CRM Email',
    'version': '16.0.1',
    'author': 'Digitz',
    'category': 'CRM',
    'sequence': 3,
    'license': 'LGPL-3',
    'website': 'https://digitztech.com/',
    'summary': 'CRM Custom Target for Users',
    'depends': ['crm'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/crm_email.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'crm_email/static/src/js/rect.js', ],
    },
    'application': True,
    'installable': True,

}
