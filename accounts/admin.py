# from django.contrib import admin
# from django.contrib import messages
# from django.template.response import TemplateResponse
# from django.urls import path
# from django.utils.translation import gettext_lazy as _
# from django.core.exceptions import PermissionDenied

# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth.forms import AdminPasswordChangeForm
# from .models import MyUser


# class UserAdmin(BaseUserAdmin):
#     model = MyUser

#     # ✅ Fields shown in the user list in admin
#     list_display = ('email','username')
#     list_filter = ('is_superuser',)  # only use fields that exist
#     date_hierarchy = 'created_at'
#     list_per_page = 10
#     save_as = True
#     save_on_top = True





#     # ✅ For ordering users in admin list
#     ordering = ('email',)

#     # ✅ Fields on the user detail page
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal Info', {'fields': ('username','gender','location','earnings',)}),
#         ('Permissions', {'fields': ('is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login',)}),
#     )

#     # ✅ Fields on the "Add user" form
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'username', 'password1', 'password2', 'is_superuser')}
#         ),
#     )

#     # ✅ This adds the per-user "Change password" view
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path(
#                 '<id>/password/',
#                 self.admin_site.admin_view(self.user_change_password),
#                 name='auth_user_password_change',
#             ),
#         ]
#         return custom_urls + urls

#     def user_change_password(self, request, id, form_url=''):
#         user = self.get_object(request, id)
#         if not self.has_change_permission(request, user):
#             raise PermissionDenied

#         if request.method == 'POST':
#             form = AdminPasswordChangeForm(user, request.POST)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, "Password changed successfully.")
#                 return TemplateResponse(
#                     request,
#                     'admin/auth/user/change_password_done.html',
#                     {'title': 'Password changed successfully.'}
#                 )
#         else:
#             form = AdminPasswordChangeForm(user)

#         context = {
#             'title': _('Change password: %s') % user.get_username(),
#             'form': form,
#             'is_popup': False,
#             'add': False,
#             'change': True,
#             'has_view_permission': self.has_view_permission(request, user),
#             'has_editable_inline_admin_formsets': False,
#             'opts': self.model._meta,
#             'original': user,
#             'save_as': False,
#             'show_save': True,
#             **self.admin_site.each_context(request),
#         }

#         return TemplateResponse(
#             request,
#             'admin/auth/user/change_password.html',
#             context,
#         )


# # ✅ Register your user model with the custom UserAdmin
# admin.site.register(MyUser, UserAdmin)
