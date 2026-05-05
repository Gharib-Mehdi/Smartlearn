import os
from openai import OpenAI
from ..models import Recommandation


def build_prompt(resultat):
    return f"""Tu es un expert en pedagogie et en styles d'apprentissage (modele VAK).

L'utilisateur a complete le test SmartLearn avec les resultats suivants :
- Style Visuel : {resultat.pct_visuel}%
- Style Auditif : {resultat.pct_auditif}%
- Style Kinesthesique : {resultat.pct_kinesthesique}%
- Style dominant : {resultat.style_dominant}

Genere une analyse personnalisee en francais, structuree en 4 parties :
1. **Profil d'apprentissage** : decris ce que revelent ces scores sur la facon dont cet apprenant fonctionne
2. **Points forts** : les avantages naturels de ce profil
3. **Strategies recommandees** : 4-5 conseils concrets et actionnables adaptes a ce style
4. **Outils & ressources** : des outils numeriques, techniques ou methodes specifiques a ce profil

Ton : encourageant, professionnel, precis. Longueur : 300-400 mots."""


def generate_recommendations(session):
    resultat = session.resultat
    prompt = build_prompt(resultat)
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un expert en sciences de l'education et en styles d'apprentissage.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        texte = response.choices[0].message.content
        return Recommandation.objects.create(session=session, texte=texte, api_provider="openai")
    except Exception:
        fallback_texts = {
            "VISUEL": """**Profil Visuel detecte**\n\nVous retenez mieux avec des schemas et contenus visuels.\n\n**Strategies recommandees :**\n- Faites des cartes mentales\n- Regardez des videos explicatives\n- Colorez vos notes\n- Utilisez des flashcards illustrees\n\n**Outils recommandés :** Notion, Canva, Anki.""",
            "AUDITIF": """**Profil Auditif detecte**\n\nVous retenez mieux en ecoutant et en verbalisant.\n\n**Strategies recommandees :**\n- Ecoutez des podcasts\n- Expliquez a voix haute\n- Enregistrez des resumes audio\n- Participez aux discussions\n\n**Outils recommandés :** Spotify, Audible, Google Recorder.""",
            "KINESTHESIQUE": """**Profil Kinesthesique detecte**\n\nVous apprenez mieux en pratiquant.\n\n**Strategies recommandees :**\n- Faites des exercices pratiques\n- Construisez des mini-projets\n- Associez mouvement et revision\n- Testez des simulations\n\n**Outils recommandés :** GitHub, laboratoires en ligne, simulations.""",
        }
        texte = fallback_texts.get(resultat.style_dominant, "Continuez a explorer votre style d'apprentissage.")
        return Recommandation.objects.create(session=session, texte=texte, api_provider="fallback")
