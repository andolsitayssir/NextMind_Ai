import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from APP.models import Participant

SAMPLES = [
    {
        "full_name": "Alice Martin",
        "big_five": {
            "openness": {"mean": 3.2, "strengths": ["Balanced curiosity and practical creativity."], "weaknesses": ["May prefer proven methods before adopting novel approaches."]},
            "conscientiousness": {"mean": 4.8, "strengths": ["Highly organized, reliable, strong follow-through."], "weaknesses": ["May overinvest in planning and perfection."]},
            "extraversion": {"mean": 2.4, "strengths": ["Thoughtful contributor in small-group settings."], "weaknesses": ["Less comfortable with spontaneous public speaking."]},
            "agreeableness": {"mean": 4.0, "strengths": ["Team-oriented, cooperative, empathetic."], "weaknesses": ["May avoid necessary confrontation."]},
            "emotional_stability": {"mean": 4.4, "strengths": ["Calm under pressure; optimistic with perspective."], "weaknesses": ["Can overlook subtle emotional cues."]},
        },
        "disc": {"scores": {"D": 3.0, "I": 2.0, "S": 4.0, "C": 3.0}, "strengths": ["Steady, cooperative; promotes team harmony (S)."], "weaknesses": ["Less comfortable with rapid-fire decisions and open conflict."]},
        "well_being": {"mean": 4.0, "strengths": ["Good perceived support and values alignment."], "weaknesses": ["Monitor workload peaks to prevent fatigue."]},
        "resilience_ie": {"mean": 4.3, "strengths": ["Labels emotions well; maintains motivation; de-escalates conflict."], "weaknesses": ["Sustain micro-breaks and mindfulness habits."]},
    },
    {
        "full_name": "John Reed",
        "big_five": {
            "openness": {"mean": 4.6, "strengths": ["High curiosity, creativity, and exploration."], "weaknesses": ["May adopt novelty before constraints are validated."]},
            "conscientiousness": {"mean": 2.8, "strengths": ["Plans effectively when impact is clear."], "weaknesses": ["Inconsistent detail checking and follow-through."]},
            "extraversion": {"mean": 4.4, "strengths": ["Energizing presence; effective public communication."], "weaknesses": ["Risk of dominating airtime if not mindful."]},
            "agreeableness": {"mean": 3.0, "strengths": ["Balanced consideration of others' views."], "weaknesses": ["May appear neutral in high-empathy contexts."]},
            "emotional_stability": {"mean": 2.6, "strengths": ["Can recover with structure and support."], "weaknesses": ["Sensitive to volatile deadlines and pressure spikes."]},
        },
        "disc": {"scores": {"D": 3.0, "I": 5.0, "S": 2.0, "C": 2.0}, "strengths": ["Influential communicator with enthusiasm (I)."], "weaknesses": ["Lower steadiness/compliance in highly procedural tasks."]},
        "well_being": {"mean": 3.5, "strengths": ["Decent autonomy and partial values alignment."], "weaknesses": ["Fluctuates with workload volatility; needs predictable routines."]},
        "resilience_ie": {"mean": 3.4, "strengths": ["Learns from setbacks; can center with simple routines."], "weaknesses": ["Benefits from consistent stress-management habits."]},
    },
    {
        "full_name": "Sofia Duarte",
        "big_five": {
            "openness": {"mean": 3.0, "strengths": ["Open when benefits are concrete and clear."], "weaknesses": ["Prefers proven methods over constant change."]},
            "conscientiousness": {"mean": 4.0, "strengths": ["Consistent, organized, and dependable delivery."], "weaknesses": ["May over-structure under uncertainty."]},
            "extraversion": {"mean": 3.0, "strengths": ["Balanced collaboration and steady participation."], "weaknesses": ["Less energized by highly dynamic environments."]},
            "agreeableness": {"mean": 4.8, "strengths": ["High empathy, active listening, and conflict de-escalation."], "weaknesses": ["May avoid necessary confrontation."]},
            "emotional_stability": {"mean": 4.0, "strengths": ["Calm under pressure; consistent emotional regulation."], "weaknesses": ["Watch for hidden stress accumulation."]},
        },
        "disc": {"scores": {"D": 1.0, "I": 3.0, "S": 5.0, "C": 3.0}, "strengths": ["High steadiness and reliability (S)."], "weaknesses": ["Low dominance—may avoid direct confrontation."]},
        "well_being": {"mean": 4.0, "strengths": ["High satisfaction and strong team climate."], "weaknesses": ["Protect recovery time during peak periods."]},
        "resilience_ie": {"mean": 4.0, "strengths": ["Robust emotional regulation and adaptation."], "weaknesses": ["Maintain habits to keep resilience high."]},
    },
    {
        "full_name": "Marc Dupont",
        "big_five": {
            "openness": {"mean": 3.2, "strengths": ["Pragmatic openness to useful ideas."], "weaknesses": ["Less attracted to abstract exploration."]},
            "conscientiousness": {"mean": 3.2, "strengths": ["Action-oriented; prioritizes essentials."], "weaknesses": ["May shorten checks and detailed verification."]},
            "extraversion": {"mean": 4.8, "strengths": ["Natural leadership, high social energy, visible initiative."], "weaknesses": ["Risk of monopolizing discussions."]},
            "agreeableness": {"mean": 2.4, "strengths": ["Directness and clarity of expectations."], "weaknesses": ["Can seem too blunt; limited diplomacy."]},
            "emotional_stability": {"mean": 3.0, "strengths": ["Functional under moderate pressure."], "weaknesses": ["Latent stress during prolonged uncertainty."]},
        },
        "disc": {"scores": {"D": 5.0, "I": 4.0, "S": 2.0, "C": 2.0}, "strengths": ["Results-driven, fast decisions (D)."], "weaknesses": ["Needs guardrails on active listening and precision."]},
        "well_being": {"mean": 3.0, "strengths": ["Stable engagement and acceptable autonomy."], "weaknesses": ["Improve recognition and material conditions."]},
        "resilience_ie": {"mean": 3.3, "strengths": ["Can recentre when needed."], "weaknesses": ["Establish more regular anti-stress routines."]},
    },
]

TRAIT_ORDER = ["openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"]
TRAIT_LABELS = {
    "openness": "Openness",
    "conscientiousness": "Conscientiousness",
    "extraversion": "Extraversion",
    "agreeableness": "Agreeableness",
    "emotional_stability": "Emotional Stability",
}

def level_from_mean(mean: float) -> str:
    if mean < 2.5: return "low"
    if mean < 3.5: return "moderate"
    return "high"

def bullets(lines): return "<br/>".join([f"• {l}" for l in lines])

def generate_pdf_for_sample(output_path: str, sample: dict):
    styles = getSampleStyleSheet()
    title, h2, h3, normal = styles['Title'], styles['Heading2'], styles['Heading3'], styles['BodyText']
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm, title=f"NextMind - Questionnaire Report - {sample['full_name']}")
    story = []
    story.append(Paragraph("NextMind – Questionnaire Report (Static)", title))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Name: {sample['full_name']}", normal))
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("Section 1 – Big Five (Score out of 5)", h2))
    for trait in TRAIT_ORDER:
        data = sample["big_five"][trait]; mean = float(data["mean"]); lvl = level_from_mean(mean); label = TRAIT_LABELS[trait]
        story.append(Paragraph(f"{label} — Score: {mean:.1f}/5 ({lvl})", h3))
        story.append(Paragraph("Strengths", h3)); story.append(Paragraph(bullets(data["strengths"]), normal))
        story.append(Paragraph("Weaknesses", h3)); story.append(Paragraph(bullets(data["weaknesses"]), normal))
        story.append(Spacer(1, 0.3*cm))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Section 2 – DISC (Score out of 5)", h2))
    d, i, s, c = (sample["disc"]["scores"][k] for k in ("D","I","S","C"))
    story.append(Paragraph(f"Scores D/I/S/C: D={d:.1f}, I={i:.1f}, S={s:.1f}, C={c:.1f}", normal))
    top_styles = ", ".join([f"{k}:{v:.1f}" for k, v in sorted(sample["disc"]["scores"].items(), key=lambda kv: kv[1], reverse=True)])
    story.append(Paragraph(f"Dominant styles: {top_styles}", normal))
    story.append(Paragraph("Strengths", h3)); story.append(Paragraph(bullets(sample["disc"]["strengths"]), normal))
    story.append(Paragraph("Weaknesses", h3)); story.append(Paragraph(bullets(sample["disc"]["weaknesses"]), normal))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Section 3 – Workplace Well-being (Score out of 5)", h2))
    story.append(Paragraph(f"Score: {sample['well_being']['mean']:.1f}/5", normal))
    story.append(Paragraph("Strengths", h3)); story.append(Paragraph(bullets(sample["well_being"]["strengths"]), normal))
    story.append(Paragraph("Weaknesses", h3)); story.append(Paragraph(bullets(sample["well_being"]["weaknesses"]), normal))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Section 4 – Resilience & Emotional Intelligence (mean out of 5)", h2))
    story.append(Paragraph(f"Score: {sample['resilience_ie']['mean']:.1f}/5", normal))
    story.append(Paragraph("Strengths", h3)); story.append(Paragraph(bullets(sample["resilience_ie"]["strengths"]), normal))
    story.append(Paragraph("Weaknesses", h3)); story.append(Paragraph(bullets(sample["resilience_ie"]["weaknesses"]), normal))
    story.append(Spacer(1, 0.7*cm))
    doc.build(story)

class Command(BaseCommand):
    help = "Create sample participants with questionnaire-based PDF reports stored in static/reports."

    def handle(self, *args, **options):
        # Use the proper path from settings
        reports_dir = settings.MEDIA_ROOT
        os.makedirs(reports_dir, exist_ok=True)
        
        self.stdout.write(f"Storing PDFs in: {reports_dir}")
        
        for data in SAMPLES:
            # Create participant without email/language
            participant, created = Participant.objects.get_or_create(
                full_name=data["full_name"]
            )
            
            # Generate filename and path
            filename = f"{slugify(data['full_name'])}.pdf"
            pdf_path = os.path.join(reports_dir, filename)
            
            # Generate PDF
            self.stdout.write(f"Generating PDF for {data['full_name']} at {pdf_path}")
            generate_pdf_for_sample(pdf_path, data)
            
            # Update participant with file path
            participant.report_file.name = filename  # just the filename since MEDIA_URL is /reports/
            participant.save()
            
            self.stdout.write(f"{'Created' if created else 'Updated'} participant: {participant.full_name}")
        
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(SAMPLES)} participants with reports"))