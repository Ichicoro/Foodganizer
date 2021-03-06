import json

from django.http import HttpResponse
from django.core.serializers import serialize
from django.db.models import Q

from website.models import Item


def search_products(request):
    text = request.GET.get('text', None)
    if not text:
        return None  # TODO: Fix
    # items = []
    items = Item.objects.filter(Q(title__icontains=text) & (Q(custom_item_kitchen__isnull=True) | Q(custom_item_kitchen=8)))[:5]
    items_json = serialize("json", queryset=items) # sanitize_json_encoder_output() no more!
    return HttpResponse(items_json)


def get_product_by_code(request):
    code = request.GET.get('code', None)
    if not code:
        return HttpResponse("Missing", status=400)
    item = Item.objects.filter(upc=code).first()
    if item is None:
        return HttpResponse("No item with specified code", status=204)
    else:
        return HttpResponse(serialize("json", queryset=[item]))
