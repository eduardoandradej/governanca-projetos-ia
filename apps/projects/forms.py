import json

from django import forms
from django.contrib.auth import get_user_model

from apps.core.forms import BootstrapMixin

from .models import Portfolio, Project

PROJECT_FIELDS = [
    "code", "name", "portfolio", "description", "business_case", "business_objectives", "target_indicators",
    "platform_type", "deployment_approach", "technology_metadata", "sponsor", "manager", "technical_lead",
    "priority", "criticality", "data_classification", "start_date", "due_date", "planned_cost", "currency",
]


class TechnologyMetadataField(forms.CharField):
    """Entrada simples 'chave: valor' por linha, convertida em objeto JSON validado."""

    def prepare_value(self, value):
        if isinstance(value, dict):
            return "\n".join(f"{k}: {v}" for k, v in value.items())
        if isinstance(value, str) and value.startswith("{"):
            try:
                return self.prepare_value(json.loads(value))
            except ValueError:
                return value
        return value or ""

    def to_python(self, value):
        value = super().to_python(value)
        result = {}
        for line in (value or "").splitlines():
            if not line.strip():
                continue
            if ":" not in line:
                raise forms.ValidationError("Use o formato 'chave: valor' em cada linha.")
            k, v = line.split(":", 1)
            result[k.strip()[:60]] = v.strip()[:200]
        return result


class ProjectForm(BootstrapMixin, forms.ModelForm):
    technology_metadata = TechnologyMetadataField(
        label="Tecnologias/fornecedores (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Metadado descritivo, um por linha (ex.: 'Orquestração: Kubernetes'). Nenhuma regra depende de marca.",
    )

    class Meta:
        model = Project
        fields = PROJECT_FIELDS
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "business_case": forms.Textarea(attrs={"rows": 4}),
            "business_objectives": forms.Textarea(attrs={"rows": 3}),
            "target_indicators": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_user_model().objects.filter(
            memberships__organization=organization, memberships__status="active"
        ).order_by("full_name", "username")
        for name in ("sponsor", "manager", "technical_lead"):
            self.fields[name].queryset = users
        self.fields["portfolio"].queryset = Portfolio.objects.filter(organization=organization)
        self.fields["code"].help_text = "Único na organização. Ex.: IA-2026-01"

    def clean_code(self):
        return (self.cleaned_data.get("code") or "").strip().upper()

    def clean(self):
        cleaned = super().clean()
        start, due = cleaned.get("start_date"), cleaned.get("due_date")
        if start and due and due < start:
            self.add_error("due_date", "O prazo final deve ser posterior ao início.")
        return cleaned


class StatusChangeForm(BootstrapMixin, forms.Form):
    to_status = forms.ChoiceField(label="Novo status")
    reason = forms.CharField(label="Justificativa / decisão formal", widget=forms.Textarea(attrs={"rows": 3}), min_length=10)

    def __init__(self, *args, choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["to_status"].choices = choices
