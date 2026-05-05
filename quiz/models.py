from django.contrib.auth.models import User
from django.db import models


class StyleEnum(models.TextChoices):
    VISUEL = "VISUEL", "Visuel"
    AUDITIF = "AUDITIF", "Auditif"
    KINESTHESIQUE = "KINESTHESIQUE", "Kinesthesique"


class Quiz(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_questions(self):
        return self.questions.all().order_by("ordre")

    def __str__(self):
        return self.titre


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    enonce = models.TextField()
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre"]

    def __str__(self):
        return f"Q{self.ordre}: {self.enonce[:60]}"


class Choix(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choix")
    texte = models.TextField()
    style = models.CharField(max_length=20, choices=StyleEnum.choices)
    lettre = models.CharField(max_length=1)

    def __str__(self):
        return f"[{self.lettre}] {self.texte[:50]} -> {self.style}"


class Session(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    terminee = models.BooleanField(default=False)

    def __str__(self):
        return f"Session de {self.utilisateur.username} - {self.date_debut.date()}"


class Reponse(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="reponses")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choix = models.ForeignKey(Choix, on_delete=models.CASCADE)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "question")


class Resultat(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name="resultat")
    score_visuel = models.IntegerField(default=0)
    score_auditif = models.IntegerField(default=0)
    score_kinesthesique = models.IntegerField(default=0)
    style_dominant = models.CharField(max_length=20, choices=StyleEnum.choices)
    pct_visuel = models.FloatField(default=0)
    pct_auditif = models.FloatField(default=0)
    pct_kinesthesique = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculer(self):
        total = self.score_visuel + self.score_auditif + self.score_kinesthesique
        if total > 0:
            self.pct_visuel = round(self.score_visuel / total * 100, 1)
            self.pct_auditif = round(self.score_auditif / total * 100, 1)
            self.pct_kinesthesique = round(self.score_kinesthesique / total * 100, 1)
        scores = {
            "VISUEL": self.score_visuel,
            "AUDITIF": self.score_auditif,
            "KINESTHESIQUE": self.score_kinesthesique,
        }
        self.style_dominant = max(scores, key=scores.get)
        self.save()


class Recommandation(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name="recommandation")
    texte = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)
    api_provider = models.CharField(max_length=50, default="openai")

    def __str__(self):
        return f"Recommandation pour {self.session}"
