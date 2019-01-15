from django.shortcuts import render
from django.http import HttpResponse

import queries


def index(request):
    if request == 'POST' and request.FILES['replay_file']:
        queries.handle_replay(request.FILES['replay_file'])

    return render(request, 'index.html')
