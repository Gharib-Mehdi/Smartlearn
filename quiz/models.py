from django.contrib.auth.models import User
from django.db import models


class StyleEnum(models.TextChoices):
    VISUEL = "VISUEL", "Visuel"
    AUDITIF = "AUDITIF", "Auditif"
    KINESTHESIQUE = "KINESTHESIQUE", "Kinesthesique"
    NEUTRE = "NEUTRE", "Neutre"


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
    neutral_count = models.IntegerField(default=0)
    profil_type = models.CharField(
        max_length=20,
        default="DOMINANT",
        choices=[
            ("DOMINANT", "Style dominant clair"),
            ("MIXTE", "Profil mixte"),
            ("EQUILIBRE", "Profil equilibre"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def calculer(self):
        total = self.score_visuel + self.score_auditif + self.score_kinesthesique
        if total > 0:
            self.pct_visuel = round(self.score_visuel / total * 100, 1)
            self.pct_auditif = round(self.score_auditif / total * 100, 1)
            self.pct_kinesthesique = round(self.score_kinesthesique / total * 100, 1)
        else:
            self.pct_visuel = self.pct_auditif = self.pct_kinesthesique = 0
        scores = {
            "VISUEL": self.pct_visuel,
            "AUDITIF": self.pct_auditif,
            "KINESTHESIQUE": self.pct_kinesthesique,
        }
        sorted_styles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        first_score = sorted_styles[0][1]
        second_score = sorted_styles[1][1]
        ecart = first_score - second_score
        self.style_dominant = sorted_styles[0][0]
        if ecart <= 2:
            self.profil_type = "EQUILIBRE"
        elif ecart <= 15:
            self.profil_type = "MIXTE"
        else:
            self.profil_type = "DOMINANT"
        self.save()

    @property
    def style_secondaire(self):
        scores = {
            "VISUEL": self.pct_visuel,
            "AUDITIF": self.pct_auditif,
            "KINESTHESIQUE": self.pct_kinesthesique,
        }
        sorted_styles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_styles[1][0]

    @property
    def label_style(self):
        labels = {
            "VISUEL": "Visuel",
            "AUDITIF": "Auditif",
            "KINESTHESIQUE": "Kinesthesique",
        }
        return labels.get(self.style_dominant, self.style_dominant)

    @property
    def label_style_secondaire(self):
        labels = {
            "VISUEL": "Visuel",
            "AUDITIF": "Auditif",
            "KINESTHESIQUE": "Kinesthesique",
        }
        return labels.get(self.style_secondaire, self.style_secondaire)


class Recommandation(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name="recommandation")
    texte = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)
    api_provider = models.CharField(max_length=50, default="openai")

    def __str__(self):
        return f"Recommandation pour {self.session}"
