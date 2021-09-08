import json

from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.db.utils import IntegrityError
from .models import Item, Kitchen, Membership, StoredItem, User, MembershipStatus
from django.forms.models import model_to_dict

# Create your views here.
from website.forms import UpdateUserForm, AddStoredItemForm, RemoveStoredItemForm, UpdateStoredItemForm
from .forms import NewKitchenForm, NewKitchenItemForm, UserRegisterForm, InviteExistingUsers

def _getKitchen(request, id, status=MembershipStatus.ACTIVE_MEMBERSHIP):
    return _getAllKitchens(request, status=status).get(id=id)

def _getAllKitchens(request, status=MembershipStatus.ACTIVE_MEMBERSHIP):
    if request.user.is_anonymous:
        return None
    return request.user.kitchen_set.filter(membership__status=status)
        

def _inviteUsersToKitchen(request, k: Kitchen, users: list[User]):
    warning_messages = []
    success_messages = []

    already_members = []
    invited_users = []
    joined_users = []
    for u in users:
        try:
            m = Membership(user=u, kitchen=k, status=MembershipStatus.PENDING_INVITATION)
            m.save()
            invited_users.append(u)
        except IntegrityError:
            if u == request.user:
                warning_messages.append("You cannot invite yourself")
            else:
                m = Membership.objects.get(user=u, kitchen=k)
                if m.status == MembershipStatus.ACTIVE_MEMBERSHIP:
                    already_members.append(u)
                elif m.status == MembershipStatus.PENDING_INVITATION:
                    invited_users.append(u)
                elif m.status == MembershipStatus.PENDING_JOIN_REQUEST:
                    m.status == MembershipStatus.ACTIVE_MEMBERSHIP
                    m.save()
                    joined_users.append(u)
    
    if len(already_members) == 1:
        warning_messages.append(f"@{already_members[0]} is already a member of {k.name}")
    elif len(already_members) > 1:
        warning_messages.append(", ".join([f"@{user.username}" for user in already_members]) + f" are already members of {k.name}")

    if len(invited_users) == 1:
        success_messages.append(f"@{invited_users[0]} has been invited")
    elif len(invited_users) > 1:
        success_messages.append(", ".join([f"@{user.username}" for user in invited_users]) + f" have been invited")

    if len(joined_users) == 1:
        success_messages.append(f"@{joined_users[0]} joined now")
    elif len(joined_users) > 1:
        success_messages.append(", ".join([f"@{user.username}" for user in joined_users]) + f" joined now")
  
    return success_messages, warning_messages
    

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
            k = form.save() # https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/#the-save-method
            
            m = Membership(user=request.user, kitchen=k, is_admin=True)
            m.save()
            
            users = [data['User'] for data in form.cleaned_data.get('invite_other_users')]
            success_messages, warning_messages = _inviteUsersToKitchen(request, k, users)
            for sm in success_messages: 
                messages.success(request, sm)
            for wm in warning_messages:
                messages.warning(request, wm)
            return redirect('kitchens')
    else:
        form = NewKitchenForm()
    return render(request, 'pages/new-kitchen.html', {'form': form})


@login_required
def kitchen(request, id):
    k = _getKitchen(request, id)
    if not k:
        return redirect('kitchens')

    memberships = k.membership_set.filter(status=MembershipStatus.ACTIVE_MEMBERSHIP)
    stored_items = k.storeditem_set.all()
    postit = k.postit_set.all()

    if 'invite_other_users_post' in request.session:
        invite_other_users = request.session['invite_other_users_post']
        del request.session['invite_other_users_post']
        invite_users_form = InviteExistingUsers({ **request.POST, "invite_other_users": invite_other_users })
        invite_users_form_open = True
    else: 
        invite_users_form = InviteExistingUsers()
        invite_users_form_open = False

    return render(request, 'pages/kitchen.html', {
        'kitchen': k,
        'memberships': memberships,
        'stored_items': stored_items,
        'remove_item_form': RemoveStoredItemForm(item_set=stored_items),
        'update_item_form': UpdateStoredItemForm(),
        'postit': postit,
        'invite_users_form': invite_users_form,
        'invite_users_form_open': invite_users_form_open
    })


@login_required
def kitchens(request):
    kitchens = _getAllKitchens(request)
    pending_kitchens = _getAllKitchens(request, status=MembershipStatus.PENDING_INVITATION)
    print(pending_kitchens)
    return render(request, "pages/kitchens.html", {'kitchens': kitchens, 'pending_kitchens': pending_kitchens})


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

@login_required
def invite_users(request, id):
    k = _getKitchen(request, id)
    if not k:
        return redirect('kitchens')

    if request.method == 'POST':
        form = InviteExistingUsers(request.POST)
        print("POST", (request.POST))
        print("form", form)
        print("errors", form.errors)
        print("cleaned data", form.cleaned_data.get('invite_other_users'))
        if form.is_valid():
            users = [data['User'] for data in form.cleaned_data.get('invite_other_users')]
            success_messages, warning_messages = _inviteUsersToKitchen(request, k, users)
            for sm in success_messages: 
                messages.success(request, sm)
            for wm in warning_messages:
                messages.warning(request, wm) 
        else:
            request.session['invite_other_users_post'] = request.POST["invite_other_users"]

    return redirect('kitchen', id=id)

@login_required
def join_kitchen(request, id):
    k = _getKitchen(request, id, status=MembershipStatus.PENDING_INVITATION)
    if not k:
        messages.error("Kitchen not found")
        return redirect('kitchens')
    
    m = request.user.membership_set.get(kitchen=k)
    if m.status == MembershipStatus.PENDING_INVITATION:
        m.status = MembershipStatus.ACTIVE_MEMBERSHIP
        m.save()
        messages.success(request, f"Joined kitchen {k.name}")
        return redirect('kitchens')
    messages.error(request, "Generic error, cannot join kitchen")
    return redirect('kitchens')


def search_item(request):
    pass
    # request
