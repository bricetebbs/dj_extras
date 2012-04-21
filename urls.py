from django.conf.urls.defaults import *
urlpatterns = patterns('',


    url (
        regex = '^xyzzy/$',
        view =  'dj_extras.views.toggle_expert_mode',
        name = 'toggle_expert_mode'
    )
    ,


)