import os, json
from typing import Dict, List

TMP = os.path.join(os.getcwd(), 'temp_clientes')
os.makedirs(TMP, exist_ok=True)
CAP_ESPERADOS = {str(i) for i in range(4,11)}

def path_cliente(cid: str) -> str:
    return os.path.join(TMP, f"{cid}.json")

def guardar_temporal(cid: str, chapter):
    # Si es un modelo Pydantic, conviértelo a dict
    if hasattr(chapter, 'dict'):
        chapter = chapter.dict()
    p = path_cliente(cid)
    arr = json.load(open(p,encoding='utf-8')) if os.path.exists(p) else []
    arr = [c for c in arr if c['id_capter']!=chapter['id_capter']]
    arr.append(chapter)
    json.dump(arr, open(p,'w',encoding='utf-8'), indent=2, ensure_ascii=False)

def cargar_temporal(cid: str) -> List[Dict]:
    p = path_cliente(cid)
    return json.load(open(p,encoding='utf-8')) if os.path.exists(p) else []

def limpiar_temporal(cid: str):
    p = path_cliente(cid)
    if os.path.exists(p): os.remove(p)

def check_completo(cid: str) -> bool:
    ids = {c['id_capter'] for c in cargar_temporal(cid)}
    return CAP_ESPERADOS.issubset(ids)