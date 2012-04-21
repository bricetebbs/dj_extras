# coding=utf8
from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from models import AnnotationNote, NoteHistory
from models import WorkflowItem, WorkflowItemStatus

from forms import ParameterTypes
import os
import pprint
from result_table import create_result_reader, create_result_writer

class ModelToAnnotate(models.Model):
    foo = models.IntegerField(default=10)
    def __unicode__(self):
        return "Annotate Object %d" % self.foo


class TestNoteHistory(NoteHistory):
    note_object = models.ForeignKey('TestNote')


class TestNote(AnnotationNote):
    base = models.ForeignKey(ModelToAnnotate)

    def make_history(self, user, txt):
        """
        This function saves a history object when update is called
        """
        return TestNoteHistory.objects.create(changed_by=user, note_object=self, old_txt = self.note_txt)

    def get_recent_items(self, count):
        return self.testnotehistory_set.all().order_by('-changed_on')[0:count]


class TestWorkFlowItem(WorkflowItem):
    base_item = models.ForeignKey(ModelToAnnotate)
    
    def get_tracking_manager(self):
        return TestWorkFlowStatus.objects

class TestWorkFlowStatus(WorkflowItemStatus):
    # this link has to be named work_flow_item
    workflow_item = models.ForeignKey(TestWorkFlowItem)



class NoteTest(TestCase):
    fixtures = ['users.json']

    def test_notes(self):
        bo = ModelToAnnotate.objects.create(foo=20)
        u = User.objects.all()[0]
        u2 = User.objects.all()[1]
        tn = TestNote.objects.create(base=bo, note_txt = "Hey there", created_by=u, changed_by=u)
        tn.update(u, "MORE", with_history=True)
        tn.update(u, "THAN", with_history=True)
        tn.update(u2, "THIS", with_history=True)
        
        tn.update(u2, "CAN", with_history=False)

        for tn in TestNote.objects.all():
            self.assertEqual(tn.changed_by, u2)
            self.assertEqual(tn.note_txt,"CAN")
            hl = list( tn.testnotehistory_set.all())
            self.assertEqual(len(hl), 3)
            self.assertEqual(hl[0].changed_by, u2)

            self.assertEqual(hl[1].changed_by, u)
            self.assertEqual("MORE", hl[1].old_txt)
        


class WorkflowTest(TestCase):
    fixtures = ['users.json']

    def test_workflow(self):
        wi = ModelToAnnotate.objects.create(foo=30)
        u = User.objects.all()[0]

        tw = TestWorkFlowItem.objects.create(name="MyItem",
                                             base_item = wi,
                                     display_name="Nice Display of Item")

        self.assertEqual(tw.get_current_state(),-1)
        tw.update(u, 2)
        self.assertEqual(tw.get_current_state(),2)
        
        tw.update(u,0)

        self.assertEqual(tw.get_current_state(),0)

        
        self.assertEqual(tw.base_item,wi)

class ResultTableTest(TestCase):

    def test_result_table(self):
        def format_text(s):
            return "%s from func:" % s[2:]

        headers = (
            dict(name='intcol1', kind=ParameterTypes.INTEGER,  display_name='Integer C1', size_info = 0),
            dict(name='floatcol2', kind=ParameterTypes.INTEGER,  display_name='Float C2', size_info = 0),
            dict(name='stringcol3', kind=ParameterTypes.STRING,  display_name='String C3', size_info = 40),
            dict(name='textcol4', kind=ParameterTypes.STRING,  display_name='Long String C4', size_info = 0),
        )



        records = (
            dict(intcol1=2, floatcol2=2.3, stringcol3=u'Eéaya', textcol4=u'Num is 2'),
            dict(intcol1=9, floatcol2=2.3, stringcol3=u'Mon Frere', textcol4=u'Num is 9'),
            dict(intcol1=10, floatcol2=99.3, stringcol3=u'Ma Soeur', textcol4=u'Num is 8'),
            dict(intcol1=22, floatcol2=-1.3e-12, stringcol3=u'alsda', textcol4=u'Num is 22'),
        )

        indicies = []

        TEST_FILE = 'tmptest$$.db'

        try:
            os.unlink(TEST_FILE)
        except OSError:
            pass


        rw = create_result_writer(TEST_FILE, headers)
        for rec in records:
            index = rw.add_result(rec)
            indicies.append(index)
        rw.close()

        rr = create_result_reader(TEST_FILE, headers)

        self.assertEquals(len(records), rr.get_item_count())

        for idx, index in enumerate(indicies):
            ditem = rr.get_result_dict(index)
            self.assertDictEqual(ditem, records[idx])


        rr.add_filter("intcol1~LE~10")
        p = rr.get_result_tuples( (('intcol1', 'ASC'), ('stringcol3', 'DESC')), limit=2, offset=0)

        self.assertEqual(p,[(1, 2, 2.3, u'E\xe9aya', u'Num is 2'), (2, 9, 2.3, u'Mon Frere', u'Num is 9')])


        view = [dict(name='pair1', group=('intcol1', 'floatcol2'), format=u'%d -> %f', display_name='Pair 1'),
                dict(name='stringcol3', format="-> %s -<"),
                dict(name='textcol4', format=format_text)]

        rr.set_view_info(view)

        headers =  rr.get_display_headers()

        self.assertEqual([('pair1', 'Pair 1'), ('stringcol3', u'String C3'), ('textcol4', u'Long String C4')], headers)


        tup = rr.get_result_tuple(1)
        interp  = rr.interpret_tuple(tup)
        self.assertEqual((u'2 -> 2.300000', u'-> E\xe9aya -<', u'm is 2 from func:'), interp)

        rr.close()
        os.unlink('tmptest$$.db')


class MyTest(TestCase):
    def no_crazy_talk(self):
        qs = ResultTable.objects.using('dummy').filter(kind=10)
     #   print unicode(qs.query)