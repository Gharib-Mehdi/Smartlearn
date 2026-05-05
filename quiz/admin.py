from django.contrib import admin
from .models import Choix, Question, Quiz, Recommandation, Reponse, Resultat, Session


class ChoixInline(admin.TabularInline):
    model = Choix
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("titre", "actif", "created_at")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("enonce", "quiz", "ordre")
    inlines = [ChoixInline]


admin.site.register(Choix)
admin.site.register(Session)
admin.site.register(Reponse)
admin.site.register(Resultat)
admin.site.register(Recommandation)
