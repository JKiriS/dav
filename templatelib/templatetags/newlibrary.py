# -*- coding: utf-8 -*-
from django import template
register = template.Library()
from django.template.base import TemplateSyntaxError, NodeList
from datetime import datetime, timedelta

class IfInNode(template.Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, var1, var2, nodelist_true, nodelist_false):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def __repr__(self):
        return "<IfInNode>"

    def render(self, context):
        val1 = self.var1.resolve(context, True)
        val2 = self.var2.resolve(context, True)
        if val2 == None:
            val2 = []
        if val1 in list(val2): 
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)

def do_ifin(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError("%r takes two arguments" % bits[0])
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])
    return IfInNode(val1, val2, nodelist_true, nodelist_false)

@register.tag
def ifin(parser, token):
    """
    Outputs the contents of the block if the two arguments equal each other.

    Examples::

        {% ifin user.id comment.users %}
            ...
        {% endifin %}

        {% ifin user.id comment.users %}
            ...
        {% else %}
            ...
        {% endifnotequal %}
    """
    return do_ifin(parser, token)

class ReorderNode(template.Node):
    def __init__(self, target, orders, var_name):
        self.target = target
        self.orders = orders
        self.var_name = var_name

    def render(self, context):
        oldlist = list(self.target.resolve(context, True))
        orders = self.orders.resolve(context, True)
        if orders == None:
            # target variable wasn't found in context; fail silently.
            context[self.var_name] = oldlist
            return ''

        ordersdict = {}
        for i, j in enumerate(orders):
            ordersdict[j] = i
        newlist = range(len(oldlist))
        for i in oldlist:   # order by rlist
            try:
                newlist[ordersdict.get(i.id)] = i
            except:
                pass

        context[self.var_name] = newlist
        return ''

@register.tag
def reorder(parser, token):
    """
    The following snippet of template code would accomplish this dubious task::

        {% reorder itemlist by orders as itemlist %}
        <ul>
        {% for item in itemlist %}
        {% endfor %}
        </ul>
    """
    bits = token.split_contents()
    if len(bits) != 6:
        raise TemplateSyntaxError("'regroup' tag takes five arguments")
    target = parser.compile_filter(bits[1])
    orders = parser.compile_filter(bits[3])
    if bits[2] != 'by':
        raise TemplateSyntaxError("second argument to 'reorder' tag must be 'by'")
    if bits[4] != 'as':
        raise TemplateSyntaxError("next-to-last argument to 'reorder' tag must"
                                  " be 'as'")
    var_name = bits[5]

    return ReorderNode(target, orders, var_name)

class DTFormatNode(template.Node):
    def __init__(self, target, dtoffset, dtfmt=None):
        self.target = target
        self.dtfmt = dtfmt
        self.dtoffset = dtoffset

    def render(self, context):
        dt = self.target.resolve(context, True)
        if not dt:
            return ''
        dtfmt = self.dtfmt.resolve(context, True) if self.dtfmt else None
        if self.dtoffset:
            dtoffset = self.dtoffset.resolve(context, True)
            if isinstance(dtoffset, timedelta):
                dt = dt + dtoffset
        if not dtfmt:
            dtfmt = '%Y-%m-%d %H:%M:%S'
        return dt.strftime(dtfmt)

@register.tag
def dtformat(parser, token):
    """
    The following snippet of template code would accomplish this dubious task::

        {% dtformat timestamp offset dtoffset dtfmt %}
    """
    bits = token.split_contents()
    if bits[2] != 'offset':
        raise TemplateSyntaxError("third argument to 'dtformat' tag must be 'offset'")
    target = parser.compile_filter(bits[1])
    dtoffset = parser.compile_filter(bits[3])
    if len(bits) == 5:
        dtfmt = parser.compile_filter(bits[4])
        return DTFormatNode(target, dtoffset, dtfmt)
    return DTFormatNode(target, dtoffset)