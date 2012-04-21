

EXPERT_MODE_TAG = '$$EXPERT$$'

def set_expert_mode(request, state):
    request.session[EXPERT_MODE_TAG] = state

def get_expert_mode(request):
    return request.session.get(EXPERT_MODE_TAG, False)


def add_context_info(request):
    return {
        'session': request.session,
        'expert_mode': request.session.get(EXPERT_MODE_TAG, False)
    }