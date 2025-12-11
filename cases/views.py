"""
Case Management Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from cases.models import Case, CaseParty, CaseNote, CaseTimeline
from cases.forms import CaseForm, CaseNoteForm, CaseTimelineForm
from audit.models import AuditLog


@login_required
def case_list(request):
    """List all cases user has access to."""
    cases = Case.objects.filter(
        parties__user=request.user,
        parties__is_active=True,
        is_active=True
    ).distinct().order_by('-created_at')

    return render(request, 'cases/case_list.html', {'cases': cases})


@login_required
def select_case(request):
    """
    Case selection screen.
    Fixes redirect-loop issue.
    """
    cases = Case.objects.filter(
        parties__user=request.user,
        parties__is_active=True,
        is_active=True
    ).distinct()

    count = cases.count()

    # 0️⃣ No cases → Create first case
    if count == 0:
        messages.info(request, "Create your first case to get started.")
        return redirect("cases:case_create")

    # 1️⃣ One case → Auto activate
    if count == 1:
        request.session["active_case_id"] = str(cases.first().id)
        return redirect("core:dashboard")

    # 2️⃣ Multiple cases → Allow selection
    if request.method == "POST":
        selected_id = request.POST.get("case_id")
        valid = CaseParty.objects.filter(
            case_id=selected_id,
            user=request.user,
            is_active=True
        ).exists()

        if valid:
            request.session["active_case_id"] = selected_id
            return redirect("core:dashboard")

        messages.error(request, "Invalid case selection.")
        return redirect("cases:select_case")

    return render(request, "cases/select_case.html", {"cases": cases})


@login_required
def case_detail(request, case_id):
    """View case details."""
    case = get_object_or_404(Case, id=case_id)

    # Permission check
    if not CaseParty.objects.filter(case=case, user=request.user, is_active=True).exists():
        messages.error(request, "You do not have access to this case.")
        return redirect("cases:case_list")

    context = {
        "case": case,
        "case_parties": case.parties.filter(is_active=True).select_related("user"),
        "recent_notes": case.notes.filter(Q(is_private=False) | Q(created_by=request.user)).order_by('-created_at')[:10],
        "timeline_events": case.timeline_events.filter(is_key_event=True).order_by('-event_date')[:10],
    }

    return render(request, "cases/case_detail.html", context)


@login_required
def case_create(request):
    """Create a new case."""
    if request.method == "POST":
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()

            # Add creator as petitioner
            CaseParty.objects.create(
                case=case,
                user=request.user,
                role="petitioner",
                can_edit_financials=True,
                can_upload_evidence=True
            )

            # Write audit log (safe)
            try:
                AuditLog.objects.create(
                    user=request.user,
                    action="create",
                    description=f"Created case: {case.case_title}",
                    case=case,
                    ip_address=get_client_ip(request)
                )
            except Exception:
                pass

            # Set as active case
            request.session["active_case_id"] = str(case.id)

            messages.success(request, "Case created successfully!")
            return redirect("core:dashboard")
    else:
        form = CaseForm()

    return render(request, "cases/case_form.html", {"form": form, "action": "Create"})


@login_required
def case_update(request, case_id):
    """Update case details."""
    case = get_object_or_404(Case, id=case_id)

    # Permission check
    if not CaseParty.objects.filter(case=case, user=request.user, is_active=True).exists():
        messages.error(request, "You do not have access to this case.")
        return redirect("cases:case_list")

    if request.method == "POST":
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            try:
                AuditLog.objects.create(
                    user=request.user,
                    action="update",
                    description=f"Updated case: {case.case_title}",
                    case=case,
                    ip_address=get_client_ip(request)
                )
            except Exception:
                pass

            messages.success(request, "Case updated successfully!")
            return redirect("cases:case_detail", case_id=case.id)
    else:
        form = CaseForm(instance=case)

    return render(request, "cases/case_form.html", {"form": form, "action": "Update", "case": case})


@login_required
def note_create(request, case_id):
    """Create a case note."""
    case = get_object_or_404(Case, id=case_id)

    if not CaseParty.objects.filter(case=case, user=request.user, is_active=True).exists():
        messages.error(request, "You do not have access to this case.")
        return redirect("cases:case_list")

    if request.method == "POST":
        form = CaseNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.case = case
            note.created_by = request.user
            note.save()

            messages.success(request, "Note added successfully!")
            return redirect("cases:case_detail", case_id=case.id)
    else:
        form = CaseNoteForm()

    return render(request, "cases/note_form.html", {"form": form, "case": case})


@login_required
def timeline_create(request, case_id):
    """Create a timeline event."""
    case = get_object_or_404(Case, id=case_id)

    if not CaseParty.objects.filter(case=case, user=request.user, is_active=True).exists():
        messages.error(request, "You do not have access to this case.")
        return redirect("cases:case_list")

    if request.method == "POST":
        form = CaseTimelineForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.case = case
            event.created_by = request.user
            event.save()

            messages.success(request, "Timeline event added successfully!")
            return redirect("cases:timeline_list", case_id=case.id)
    else:
        form = CaseTimelineForm()

    return render(request, "cases/timeline_form.html", {"form": form, "case": case})


@login_required
def timeline_list(request, case_id):
    """View case timeline."""
    case = get_object_or_404(Case, id=case_id)

    if not CaseParty.objects.filter(case=case, user=request.user, is_active=True).exists():
        messages.error(request, "You do not have access to this case.")
        return redirect("cases:case_list")

    events = case.timeline_events.all().order_by('-event_date')

    return render(request, "cases/timeline_list.html", {"case": case, "events": events})


def get_client_ip(request):
    """Extract client IP safely."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded.split(",")[0] if forwarded else request.META.get("REMOTE_ADDR")
