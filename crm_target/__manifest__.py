{
    'name': 'CRM TARGET',
    'version': '16.0.1',
    'author': 'Digitz',
    'category': 'CRM',
    'sequence': 2,
    'license': 'LGPL-3',
    'website': 'https://digitztech.com/',
    'summary': 'CRM Custom Target for Users',
    'depends': ['crm', 'mail','sale'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'reports/commercial.xml',
        'reports/commercial_main.xml',
        'views/crm_track.xml',
        'views/cron.xml',
        'views/menu.xml',
    ],
    'application': True,
    'installable': True,

}
