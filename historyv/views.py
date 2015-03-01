from django.shortcuts import render

# Create your views here.


def showhistory(request):
	return render(request, 'history.html')