from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict

# ---- Esquema de petición ----
class QuestionsIn(BaseModel):
    id_pregunta: str
    pregunta: str
    respuesta: str

class SectionInput(BaseModel):
    id_seccion: str
    seccion: str
    preguntas_y_respuestas: List[QuestionsIn]
    subsecciones: Optional[List[Dict]] = None

class PromptInput(BaseModel):
    id_cliente: str
    capitulo_id: str
    secciones: List[SectionInput]

# ---- Esquemas de respuesta (tus modelos Pydantic) ----
class Questions(BaseModel):
    question: str
    id_question: str
    evaluation: Literal["COMPLETO", "PARCIAL", "NINGUNO", "NO_APLICA"]

class SummaryCounts(BaseModel):
    completo: int
    parcial: int
    ninguno: int
    no_aplica: int

class Subsection(BaseModel):
    id_subsection: str
    name_subsection: str
    areas_for_improvement: List[str] = []
    fulfilled_aspects: List[str] = []
    questions_of_the_subsection: List[Questions] = []
    counts_sum: SummaryCounts

class Section(BaseModel):
    id_section: str
    name_section: str
    areas_for_improvement: List[str]
    fulfilled_aspects: List[str]
    questions_of_the_section: Optional[List[Questions]] = None
    subsections: Optional[List[Subsection]] = None
    counts_sum: SummaryCounts

class Chapter(BaseModel):
    id_capter: str
    sections_of_the_capter: List[Section]