from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.forms import BootstrapMixin

from . import rbac, services
from .models import Membership, Organization, Role, RoleAssignment


def _get_org(user, org_id) -> Organization:
    try:
        org = Organization.objects.get(pk=org_id)
    except (Organization.DoesNotExist, ValueError, ValidationError):
        raise Http404 from None
    if not rbac.has_perm(user, "org.view", org):
        rbac.require_perm(user, "org.view", org)  # audita e nega
    return org


@login_required
def organization_list(request):
    return render(request, "organizations/list.html", {"organizations": rbac.organizations_for(request.user)})


class RoleAssignForm(BootstrapMixin, forms.Form):
    user = forms.ModelChoiceField(label="Usuário", queryset=get_user_model().objects.none())
    role = forms.ChoiceField(label="Papel", choices=Role.choices)
    project = forms.ModelChoiceField(label="Projeto (vazio = toda a organização)", queryset=None, required=False)
    reason = forms.CharField(label="Motivo da concessão", max_length=255)

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.projects.models import Project

        self.fields["user"].queryset = get_user_model().objects.filter(
            memberships__organization=organization, memberships__status="active"
        ).order_by("username")
        self.fields["project"].queryset = Project.objects.filter(organization=organization)


@login_required
def organization_detail(request, org_id):
    org = _get_org(request.user, org_id)
    can_manage = rbac.has_perm(request.user, "roles.manage", org)
    form = RoleAssignForm(organization=org) if can_manage else None
    if request.method == "POST":
        rbac.require_perm(request.user, "roles.manage", org)
        form = RoleAssignForm(request.POST, organization=org)
        if form.is_valid():
            try:
                services.assign_role(
                    actor=request.user, organization=org, user=form.cleaned_data["user"],
                    role=form.cleaned_data["role"], project=form.cleaned_data["project"],
                    reason=form.cleaned_data["reason"],
                )
            except (PermissionDenied, ValidationError) as exc:
                messages.error(request, " ".join(getattr(exc, "messages", [str(exc)])))
            else:
                messages.success(request, "Papel concedido e registrado na auditoria.")
                return redirect("organizations:detail", org_id=org.pk)
    memberships = Membership.objects.filter(organization=org).select_related("user").order_by("user__username")
    assignments = (
        RoleAssignment.objects.filter(organization=org)
        .select_related("user", "project", "granted_by")
        .order_by("revoked_at", "user__username")
    )
    return render(
        request,
        "organizations/detail.html",
        {"org": org, "memberships": memberships, "assignments": assignments, "form": form, "can_manage": can_manage},
    )


@login_required
@require_POST
def revoke_role(request, org_id, assignment_id):
    org = _get_org(request.user, org_id)
    assignment = get_object_or_404(RoleAssignment, pk=assignment_id, organization=org)
    try:
        services.revoke_role(actor=request.user, assignment=assignment, reason=request.POST.get("reason", ""))
    except PermissionDenied as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Papel revogado (histórico preservado).")
    return redirect("organizations:detail", org_id=org.pk)
