{
    'name': 'Survey_DGZ',
    'version': '16.0.1',
    'author': 'Digitz',
    'category': 'CRM',
    'sequence': 3,
    'license': 'LGPL-3',
    'website': 'https://digitztech.com/',
    'summary': 'CRM Custom Target for Users',
    'depends': ['survey', 'web'],
    'data': [
        'security/security.xml',
        'views/survey_inh.xml',
        'views/menu.xml',
        'views/survey.xml',
        'reports/feedback_report.xml',
        'reports/page_format.xml'
    ],
    'application': True,
    'installable': True,

}
