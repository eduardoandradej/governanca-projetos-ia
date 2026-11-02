"""Exportação CSV segura, autorizada, filtrada por escopo e auditada (RN-014, T-020)."""

import csv
import io

from django.http import HttpResponse

from apps.auditlog import services as audit
from apps.auditlog.models import ExportRecord

DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n", "|", "%")


def neutralize(value) -> str:
    """Neutraliza células que planilhas interpretariam como fórmula (CSV injection)."""
    text = "" if value is None else str(value)
    if text and text[0] in DANGEROUS_PREFIXES:
        return "'" + text
    return text


def csv_response(*, user, report: str, header: list[str], rows, organization_id=None, filters=None,
                 filename="relatorio.csv") -> HttpResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow([neutralize(h) for h in header])
    count = 0
    for row in rows:
        writer.writerow([neutralize(c) for c in row])
        count += 1
    ExportRecord.objects.create(user=user, organization_id=organization_id, report=report, filters=filters or {},
                                row_count=count)
    audit.record("export.csv", actor=user, organization_id=organization_id,
                 after={"report": report, "rows": count, "filters": filters or {}})
    response = HttpResponse("﻿" + buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
