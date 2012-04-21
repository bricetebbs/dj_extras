from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


from forms import ParameterTypes

from regexes import LEGAL_FILENAME_REGEX, LEGAL_PATHNAME_REGEX, HEX_REGEX

TITLE_FIELD_LENGTH = 250
MODEL_NAME_FIELD_LENGTH = 100
MODEL_SHORT_NAME_LENGTH = 25
MODEL_LABEL_FIELD_LENGTH = 50
MODEL_PATH_NAME_LENGTH = 500
MODEL_FILE_NAME_LENGTH = 250
MODEL_DIGEST_NAME_LENGTH = 64
SHORT_MESSAGE_FIELD_LENGTH = 250

class PercentageField(models.FloatField):
    """
    A field for storing percentages in the model
    """
    def __init__(self, *args, **kwargs):
        super(PercentageField, self).__init__(*args, **kwargs)


class CleanLabelField(models.CharField):
    """
    A field for text labels which only allows clean characters that are ASCII and can be in a filename with no trouble
    Used mostly for internally facing names or things like Account Numbers which have a rigid format
    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = MODEL_LABEL_FIELD_LENGTH
        kwargs['validators'] = kwargs.get('validators',[]) + [RegexValidator(regex=LEGAL_FILENAME_REGEX)]
        super(CleanLabelField, self).__init__(*args, **kwargs)

class NameField(models.CharField):
    """
    Used for the real names of things like people or places.

    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = MODEL_NAME_FIELD_LENGTH

        super(NameField, self).__init__(*args, **kwargs)

class TitleField(models.CharField):
    """
    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = TITLE_FIELD_LENGTH

        super(TitleField, self).__init__(*args, **kwargs)



class ShortMessageField(models.CharField):
    """
    Used for the real names of things like people or places.

    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = SHORT_MESSAGE_FIELD_LENGTH

        super(ShortMessageField, self).__init__(*args, **kwargs)



class ShortNameField(models.CharField):
    """
    Used for tnames of things we know will be short

    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = MODEL_SHORT_NAME_LENGTH

        super(ShortNameField, self).__init__(*args, **kwargs)


class DigestField(models.CharField):
    """
    Used for she256 digests

    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = MODEL_DIGEST_NAME_LENGTH

        kwargs['validators'] = kwargs.get('validators',[]) + [RegexValidator(regex=HEX_REGEX)]

        super(DigestField, self).__init__(*args, **kwargs)


class FileNameField(models.CharField):
    """
    For storing a filename in a model
    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = MODEL_FILE_NAME_LENGTH
        kwargs['validators'] = kwargs.get('validators',[]) + [RegexValidator(regex=LEGAL_FILENAME_REGEX)]
        super(FileNameField, self).__init__(*args, **kwargs)


class PathNameField(models.CharField):
    """
    For storing a full filesystem path name in a model
    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = MODEL_PATH_NAME_LENGTH
        kwargs['validators'] = kwargs.get('validators',[]) + [RegexValidator(regex=LEGAL_PATHNAME_REGEX)]
        super(PathNameField, self).__init__(*args, **kwargs)

class ChildClassViewer(models.Model):
    _item_subclass = CleanLabelField()

    class Meta:
        abstract = True

    def as_child(self):
        return getattr(self, self._item_subclass)

    def sub_class(self):
        return self._item_subclass

    def save(self, *args, **kwargs):
        self._item_subclass = self.__class__.__name__.lower()   # save what kind we are.
        super(ChildClassViewer, self).save(*args, **kwargs) # Call the "real" save() method.


class TrackingChangesDateUser(models.Model):
    changed_by = models.ForeignKey(User, related_name="%(class)s_changed_by")
    changed_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class TrackingCreatedDateUser(models.Model):
    created_by = models.ForeignKey(User, related_name="%(class)s_created_by")
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class TrackingFullDateUser(TrackingCreatedDateUser, TrackingChangesDateUser):
    class Meta:
        abstract = True


class TrackingFullDate(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    changed_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HistoryTrack(TrackingChangesDateUser):
    """
    Base Class for objects which track history of database changes
    """

    class Meta:
        ordering = ['-changed_on']
        abstract = True


    def __unicode__(self):
        return self.changed_by.username + u":" + unicode(self.changed_on)



#
# Some classes for making notes which can be attached to other objects
# See tests.py for example
#
class AnnotationNote(TrackingFullDateUser):

    note_txt = models.TextField()


    class Meta:
        abstract = True

    def make_history(self, user, txt):
        pass
    
    def update(self, user, txt, with_history=True):
        self.changed_by = user
        if with_history:
           self.make_history(user, txt)
        self.note_txt = txt
        self.save()

    def get_recent_items(self, count):
        # return self.linkedhistory_set.all().order_by('-changed_on')[0:count]
        pass


class NoteHistory(HistoryTrack):
    old_txt = models.TextField()
    class Meta:
        abstract =True
        ordering = ['-changed_on']


#
# SOme classes for making "Done" checkboxes which can be attached to other objects
# see tests.py for examples
#
class WorkflowItem(models.Model):
    """
    A base class for workflow item status.

    You Can make a derived class of this so you can FK to a Case you want to track
    
    You must define get_tracking_manager!!!
    """
    name = CleanLabelField(help_text="Internal Name for this")
    display_name = NameField(help_text="External Name")
    kind = models.PositiveSmallIntegerField(default=0,
                                            choices = ((0, "Boolean"), (1, "Enum")),
                                            help_text="Data type for status. Currently not used")
    
    link_info = models.CharField(max_length=200)
    priority = models.PositiveSmallIntegerField(default=0, help_text="Order to show in list")

    class Meta:
        abstract = True
        ordering = ['priority']


    def current_tracker(self):
        try:
            tracker=self.get_tracking_manager().filter(workflow_item = self).order_by('-changed_on')[0]
            return tracker
        except IndexError:
            return None

    def get_current_state(self):
        tracker = self.current_tracker()
        if tracker:
            return tracker.state
        else:
            return -1

    def get_display_name(self):
        """
        This is so child classes can override this
        """
        return self.display_name
    
    def update(self, user, state):
        return self.get_tracking_manager().create(workflow_item = self, changed_by=user, state = state)


    def get_info_html(self):
        tracker = self.current_tracker()
        if tracker and tracker.state:
            return u"- by %s on %s" % (tracker.changed_by.username, str(tracker.changed_on.ctime()))
        else:
            return ""
    # Derived classes must implement this!!

    def get_tracking_manager(self):
        # return ChildOfWorkFlowItemStatus.objects
        raise AssertionError

    def get_display_class(self):
        return "workflow_widget"
    def __unicode__(self):
        return u"%s" % self.display_name



class WorkflowItemStatus(HistoryTrack):
    """
    A base class for trackers of workflow item status.
    Just need to add a link to the derived class of WorkflowItem and
    you should be good to go
    """
    state = models.PositiveIntegerField(default=0, help_text="The state of the item.")

    #
    # Need to add a link field called
    #
    # workflow_item
    class Meta:
        abstract = True
        ordering = ('-changed_on',)

    def __unicode__(self):
        return u"%d: %s %s" % (self.state, str(self.changed_on), self.changed_by.username)


class OptionInfo(models.Model):
    name = CleanLabelField()
    display_name = NameField(blank=True)

    type = models.PositiveIntegerField(default=0, choices=ParameterTypes.CHOICES, help_text='The datatype of the argument or None if its just a flag')
    min_values = models.PositiveSmallIntegerField(default=1)
    max_values = models.PositiveSmallIntegerField(default=1)
    required = models.BooleanField(default = False)
    switch_txt = models.CharField(max_length=20, blank=True, help_text="Like -f")
    is_output = models.BooleanField(default=False, help_text='Is this parameter output by the tool')
    is_stdout = models.BooleanField(default=False, help_text='This should be the capture of stdout')
    file_format = CleanLabelField(blank=True)
    priority = models.PositiveSmallIntegerField(default =0)

    option_documentation = models.TextField(blank=True, null=True, help_text='Info to show the user')
    option_info = models.TextField(blank=True, null=True, help_text="For Enum:options separated with | For others range")
    default_value = models.TextField(blank=True, null=True, help_text='For NONE type options set this to the string "True" to force the option by default')

    class Meta:
        abstract = True

    def get_ui_name(self):
        return self.display_name if self.display_name else self.name

    def __unicode__(self):
        return self.get_ui_name()



#
# Stuff for managing the Inbox
#
class InboxFileStoreTrackFile(models.Model):
    filename = FileNameField()
    folder = CleanLabelField() # could be lab name
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User)


class InboxFileStoreTrackItem(models.Model):
    file = models.ForeignKey(InboxFileStoreTrackFile)
    item = CleanLabelField() # could be sample id
    used = models.BooleanField()
    used_on = models.DateTimeField(auto_now=True)
    used_by = models.ForeignKey(User)

#
##
##
##
#class ResultTableKind(models.Model):
#    name=CleanLabelField()
#
#    def add_columns(self, columns):
#        for idx,col in enumerate(columns):
#            column, created, update = get_or_create_or_update(ResultTableColumnHeader,
#                                                          dict(table=self,
#                                                          name = col['name']),
#
#                                                          dict(
#                                                              display_name = col['display_name'],
#                                                              kind = col['kind'],
#                                                              size_info = col.get('size_info', 0),
#                                                              extra_info = col.get('extra_info', {}),
#                                                              order = idx,
#                                                              visibility= col.get('visibility', ResultTableVisibility.VISIBLE),
#                                                              index = col.get('index', False)
#                                                        )
#                                                    )
#            if col.get('enum_labels', []):
#                for label in col['enum_labels']:
#                    ResultTableEnumLabel.objects.get_or_create(column=column,
#                                                    value = label[0],
#                                                    display_name=label[1])

#class ResultTableColumnHeader(models.Model):
#    table = models.ForeignKey(ResultTableKind)
#    name = CleanLabelField()
#    display_name = CleanLabelField()
#
#    kind = models.PositiveIntegerField(choices=ParameterTypes.CHOICES, default=ParameterTypes.INTEGER)
#    size_info = models.PositiveIntegerField(help_text="Mostly for text length 0 is LONGTEXT")
#    extra_info = JSONField(help_text="For anything else that doesn't fit in this so far")
#    index = models.PositiveSmallIntegerField(default=0)
#
#    visibility = models.PositiveSmallIntegerField(choices=ResultTableVisibility.CHOICES,
#                                                  default=ResultTableVisibility.VISIBLE)
#    order = models.PositiveIntegerField(default=0)
#
#    def to_dict(self):
#        return dict(name=self.name,
#                    display_name=self.display_name,
#                    kind=self.kind,
#                    size_info=self.size_info,
#                    extra_info= self.extra_info,
#                    index = self.index,
#                    visibility = self.visibility,
#                    enum_labels = [(x.value, x.display_name) for x in self.resulttableenumlabel_set.all()]
#                )
#
#class ResultTableEnumLabel(models.Model):
#    column = models.ForeignKey(ResultTableColumnHeader)
#    display_name = CleanLabelField()
#    value = models.PositiveSmallIntegerField()

#class ResultTableMixin(models.Model):
#
#    # Maybe this just mixes into AnalysisFilterApplication or links to it
#    #table_kind = models.ForeignKey(ResultTableKind, null=True, blank=True)
#
#
#
#    class Meta:
#        abstract = True
#
#class ResultTable(ResultTableMixin):
#    file_path = FileNameField()
#
#    def get_pathname(self):
#        return self.file_path







