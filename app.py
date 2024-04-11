from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import unidecode




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'une_cle_secrete_tres_securisee'
db = SQLAlchemy(app)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step = db.Column(db.Integer, nullable=False, default=0)
    context = db.Column(db.String(2000))

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step = db.Column(db.Integer, unique=True, nullable=False)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.String(2000), nullable=False)
    expected_keywords = db.Column(db.String(2000))

class OpenFAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keywords = db.Column(db.String(500), nullable=False)
    response = db.Column(db.String(2000), nullable=False)

def normalize_text(text):
    """Normalise le texte en retirant les accents, en mettant en minuscule, et en tentant de simplifier le genre et le pluriel."""
    text = unidecode.unidecode(text).lower()  # Enlever les accents et mettre en minuscule
    words = text.split()
    normalized_words = []
    for word in words:
        # Tentatives simples de gérer les pluriels et le genre
        if word.endswith('aux'):
            word = word[:-3] + 'al'  # Cas spécial pour le passage de "aux" à "al"
        elif word.endswith('es'):
            word = word[:-2]  # Enlever le "es" final pour simplifier le pluriel féminin
        elif word.endswith('s') or word.endswith('x'):
            word = word[:-1]  # Enlever le "s" ou "x" final pour simplifier le pluriel
        elif word.endswith('e'):
            word = word[:-1]  # Tentative de gérer le féminin en enlevant le "e" final
        normalized_words.append(word)
    return ' '.join(normalized_words)


@app.route('/chris', methods=['POST'])
def chris_bot():
    conversation = Conversation.query.first()
    if not conversation:
        conversation = Conversation(step=1)
        db.session.add(conversation)
        db.session.commit()

    user_message = request.json['message'].lower()
    normalized_message = normalize_text(user_message)  # Normaliser le message utilisateur

    response = ""

    if conversation.step > 9:
        if 'non' in normalized_message:
            response = "Merci d'avoir utilisé notre service de chat. Bonne journée !"
            conversation.step = 1
            db.session.commit()
        else:
            open_faqs = OpenFAQ.query.all()
            max_keyword_matches = 0
            selected_response = "Pouvez-vous en dire plus ou poser une autre question ?"
            for open_faq in open_faqs:
                # Normaliser et séparer les mots-clés pour cette entrée FAQ
                keywords = normalize_text(open_faq.keywords).split(',')
                keyword_matches = sum(keyword.strip() in normalized_message.split() for keyword in keywords)
                if keyword_matches > max_keyword_matches:
                    max_keyword_matches = keyword_matches
                    selected_response = open_faq.response
            response = selected_response
    else:
        current_faq = FAQ.query.filter_by(step=conversation.step).first()
        if current_faq:
            expected_keywords = [normalize_text(kw.strip()) for kw in current_faq.expected_keywords.split(',')]
            if any(keyword in normalized_message.split() for keyword in expected_keywords):
                conversation.step += 1
                db.session.commit()
                next_faq = FAQ.query.filter_by(step=conversation.step).first()
                response = next_faq.question if next_faq else "Avez-vous d'autres questions ou des préoccupations ?"
            else:
                response = f"Je ne suis pas sûr de comprendre. {current_faq.question}"
        else:
            response = "Je suis désolé, je n'ai pas d'autres questions. Comment puis-je vous aider ?"

    return jsonify({"response": response})







@app.route('/')
def index():
    # Obtenez la première question de la FAQ
    first_question = FAQ.query.filter_by(step=1).first()
    question = first_question.question if first_question else "Bonjour, comment puis-je vous aider ?"
    # Passez la première question à votre template HTML
    return render_template('index.html', first_question=question)

def populate_db():
    # Supprimer toutes les données existantes et réinitialiser
    db.drop_all()
    db.create_all()

    # Ici, expected_keywords peut inclure des synonymes et des mots-clés liés séparés par des virgules
    faq_pairs = [
        FAQ(step=1, question="Pouvez-vous nous parler un peu de vous et de ce qui vous amène ici aujourd'hui ?",
            answer="",
            expected_keywords="experience, competence, personnalite, background, parcours, qualite, motivation, raison, ambition, stage, emploi, objectif, intention, integrer, aspiration, projet professionnel, interet, desir, engagement, candidature, motivation pour le poste, ambition future"),
        FAQ(step=2, question="Quelle expérience avez-vous dans le domaine de la restauration rapide ?", answer="",
            expected_keywords="restauration rapide, experience, fast food, service, client, cuisine, caisse, gestion, equipe, aucune, alimentation, rapide, dynamique, mcdo, kfc, service comptoir, travail cuisine, preparation alimentaire, gestion commande, travail equipe, experience client, service rapide, environnement travail dynamique"),
        FAQ(step=3,
            question="Comment gérez-vous les situations stressantes, par exemple un afflux soudain de clients ?",
            answer="",
            expected_keywords="calme, gestion stress, panique, resolution probleme, sang-froid, pression, urgence, patience, rapidite, efficacite, crise, adaptation, gestion crise, reactivite, maitrise soi, gestion priorite, resilience, tranquillite, gestion urgence, anticipation, gestion conflit"),
        FAQ(step=4, question="Donnez-nous un exemple d'une fois où vous avez travaillé efficacement en équipe.",
            answer="",
            expected_keywords="collaboration, cooperation, equipe, travail equipe, synergie, projet, groupe, partage, communication, soutien, esprit equipe, ami, unite, travail collaboratif, interaction, coordination, alliance, participation, effort collectif, dynamique groupe, solidarite, travail synergie"),
        FAQ(step=5, question="Si un client se plaint d'une erreur dans sa commande, comment réagiriez-vous ?",
            answer="",
            expected_keywords="ecoute, empathie, solution, satisfaction client, resoudre, plainte, erreur, service, reclamation, comprehension, rectification, politesse, reponse, gestion reclamation, attitude positive, correction, service apres-vente, adaptation, assurance qualite, accueil feedback, gestion erreur"),
        FAQ(step=6, question="Comment assurez-vous d'offrir un excellent service client à chaque interaction ?",
            answer="",
            expected_keywords="service client, courtoisie, amabilite, satisfaction, qualite, accueil, reponse, besoin, exigence, standard, fidelisation, experience client, engagement, excellence, interaction client, approche client, qualite service, personnalisation service, attention detail, anticipation besoin, suivi client"),
        FAQ(step=7,
            question="Quelles sont vos attentes en matière de croissance professionnelle et d'opportunités de carrière ?",
            answer="",
            expected_keywords="evolution, ambition, carriere, developpement professionnel, progression, formation, apprentissage, promotion, perspective, objectif, aspiration, avancement, opportunite, epanouissement professionnel, ambition carriere, plan carriere, developpement competence, ascension professionnelle, objectif developpement, opportunite evolution"),
        FAQ(step=8,
            question="Pouvez-vous nous donner un exemple de la façon dont vous gérez votre temps pendant une journée de travail chargée ?",
            answer="",
            expected_keywords="gestion temps, organisation, priorite, efficacite, planification, agenda, multitache, delai, horaire, productivite, tache, deadline, gestion, optimisation temps, ordonnancement tache, gestion priorite, efficience, agenda travail, gestion activite, plan travail, echeance"),
        FAQ(step=9,
            question="Quels sont, selon vous, les traits les plus importants qu'un employé de fast food devrait avoir ?",
            answer="",
            expected_keywords="patience, rapidite, efficacite, amabilite, resilience, ponctualite, flexibilite, fiabilite, endurance, energie, travail pression, orientation client, esprit initiative, adaptabilite, devouement, efficience, courtoisie, dynamisme, capacite travail environnement rapide, competence interpersonnelle, fiabilite professionnelle"),
    ]

    db.session.bulk_save_objects(faq_pairs)
    db.session.commit()


def populate_open_faq():
    # Cette fonction ajoutera les mots-clés et les réponses à la base de données
    open_faq_pairs = [

        # Question 1
        {
            'keywords': 'horaires, heure, ouvert, emploi du temps, planning, disponibilités, bureau, travail, flexibilite, temps partiel',
            'response': "Nos heures d'ouverture sont de 9h à 17h du lundi au vendredi. Nous sommes flexibles et pouvons discuter des arrangements de temps partiel si nécessaire."
        },
        # Question 2
        {
            'keywords': 'mission, valeurs, entreprise, objectifs, engagement, principes, éthique, vision, stratégie, philosophie',
            'response': "Notre mission est de fournir les meilleurs produits et services à nos clients, en alignement avec nos valeurs fondamentales d'intégrité, de qualité et de service."
        },
        # Question 3
        {
            'keywords': 'culture, entreprise, environnement de travail, ambiance, collègues, éthique, diversité, inclusion',
            'response': "Nous valorisons une culture d'entreprise positive, où diversité et inclusion sont primordiales pour créer un environnement de travail où chacun peut s'épanouir."
        },
        # Question 4
        {
            'keywords': 'salaire, rémunération, avantages, compétitif, paie, bonus, sociaux, paquet salarial, grille, négociation',
            'response': "Nous offrons une rémunération compétitive qui reconnaît l'expérience et les compétences. Nos avantages incluent également des bonus et des avantages sociaux attractifs."
        },
        # Question 5
        {
            'keywords': 'opportunités, croissance, carrière, promotion, avancement, développement professionnel, évolution, ascension, perspectives, potentiel',
            'response': "Nous offrons d'excellentes opportunités de croissance à nos employés, y compris des promotions internes et un développement professionnel continu."
        },
        # Question 6
        {
            'keywords': 'formation, développement, compétences, apprentissage, éducation, perfectionnement, continue, compétence, qualification, initiatives',
            'response': "Notre programme de formation aide les employés à acquérir de nouvelles compétences et à rester compétitifs. Nous investissons dans des initiatives d'apprentissage et de développement."
        },
        # Question 7
        {
            'keywords': 'équipe, collègues, manager, management, travail d’équipe, supérieur, hiérarchie, leadership, coopération, mentorat',
            'response': "Nos équipes sont dirigées par des managers qui prônent le mentorat et la coopération. Nous valorisons le leadership et la capacité à travailler ensemble vers un objectif commun."
        },
        # Question 8
        {
            'keywords': 'défis, projets, responsabilités, tâches, missions, objectifs, travail, activités, rôle, initiative',
            'response': "Nous encourageons nos employés à prendre des initiatives et à gérer des projets passionnants. Les défis font partie intégrante de notre quotidien et stimulent le développement professionnel."
        },
        # Question 9
        {
            'keywords': 'poste, description, responsabilités, tâches, quotidien, rôle, fonction, exigences, qualifications, profil',
            'response': "Le poste pour lequel vous postulez comprend diverses responsabilités, qui seront détaillées dans la description de poste."
        },
        # Question 10
        {
            'keywords': 'entreprise, informations, historique, fondation, marché, concurrence, positionnement, stratégie, innovation, croissance',
            'response': "Notre entreprise a un historique solide sur le marché, avec une stratégie axée sur l'innovation et une croissance soutenue."
        },
        # Question 11
        {
            'keywords': 'collaborateurs, nombre, équipes, taille, organisation, structure, hiérarchie, départements, bureaux, effectif',
            'response': "Notre entreprise compte un nombre significatif de collaborateurs répartis en divers départements et équipes. La taille et la structure de notre organisation favorisent l'efficacité et la collaboration."
        },
        # Question 12
        {
            'keywords': 'clients, service, satisfaction, fidélisation, relations, clientèle, support, assistance, expérience, engagement',
            'response': "La satisfaction de nos clients est au cœur de notre stratégie. Nous nous engageons à offrir une expérience exceptionnelle pour fidéliser notre clientèle."
        },
        # Question 13
        {
            'keywords': 'processus, recrutement, étapes, sélection, critères, évaluation, entrevue, entretien, procédure, candidature',
            'response': "Notre processus de recrutement est conçu pour être transparent et équitable, avec plusieurs étapes d'évaluation pour sélectionner le meilleur candidat."
        },
        # Question 14
        {
            'keywords': 'valeurs, culture, principes, normes, comportement, éthique, morale, intégrité, responsabilité, engagement',
            'response': "Nos valeurs culturelles sont basées sur l'intégrité, la responsabilité et l'engagement. Elles définissent notre comportement et notre manière de faire des affaires."
        },
        # Question 15
        {
            'keywords': 'communauté, social, responsabilité, impact, environnement, durable, initiatives, projets, société, contribution',
            'response': "Nous prenons notre responsabilité sociale d'entreprise très au sérieux, avec un impact positif sur la communauté et l'environnement. Nous menons plusieurs initiatives durables."
        },

        # Question 16
        {
            'keywords': 'uniforme, code vestimentaire, tenue, apparence, vêtements, image, professionnel, normes, consignes, uniformité',
            'response': "Nous fournissons un uniforme et des consignes claires en matière d'apparence professionnelle pour garantir une image cohérente et professionnelle dans tous nos restaurants."
        },

        # Question 17
        {
            'keywords': 'politique, règlement, discipline, conduite, comportement, sanctions, respect, réglementation, normes, règles',
            'response': "Nous avons des politiques et des règlements en place pour assurer un comportement respectueux et professionnel de la part de nos employés. Des mesures disciplinaires sont prises en cas de non-respect de ces règles."
        },

        # Question 18
        {
            'keywords': 'sécurité, hygiène, santé, précautions, normes, réglementation, protocoles, risques, mesures, formations',
            'response': "La sécurité, l'hygiène et la santé de nos employés et de nos clients sont notre priorité. Nous respectons strictement les normes et réglementations en vigueur et fournissons des formations régulières sur ces sujets."
        },

        # Question 19
        {
            'keywords': 'feedback, évaluation, performance, suivi, rétroaction, évaluations, entretiens, progrès, amélioration, développement',
            'response': "Nous offrons des processus d'évaluation et de rétroaction réguliers pour suivre la performance de nos employés, les aider à progresser et encourager leur développement professionnel."
        },

        # Question 20
        {
            'keywords': 'avantages, rabais, repas, réductions, offres, employé, gratuité, promotion, privilèges, avantages sociaux',
            'response': "En plus d'une rémunération compétitive, nos employés bénéficient d'avantages tels que des repas gratuits ou à prix réduit, des réductions sur nos produits et d'autres privilèges."
        },

        # Question 21
        {
            'keywords': 'équilibre, vie professionnelle, personnelle, flexibilité, horaires, temps, famille, travail, repos, bien-être',
            'response': "Nous comprenons l'importance d'un équilibre entre vie professionnelle et vie personnelle. Nous offrons des horaires flexibles et encourageons nos employés à prendre soin de leur bien-être."
        },

        # Question 22
        {
            'keywords': 'innovation, idées, suggestions, amélioration, créativité, propositions, solutions, contribution, participation, feedback',
            'response': "Nous encourageons l'innovation et la créativité chez nos employés. Nous valorisons les idées et les suggestions qui peuvent améliorer nos opérations et nos services."
        },

        # Question 23
        {
            'keywords': 'divertissement, activités, événements, fêtes, célébrations, équipe, convivialité, socialisation, camaraderie, cohésion',
            'response': "Nous organisons régulièrement des activités et des événements pour favoriser la camaraderie et renforcer l'esprit d'équipe entre nos employés."
        },

        # Question 24
        {
            'keywords': 'engagement, association, implication, bénévolat, volontariat, initiatives, responsabilité, soutien, solidarité, causes',
            'response': "Nous encourageons l'engagement de nos employés dans des activités bénévoles et des initiatives communautaires. Nous soutenons les causes qui nous tiennent à cœur."
        }

    ]

    # Vérifiez si des données existent déjà pour éviter les doublons
    if not OpenFAQ.query.first():
        for entry in open_faq_pairs:
            new_entry = OpenFAQ(keywords=entry['keywords'], response=entry['response'])
            db.session.add(new_entry)
        db.session.commit()


if __name__ == '__main__':
    with app.app_context():  # Utilisation d'un contexte d'application pour les opérations de base de données
        db.drop_all()  # Optionnel : supprime toutes les tables
        db.create_all()  # Crée toutes les tables définies par les modèles
        populate_db()  # Peuple la base de données avec les données initiales
        populate_open_faq()  # Peuple la base de données avec les réponses ouvertes
    app.run(debug=True)
