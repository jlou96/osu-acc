from django.shortcuts import render
from django.http import HttpResponseRedirect

from . import queries
from .forms import ReplayForm


def index(request):
    print('index view method')
    if request.method == 'POST':
        print('Got POST request')
        form = ReplayForm(request.POST, request.FILES)
        if form.is_valid():
            replay_id = queries.handle_replay(request.FILES['replay_file'])
            return HttpResponseRedirect('/replay/{}/'.format(replay_id))
    else:
        print('Not a POST request')
        form = ReplayForm()

    return render(request, 'index.html', {'form': form})


def analytics(request, replay_id):
    print('analytics view method')
    # TODO

    return render(request, 'analytics.html', {'replay_id': replay_id})
