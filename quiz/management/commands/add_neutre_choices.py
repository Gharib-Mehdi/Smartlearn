from django.core.management.base import BaseCommand
from quiz.models import Choix, Question


class Command(BaseCommand):
    help = "Ajoute le choix D (Neutre/Autre) a toutes les questions qui ne l ont pas encore"

    def handle(self, *args, **options):
        questions = Question.objects.all()
        added = 0
        skipped = 0

        for question in questions:
            already_has_d = question.choix.filter(lettre="D").exists()
            if already_has_d:
                skipped += 1
                self.stdout.write(f"  [SKIP] Q{question.ordre}: choix D deja present")
                continue

            Choix.objects.create(
                question=question,
                texte="Aucune de ces reponses ne me correspond vraiment",
                style="NEUTRE",
                lettre="D",
            )
            added += 1
            self.stdout.write(f"  [OK] Q{question.ordre}: choix D ajoute")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTermine : {added} choix D ajoutes, {skipped} questions ignorees (D deja present)"
            )
        )
