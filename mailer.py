"""
File: mailer.py
Module: django-exception-mailer.mailer
Author: Jonathan Sawyer <jonmsawyer (@) gmail (DOT) com>
"""

import traceback
import json
import collections
import inspect
from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail, mail_admins

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

__version__ = "0.1"

lexer = get_lexer_by_name("python", stripall=True)
formatter = HtmlFormatter(cssclass="source")

def pretty_print(d, indent=0):
    if not isinstance(d, dict):
        return d
    # Sometimes our dictionary will have non-string keys. Stringify the keys so they can be
    # ordered without raising a TypeError exception.
    new_dict = {}
    for key in d.keys():
        new_dict[str(key)] = d.get(key)
    try:
        od = collections.OrderedDict(sorted(new_dict.items()))
    except TypeError as e:
        od = collections.OrderedDict(new_dict)
    del new_dict
    txt = ''
    t = '  ' * (indent+1)
    for key, value in od.items():
        txt = txt + t + str(key) + ": "
        if isinstance(value, dict):
            txt = txt + '{\n' + pretty_print(value, indent+1) + t + '}\n'
        elif value == None:
            txt = txt + '<None>' + ',\n'
        elif isinstance(value, bool):
            if value:
                txt = txt + 'True,\n'
            else:
                txt = txt + 'False,\n'
        else:
            txt = txt + repr(value) + ',\n'
    return txt

class AdminMailer(object):
    # mail_admins(subject, message, fail_silently=False,
    #             connection=None, html_message=None)
    @staticmethod
    def mail(subject='', message='',
             fail_silently=True, connection=None, html_message=None):
        mail_admins(subject, message, fail_silently, connection, html_message)

class ExceptionMailer(AdminMailer):
    subject = 'Exception!'
    
    @staticmethod
    def get_name(name):
        if name is None:
            return ''
        if isinstance(name, str):
            return repr(name.strip())
        return repr(name)
    
    @staticmethod
    def get_subject(name):
        if name != '' and name is not None:
            return "%s [%s]" % (ExceptionMailer.subject, name)
        return ExceptionMailer.subject
    
    @staticmethod
    def get_mailer_traceback(stack, exception):
        frame, from_file, line_no, where_in, code, something_else = stack
        if isinstance(exception, Exception):
            e = "\nException is %r" % (exception,)
        else:
            e = ''
        code = (''.join(code)).strip()
        return (
            'File "%s", line %s, in %s\n  %s%s' % (from_file, line_no, where_in, code, e)
        ).strip()
    
    @staticmethod
    def get_session(request):
        try:
            return pretty_print(request.session.__dict__)
        except Exception as e:
            return "(No session available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_meta(request):
        try:
            return pretty_print(request.META)
        except Exception as e:
            return "(No META available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_ip(request):
        try:
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
            if ip == '':
                return "%s (not proxied)" % (request.META.get('REMOTE_ADDR', ''),)
            else:
                return "%s (proxied)" % (ip,)
        except Exception as e:
            return "(No IP available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_method(request):
        try:
            return request.META.get('REQUEST_METHOD', '???')
        except Exception as e:
            return "(No request method available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_base_path(request):
        try:
            return request.META.get('REQUEST_URI', '').split('?')[0]
        except Exception as e:
            return "(No base path available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_user_agent(request):
        try:
            return request.META.get('HTTP_USER_AGENT')
        except Exception as e:
            return "(No user agent available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_request_url(request):
        try:
            proto = request.META.get('HTTP_X_FORWARDED_PROTO', 'proto')
            host = request.META.get('HTTP_X_FORWARDED_HOST', 'unknown.host')
            uri = request.META.get('REQUEST_URI', '/#unknown_request_uri')
            
            if proto == 'proto' or host == 'unknown.host' or uri == '/#unknown_request_uri':
                proto = request.META.get('REQUEST_SCHEME', 'proto')
                host = request.META.get('HTTP_HOST', 'unknown.host')
                uri = request.META.get('SCRIPT_URL', '/#unknown_script_url')
            
            return "%s://%s%s" % (proto, host, uri)
        except Exception as e:
            return "(No request URL available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_referer(request):
        try:
            return request.META.get('HTTP_REFERER', '')
        except Exception as e:
            return "(No referer available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_query_string(request):
        try:
            return request.META.get('QUERY_STRING', '')
        except Exception as e:
            return "(No query string available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_get_params(request):
        try:
            return pretty_print(request.GET)
        except Exception as e:
            return "(No GET available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_post_params(request):
        try:
            return pretty_print(request.POST)
        except Exception as e:
            return "(No POST available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_path_info(request):
        try:
            return request.META.get('mod_wsgi.path_info', '/#unknown_path_info')
        except Exception as e:
            return "(No path info available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_proxied_url(request):
        try:
            return request.META.get('SCRIPT_URI', '???')
        except Exception as e:
            return "(No proxied url available. Reason: %s)" % (e,)
    
    @staticmethod
    def get_globals(_globals):
        if _globals is None:
            return ''
        return pretty_print(_globals)
    
    @staticmethod
    def get_locals(_locals):
        if _locals is None:
            return ''
        return pretty_print(_locals)
    
    @staticmethod
    def mail(request, name='', ignore=False, exception=None, _globals=None, _locals=None):
        if ignore is True:
            return
        
        dttm = datetime.now().isoformat(' ')
        name = ExceptionMailer.get_name(name)
        subject = ExceptionMailer.get_subject(name)
        stack_frame = inspect.stack()[1]
        text_msg_params = {
            'timestamp': dttm,
            'mailer_traceback': ExceptionMailer.get_mailer_traceback(stack_frame, exception),
            'exception_traceback': traceback.format_exc().strip(),
            'session': ExceptionMailer.get_session(request),
            'meta': ExceptionMailer.get_meta(request),
            'ip': ExceptionMailer.get_ip(request),
            'method': ExceptionMailer.get_method(request),
            'base_path': ExceptionMailer.get_base_path(request),
            'user_agent': ExceptionMailer.get_user_agent(request),
            'request_url': ExceptionMailer.get_request_url(request),
            'referer': ExceptionMailer.get_referer(request),
            'query_string': ExceptionMailer.get_query_string(request),
            'get': ExceptionMailer.get_get_params(request),
            'post': ExceptionMailer.get_post_params(request),
            'path_info': ExceptionMailer.get_path_info(request),
            'proxied_url': ExceptionMailer.get_proxied_url(request),
            'globals': ExceptionMailer.get_globals(_globals),
            'locals': ExceptionMailer.get_locals(_locals),
            'subject': subject,
        }
        
        text_message = '''

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# == {subject} ==

Remote IP: {ip}

Method: {method}

Request URI: {request_url}
     Base Path: {base_path}
     Query String: ?{query_string}
     WSGI Path Info: {path_info}
     User Agent: {user_agent}
 
Proxied URI: {proxied_url}

Referer: {referer}

Timestamp: {timestamp}

# == Parameters ==

GET: {{
{get}}}

POST: {{
{post}}}

# == Exception Traceback ==

{exception_traceback}

# == ExceptionMailer Traceback ==

{mailer_traceback}

# == Client Session ==

{{
{session}}}

# == Request META (HTTP Headers and Env Variables) ==

{{
{meta}}}

# == Locals ==

{{
{locals}}}

# == Globals ==

{{
{globals}}}

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# --OQ Mailer
'''.format(**text_msg_params)
        
        html_params = {
            'style': formatter.get_style_defs(),
            'body': highlight(text_message, lexer, formatter)
        }
        
        html_message = '''<!DOCTYPE html>
<html>
<head><style>{style}</style></head>
<body>{body}</body>
</html>
'''.format(**html_params)
        
        # Mail it off
        mail_admins(
            subject=subject,
            message=text_message,
            fail_silently=True,
            connection=None,
            html_message=html_message
        )
