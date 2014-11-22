
from django.conf import settings

def get_or_none(model, **kwargs):
    """
    Gets the model you specify or returns none if it doesn't exist.
    """
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def update_model_from_dict(instance, d):
    """
    Update a model instance's fieled from the specified dictionary
    This does not save the model
    """
    field_dict = dict((x.name, getattr(instance, x.name)) for x in instance._meta.fields)
    changed = {}
    for field in d:
        if field in field_dict:
            if getattr(instance, field) != d[field]:
                changed[field] = d[field]

    if changed:
        for x in changed:
            setattr(instance, x, changed[x])
        return True
    else:
        return False

def get_or_create_or_update(model_class, key_dict, values_dict):
    """
    If a model matching key_dict for model_class exists then update it with values dict
    If it doesn't exist then create it used the defaults from values dict
    """
    updated = False
    key_dict['defaults'] = values_dict
    instance, created = model_class.objects.get_or_create(**key_dict)
    if not created:
        updated = update_model_from_dict(instance, values_dict)
        if updated:
            instance.save()
    return instance, created, updated


def get_array_from_raw(name, raw):
    """
    For parsing out jquery array ajax stuff
    """
    array = []
    for term in raw.split('&'):
        if term.startswith(name + '%5B%5D='):
            array.append(term[len(name)+7:])
    return array
