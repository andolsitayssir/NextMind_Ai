import openai
import os

openai.api_key = os.getenv("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"

def generate_question(trait, section, language):
    prompts = {
        "fr": f"Génère une question courte et claire pour évaluer le trait '{trait}' dans la section '{section}'. La question doit inviter à une réponse libre.",
        "en": f"Generate a short and clear question to assess the trait '{trait}' in the section '{section}'. The question should invite a free-text answer.",
        "ar": f"أنشئ سؤالًا قصيرًا وواضحًا لقياس السمة '{trait}' في القسم '{section}'. يجب أن يشجع السؤال المستخدم على كتابة إجابة حرة."
    }

    prompt = prompts.get(language, prompts["fr"])

    try:
        res = openai.ChatCompletion.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("Error generating question:", e)
        return "Erreur lors de la génération de la question."

def score_answer(answer_text, trait, section, language):
    prompts = {
        "fr": f"""Tu es un psychologue expert. Voici une réponse à une question liée au trait '{trait}' dans la section '{section}' :
\"{answer_text}\"

Sur une échelle de 1 à 5, évalue ce trait. Réponds uniquement par un chiffre.""",

        "en": f"""You are an expert psychologist. Here is an answer related to the trait '{trait}' in section '{section}':
\"{answer_text}\"

On a scale from 1 to 5, rate this trait. Respond only with a number.""",

        "ar": f"""أنت خبير نفسي. هذه إجابة تتعلق بالسمة '{trait}' في القسم '{section}' :
\"{answer_text}\"

قيّم هذه السمة من 1 إلى 5. أجب برقم فقط."""
    }

    prompt = prompts.get(language, prompts["fr"])

    try:
        res = openai.ChatCompletion.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.3,
        )
        return int(res.choices[0].message.content.strip())
    except Exception as e:
        print("Error scoring answer:", e)
        return None
