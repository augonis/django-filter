from __future__ import absolute_import
from __future__ import unicode_literals

from itertools import chain
try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode  # noqa

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.widgets import flatatt
try:
    from django.utils.encoding import force_text
except:  # pragma: nocover
    from django.utils.encoding import force_unicode as force_text  # noqa
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


class LinkWidget(forms.Widget):
    def __init__(self, attrs=None, choices=()):
        super(LinkWidget, self).__init__(attrs)

        self.choices = choices

    def value_from_datadict(self, data, files, name):
        value = super(LinkWidget, self).value_from_datadict(data, files, name)
        self.data = data
        return value

    def render(self, name, value, attrs=None, choices=()):
        if not hasattr(self, 'data'):
            self.data = {}
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs)
        output = ['<ul%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value], name)
        if options:
            output.append(options)
        output.append('</ul>')
        return mark_safe('\n'.join(output))

    def render_options(self, choices, selected_choices, name):
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                for option in option_label:
                    output.append(
                        self.render_option(name, selected_choices, *option))
            else:
                output.append(
                    self.render_option(name, selected_choices,
                                       option_value, option_label))
        return '\n'.join(output)

    def render_option(self, name, selected_choices,
                      option_value, option_label):
        option_value = force_text(option_value)
        if option_label == BLANK_CHOICE_DASH[0][1]:
            option_label = _("All")
        data = self.data.copy()
        data[name] = option_value
        selected = data == self.data or option_value in selected_choices
        try:
            url = data.urlencode()
        except AttributeError:
            url = urlencode(data)
        return self.option_string() % {
             'attrs': selected and ' class="selected"' or '',
             'query_string': url,
             'label': force_text(option_label)
        }

    def option_string(self):
        return '<li><a%(attrs)s href="?%(query_string)s">%(label)s</a></li>'


class RangeWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (forms.TextInput(attrs=attrs), forms.TextInput(attrs=attrs))
        super(RangeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        return '-'.join(rendered_widgets)


class LookupTypeWidget(forms.MultiWidget):
    def decompress(self, value):
        if value is None:
            return [None, None]
        return value

class BooleanSelect(forms.Select):
    """
    A Select Widget intended to be used with NullBooleanField.
    """
    def __init__(self, attrs=None):
        choices = (('', _('Any')),
                   ('2', _('Yes')),
                   ('3', _('No')))
        super(BooleanSelect, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None, choices=()):
        try:
            value = {True: '2', False: '3', '2': '2', '3': '3'}[value]
        except KeyError:
            value = '1'
        return super(BooleanSelect, self).render(name, value, attrs, choices)

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        return {'2': True,
                True: True,
                'True': True,
                '3': False,
                'False': False,
                False: False}.get(value, None)

class DateOffsetWidget(forms.Select):
    directions = {'past':_('last'), 'future':_('next')}
    def __init__(self, attrs=None, direction='past'):
        choices = ('', _('unit')), (1, _('days')), (7, _('weeks')), (30, _('months')), (365, _('years'))
        self.direction = direction
        super(DateOffsetWidget, self).__init__(attrs, choices)
    
    def render(self, name, value, attrs=None, choices=()):
        output=['<span>%s</span>'%(self.directions[self.direction].capitalize())]
        output.append('<input placeholder="number" type="number" name="%s_n"/>'%name)
        output.append(super().render("%s_m"%name, value, attrs=attrs))
        
        return mark_safe('\n'.join(output))
    
    
    def value_from_datadict(self, data, files, name):
        
        number = data.get("%s_n"%name, None)
        multiplier = data.get("%s_m"%name, None)
        if number and multiplier:
            return number, multiplier
        
    

