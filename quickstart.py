from optparse import OptionParser
import os
import sys
import re
from django.core.management import execute_from_command_line
import json
import shutil


tut_header = '''# -*- coding: utf-8 -*-
import os
gettext = lambda s: s
PROJECT_PATH = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
'''


quickstart_dict = dict(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': "os.path.split(('database.sqlite')",
        }
    },
    LANGUAGES = [
        ('en', 'English'),
    ],
    CMS_TEMPLATES = (
        ('template_1.html', 'Template One'),
        ('template_2.html', 'Template Two'),
    ),
    MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
    ),
    TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'cms.context_processors.media',
    'sekizai.context_processors.sekizai',
    ),
    INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'djangocms_text_ckeditor',
    'cms',
    'cms.stacks',
    'mptt',
    'menus',
    'south',
    'sekizai',
    'djangocms_admin_style',
    'django.contrib.messages',
    'django_markdown',
    'cms.plugins.file',
    'cms.plugins.flash',
    'cms.plugins.googlemap',
    'cms.plugins.link',
    'cms.plugins.picture',
    'cms.plugins.snippet',
    'cms.plugins.teaser',
    'cms.plugins.video',
    ),
    TEMPLATE_DIRS = []
)


def main():
    global _proj_path
    global _proj_name
    global _inner_path
    DEBUG = False
    TESTING = False
    argv = sys.argv[:]
    _proj_name = 'gabe_test'
    try:
        directory = argv[1]
    except IndexError:
        print_help()
    try:
        _proj_name = argv[2]
    except IndexError:
        print_help()

    _proj_path = os.path.join(directory, _proj_name)
    _inner_path =  os.path.join(_proj_path, _proj_name)

    if os.path.exists(_proj_path):
        if not TESTING:
            sys.stderr.write('"%s" already exists, will not overwrite.' % (_proj_path))
            sys.exit(2)
        else:
            shutil.rmtree(_proj_path)
    os.chdir(directory)
    if not DEBUG:
        execute_from_command_line(['django-admin.py', 'startproject', _proj_name])
    #move down into the project folder
    patch_settings()
    write_urls()
    setup_directories()
    write_templates()
    setup_database()
    print 'Done.\nHead to %s and run [python manage.py runserver] to try things out.\n' % (_proj_path)


def patch_settings():
    os.chdir(_inner_path)
    if not os.path.exists('settings.py'):
        sys.stderr.write('No settings file present.')
        sys.exit(2)

    with open('settings.py', 'r') as settings_file:
        orig_settings = settings_file.read()

    #use of os.path means we have to do these items manually
    orig_settings = tut_header + orig_settings
    orig_settings = orig_settings.replace("MEDIA_URL = ''", "MEDIA_URL = '/media/'")
    orig_settings = orig_settings.replace("MEDIA_ROOT = ''", "MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')")
    orig_settings = orig_settings.replace("STATIC_ROOT = ''", "STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')")
    orig_settings = orig_settings.replace("TEMPLATE_DIRS = ''", "STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')")
    for key in quickstart_dict:
        replace = '%s = ' % key
        if key is 'DATABASES':
            reg_exp = re.compile(r'%s[^}]+\}[^\}]+\}' % replace, re.MULTILINE)
        else:
            reg_exp = re.compile(r'%s[^\)]+\)'% replace, re.MULTILINE)
        orig_settings = reg_exp.sub('', orig_settings)

    orig_settings += dgcms_settings()

    with open('settings.py', 'w') as settings_out:
        settings_out.write(orig_settings)


def dgcms_settings():
    settings = []
    tab = '    ' #four space tab
    for key in quickstart_dict.iterkeys():
        pre = '%s = (\n%s' % (key, tab)
        post = ',\n)'
        if key is 'DATABASES':
            #It's so bad, please forgivveee meee
            settings.append('''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_PATH, 'database.sqlite'),
    }
}''')
            continue
        elif key is 'TEMPLATE_DIRS':
            body = 'os.path.join(PROJECT_PATH, "templates")'
        elif key is 'CMS_TEMPLATES' or key is 'LANGUAGES':
            body = (',\n' + tab).join([str(var) for var in quickstart_dict[key]])
        else:
            body = (',\n' + tab).join(["'%s'" % var for var in quickstart_dict[key]])
        entry = pre + body + post
        settings.append(''.join([pre, body, post]))
    return '\n\n'.join(settings)


def setup_database():
    import subprocess
    os.chdir(_proj_path)
    subprocess.check_call(['python', 'manage.py',
                          'syncdb', '--noinput'])
    subprocess.check_call(['python', 'manage.py', 'migrate'])
    subprocess.check_call(['python', '-W', 'ignore', 'manage.py', 'createsuperuser'])


def setup_directories():
    os.chdir(_proj_path)
    os.makedirs('static')
    os.makedirs('templates')
    os.makedirs('media')


def write_urls():
    os.chdir(_inner_path)
    if not os.path.exists('urls.py'):
        sys.sterr.write('no url file present in project path.')
        sys.exit(2)

    with open('urls.py', 'w') as urls_out:
        urls = '''from django.conf.urls.defaults import *
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = i18n_patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('cms.urls')),
)

if settings.DEBUG:
    urlpatterns = patterns('',
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'', include('django.contrib.staticfiles.urls')),
) + urlpatterns'''
        urls_out.write(urls)

def write_templates():
    #Really inelligent, but with no customization, this is all we need
    os.chdir(os.path.join(_proj_path, 'templates'))
    base = '''{% load cms_tags sekizai_tags %}
<html>
  <head>
      {% render_block "css" %}
  </head>
  <body>
      {% cms_toolbar %}
      {% placeholder base_content %}
      {% block base_content %}{% endblock %}
      {% render_block "js" %}
  </body>
</html>'''
    t1 = '''{% extends "base.html" %}
{% load cms_tags %}

{% block base_content %}
  {% placeholder template_1_content %}
{% endblock %}'''
    with open('base.html', 'w') as base_out:
        base_out.write(base)
    with open('template_1.html', 'w') as t1_out:
        t1_out.write(t1)
    shutil.copyfile('template_1.html', 'template_2.html')
    os.chdir('..')

def print_help():
    print '\nusage --- quickstart.py [project_directory] [project_name]\n'
    sys.exit(2)


if __name__ == '__main__':
    main()# -*- coding: utf-8 -*-
