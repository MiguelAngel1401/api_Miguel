import os
import json
from supabase import create_client, Client
from openai import OpenAI
from typing import List, Dict
from .modelos import PromptInput, Chapter
from dotenv import load_dotenv

load_dotenv()

# Config Supabase
SUPABASE_URL = "https://wvjctwtujcmkomvconae.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Config OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class Evaluador:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4.1-mini-2025-04-14"

    def get_norm_text(self, cap_id: str) -> str:
        resp = (
            supabase.table("Normas ISO")
            .select("texto")
            .eq("Capitulo", cap_id)
            .single().execute()
        )
        if resp.data and isinstance(resp.data, dict):
            return resp.data.get("texto", "")
        return ""

    def extract(self, prompt: PromptInput) -> Chapter:
        cap_id = prompt.capitulo_id
        texto = self.get_norm_text(cap_id)

        system_prompt = (f"""
Eres un asistente experto en auditoría de sistemas de gestión de calidad basados en la norma ISO 9001:2015.

A continuación se te proporciona el **contenido oficial del capítulo {cap_id} de la norma** ISO 9001:2015, el cual debe ser utilizado como contexto obligatorio para evaluar correctamente las respuestas que entregará la organización.

Contenido de la norma (capítulo {cap_id}):
\"\"\"
{texto}
\"\"\"

Se te dará información correspondiente a una sección evaluada. Para cada sección recibirás:

1. Una o más preguntas de auditoría basadas en ISO 9001.
2. Una respuesta por cada pregunta, según lo que informa la organización.

Tu tarea es:

1. Analizar cada pregunta con su respectiva respuesta y clasificar el nivel de cumplimiento individual según estas opciones (elige solo una por pregunta):
  - "completo": se cumple totalmente.
  - "parcial": se cumple parcialmente.
  - "ninguno": no hay evidencia de cumplimiento.
  - "no aplica": la pregunta no aplica a la organización.

**Importante**: El campo "cumplimiento" debe contener exactamente uno de los valores anteriores. No escribas explicaciones allí.

2. Luego, analiza la sección completa en conjunto y realiza lo siguiente:
  - Genera una lista de **fulfilled_aspects** (aspectos que se cumplen a nivel de sección). Escribe frases claras y específicas basadas en el contenido proporcionado.
  - Genera una lista de **areas_for_improvement** (aspectos a mejorar a nivel de sección). Escribe observaciones concretas y profesionales, también basadas en la información entregada.

3. No repitas preguntas: una vez que una pregunta está en su subsección, **no** la pongas en `"questions_of_the_section"`.
"""
        )
        user_prompt = json.dumps(prompt.dict(), ensure_ascii=False)

        # Log del prompt
        print("=== SYSTEM PROMPT ===")
        print(system_prompt[:500] + "...\n")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        resp = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            temperature=0.3,
            response_format=Chapter
        )
        return resp.choices[0].message.parsed

# Scoring PHVA
PONDERACIONES = {'4':0.15,'5':0.10,'6':0.10,'7':0.10,'8':0.20,'9':0.20,'10':0.15}
ETAPAS = {
    "PLANEAR": {"capitulos":["4","5","6"],"peso":0.35},
    "HACER":   {"capitulos":["7","8"],"peso":0.30},
    "VERIFICAR": {"capitulos":["9"],"peso":0.20},
    "ACTUAR":    {"capitulos":["10"],"peso":0.15}
}

def score_capitulo(data: Dict) -> Dict:
    # Si es un modelo Pydantic, conviértelo a dict
    if hasattr(data, 'dict'):
        data = data.dict()
    # calcula evaluation_score y chapter_system_score
    for sec in data['sections_of_the_capter']:
        if sec.get('subsections'):
            ss = []
            for sub in sec['subsections']:
                c = sub['counts_sum']
                total = c['completo'] + c['parcial'] + c['ninguno'] + c['no_aplica']
                s = (c['completo'] + 0.5*c['parcial'])/total if total else 0
                sub['evaluation_score'] = round(s,3)
                ss.append(s)
            sec['evaluation_score'] = round(sum(ss)/len(ss),3) if ss else 0
        else:
            c = sec['counts_sum']
            tot = c['completo'] + c['parcial'] + c['ninguno'] + c['no_aplica']
            sc = (c['completo'] + 0.5*c['parcial'])/tot if tot else 0
            sec['evaluation_score'] = round(sc,3)
    avg = sum(s['evaluation_score'] for s in data['sections_of_the_capter'])/len(data['sections_of_the_capter'])
    data['chapter_average_score'] = round(avg,3)
    pid = data['id_capter']
    data['chapter_system_score'] = round(data['chapter_average_score']*PONDERACIONES.get(pid,0),3)
    return data


def generar_reporte_phva(capitulos: List[Dict]) -> Dict:
    resultado = {"etapas_phva": []}
    caps = {c['id_capter']:c for c in capitulos}
    for etapa,info in ETAPAS.items():
        s=0; lst=[]
        for cid in info['capitulos']:
            chap=caps.get(cid)
            if chap:
                lst.append(chap)
                s+=chap.get('chapter_system_score',0)
        resultado['etapas_phva'].append({
            'etapa':etapa,'peso_etapa':info['peso'],
            'puntaje_etapa':round(s,3),'capitulos':lst
        })
    return resultado