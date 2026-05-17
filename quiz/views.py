import json
from datetime import timedelta
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import QuizAnswerForm
from .models import Choix, Question, Quiz, Reponse, Resultat, Session, StyleEnum
from .services.llm_service import generate_recommendations


def _finalize_session(session):
    reponses = session.reponses.select_related("choix")
    score_visuel = 0
    score_auditif = 0
    score_kinesthesique = 0
    neutral_count = 0
    for reponse in reponses:
        style = reponse.choix.style
        if style == StyleEnum.VISUEL:
            score_visuel += 1
        elif style == StyleEnum.AUDITIF:
            score_auditif += 1
        elif style == StyleEnum.KINESTHESIQUE:
            score_kinesthesique += 1
        elif style == StyleEnum.NEUTRE:
            neutral_count += 1
    resultat = Resultat.objects.create(
        session=session,
        score_visuel=score_visuel,
        score_auditif=score_auditif,
        score_kinesthesique=score_kinesthesique,
        neutral_count=neutral_count,
        style_dominant=StyleEnum.VISUEL,
    )
    resultat.calculer()
    session.terminee = True
    session.date_fin = timezone.now()
    session.save(update_fields=["terminee", "date_fin"])
    generate_recommendations(session)
    return session.id


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "quiz/landing.html")


@login_required
def dashboard_view(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin_dashboard")
    sessions = (
        Session.objects.filter(utilisateur=request.user, terminee=True)
        .select_related("resultat")
        .order_by("-date_fin")
    )
    last_result = None
    evolution_data = []
    if sessions.exists():
        first_session = sessions.first()
        last_result = first_session.resultat if hasattr(first_session, "resultat") else None
        for session in reversed(sessions[:6]):
            if hasattr(session, "resultat") and session.date_fin:
                evolution_data.append(
                    {
                        "date": session.date_fin.strftime("%d/%m"),
                        "visuel": session.resultat.pct_visuel,
                        "auditif": session.resultat.pct_auditif,
                        "kinesthesique": session.resultat.pct_kinesthesique,
                        "dominant": session.resultat.style_dominant,
                    }
                )
    return render(
        request,
        "quiz/dashboard.html",
        {
            "sessions": sessions,
            "last_result": last_result,
            "evolution_data": evolution_data,
            "evolution_json": json.dumps(evolution_data),
            "has_evolution": len(evolution_data) >= 2,
        },
    )


@login_required
def quiz_start_view(request):
    quiz = Quiz.objects.filter(actif=True).first()
    if not quiz:
        messages.error(request, "Aucun quiz actif n'est disponible.")
        return redirect("dashboard")
    session = Session.objects.create(utilisateur=request.user, quiz=quiz)
    request.session["session_id"] = session.id
    return redirect("quiz_question", numero=1)


@login_required
def quiz_question_view(request, numero):
    session_id = request.session.get("session_id")
    if not session_id:
        messages.error(request, "Aucune session de quiz en cours.")
        return redirect("quiz_start")

    session = get_object_or_404(Session, id=session_id, utilisateur=request.user, terminee=False)
    questions = list(session.quiz.get_questions())
    total = len(questions)
    if total == 0:
        messages.error(request, "Ce quiz ne contient aucune question.")
        return redirect("dashboard")
    if numero < 1 or numero > total:
        return redirect("quiz_question", numero=1)

    question = questions[numero - 1]
    progress_pct = round((numero - 1) / total * 100)

    if request.method == "POST":
        form = QuizAnswerForm(request.POST)
        if form.is_valid():
            choice_id = form.cleaned_data["choice_id"]
            choix = get_object_or_404(Choix, id=choice_id, question=question)
            Reponse.objects.update_or_create(
                session=session, question=question, defaults={"choix": choix}
            )
            if numero >= total:
                session_id = _finalize_session(session)
                request.session.pop("session_id", None)
                return redirect("results", session_id=session_id)
            return redirect("quiz_question", numero=numero + 1)
        messages.error(request, "Veuillez selectionner une reponse valide.")
    else:
        form = QuizAnswerForm()

    return render(
        request,
        "quiz/quiz.html",
        {
            "session": session,
            "question": question,
            "choix": question.choix.all().order_by("lettre"),
            "numero": numero,
            "total": total,
            "progress_pct": progress_pct,
            "form": form,
        },
    )


@login_required
def quiz_submit_view(request):
    session_id = request.session.get("session_id")
    session = get_object_or_404(Session, id=session_id, utilisateur=request.user, terminee=False)
    session_id = _finalize_session(session)
    request.session.pop("session_id", None)
    return redirect("results", session_id=session_id)


@login_required
def results_view(request, session_id):
    session = get_object_or_404(
        Session.objects.select_related("resultat", "recommandation", "utilisateur"), id=session_id
    )
    if session.utilisateur != request.user:
        return HttpResponseForbidden("Acces interdit.")

    resultat = session.resultat
    recommandation = session.recommandation
    scores_json = json.dumps(
        {
            "labels": ["Visuel", "Auditif", "Kinesthesique"],
            "scores": [resultat.pct_visuel, resultat.pct_auditif, resultat.pct_kinesthesique],
        }
    )
    return render(
        request,
        "quiz/results.html",
        {
            "session": session,
            "resultat": resultat,
            "recommandation": recommandation,
            "scores_json": scores_json,
        },
    )


@staff_member_required(login_url="/accounts/login/")
def admin_dashboard_view(request):
    total_users = User.objects.filter(is_staff=False).count()
    total_sessions = Session.objects.filter(terminee=True).count()
    style_distribution = Resultat.objects.values("style_dominant").annotate(count=Count("id")).order_by("-count")
    total_resultats = Resultat.objects.count()
    styles_data = []
    for item in style_distribution:
        pct = round(item["count"] / total_resultats * 100, 1) if total_resultats > 0 else 0
        styles_data.append({"style": item["style_dominant"], "count": item["count"], "pct": pct})
    recent_sessions = Session.objects.filter(terminee=True).select_related("utilisateur", "resultat").order_by("-date_fin")[:10]
    weekly_stats = []
    for i in range(4):
        week_start = timezone.now() - timedelta(weeks=i + 1)
        week_end = timezone.now() - timedelta(weeks=i)
        count = Session.objects.filter(terminee=True, date_fin__gte=week_start, date_fin__lt=week_end).count()
        weekly_stats.append({"week": f"S-{i+1}", "count": count})
    weekly_stats.reverse()
    quiz = Quiz.objects.filter(actif=True).first()
    questions = Question.objects.filter(quiz=quiz).prefetch_related("choix").order_by("ordre") if quiz else []
    return render(
        request,
        "quiz/admin_dashboard.html",
        {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "styles_data": styles_data,
            "styles_json": json.dumps(styles_data),
            "recent_sessions": recent_sessions,
            "weekly_stats": weekly_stats,
            "weekly_json": json.dumps(weekly_stats),
            "questions": questions,
            "quiz": quiz,
            "choices_config": [
                ("A", "Visuel", "VISUEL"),
                ("B", "Auditif", "AUDITIF"),
                ("C", "Kinesthesique", "KINESTHESIQUE"),
                ("D", "Neutre", "NEUTRE"),
            ],
        },
    )


@staff_member_required(login_url="/accounts/login/")
def admin_question_add(request):
    if request.method == "POST":
        quiz = Quiz.objects.filter(actif=True).first()
        enonce = request.POST.get("enonce", "").strip()
        if enonce and quiz:
            last_order = Question.objects.filter(quiz=quiz).count()
            question = Question.objects.create(quiz=quiz, enonce=enonce, ordre=last_order + 1)
            for lettre in ["A", "B", "C", "D"]:
                texte = request.POST.get(f"choix_{lettre}", "").strip()
                style = request.POST.get(f"style_{lettre}", "NEUTRE")
                if texte:
                    Choix.objects.create(question=question, texte=texte, style=style, lettre=lettre)
            messages.success(request, f'Question "{enonce[:40]}..." ajoutee avec succes.')
    return redirect("admin_dashboard")


@staff_member_required(login_url="/accounts/login/")
def admin_question_delete(request, question_id):
    if request.method == "POST":
        try:
            question = Question.objects.get(id=question_id)
            question.delete()
            messages.success(request, "Question supprimee.")
        except Question.DoesNotExist:
            messages.error(request, "Question introuvable.")
    return redirect("admin_dashboard")


@staff_member_required(login_url="/accounts/login/")
def admin_question_edit(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == "POST":
        enonce = request.POST.get("enonce", "").strip()
        if enonce:
            question.enonce = enonce
            question.save()
        for choix in question.choix.all():
            texte = request.POST.get(f"choix_{choix.lettre}", "").strip()
            style = request.POST.get(f"style_{choix.lettre}", choix.style)
            if texte:
                choix.texte = texte
                choix.style = style
                choix.save()
        messages.success(request, "Question modifiee.")
        return redirect("admin_dashboard")
    return render(request, "quiz/admin_question_edit.html", {"question": question})


def ressources_view(request):
    style_filtre = request.GET.get("style", None)
    return render(request, "quiz/ressources.html", {"style_filtre": style_filtre})
