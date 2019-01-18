from django.shortcuts import render
from django.http import HttpResponseRedirect

from osu_acc.replay import handlers
from osu_acc.replay.forms import ReplayForm


def index(request):
    """
    View function for /replay/
    """
    if request.method == 'POST':
        form = ReplayForm(request.POST, request.FILES)
        if form.is_valid():
            replay_id = handlers.handle_replay(request.FILES['replay_file'])
            return HttpResponseRedirect('/replay/{}/'.format(replay_id))
    else:
        form = ReplayForm()

    return render(request, 'index.html', {'form': form})


def analytics(request, replay_id):
    """
    View function for /replay/<replay_id>
    """
    ctx = handlers.get_replay_context(replay_id)
    return render(request, 'analytics.html', ctx)
