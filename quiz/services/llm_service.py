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
            "VISUEL": (
                "**Profil Visuel detecte**\n\n"
                "Vous retenez mieux l'information quand elle est presentee "
                "sous forme d'images, de schemas, de graphiques ou de videos.\n\n"
                "**Strategies recommandees :**\n"
                "- Utilisez des mind maps pour organiser vos idees\n"
                "- Regardez des videos explicatives (YouTube, Khan Academy)\n"
                "- Colorez et surlignez vos notes\n"
                "- Transformez vos resumes en schemas visuels\n"
                "- Utilisez des flashcards avec des images\n\n"
                "**Outils recommandes :** Notion, Canva pour les schemas, Anki pour les flashcards."
            ),
            "AUDITIF": (
                "**Profil Auditif detecte**\n\n"
                "Vous retenez mieux l'information quand vous l'entendez "
                "ou en la verbalisant.\n\n"
                "**Strategies recommandees :**\n"
                "- Ecoutez des podcasts et des cours audio\n"
                "- Expliquez les concepts a voix haute ou a quelqu'un d'autre\n"
                "- Enregistrez vos propres resumes vocaux\n"
                "- Participez activement aux discussions de groupe\n"
                "- Lisez a voix haute lors de vos revisions\n\n"
                "**Outils recommandes :** Spotify Podcasts, Audible, Google Recorder."
            ),
            "KINESTHESIQUE": (
                "**Profil Kinesthesique detecte**\n\n"
                "Vous retenez mieux l'information en la pratiquant, "
                "en l'experimentant concretement.\n\n"
                "**Strategies recommandees :**\n"
                "- Faites des exercices pratiques immediatement apres chaque lecon\n"
                "- Apprenez en faisant des projets concrets\n"
                "- Prenez des pauses regulieres pour integrer l'information\n"
                "- Associez le mouvement a l'apprentissage\n"
                "- Creez des maquettes ou des prototypes\n\n"
                "**Outils recommandes :** GitHub pour les projets, laboratoires en ligne."
            ),
        }
        fallback_equilibre = (
            "Profil Multimodal detecte\n\n"
            "Felicitations ! Votre profil d'apprentissage est parfaitement equilibre "
            "entre les styles Visuel, Auditif et Kinesthesique. "
            "C'est une caracteristique rare et precieuse : vous etes capable de vous adapter "
            "a n'importe quelle methode d'enseignement.\n\n"
            "Ce que cela signifie :\n"
            "- Vous pouvez apprendre aussi bien par des videos que des podcasts ou des exercices\n"
            "- Vous vous adaptez facilement a differents formateurs et environnements\n"
            "- Vous pouvez choisir votre methode selon votre humeur ou le sujet\n\n"
            "Strategies recommandees :\n"
            "- Variez vos methodes pour maintenir l'engagement\n"
            "- Combinez : lisez un chapitre, ecoutez un podcast, puis faites un exercice\n"
            "- Profitez de cette flexibilite pour experimenter de nouvelles approches\n\n"
            "Outils recommandes : Notion (visuel), Anki (pratique), Audible (auditif)."
        )
        if hasattr(resultat, "profil_type") and resultat.profil_type == "EQUILIBRE":
            texte = fallback_equilibre
        else:
            texte = fallback_texts.get(
                resultat.style_dominant,
                "Continuez a explorer votre style d'apprentissage !",
            )
        return Recommandation.objects.create(session=session, texte=texte, api_provider="fallback")
