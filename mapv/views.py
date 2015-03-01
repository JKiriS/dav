from django.shortcuts import render

# Create your views here.


def showchina(request):
	return render(request, 'china.html')