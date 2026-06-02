import os
import requests
from ..models import Recommandation
from django.conf import settings



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
        from django.conf import settings
        groq_api_key = settings.GROQ_API_KEY
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",  # ← modèle mis à jour
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es un expert en sciences de l'education et en styles d'apprentissage.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1024,
                "temperature": 0.7,
            },
            timeout=15,
        )
        response.raise_for_status()  # ← lève une exception si status != 200
        texte = response.json()["choices"][0]["message"]["content"]
        return Recommandation.objects.create(session=session, texte=texte, api_provider="groq")
    except Exception as e:
        print(f">>> GROQ ERROR: {e}")
        # ... ton fallback existant inchangé