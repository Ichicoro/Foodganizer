from django.http import JsonResponse

def search_products(request):
    return JsonResponse({
        'foo': 'bar'
    })