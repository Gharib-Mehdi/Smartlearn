import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import QuizAnswerForm
from .models import Choix, Quiz, Reponse, Resultat, Session, StyleEnum
from .services.llm_service import generate_recommendations


def _finalize_session(session):
    reponses = session.reponses.select_related("choix")
    score_visuel = sum(1 for r in reponses if r.choix.style == StyleEnum.VISUEL)
    score_auditif = sum(1 for r in reponses if r.choix.style == StyleEnum.AUDITIF)
    score_kinesthesique = sum(1 for r in reponses if r.choix.style == StyleEnum.KINESTHESIQUE)
    resultat = Resultat.objects.create(
        session=session,
        score_visuel=score_visuel,
        score_auditif=score_auditif,
        score_kinesthesique=score_kinesthesique,
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
    sessions = (
        Session.objects.filter(utilisateur=request.user, terminee=True)
        .select_related("resultat")
        .order_by("-date_fin")
    )
    last_result = sessions.first().resultat if sessions else None
    return render(request, "quiz/dashboard.html", {"sessions": sessions, "last_result": last_result})


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
