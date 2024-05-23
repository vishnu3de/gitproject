{
    'name': 'Feedback Form',
    'version': '16.0.1',
    'author': 'Digitz/Vishnu',
    'category': 'Feedback',
    'sequence': 1,
    'license': 'LGPL-3',
    'website': 'https://digitztech.com/',
    'summary': 'Feedback form through mail for customers',
    'depends': ['survey', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/survey_inh.xml',
        'views/menu.xml',
        'views/survey.xml',
        'wizards/wizard.xml',
        'reports/feedback_report.xml',
        'reports/page_format.xml',
        'data/certification_hide.xml'
    ],
    'application': True,
    'installable': True,

}
