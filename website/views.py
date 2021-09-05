import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.forms.models import model_to_dict

from .models import Item, Kitchen, Membership, StoredItem, User

# Create your views here.
from website.forms import UpdateUserForm, AddStoredItemForm, RemoveStoredItemForm, UpdateStoredItemForm
from .forms import NewKitchenForm, NewKitchenItemForm, UserRegisterForm


def _getKitchen(request, id):
    if request.user.is_anonymous:
        return None
    return request.user.kitchen_set.get(id=id)


def index(request):
    return render(request, "pages/index.html")


def signup(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/signup.html', {'form': form})


def quaggatest(request):
    return render(request, "pages/quaggatest.html", {})


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(data=request.POST, instance=request.user, files=request.FILES)
        if user_form.is_valid():
            user_form.save()
    else:
        user_form = UpdateUserForm(instance=request.user)
    print(f"{user_form.files=}")  # TODO: Remove me
    print(f"{user_form.is_valid()=}")  # TODO: Remove me
    return render(request, "pages/own_profile.html", {
        'user_form': user_form,
    })


def view_profile(request, username):
    return render(request, "pages/view_profile.html", {
        'user': User.objects.get(username=username)
    })


@login_required
def new_kitchen(request):
    if request.method == 'POST':
        form = NewKitchenForm(request.POST)
        if form.is_valid():
            k = form.save()  # https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/#the-save-method
            m = Membership(user=request.user, kitchen=k, is_admin=True)
            m.save()
            kitchen_name = form.cleaned_data.get('name')
            invite_other_users = form.cleaned_data.get('invite_other_users')
            # TODO: idk send an email to this addresses or something
            messages.success(request, f'Kitchen "{kitchen_name}" created successfully!')
            return redirect('index')
    else:
        form = NewKitchenForm()
    return render(request, 'pages/new-kitchen.html', {'form': form})


@login_required
def kitchen(request, id):
    k = _getKitchen(request, id)
    if not k:
        return redirect('kitchens')

    users = k.users.all()
    memberships = k.membership_set.all()
    members = []
    stored_items = k.storeditem_set.all()
    print(stored_items[0].quantity)
    postit = k.postit_set.all()
    for u in users:
        m = memberships.get(user=u)
        members.append({"user": u, "is_admin": m.is_admin})
    return render(request, 'pages/kitchen.html', {
        'kitchen': k,
        'members': members,
        'stored_items': stored_items,
        'remove_item_form': RemoveStoredItemForm(item_set=stored_items),
        'update_item_form': UpdateStoredItemForm(),
        'postit': postit
    })


@login_required
def kitchens(request):
    user = request.user
    kitchens = []
    if user.is_authenticated:
        kitchens = user.kitchen_set.all()

    return render(request, "pages/kitchens.html", {'kitchens': kitchens})


@login_required
def add_item_kitchen(request, id):
    k = _getKitchen(request, id)
    if not k:
        return redirect('kitchens')
    custom_items = k.item_set.all()  # foreign key Item.custom_item_kitchen
    if request.method == 'POST':
        form = AddStoredItemForm(request.POST)
        if form.is_valid():
            si = form.save(commit=False)
            si.added_by = request.user
            si.kitchen = k
            si.save()
            messages.success(request, f'Item "{si}" added successfully!')
            return redirect('kitchen', id=id)
        else:
            messages.error(request, 'Error, check console.')
            print(form.is_valid())
            print(form.fields['item'])
            print(f"{form.errors=}")
            print(f"{form.non_field_errors()=}")
            return render(request, "pages/add-item-kitchen.html", {
                'form': None,
                'kitchen': k,
                'custom_items': custom_items,
                'add_item_form': form,
                'new_custom_item_form': NewKitchenItemForm(),
                'back': reverse('kitchen', args=[id])
            })
    elif request.method == 'PUT':
        pass
    else:
        return render(request, "pages/add-item-kitchen.html", {
            'form': None,
            'kitchen': k,
            'custom_items': custom_items,
            'add_item_form': AddStoredItemForm(),
            'new_custom_item_form': NewKitchenItemForm(),
            'back': reverse('kitchen', args=[id])
        })


@login_required
def delete_item_kitchen(request, id):
    k = _getKitchen(request, id)
    if not k:
        return redirect('kitchens')
    if request.method == 'POST':
        print(k.storeditem_set.all())
        form = RemoveStoredItemForm(request.POST, item_set=k.storeditem_set.all())
        print(form.data)
        if form.is_valid():
            custom_items = form.cleaned_data.get("item").delete()
            messages.success(request, "Item deleted successfully!")
            return redirect('kitchen', id=id)
        else:
            print(form.errors)
            messages.error(request, "Error, please check console :(")
            return redirect('kitchen', id=id)


@login_required
def update_item_kitchen(request, id, item_id):
    k = _getKitchen(request, id)
    if not k:
        return redirect('kitchens')
    if request.method == 'POST':
        instance = k.storeditem_set.get(id=item_id)
        form = UpdateStoredItemForm(request.POST or None, instance=instance)
        print(form.data)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully!")
            return redirect('kitchen', id=id)
        else:
            print(form.errors)
            messages.error(request, "Error, please check console :(")
            return redirect('kitchen', id=id)


@login_required
def new_kitchen_item(request, id):
    k = _getKitchen(request, id)
    if not k:
        return redirect('kitchens')

    if request.method == 'POST':
        form = NewKitchenItemForm(request.POST, files=request.FILES)
        if form.is_valid():
            i = form.save(commit=False)  # https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/#the-save-method
            i.added_by = request.user
            i.custom_item_kitchen = k
            i.save()
            messages.success(request, f'Item {i} added successfully to {k}!')
            return redirect('add_item_kitchen', id=id)
    # else:
    #     form = NewKitchenItemForm()
    # return render(request, 'pages/new-kitchen-item.html', {'form': form})
