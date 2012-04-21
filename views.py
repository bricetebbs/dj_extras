
from django.shortcuts import  render
from session import get_expert_mode, set_expert_mode

def simple_error(request, error_text):
    return render(request, 'general/error.html', dict(error_text=error_text))


def toggle_expert_mode(request):
    if not request.user.is_superuser:
        return simple_error(request, "You are not authorized for this operation")
    em = get_expert_mode(request)
    em = not em
    set_expert_mode(request, em)

    return render(request, 'general/message.html', dict(message_text="Expert Mode is now %s" % str(em)))
