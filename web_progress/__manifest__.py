{
    'name': "Dynamic Progress Bar",

    'summary': """
        Progress bar for operations that take more than 5 seconds.
    """,

    # 'description': """
    # Adds dynamic progress bar and cancel button to gray waiting screen.
    # Try to import some CSV file to any model to see it in action.
    # """,

    'author': "Grzegorz Marczyński",
    'category': 'Productivity',

    'version': '12.0.1.3',

    'depends': ['web',
                'bus',
                'base_import'
                ],

    'data': [
        'views/templates.xml',
    ],

    'qweb': [
        'static/src/xml/progress_bar.xml',
        'static/src/xml/web_progress_menu.xml',
        ],

    'demo': [
    ],
    'images': ['static/description/progress_bar_loading_compact.gif',
               'static/description/progress_bar_loading_cancelling.gif',
               'static/description/progress_bar_loading_systray.gif',
               ],

    'license': 'LGPL-3',

    'installable': True,
    'auto_install': True,
    'application': False,
}
