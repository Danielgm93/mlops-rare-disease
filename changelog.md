# CHANGELOG — Pipeline MLOps Rare Disease Triage

Este archivo documenta los cambios entre:

- **Versión inicial del pipeline** — Semanas **1–2**
- **Versión reestructurada del pipeline** — Semanas **5–6**

El objetivo es dejar explícito cómo evolucionó la propuesta a partir de los conceptos vistos en MLOps, alineando el diseño con el proyecto final (modelos ONNX, buckets, CI/CD dev/prod y despliegue automático).

---

## 1. Resumen de versiones

| Versión     | Descripción breve                                                                           |
| ----------- | ------------------------------------------------------------------------------------------- |
| Semana 1–2  | Pipeline conceptual de alto nivel: diseño, desarrollo y producción.                         |
| Semanas 5–6 | Pipeline end-to-end **implementable**, con tecnologías concretas y alineado a ONNX + CI/CD. |

---

## 2. Cambios en Diseño y Supuestos

### Semana 1–2

- Enfoque en un **panorama general** de MLOps:
  - Tipos de datos (numéricos, categóricos, texto, señales).
  - Consideraciones de **privacidad y ética**.
  - Reconocimiento del **desbalance** por enfermedades huérfanas.
- El sistema se describía como herramienta de apoyo, **no diagnóstico médico**.
- Métricas divididas entre enfermedades comunes y huérfanas (AUROC, F1, recall, PR-AUC, calibration error).

### Semanas 5–6

- Se detalla explícitamente el **objetivo clínico** de triage:
  - Estados: NO ENFERMO / LEVE / AGUDA / CRÓNICA.
  - Prioridad en **sensibilidad para enfermedades huérfanas**.
- Nuevas **suposiciones fundamentales**:
  - Existencia de HCE/EHR como fuente principal.
  - Ingesta **batch** de datos anonimizados.
  - Entrenamiento en entorno offline y servicio de inferencia en FastAPI + Docker.
  - Almacenamiento de modelos en **bucket externo** (no en el repo).
- Se documentan **restricciones** explícitas:
  - Privacidad, trazabilidad de acceso, desbalance extremo.
  - Soporte para ejecución local o en la nube.
  - Uso obligatorio de **ONNX** para el modelo final.
- Se amplía la sección de **métricas**, separando:
  - Comunes vs huérfanas.
  - Evaluación por subgrupos (edad, sexo, centro).

**Conclusión:** el diseño pasa de ser conceptual a un conjunto de **supuestos implementables**, con implicaciones claras para privacidad, despliegue y evaluación.

---

## 3. Cambios en el Pipeline Offline (Datos → Modelo → ONNX)

### Semana 1–2

- Se definían etapas generales:
  - Ingesta desde EHR/CSV/APIs.
  - Validación de datos (esquema, rangos, leakage).
  - Uso de un **feature store** (time-travel) de forma conceptual.
  - Modelos candidatos:
    - LogReg/GBM para comunes.
    - Transfer/meta-learning y ensembles calibrados para huérfanas.
  - Validación estratificada, holdout temporal, evaluación por subgrupos.
- No se detallaban tecnologías específicas ni flujos operativos con nombres de herramientas concretas.

### Semanas 5–6

- Se introduce un **pipeline offline detallado**:

  1. **Ingesta y gobierno de datos**

     - Extracción batch desde HCE/EHR.
     - Anonimización/pseudonimización.
     - Validación de esquema.
     - Carga a:
       - Data Lake (Parquet).
       - Data Warehouse (PostgreSQL / BigQuery).
     - Tecnologías explícitas:
       - Python + pandas, Airflow, S3/GCS/Azure Blob, Great Expectations (opcional).

  2. **Preprocesamiento y feature engineering**

     - Validación de rangos clínicos (fiebre, edad, días de síntomas).
     - Manejo de valores faltantes.
     - Pipelines `sklearn` con:
       - `Pipeline`, `ColumnTransformer`.
       - `StandardScaler` / `RobustScaler`, `OneHotEncoder`, etc.
     - Features derivadas (scores de comorbilidad, duración, interacciones).

  3. **Manejo de desbalance y modelado**

     - Separación explícita entre modelos para:
       - Enfermedades comunes.
       - Enfermedades huérfanas.
     - Técnicas mencionadas:
       - `class_weight="balanced"`, SMOTE/oversampling.
       - Transfer learning, few-shot/meta-learning (conceptual).
       - Ensembles calibrados (Platt / Isotonic).
     - Introducción del concepto de **umbral “no seguro”**.

  4. **Entrenamiento y validación**

     - Uso explícito de:
       - `StratifiedKFold`.
       - Splits temporales.
     - Métricas:
       - ROC-AUC, F1 macro, PR-AUC, calibración, análisis por subgrupos.
     - Registro de experimentos con **MLflow Tracking**.

  5. **Registro, versionado y exportación a ONNX**
     - Registro en **MLflow Model Registry** (nombre, versiones, estados).
     - Exportación con `skl2onnx`.
     - Artefactos ONNX separados para dev/prod:
       - `models/rare-disease/dev/model.onnx`
       - `models/rare-disease/prod/model.onnx`
     - Ejemplo de código de conversión a ONNX.
     - Subida de artefactos al **bucket externo**.

**Conclusión:** se pasa de un pipeline offline descrito conceptualmente a un flujo **concreto, versionable y ONNX-ready**, con herramientas y pasos bien definidos.

---

## 4. Cambios en el Pipeline Online (Servicio de Inferencia)

### Semana 1–2

- Se incluía un diagrama general donde “Despliegue” consistía en:
  - Construir una imagen Docker de la API.
  - Orquestación con K8s/edge.
- El énfasis estaba en:
  - Servicio HTTP como API.
  - Monitoreo de servicio, datos y modelo.
  - Reentrenamiento en caso de drift.

### Semanas 5–6

- Se conecta explícitamente el pipeline online con el **repositorio actual**:

  - Estado actual:

    - API FastAPI (`app/app.py`) con endpoints `/`, `/predict`, `/health`.
    - Modelo placeholder determinístico en `model/rules.py`.
    - Dockerfile para contenerización.
    - Tests (`tests/test_rules.py`).
    - Workflows de GitHub Actions (`pr-ci.yml`, `develop-cicd.yml`).

  - Diseño objetivo con ONNX:

    - Configuración mediante variables de entorno:
      - `MODEL_ENV` (dev/prod).
      - `MODEL_URI` (ruta en bucket).
    - Descarga del modelo ONNX en el contenedor.
    - Carga mediante `onnxruntime.InferenceSession`.
    - Validación de inputs con Pydantic.
    - Devolución de clase + probabilidad + metadatos.

  - Escenarios de uso:
    - Ejecución local en PC del médico usando Docker.
    - Despliegue en servidor o nube (EC2/VM/ECS/Kubernetes).

**Conclusión:** la versión 5–6 aterriza el diseño en la arquitectura **FastAPI + Docker + ONNX**, mostrando cómo se integrará el modelo real con el servicio de inferencia y el estado actual del repositorio.

---

## 5. Cambios en MLOps, CI/CD y Monitoreo

### Semana 1–2

- Se describía de forma general:
  - Despliegue de imagen Docker.
  - Monitoreo de servicio, datos y modelo (latencia, errores, drift).
  - Reentrenamiento cuando hubiera drift o nuevos datos.
- No se detallaba la integración con un repositorio concreto o con GitHub Actions.

### Semanas 5–6

- Se alinea explícitamente la propuesta con el **repositorio y los workflows actuales**:

  1. **CI/CD existente**:

     - `pr-ci.yml`:
       - Ejecuta `pytest` en cada Pull Request.
     - `develop-cicd.yml`:
       - Ejecuta `pytest`.
       - Construye la imagen Docker.
       - Publica en GHCR con tags `latest` y `<commit_sha>`.

  2. **Extensión hacia dev/prod (proyecto final)**:

     - Etapa `test`:
       - Descarga datos de prueba desde bucket/database.
       - Descarga modelo ONNX (dev/prod).
       - Corre tests de:
         - Respuesta a entradas definidas.
         - Métrica mínima (p.ej. ROC-AUC ≥ umbral).
     - Etapa `build/promote`:
       - Construye imagen Docker que descarga y sirve el modelo ONNX.
       - Push al registry (GHCR/ECR/otro).
       - Actualización del endpoint dev/prod en la plataforma de despliegue.

  3. **Monitoreo y logging**:

     - Uso de `/health` para verificar disponibilidad.
     - **Logs de predicciones**:
       - Escritura en `predicciones_dev.txt` o `predicciones_prod.txt` en un bucket.
     - Uso de estos logs para:
       - Análisis de distribución de entradas y salidas.
       - Detección de drift.
       - Generación de datasets para reentrenamiento.

  4. **Reentrenamiento**:
     - Orquestado con Airflow o scripts programados.
     - Reingesta de nuevos casos etiquetados.
     - Reejecución del pipeline offline.
     - Comparación con modelo actual.
     - Promoción en MLflow (Staging → Production).
     - Actualización del ONNX en el bucket y despliegue vía CI/CD.

**Conclusión:** la versión 5–6 concreta el diseño de MLOps, conectando:

- **Código actual** del repo,
- **modelos ONNX en bucket**,
- **GitHub Actions**,
- y el ciclo completo de monitoreo + reentrenamiento.

---

## 6. Cambios en Diagrama y Documentación

### Semana 1–2

- Diagrama Mermaid único con bloques:
  - Ingesta.
  - Entrenamiento.
  - Despliegue.
  - Operación (monitoreo + reentrenamiento).

### Semanas 5–6

- Nuevo diagrama Mermaid más detallado que separa:

  - **Diseño del sistema** (problema, tipos de datos, métricas).
  - **Pipeline offline** (ingesta, limpieza, preprocesamiento, modelos comunes/huérfanos, evaluación, registro + ONNX + bucket).
  - **Pipeline online** (FastAPI, descarga de ONNX, inferencia, logs TXT dev/prod).
  - **MLOps** (CI/CD, registro de imágenes, monitoreo, reentrenamiento).

- Documentación ampliada:
  - `pipeline.md` contiene el pipeline reestructurado, listo para ser implementado.
  - El README de Semanas 5–6 referencia a:
    - `pipeline.md` como documento principal del pipeline.
    - `CHANGELOG.md` como registro de cambios respecto a la versión inicial.

---

## 7. Resumen final de evolución

1. **De conceptual a implementable**  
   La propuesta pasó de un pipeline MLOps conceptual (Semana 1–2) a un diseño **implementable y alineado con el proyecto final** (Semanas 5–6), con tecnologías concretas y flujos claramente definidos.

2. **De “modelo genérico” a ONNX + buckets**  
   Se introdujo el uso de **ONNX**, MLflow Model Registry y almacenamiento de modelos en **buckets externos**, separando código y artefactos.

3. **De despliegue genérico a FastAPI + Docker + GitHub Actions**  
   El pipeline ahora se integra con:

   - La API FastAPI real del repositorio.
   - La imagen Docker y su despliegue.
   - Workflows de CI/CD en GitHub Actions.

4. **De monitoreo abstracto a logs TXT dev/prod + reentrenamiento**  
   Se definió el uso de archivos de texto (`predicciones_dev.txt`, `predicciones_prod.txt`) y su rol en monitoreo y reentrenamiento.

Esta evolución refleja la incorporación progresiva de conceptos de **MLOps** llevando la idea original a una arquitectura que un equipo de ML podría implementar de extremo a extremo.
