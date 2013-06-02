
from django.forms.widgets import TextInput
from django.db.models import PositiveIntegerField, EmailField, URLField, TimeField, DateField, DateTimeField
from django.core.validators import MaxValueValidator, MinValueValidator
from django import forms

import models
import datetime


class PositiveIntegerWidget(TextInput):
    input_type = 'number'
    def __init__(self, *args, **kwargs):
        if not 'attrs' in kwargs:
            kwargs['attrs'] = dict(min=0)
        else:
            kwargs['attrs'].setdefault('min', 0)
        super(PositiveIntegerWidget, self).__init__(*args, **kwargs)


class EmailWidget(TextInput):
    input_type = 'email'
    def __init__(self, *args, **kwargs):
        super(EmailWidget, self).__init__(*args, **kwargs)


class URLWidget(TextInput):
    input_type = 'url'
    def __init__(self, *args, **kwargs):
        super(URLWidget, self).__init__(*args, **kwargs)


class DateWidget(TextInput):
    input_type = 'text'
    def __init__(self, *args, **kwargs):
        if not 'attrs' in kwargs:
            kwargs['attrs'] = {'class' : 'datepicker',
                                         'bs-datepicker' : '1',
                                         'data-date-format' :"mm/dd/yyyy"}
        super(DateWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if isinstance(value, datetime.date):
            value=value.strftime("%d/%m/%Y")
        return super(DateWidget, self).render(name, value, attrs)


class TimeWidget(TextInput):
    input_type = 'time'
    def __init__(self, *args, **kwargs):
        super(TimeWidget, self).__init__(*args, **kwargs)


class DateTimeWidget(TextInput):
    input_type = 'datetime'
    def __init__(self, *args, **kwargs):

        super(DateTimeWidget, self).__init__(*args, **kwargs)


class PercentageWidget(TextInput):
    """
    A widget for entering percentages. Using html5 'number'
    """
    input_type = 'number'
    def __init__(self, *args, **kwargs):
        #
        # Set defaults to 0 and 100 if not overriden
        #
        if not 'attrs' in kwargs:
            kwargs['attrs'] = dict(min=0, max=100)
        else:
            for x in (('min', 0), ('max', 100)):
                kwargs['attrs'].setdefault(x[0], x[1])

        super(PercentageWidget, self).__init__(*args, **kwargs)


forms.ModelChoiceField

class DateFormField(forms.DateField):
    """
    A custom formfield we are going to use because we need to change the acceptable input formats
    """
    widget = DateWidget

    def __init__(self, *args, **kwargs):
        super(DateFormField, self).__init__(*args, **kwargs)
        self.input_formats = ("%m/%d/%Y",) + (self.input_formats,)


class PercentageField(forms.FloatField):
    def __init__(self, *args, **kwargs):

        if not 'widget' in kwargs:
            kwargs['widget'] = PercentageWidget()

        super(PercentageField, self).__init__(*args, **kwargs)


class RatingSliderWidget(TextInput):
    """
     A widget for entering ratings using the html5 range
    """
    input_type = 'range'
    def __init__(self, *args, **kwargs):
        #
        # Set defaults to 0 and 100 if not overriden
        #
        if not 'attrs' in kwargs:
            kwargs['attrs'] = dict(min=0, max=100)
        else:
            for x in (('min', 0), ('max', 100)):
                kwargs['attrs'].setdefault(x[0], x[1])
        super(RatingSliderWidget, self).__init__(*args, **kwargs)


class SliderField(forms.FloatField):
    def __init__(self, *args, **kwargs):
        if not 'widget' in kwargs:
            kwargs['widget'] = RatingSliderWidget()

        super(SliderField, self).__init__(*args, **kwargs)


def custom_formfield_callback(f, **kwargs):
    """
    Applies our own assignment of widgets etc when using model forms
    """

    #
    # Percentage fields have their own widget
    #
    if isinstance(f, models.PercentageField):
        return f.formfield(widget = PercentageWidget(), **kwargs)
    elif isinstance(f, PositiveIntegerField):
        #
        # Check in the validators for a Positive integer field
        # If it has a MaxValue Validator then it gets a special widget
        #
        attrs = {}
        for v in f.validators:
            if isinstance(v, MaxValueValidator):
                attrs['max'] = v.limit_value
            elif isinstance(v, MinValueValidator):
                attrs['min'] = v.limit_value
        if 'max' in attrs:
            return f.formfield(widget=PositiveIntegerWidget(attrs=attrs), **kwargs)
        

    #
    # Fallthrough and just do the default
    #
    return f.formfield(**kwargs)



def angular_formfield_callback(f, **kwargs):
    """
    Applies our own assignment of widgets etc when using model forms
    """
    if isinstance(f, PositiveIntegerField):
        field = f.formfield(widget = PositiveIntegerWidget(), **kwargs)
    elif isinstance(f, EmailField):
        field = f.formfield(widget = EmailWidget, **kwargs)
    elif isinstance(f, URLField):
        field = f.formfield(widget = URLWidget, **kwargs)
    elif isinstance(f, DateField):
        defaults = dict(form_class = DateFormField)
        defaults.update(kwargs)
        field = f.formfield(**defaults)
        field.widget.attrs['ng-model'] = 'datepicker.dj_' + f.name
        field.widget.attrs['dj_init'] = field.__class__.__name__.lower()
    elif isinstance(f, TimeField):
        field = f.formfield(widget = TimeWidget, **kwargs)
    elif isinstance(f, DateTimeField):
        field = f.formfield(widget = DateTimeWidget, **kwargs)
    else:
        # If we don't have a special one just let django pick for us
        field = f.formfield(**kwargs)

    if field:  # sometimes there is no field...
        for v in f.validators:
            if isinstance(v, MaxValueValidator):
                field.widget.attrs['max'] = v.limit_value
            elif isinstance(v, MinValueValidator):
                field.widget.attrs['min'] = v.limit_value


        if 'ng-model' not in field.widget.attrs:
            # set up a model for this so ng can do stuff with it
            field.widget.attrs['ng-model'] = 'dj_%s' % f.name
        if 'dj_init' not in field.widget.attrs:
            # set the model name as an attribute of the init directive so we can set up the scope
            field.widget.attrs['dj_init'] = field.__class__.__name__.lower()

    return field


def get_form_class_for_class(klass):
    """
    A helper function for creating a model form class for a model on the fly. This is used with models (usually
    part of an inheritance hierarchy) which define a function **get_editable_fields** which returns an iterable
    of the field names which should be placed in the form.
    """
    meta_dict = dict(model=klass)
    if hasattr(klass, 'get_editable_fields'):
        meta_dict['fields'] = klass.get_editable_fields()

    meta = type('Meta', (),meta_dict)
    modelform_class = type('modelform', (forms.ModelForm,), {"Meta": meta})
    return modelform_class


# Stuff using the ParameterTypes follows


class ParameterTypes(object):
    NONE = 0
    FILE = 10
    STRING = 20
    INTEGER = 30
    FLOAT = 40
    BOOLEAN = 50
    ENUM = 60
    LABEL = 100
    URL = 110
    UUID = 120

    CHOICES = (
        (NONE, "None"),
        (FILE, "FILE"),
        (STRING, "String"),
        (INTEGER, "Integer"),
        (FLOAT, "Float"),
        (BOOLEAN, "Bool"),
        (ENUM, "Enum"),
        (LABEL, "Label"),
        (URL, "URL"),
        (UUID, "UUID")
        )


def create_form_field_with_parameter(parameter):
    field = None
    label = parameter.get('display', parameter['name'])
    kind = parameter['kind']

    if parameter['kind'] == ParameterTypes.BOOLEAN:
        field =  forms.BooleanField(label=label)
    elif kind == ParameterTypes.NONE:
        field =  forms.BooleanField(label=label)
    elif kind == ParameterTypes.INTEGER:
        field = SliderField(label=label)
    elif kind == ParameterTypes.FLOAT:
        field = forms.FloatField(label=label)
    elif kind == ParameterTypes.STRING:
        field = forms.CharField(label=label)
    elif kind == ParameterTypes.FILE:
        field = forms.FileField(label=label)
    elif kind == ParameterTypes.ENUM:
        field = forms.ChoiceField(choices=parameter['choices'], label=label)

    return field


def create_form_class_with_parameter_list(param_list, name='dynform'):

    field_dict = {}

    for x in param_list:
        field = create_form_field_with_parameter(x)
        if field:
            field_dict[x['name']] = field

    return type(name, (forms.BaseForm,), dict(base_fields=field_dict, formfield_callback = custom_formfield_callback ))

def create_form_with_parameter_list(param_list, name='dynform', initial_dict={}):

    form_class = create_form_class_with_parameter_list(param_list, name)

    form = form_class(initial=initial_dict)

    return form
