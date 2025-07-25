import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
from typing import Dict
from .modelos import PromptInput
from .inferencia import Evaluador, score_capitulo, generar_reporte_phva
from .utils import guardar_temporal, cargar_temporal, check_completo, limpiar_temporal

load_dotenv()

app = FastAPI()
eval = Evaluador()

@app.post("/evaluar")
async def evaluar(raw_input: Dict):
    try:
        # Asegura que exista siempre la lista de preguntas
        for sec in raw_input.get('secciones', []):
            sec.setdefault('preguntas_y_respuestas', [])
            for sub in sec.get('subsecciones', []):
                sub.setdefault('preguntas_y_respuestas', [])

        # Validación Pydantic
        input_data = PromptInput(**raw_input)

        # Inferencia + Scoring
        raw = eval.extract(input_data)
        scored = score_capitulo(raw)

        # Guardado
        guardar_temporal(input_data.id_cliente, scored)

        # Informe final si ya están todos
        if check_completo(input_data.id_cliente):
            todos = cargar_temporal(input_data.id_cliente)
            informe = generar_reporte_phva(todos)
            limpiar_temporal(input_data.id_cliente)
            return {"status": "completo", "informe": informe}
        else:
            ids = sorted([c['id_capter'] for c in cargar_temporal(input_data.id_cliente)])
            return {"status": "pendiente", "recibidos": ids}

    except ValidationError as ve:
        # Errores de esquema
        raise HTTPException(status_code=422, detail=ve.errors())
    except Exception as e:
        # Imprime rastro en consola y devuelve detalle al cliente
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
