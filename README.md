# Exception Mailer for Django

`django_exception_mailer` contains a module called `mailer` which exposes a class called `ExceptionMailer`.
When used properly, `ExceptionMailer` will help you debug your Django projects in finer detail and as errors
are encountered.

The result of which will be a remarkably defect free (well, there is no such thing as "defect free software",
but still...) Django application that you can feel safe deploying into production. This is especially helpful
in catching previously undiscovered production environment defects that you'd otherwise not have handled!

## Dependencies

Exception Mailer was written and tested in Python >= 3.4.3. To check your Python version:

```bash
$ python --version
```
Exception Mailer requires the use of [Pygments](http://pygments.org/):

```bash
$ pip install pygments
```

## Get Exception Mailer

```bash
$ cd /path/to/local/django/project/lib
$ git clone --depth 1 -b master https://github.com/jonmsawyer/django_exception_mailer.git
# Remove .git directory to keep this as a clean library:
$ rm -rf .git/
```

## Set it all up

#### settings.py

`ADMINS` setting is required:

```python
ADMINS = (
    ('Your Name', 'your@email.address'),
    # Add more as needed
)
```

`EMAIL_HOST`, `EMAIL_PORT`, and `SERVER_EMAIL` are required:

```python
EMAIL_HOST = 'smtp.host.local'
EMAIL_PORT = 25
# Set SERVER_EMAIL to be unique for your project name and environment so that it's easy to
# filter. The idea here is that you'll have a DEV, STAGE, and PROD environment, each with
# the same project name, but different environments. If you get an email from
# `<projname>-dev@host.local`, then you know it is from your DEV environment, `-stage` for
# STAGE and so on.
SERVER_EMAIL = 'my-project-dev@host.local'
```

## Now, in your code...

```python
from django_exception_mailer.mailer import ExceptionMailer

def some_view(request):
    arr = [0, 1, 2]

    try:
        my_var = arr[99]
    except Exception as e:
        # Exception Mailer was designed to catch *generic* exceptions so that you, as the
        # programmer, can catch each specific (unknown) Exception and deal with those individually.
        ExceptionMailer.mail(request, name='app_name.views.some_view: Get my_var',
                             exception=e, ignore=False, _globals=globals(), _locals=locals())
```

When this code is run, an Exception will be raised and the details in the email message will
help you make this particular portion defect free.

### After you received the email and identified the problem...

The email message in this example told us that the Exception raised was an `IndexError`. Woops!
Let's go back and fix our code:

```python
from django_exception_mailer.mailer import ExceptionMailer

def some_view(request):
    arr = [0, 1, 2]

    try:
        my_var = arr[99]
    except IndexError as e:
        my_var = 0 # There, we've handled the error, but we still leave the `ExceptoinMailer` class
                   # below to catch any voodoo runtime errors that happen to pop up.
    except Exception as e:
        # Exception Mailer was designed to catch *generic* exceptions so that you, as the
        # programmer, can catch each specific (unknown) Exception and deal with those individually.
        ExceptionMailer.mail(request, name='app_name.views.some_view: Get my_var',
                             exception=e, ignore=False, _globals=globals(), _locals=locals())
```

## How to use

Simply call the `@staticmethod` `mail` from the `ExceptionMailer` class with the following arguments:

 * `request` - (django.http.HttpRequest)
   * Required. Send the view's `request` object along so the mailer can parse out your environment.
 * `name` - (str)
   * Optional. Defaults to `''`. Pass in `name` to extend the email's subject as well as to identify
     (make this name unique, app-wide, so you can easily find it in your code) where the error took place.
     Sometimes a line number and a stacktrace isn't quite sufficient.
 * `exception` - (Exception)
   * Optional. Defaults to `None`. Pass in `exception` to obtain two key pieces of information:
     1. the stacktrace that triggered the exception
     2. the stacktrace of ExceptionMailer itself
     Both of which give you the line numbers and context for the error.
 * `ignore` - (bool)
   * Optional. Defaults to `False`. Set this to `True` to ignore the exception. This is useful if you want
     to disable an ExceptionMailer call without having to remove the code from the source file. This also
     allows you to enable it at any time without having to add the code back in.
 * `_locals` - (dict)
   * Optional. Defaults to `None`. Pass in the output of `locals()` to obtain the local variables at the
     time of the exception.
 * `_globals` - (dict)
   * Optional. Defaults to `None`. Pass in the output of `globals()` to obtain the global variables at the
     time of the exception.
