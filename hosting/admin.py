from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.core import urlresolvers
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin

from .models import Profile, Place, Phone, Website, Condition, ContactPreference
from .admin_utils import (
    ShowConfirmedMixin, ShowDeletedMixin,
    CountryMentionedOnlyFilter, ProfileHasUserFilter
)
from .widgets import AdminImageWithPreviewWidget


admin.site.disable_action('delete_selected')

# admin.site.unregister(Group)
admin.site.unregister(User)


class PlaceInLine(ShowConfirmedMixin, ShowDeletedMixin, admin.StackedInline):
    model = Place
    extra = 0
    can_delete = False
    show_change_link = True
    fields = (
        'country', 'state_province', ('city', 'closest_city'), 'postcode', 'address',
        ('latitude', 'longitude'),
        'description', 'short_description',
        ('max_guest', 'max_night', 'contact_before'), 'conditions',
        'available', 'in_book', ('tour_guide', 'have_a_drink'), 'sporadic_presence',
        'display_confirmed', 'is_deleted',
    )
    raw_id_fields = ('owner', 'family_members', 'authorized_users', 'checked_by')
    readonly_fields = ('display_confirmed', 'is_deleted',)
    fk_name = 'owner'
    classes = ('collapse',)


class PhoneInLine(ShowDeletedMixin, admin.TabularInline):
    model = Phone
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ('number', 'country', 'type', 'comments', 'confirmed_on', 'is_deleted')
    readonly_fields = ('confirmed_on', 'is_deleted',)
    fk_name = 'profile'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'email', 'password_algorithm', 'profile_link',
        'last_login', 'date_joined',
        'is_active', 'is_staff', 'is_superuser',
    )
    list_display_links = ('id', 'username')
    list_select_related = ('profile',)
    date_hierarchy = 'date_joined'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Supervisors'), {'fields': ('groups',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('date_joined',)

    def password_algorithm(self, obj):
        if len(obj.password) == 32:
            return _("MD5 (weak)")
        if obj.password[:13] == 'pbkdf2_sha256':
            return 'PBKDF2 SHA256'
    password_algorithm.short_description = _("Password algorithm")

    def profile_link(self, obj):
        try:
            fullname = obj.profile if (obj.profile.first_name or obj.profile.last_name) else "--."
            return format_html('<a href="{url}">{name}</a>', url=obj.profile.get_admin_url(), name=fullname)
        except AttributeError:
            return '[ - ]'
    profile_link.short_description = _("profile")
    profile_link.admin_order_field = 'profile'


class TrackingModelAdmin(ShowConfirmedMixin):
    fields = (
        ('checked_on', 'checked_by'), 'display_confirmed', 'deleted_on',
    )
    readonly_fields = ('display_confirmed',)


@admin.register(Profile)
class ProfileAdmin(TrackingModelAdmin, ShowDeletedMixin, admin.ModelAdmin):
    list_display = (
        'id', '__str__', 'title', 'first_name', 'last_name',
        'birth_date', #'avatar', 'description',
        'user__email', 'user_link',
        'confirmed_on', 'checked_by', 'is_deleted', 'modified',
    )
    list_display_links = ('id', '__str__')
    search_fields = [
        'id', 'first_name', 'last_name', 'user__email', 'user__username',
    ]
    list_filter = (
        'confirmed_on', 'checked_on', 'deleted_on', ProfileHasUserFilter,
    )
    date_hierarchy = 'birth_date'
    fields = (
        'user', 'title', 'first_name', 'last_name', 'names_inversed', 'birth_date',
        'description', 'avatar', 'contact_preferences',
    ) + TrackingModelAdmin.fields
    raw_id_fields = ('user', 'checked_by')
    radio_fields = {'title': admin.HORIZONTAL}
    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWithPreviewWidget},
    }
    inlines = [PlaceInLine,] #PhoneInLine] # https://code.djangoproject.com/ticket/26819

    def user__email(self, obj):
        try:
            return obj.user.email
        except AttributeError:
            return '-'
    user__email.short_description = _("Email")
    user__email.admin_order_field = 'user__email'

    def user_link(self, obj):
        try:
            link = urlresolvers.reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{url}">{username}</a>', url=link, username=obj.user)
        except AttributeError:
            return '-'
    user_link.short_description = _("user")
    user_link.admin_order_field = 'user'

    def get_queryset(self, request):
        return super(ProfileAdmin, self).get_queryset(request).select_related('user', 'checked_by')


@admin.register(Place)
class PlaceAdmin(TrackingModelAdmin, ShowDeletedMixin, admin.ModelAdmin):
    list_display = (
        'city', 'postcode', 'state_province', 'display_country',
        'display_latitude', 'display_longitude',
        # 'max_host', 'max_night', 'contact_before',
        'available', 'in_book',
        'owner_link',
        'confirmed_on', 'checked_by', 'is_deleted', 'modified',
    )
    list_display_links = (
        'city', 'state_province', 'display_country',
        'display_latitude', 'display_longitude',
    )
    search_fields = [
        'address', 'city', 'postcode', 'country', 'state_province',
        'owner__first_name', 'owner__last_name', 'owner__user__email',
    ]
    list_filter = (
        'confirmed_on', 'checked_on', 'in_book', 'available', 'deleted_on',
        CountryMentionedOnlyFilter,
    )
    fields = (
        'owner', 'country', 'state_province', ('city', 'closest_city'), 'postcode', 'address',
        ('latitude', 'longitude'),
        'description', 'short_description',
        ('max_guest', 'max_night', 'contact_before'), 'conditions',
        'available', 'in_book', ('tour_guide', 'have_a_drink'), 'sporadic_presence',
        'family_members', 'authorized_users',
    ) + TrackingModelAdmin.fields
    raw_id_fields = ('owner', 'authorized_users', 'checked_by',)
    filter_horizontal = ('family_members',)

    def display_country(self, obj):
        return "%s: %s" % (obj.country.code, obj.country.name)
    display_country.short_description = _("country")
    display_country.admin_order_field = 'country'

    def display_latitude(self, obj):
        return "%.4f" % float(obj.latitude) if obj.latitude else None
    display_latitude.short_description = _("latitude")
    display_latitude.admin_order_field = 'latitude'

    def display_longitude(self, obj):
        return "%.4f" % float(obj.longitude) if obj.longitude else None
    display_longitude.short_description = _("longitude")
    display_longitude.admin_order_field = 'longitude'

    def owner_link(self, obj):
        return format_html('<a href="{url}">{name}</a>', url=obj.owner.get_admin_url(), name=obj.owner)
    owner_link.short_description = _("owner")
    owner_link.admin_order_field = 'owner'

    class FamilyMember(Profile):
        class Meta:
            ordering = ['first_name', 'last_name', 'id']
            proxy = True
        def __str__(self):
            return "(p:%05d, u:%05d) %s" % (self.id,
                                            self.user_id if self.user else 0,
                                            super(PlaceAdmin.FamilyMember, self).__str__())

    def get_queryset(self, request):
        cached_qs = cache.get('PlaceQS:Req:'+request.path)
        if cached_qs:
            return cached_qs
        qs = super(PlaceAdmin, self).get_queryset(request).select_related('owner__user', 'checked_by')
        qs = qs.defer('owner__description')
        try:
            if not self.single_object_view:
                qs = qs.defer('description', 'short_description')
        except:
            pass
        cache.set('PlaceQS:Req:'+request.path, qs, 5)
        return qs

    def get_field_queryset(self, db, db_field, request):
        if db_field.name == 'family_members':
            return PlaceAdmin.FamilyMember.objects.defer('description').select_related('user')
        return super(PlaceAdmin, self).get_field_queryset(db, db_field, request)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.single_object_view = True
        return super(PlaceAdmin, self).change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        self.single_object_view = True
        return super(PlaceAdmin, self).add_view(
            request, form_url=form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        self.single_object_view = False
        return super(PlaceAdmin, self).changelist_view(request, extra_context=extra_context)


@admin.register(Phone)
class PhoneAdmin(TrackingModelAdmin, ShowDeletedMixin, admin.ModelAdmin):
    list_display = ('number_intl', 'profile_link', 'country_code', 'display_country', 'type', 'is_deleted')
    list_select_related = ('profile__user',)
    search_fields = ['number', 'country']
    list_filter = ('type', 'deleted_on', CountryMentionedOnlyFilter)
    fields = (
        'profile', 'number', 'country', 'type', 'comments',
    ) + TrackingModelAdmin.fields
    raw_id_fields = ('profile',)
    radio_fields = {'type': admin.VERTICAL}

    def number_intl(self, obj):
        return obj.number.as_international
    number_intl.short_description = _("number")
    number_intl.admin_order_field = 'number'

    def profile_link(self, obj):
        return format_html('<a href="{url}">{name}</a>', url=obj.profile.get_admin_url(), name=obj.profile)
    profile_link.short_description = _("profile")
    profile_link.admin_order_field = 'profile'

    def country_code(self, obj):
        return obj.number.country_code
    country_code.short_description = _("country code")

    def display_country(self, obj):
        return "%s: %s" % (obj.country.code, obj.country.name)
    display_country.short_description = _("country")
    display_country.admin_order_field = 'country'


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr')
    prepopulated_fields = {'slug': ("name",)}

    fields = ('name', 'abbr', 'slug', 'latex', 'icon')

    def icon(self, obj):
        return format_html('<img src="{static}img/cond_{slug}.svg" style="width:4ex; height:4ex;"/>',
                           static=settings.STATIC_URL, slug=obj.slug)
    icon.short_description = _("image")

    def add_view(self, request, form_url='', extra_context=None):
        self.readonly_fields = ()
        return super(ConditionAdmin, self).add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.readonly_fields = ('icon',)
        return super(ConditionAdmin, self).change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)


@admin.register(Website)
class WebsiteAdmin(TrackingModelAdmin, admin.ModelAdmin):
    list_display = ('url', 'profile')
    search_fields = [
        'url',
        'profile__first_name', 'profile__last_name', 'profile__user__email', 'profile__user__username',
    ]
    fields = ('profile', 'url') + TrackingModelAdmin.fields
    raw_id_fields = ('profile',)


@admin.register(ContactPreference)
class ContactPreferenceAdmin(admin.ModelAdmin):
    pass
