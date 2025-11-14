
# Rare Disease Triage — Demo en Docker

Servicio sencillo para demostrar un **pipeline MLOps** y un **servicio contenedorizado** que, a partir de síntomas,
retorna uno de los estados:
- **NO ENFERMO**
- **ENFERMEDAD LEVE**
- **ENFERMEDAD AGUDA**
- **ENFERMEDAD CRÓNICA**

> Nota: el "modelo" es una función determinística de reglas (archivo `model/rules.py`).
> Este reemplazo permite probar despliegue, contratos de entrada/salida y CI/CD sin entrenar nada.

## Requisitos
- Docker 20+

## Construir la imagen
```bash
docker build -t rare-disease:latest .
```

## Ejecutar el contenedor
```bash
docker run --rm -p 8000:8000 rare-disease:latest
```
La API quedará disponible en: `http://localhost:8000/` (formulario HTML)  
Endpoint JSON: `POST http://localhost:8000/predict`

### Ejemplo con `curl`
```bash
curl -s -X POST http://localhost:8000/predict   -H "Content-Type: application/json"   -d '{"fever":2.5,"pain":3,"days":3,"comorbidity":0,"age":40}'
```

### Cobertura de los 4 estados (ejemplos)
```bash
# NO ENFERMO
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json"   -d '{"fever":0.5,"pain":1.0,"days":0}'

# ENFERMEDAD LEVE
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json"   -d '{"fever":2.0,"pain":3.0,"days":3}'

# ENFERMEDAD AGUDA
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json"   -d '{"fever":6.0,"pain":6.0,"days":10,"comorbidity":1}'

# ENFERMEDAD CRÓNICA
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json"   -d '{"fever":4.0,"pain":4.0,"days":45}'
```

## Estructura
```
/mlops-rare-disease
├─ pipeline.md            # Descripción y diagrama Mermaid del pipeline MLOps
├─ Dockerfile
├─ .dockerignore
├─ requirements.txt
├─ app/
│  └─ app.py              # API FastAPI (form + endpoint /predict)
└─ model/
   └─ rules.py            # "Modelo" basado en reglas
```

## Notas
- Sustituye `model/rules.py` por un modelo real (p. ej., ONNX/Sklearn). Respeta el contrato de entrada/salida.
- Para despliegue a escala, usar orquestador (K8s) y observabilidad (métricas, *logs* y *alerts*).
