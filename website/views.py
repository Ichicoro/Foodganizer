from datetime import datetime
import json
import uuid
from typing import List, Optional

from urllib.parse import urlencode
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.messages.api import warning
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.db.utils import IntegrityError
from django.db.models import ProtectedError, ObjectDoesNotExist

from .models import Item, Kitchen, Membership, StoredItem, User, MembershipStatus, ShoppingCartItem
from django.forms.models import model_to_dict
from django.views.decorators.http import require_POST

# Create your views here.
from website.forms import UpdateUserForm, AddStoredItemForm, RemoveStoredItemForm, UpdateStoredItemForm, NewPostItForm, \
    AddShoppingCartItemForm, UpdateShoppingCartItemForm
from .forms import NewKitchenForm, NewKitchenItemForm, ShareKitchenForm, UpdateKitchenForm, UserRegisterForm, InviteExistingUsers


def _get_kitchen(request, id, status__in: List[MembershipStatus] = None):
    if request.user.is_anonymous:
        raise Kitchen.DoesNotExist()

    kitchens = request.user.kitchen_set.all()
    if status__in:
        filtered_kitchens = kitchens.filter(membership__status__in=status__in)
    else:
        filtered_kitchens = kitchens.filter(
            membership__status__in=[MembershipStatus.ADMIN, MembershipStatus.ACTIVE_MEMBERSHIP])

    return filtered_kitchens.get(id=id)


def _inviteUsersToKitchen(request, k: Kitchen, users: List[User]):
    warning_messages = []
    success_messages = []

    already_members = []
    invited_users = []
    joined_users = []
    for u in users:
        try:
            m = Membership(user=u, kitchen=k, status=MembershipStatus.PENDING_INVITATION, invited_by=request.user)
            m.save()
            invited_users.append(u)
        except IntegrityError:
            if u == request.user:
                warning_messages.append("You cannot invite yourself")
            else:
                m = Membership.objects.get(user=u, kitchen=k)
                if m.status in [MembershipStatus.ACTIVE_MEMBERSHIP, MembershipStatus.ADMIN]:
                    already_members.append(u)
                elif m.status == MembershipStatus.PENDING_INVITATION:
                    invited_users.append(u)
                elif m.status == MembershipStatus.PENDING_JOIN_REQUEST:
                    m.status = MembershipStatus.ACTIVE_MEMBERSHIP
                    m.invited_by = request.user
                    m.save()
                    joined_users.append(u)

    if len(already_members) == 1:
        warning_messages.append(f"@{already_members[0]} is already a member of {k.name}")
    elif len(already_members) > 1:
        warning_messages.append(
            ", ".join([f"@{user.username}" for user in already_members]) + f" are already members of {k.name}")

    if len(invited_users) == 1:
        success_messages.append(f"@{invited_users[0]} has been invited")
    elif len(invited_users) > 1:
        success_messages.append(", ".join([f"@{user.username}" for user in invited_users]) + f" have been invited")

    if len(joined_users) == 1:
        success_messages.append(f"@{joined_users[0]} joined now")
    elif len(joined_users) > 1:
        success_messages.append(", ".join([f"@{user.username}" for user in joined_users]) + f" joined now")

    return success_messages, warning_messages


def _load_post_data_from_session(request, prefix, keys):
    found_all = True
    new_post = {**request.POST}
    for k in keys:
        session_key = f"{prefix}__{k}"
        if session_key in request.session:
            new_post[k] = request.session[session_key]
            del request.session[session_key]
        else:
            found_all = False
    return new_post, found_all


def _save_post_data_to_session(request, prefix, keys):
    for k in keys:
        session_key = f"{prefix}__{k}"
        request.session[session_key] = request.POST[k]


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
            status = 400
    else:
        form = UserRegisterForm()
        status = 200
    return render(request, 'registration/signup.html', {'form': form}, status=status)


def quaggatest(request):
    return render(request, "pages/quaggatest.html", {})


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(data=request.POST, instance=request.user, files=request.FILES)
        if user_form.is_valid():
            user_form.save()
            return redirect("profile")
        else:
            messages.error(request, user_form.errors)
    else:
        user_form = UpdateUserForm(instance=request.user)

    return render(request, "pages/own_profile.html", {
        'user_form': user_form,
    })


def view_profile(request, username):
    http_status = 200
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        http_status = 404
        u = None

    return render(request, "pages/view_profile.html", {
        'user': u
    }, status=http_status)


@login_required
def new_kitchen(request):
    if request.method == 'POST':
        form = NewKitchenForm(request.POST)
        if form.is_valid():
            k = form.save()  # https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/#the-save-method

            m = Membership(user=request.user, kitchen=k, status=MembershipStatus.ADMIN)
            m.save()

            users = [data['User'] for data in form.cleaned_data.get('invite_other_users')]
            success_messages, warning_messages = _inviteUsersToKitchen(request, k, users)
            for sm in success_messages:
                messages.success(request, sm)
            for wm in warning_messages:
                messages.warning(request, wm)
            return redirect('kitchens')
        else:
            status = 400
    else:
        form = NewKitchenForm()
        status = 200
    return render(request, 'pages/new-kitchen.html', {'form': form}, status=status)


@login_required
def kitchen(request, id):
    try:
        k: Kitchen = _get_kitchen(request, id)
        user_membership = request.user.membership_set.get(kitchen=k)
    except (Kitchen.DoesNotExist, Membership.DoesNotExist):
        return redirect('kitchens')

    memberships = k.membership_set.filter(status__in=[MembershipStatus.ACTIVE_MEMBERSHIP, MembershipStatus.ADMIN])
    pending_memberships = k.membership_set.filter(
        status__in=[MembershipStatus.PENDING_INVITATION, MembershipStatus.PENDING_JOIN_REQUEST])
    stored_items = k.storeditem_set.all()
    shopping_cart = k.shoppingcartitem_set.all()
    postit = k.postit_set.all()

    invite_users_post, invite_users_form_open = _load_post_data_from_session(
        request=request,
        prefix="invite_existing_users_form",
        keys=InviteExistingUsers.declared_fields.keys()
    )

    share_kitchen_post, share_kitchen_form_open = _load_post_data_from_session(
        request=request,
        prefix="share_kitchen_form",
        keys=ShareKitchenForm.declared_fields.keys()
    )
    share_kitchen_post["enable_kitchen_sharing_link"] = k.public_access_uuid != None
    share_kitchen_post["join_confirmation_needed"] = k.join_confirmation

    if k.public_access_uuid != None:
        share_url = request.build_absolute_uri(reverse("share_kitchen_link", args=[k.public_access_uuid]))
        whatsapp_share_query_params = urlencode({"text": f"Hey, join my kitchen on Foodganizer! { share_url }"})
        telegram_share_query_params = urlencode({"url": share_url,"text": "Hey, join my kitchen on Foodganizer!"}) 
        email_share_query_params = urlencode({"subject": "Join my kitchen on Foodganizer!","body": f"Hey, join my kitchen on Foodganizer at this link: {share_url}"}).replace("+","%20")
    else:
        share_url = None
        whatsapp_share_query_params = None
        telegram_share_query_params = None
        email_share_query_params = None

    open_edit_kitchen_name = False
    if user_membership.status == MembershipStatus.ADMIN:
        if request.method == 'POST':
            update_kitchen_form = UpdateKitchenForm(request.POST, instance=k, files=request.FILES)
            if update_kitchen_form.is_valid():
                update_kitchen_form.save()
                return redirect("kitchen", id=k.id)
            else:
                open_edit_kitchen_name = True
        else:
            update_kitchen_form = UpdateKitchenForm(instance=k)
    else:
        update_kitchen_form = None

    return render(request, 'pages/kitchen.html', {
        'kitchen': k,
        'user_membership': user_membership,
        'memberships': memberships,
        'pending_memberships': pending_memberships,
        'stored_items': stored_items,
        'shopping_cart': shopping_cart,
        'remove_item_form': RemoveStoredItemForm(item_set=stored_items),
        'update_item_form': UpdateStoredItemForm(),
        'postit': postit,
        'new_postit_form': NewPostItForm(),
        'open_edit_kitchen_name': open_edit_kitchen_name,
        'update_kitchen_form': update_kitchen_form if (update_kitchen_form) else None,
        'invite_users_form': InviteExistingUsers(invite_users_post),
        'invite_users_form_open': invite_users_form_open,
        'share_kitchen_form': ShareKitchenForm(share_kitchen_post),
        'share_kitchen_form_open': share_kitchen_form_open,
        'edit_shopping_cart_item_form': UpdateShoppingCartItemForm(),
        'share_kitchen_url': share_url,
        'whatsapp_share_query_params': whatsapp_share_query_params,
        'telegram_share_query_params': telegram_share_query_params,
        'email_share_query_params': email_share_query_params
    })


@login_required
def kitchens(request):
    active_memberships = request.user.membership_set.filter(
        status__in=[MembershipStatus.ACTIVE_MEMBERSHIP, MembershipStatus.ADMIN])
    u: User = request.user
    invitations = u.membership_set.filter(status=MembershipStatus.PENDING_INVITATION)
    requests = u.membership_set.filter(status=MembershipStatus.PENDING_JOIN_REQUEST)
    return render(request, "pages/kitchens.html",
                  {'active_memberships': active_memberships, 'invitations': invitations, 'requests': requests})


def add_item_kitchen(request, id, is_shopping_cart_item=False):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
        return redirect('kitchens')

    custom_items = k.item_set.all()  # foreign key Item.custom_item_kitchen
    if request.method == 'POST':
        form = AddStoredItemForm(request.POST) if not is_shopping_cart_item else AddShoppingCartItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.added_by = request.user
            item.kitchen = k
            item.save()
            messages.success(request, f'Item "{item}" added successfully!')
            return redirect('kitchen', id=id)
        else:
            messages.error(request, 'Error, check console.')
            return render(request, "pages/add-item-kitchen.html", {
                'form': None,
                'kitchen': k,
                'custom_items': custom_items,
                'add_item_form': form,
                'new_custom_item_form': NewKitchenItemForm(),
                'back': reverse('kitchen', args=[id]),
                'is_shopping_cart_item': is_shopping_cart_item
            })
    elif request.method == 'PUT':
        pass
    else:
        return render(request, "pages/add-item-kitchen.html", {
            'form': None,
            'kitchen': k,
            'custom_items': custom_items,
            'add_item_form': AddShoppingCartItemForm() if is_shopping_cart_item else AddStoredItemForm(),
            'new_custom_item_form': NewKitchenItemForm(),
            'back': reverse('kitchen', args=[id]),
            'is_shopping_cart_item': is_shopping_cart_item
        })


@login_required
def add_storeditem_kitchen(request, id):
    return add_item_kitchen(request, id, is_shopping_cart_item=False)


@login_required
def add_cartitem_kitchen(request, id):
    return add_item_kitchen(request, id, is_shopping_cart_item=True)


@login_required
def update_cartitem_kitchen(request, id, item_id):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
        return redirect('kitchens')

    if request.method == 'POST':
        instance = k.shoppingcartitem_set.get(id=item_id)
        form = UpdateShoppingCartItemForm(request.POST or None, instance=instance)
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
def delete_cartitem_kitchen(request, id, item_id):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
        return redirect('kitchens')

    try:
        item = ShoppingCartItem.objects.get(id=item_id)
        item.delete()
    except ObjectDoesNotExist:
        messages.error(request, "Item does not exist")
    return redirect("kitchen", id=id)


@login_required
def move_cartitem_kitchen(request, id, item_id):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
        return redirect('kitchens')

    try:
        cart_item = ShoppingCartItem.objects.get(id=item_id)
        curr_time = datetime.now()
        item = StoredItem.objects.create(
            item=cart_item.item,
            kitchen=k,
            added_by=request.user,
            last_update=curr_time,
            created_at=curr_time,
            quantity=cart_item.quantity
        )
        item.save()
        cart_item.delete()
    except ObjectDoesNotExist:
        messages.error(request, "Item does not exist")
    return redirect("kitchen", id=id)


@login_required
def delete_storeditem_kitchen(request, id):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
        return redirect('kitchens')

    if request.method == 'POST':
        print(k.storeditem_set.all())
        form = RemoveStoredItemForm(request.POST, item_set=k.storeditem_set.all())
        print(form.data)
        if form.is_valid():
            item = form.cleaned_data.get("item")
            if form.cleaned_data.get("add_to_shopping_list"):
                curr_time = datetime.now()
                cart_item = ShoppingCartItem.objects.create(
                    item=item.item,
                    kitchen=k,
                    added_by=request.user,
                    last_update=curr_time,
                    created_at=curr_time,
                    quantity=item.quantity
                )
                cart_item.save()
            item.delete()
            messages.success(request, "Item deleted successfully!")
            return redirect('kitchen', id=id)
        else:
            print(form.errors)
            messages.error(request, "Error, please check console :(")
            return redirect('kitchen', id=id)


@login_required
def move_storeditem_kitchen(request, id, item_id):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
        return redirect('kitchens')

    try:
        stored_item = StoredItem.objects.get(id=item_id)
        curr_time = datetime.now()
        item = ShoppingCartItem.objects.create(
            item=stored_item.item,
            kitchen=k,
            added_by=request.user,
            last_update=curr_time,
            created_at=curr_time,
            quantity=stored_item.quantity
        )
        item.save()
        stored_item.delete()
    except ObjectDoesNotExist:
        messages.error(request, "Item does not exist")
    return redirect("kitchen", id=id)


@login_required
def update_storeditem_kitchen(request, id, item_id):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
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


@require_POST
@login_required
def new_kitchen_item(request, id):
    try:
        k = _get_kitchen(request, id)
    except Kitchen.DoesNotExist:
        return redirect('kitchens')

    form = NewKitchenItemForm(request.POST, files=request.FILES)
    if form.is_valid():
        i = form.save(commit=False)  # https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/#the-save-method
        i.added_by = request.user
        print(form.cleaned_data)
        upc_data = form.data["upc"]
        if upc_data == "":
            i.custom_item_kitchen = k
            messages.success(request, f'Item {i} created successfully in {k}!')
        else:
            messages.success(request, f'Item {i} created successfully!')
        i.save()
        next_url = request.GET.get("next", reverse("add_storeditem_kitchen", args={id}))
        return redirect(next_url)
    else:
        print(form.errors)
        messages.error(request, f"{form.errors}")
        return redirect(reverse("add_storeditem_kitchen", args={id}))


@login_required
def delete_customitem_kitchen(request, id, item_id):
    try:
        k = _get_kitchen(request, id)
    except ObjectDoesNotExist:
        return redirect('kitchens')

    try:
        item = Item.objects.get(id=item_id)
        item.delete()
    except ObjectDoesNotExist:
        messages.error(request, "Item does not exist")
    except ProtectedError:
        messages.warning(request,
                         "Item is in use. Please delete all stored items referencing this item before trying again")
    next_url = request.GET.get("next", reverse("add_storeditem_kitchen", args={id}))
    return redirect(next_url)


@login_required
@require_POST
def invite_users(request, id):
    try:
        k = _get_kitchen(request, id, status__in=[MembershipStatus.ADMIN])
    except Kitchen.DoesNotExist:
        return redirect('kitchens')

    if request.method == 'POST':
        form = InviteExistingUsers(request.POST)
        if form.is_valid():
            users = [data['User'] for data in form.cleaned_data.get('invite_other_users')]
            success_messages, warning_messages = _inviteUsersToKitchen(request, k, users)
            for sm in success_messages:
                messages.success(request, sm)
            for wm in warning_messages:
                messages.warning(request, wm)
        else:
            _save_post_data_to_session(request, "invite_existing_users_form",
                                       InviteExistingUsers.declared_fields.keys())

    return redirect('kitchen', id=id)


@login_required
@require_POST
def join_kitchen(request, id):
    try:
        k = _get_kitchen(request, id, status__in=[MembershipStatus.PENDING_INVITATION])
    except ObjectDoesNotExist:
        messages.error(request, "Kitchen not found")
        return redirect('kitchens')

    m = request.user.membership_set.get(kitchen=k)
    if m.status == MembershipStatus.PENDING_INVITATION:
        m.status = MembershipStatus.ACTIVE_MEMBERSHIP
        m.save()
        messages.success(request, f"Joined kitchen {k.name}")
        return redirect('kitchens')
    messages.error(request, "Generic error, cannot join kitchen")
    return redirect('kitchens')


@login_required
def set_kitchen_sharing(request, id):
    try:
        k: Kitchen = _get_kitchen(request, id, status__in=[MembershipStatus.ADMIN])
    except ObjectDoesNotExist:
        return redirect('kitchens')

    if request.method == 'POST':
        form = ShareKitchenForm(request.POST)
        if form.is_valid():
            enabled = form.cleaned_data.get('enable_kitchen_sharing_link')
            join_confirmation = form.cleaned_data.get('join_confirmation_needed')

            edit = False
            if enabled != bool(k.public_access_uuid):
                k.public_access_uuid = (uuid.uuid4() if enabled else None)
                edit = True
            if join_confirmation != k.join_confirmation:
                k.join_confirmation = join_confirmation
                edit = True

            if edit:
                k.save()
        else:
            _save_post_data_to_session(request, "share_kitchen_form", ShareKitchenForm.declared_fields.keys())

    return redirect('kitchen', id=id)


@login_required
def shared_kitchen(request, share_uuid):
    try:
        k: Kitchen = Kitchen.objects.get(public_access_uuid=share_uuid)
    except Kitchen.DoesNotExist:
        messages.error(request, 'No kitchen found, the link might be out of date')
        return redirect('kitchens')

    if request.method == "POST":
        try:
            m: Membership = Membership.objects.get(kitchen=k, user=request.user)
            if m.status in [MembershipStatus.ACTIVE_MEMBERSHIP, MembershipStatus.ADMIN]:
                messages.warning(request, f"You are already a member of {k}")
            elif m.status == MembershipStatus.PENDING_INVITATION:
                m.status = MembershipStatus.ACTIVE_MEMBERSHIP
                m.save()
                messages.success(request, f"{m.invited_by} accepted you into {k}")
            elif m.status == MembershipStatus.PENDING_JOIN_REQUEST:
                # pretend there isn't already a pending request
                m.delete()
                raise Membership.DoesNotExist()
            else:
                messages.error(request, "Something went wrong...")
        except Membership.DoesNotExist:
            if k.join_confirmation:
                requested_status = MembershipStatus.PENDING_JOIN_REQUEST
            else:
                requested_status = MembershipStatus.ACTIVE_MEMBERSHIP
            m = Membership(user=request.user, kitchen=k, status=requested_status)
            m.save()
            if k.join_confirmation:
                messages.success(request, f"Your request to join {k} has been sent to kitchen admins")
            else:
                messages.success(request, f"You joined {k} from shared link")
        if m.status in [MembershipStatus.ACTIVE_MEMBERSHIP, MembershipStatus.ADMIN]:
            return redirect("kitchen", id=k.id)
        else:
            return redirect("kitchens")
    else:
        return render(request, "pages/join-shared-kitchen.html", {"kitchen": k})


@require_POST
def delete_membership(request, id):
    try:
        m: Membership = Membership.objects.get(id=id)
        if request.user == m.user:
            k: Kitchen = m.kitchen
        else:
            k: Kitchen = _get_kitchen(request, m.kitchen.id, status__in=[MembershipStatus.ADMIN])
    except (Kitchen.DoesNotExist, Membership.DoesNotExist):
        return redirect('kitchens')

    if request.user == m.user:
        if m.status in [MembershipStatus.ADMIN, MembershipStatus.ACTIVE_MEMBERSHIP]:
            _users = k.users.filter(membership__status__in=[MembershipStatus.ADMIN, MembershipStatus.ACTIVE_MEMBERSHIP])
            _other_users = _users.exclude(id=request.user.id)
            _admins = k.users.filter(membership__status=MembershipStatus.ADMIN)
            # if you are last user
            if len(_other_users) == 0:
                m.delete()
                k.delete()
            # if you are last admin
            elif len(_admins) == 1 and _admins.first().id == request.user.id:
                _new_admin: Membership = _other_users.first().membership_set.get(kitchen=k)
                _new_admin.status = MembershipStatus.ADMIN
                _new_admin.save()
                m.delete()
            else:
                m.delete()
            messages.success(request, f"You left {k}")
        elif m.status == MembershipStatus.PENDING_INVITATION:
            m.delete()
            messages.success(request, f"You declined @{m.invited_by}'s invitation to join {k}")
        elif m.status == MembershipStatus.PENDING_JOIN_REQUEST:
            m.delete()
            messages.success(request, f"You have withdrawn your request to join {k}")
        return redirect('kitchens')
    else:
        if m.status in [MembershipStatus.ACTIVE_MEMBERSHIP, MembershipStatus.ADMIN]:
            m.delete()
            messages.success(request, f"User @{m.user} has been kicked")
        elif m.status == MembershipStatus.PENDING_INVITATION:
            m.delete()
            messages.success(request, f"Invitation for @{m.user} withdrawn")
        elif m.status == MembershipStatus.PENDING_JOIN_REQUEST:
            m.delete()
            messages.success(request, f"@{m.user}'s join request has been rejected")
        return redirect('kitchen', id=k.id)


@require_POST
def promote_membership(request, id):
    try:
        m: Membership = Membership.objects.get(id=id)
        if request.user == m.user:
            messages.error(request, "You can't promote yourself")
            return redirect('kitchen', id=m.kitchen.id)
        else:
            k: Kitchen = _get_kitchen(request, m.kitchen.id, status__in=[MembershipStatus.ADMIN])
    except Membership.DoesNotExist:
        return redirect('kitchens')
    except Kitchen.DoesNotExist:
        messages.error(request, "You don't have the required permissions")
        return redirect('kitchen', id=m.kitchen.id)
    
    if m.status == MembershipStatus.ADMIN:
        messages.error(request, f"@{m.user.username} is already an admin of {m.kitchen.name}")
        return redirect('kitchen', id=m.kitchen.id)
    elif m.status == MembershipStatus.ACTIVE_MEMBERSHIP:
        m.status = MembershipStatus.ADMIN
        m.save()
        messages.success(request, f"@{m.user.username} promoted to admin")
        return redirect('kitchen', id=m.kitchen.id)
    else:
        messages.error(request, f"@{m.user.username} is not a member of {m.kitchen.name}")
        return redirect('kitchen', id=m.kitchen.id)


@login_required
def create_postit(request, id):
    k = _get_kitchen(request, id)
    if not k:
        messages.error(request, "Invalid kitchen")
        return redirect('kitchens')

    if request.method == 'POST':
        form = NewPostItForm(request.POST)
        if form.is_valid():
            i = form.save(commit=False)
            i.author = request.user
            i.kitchen = k
            i.save()
            messages.success(request, f'PostIt added successfully to {k}!')
            return redirect('kitchen', id=id)


@login_required
def edit_postit(request, id, postit_id):
    k = _get_kitchen(request, id)
    if not k:
        messages.error(request, "Invalid kitchen")
        return redirect('kitchens')
    if request.method == 'POST':
        instance = k.postit_set.get(id=postit_id)
        form = NewPostItForm(request.POST or None, instance=instance)
        print(form.data)
        if form.is_valid():
            editable_instance = form.save(commit=False)
            editable_instance.last_edited_by = request.user
            editable_instance.save()
            messages.success(request, "Item updated successfully!")
            return redirect('kitchen', id=id)
        else:
            print(form.errors)
            messages.error(request, "Error, please check console :(")
            return redirect('kitchen', id=id)


@login_required
def delete_postit(request, id, postit_id):
    k = _get_kitchen(request, id)
    if not k:
        return redirect('kitchens')

    try:
        postit = k.postit_set.get(id=postit_id)
        if postit:
            print(postit)
            postit.delete()
            messages.success(request, "Item deleted successfully!")
        else:
            messages.error(request, "Invalid PostIt :/")
    except ObjectDoesNotExist:
        messages.error(request, "Invalid PostIt :/")
    return redirect('kitchen', id=id)
