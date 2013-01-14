# !title: Edited query_string tag without XSS-injections
# !date: 2013-01-14
# !tags: Django
# !author: Dima Kukushkin and Denis Veselov


# You should be create context processor with request.path
# and add this in settings.TEMPLATE_CONTEXT_PROCESSORS
# Example: core/context_processors.py

def request_path(request):
    return {'path': request.path}


# query_string template tag
# Example of usage:
# {% query_string "add_first_param=123,add_second_param=object.id" "remove_param,remove_second_param" %}

from urllib import quote_plus

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.tag
def query_string(parser, token):
    try:
        tag_name, add, remove = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires two arguments" % token.contents.split()[0]
        )
    if not (add[0] == add[-1] and add[0] in ('"', "'")) \
       or not (remove[0] == remove[-1] and remove[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name
        )

    add = string_to_dict(add[1:-1])
    remove = string_to_list(remove[1:-1])
    return QueryStringNode(add, remove)


class QueryStringNode(template.Node):

    def __init__(self, add, remove):
        self.add = add
        self.remove = remove

    def render(self, context):
        p = {}
        for k, v in context.get("request_get_items"):
            p[k] = v
        return get_query_string(p, self.add, self.remove, context)


def get_query_string(p, new_params, remove, context):
    """
    Add and remove query parameters. From `django.contrib.admin`.
    """
    for r in remove:
        for k in p.keys():
            if k.startswith(r):
                del p[k]
    for k, v in new_params.items():
        if k in p and v is None:
            del p[k]
        elif v is not None:
            p[k] = v

    for k, v in p.items():
        try:
            p[k] = template.Variable(v).resolve(context)
        except:
            p[k] = v

    query_list = []
    for k, v in p.items():
        if hasattr(k, 'encode'):
            k = quote_plus(k.encode('utf-8'))
        if hasattr(v, 'encode'):
            v = quote_plus(v.encode('utf-8'))

        query_list += ['%s=%s' % (k, v)]

    if not query_list:
        if context.get('path'):
            return context['path']
        return ''
    return mark_safe('?' + '&amp;'.join(query_list).replace(' ', '%20'))


def string_to_dict(string):
    kwargs = {}

    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '':
                continue
            kw, val = arg.split('=', 1)
            kwargs[kw] = val
    return kwargs


def string_to_list(string):
    args = []
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '':
                continue
            args.append(arg)
    return args
