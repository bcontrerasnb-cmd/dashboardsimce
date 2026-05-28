from django.shortcuts import render
from django.db.models import Avg, Sum
from .models import ResultadoSimce, Curso
import json

def dashboard_estrategico(request):
    # 1. Filtros del Dashboard Interactivo
    curso_filtro = request.GET.get('curso', '')
    asignatura_filtro = request.GET.get('asignatura', '')

    resultados = ResultadoSimce.objects.all()

    if curso_filtro:
        resultados = resultados.filter(curso__id=curso_filtro)
    if asignatura_filtro:
        resultados = resultados.filter(asignatura=asignatura_filtro)

    promedio_mat = resultados.filter(asignatura='MAT').aggregate(Avg('porcentaje_logro'))['porcentaje_logro__avg'] or 0
    promedio_len = resultados.filter(asignatura='LEN').aggregate(Avg('porcentaje_logro'))['porcentaje_logro__avg'] or 0
    cursos_criticos = resultados.filter(asignatura='MAT', porcentaje_logro__lt=40).count()
    total_riesgo = resultados.filter(asignatura='MAT').aggregate(Sum('estudiantes_riesgo'))['estudiantes_riesgo__sum'] or 0

    stats_generales = {
        'promedio_matematica': round(promedio_mat, 1),
        'promedio_lenguaje': round(promedio_len, 1),
        'cursos_criticos': cursos_criticos,
        'total_riesgo': total_riesgo
    }

    if curso_filtro:
        cursos_labels = list(Curso.objects.filter(id=curso_filtro).values_list('nivel', flat=True))
    else:
        cursos_labels = list(Curso.objects.values_list('nivel', flat=True).distinct())

    logro_matematica = []
    logro_lenguaje = []

    for curso_nombre in cursos_labels:
        res_mat = resultados.filter(curso__nivel=curso_nombre, asignatura='MAT').first()
        logro_matematica.append(res_mat.porcentaje_logro if res_mat else 0)
        res_len = resultados.filter(curso__nivel=curso_nombre, asignatura='LEN').first()
        logro_lenguaje.append(res_len.porcentaje_logro if res_len else 0)

    # 2. Datos Estáticos de Hojas Complementarias (Excel)
    brechas = [
        {'nivel': '4° básico', 'asignatura': 'Matemática', 'curso_a': '4° A (55.7%)', 'curso_b': '4° B (48.4%)', 'brecha': 7.3, 'lectura': 'Brecha alta: revisar planificación y práctica.'},
        {'nivel': '6° básico', 'asignatura': 'Matemática', 'curso_a': '6° A (35.7%)', 'curso_b': '6° B (44.5%)', 'brecha': 8.8, 'lectura': 'Brecha alta: revisar planificación y práctica.'},
        {'nivel': 'II° medio', 'asignatura': 'Matemática', 'curso_a': 'II° A (31.0%)', 'curso_b': 'II° B (30.6%)', 'brecha': 0.4, 'lectura': 'Problema homogéneo crítico.'},
        {'nivel': '4° básico', 'asignatura': 'Lenguaje', 'curso_a': '4° A (63.4%)', 'curso_b': '4° B (55.5%)', 'brecha': 7.9, 'lectura': 'Brecha alta: revisar planificación y práctica.'},
        {'nivel': 'II° medio', 'asignatura': 'Lenguaje', 'curso_a': 'II° A (53.7%)', 'curso_b': 'II° B (46.8%)', 'brecha': 6.9, 'lectura': 'Brecha alta: revisar planificación y práctica.'},
    ]

    alertas = [
        {'nivel': 'Alto', 'criterio': 'Estudiante <40% o curso <40%', 'accion': 'Plan individual/grupal, reforzamiento obligatorio', 'frecuencia': 'Semanal'},
        {'nivel': 'Medio', 'criterio': 'Estudiante 40%-55%', 'accion': 'Grupo de nivelación, práctica guiada', 'frecuencia': 'Quincenal'},
        {'nivel': 'Institucional', 'criterio': '>15 preguntas bajo 40%', 'accion': 'Reenseñanza de OA críticos', 'frecuencia': 'Quincenal'},
    ]

    plan_accion = [
        {'plazo': '30 días', 'foco': 'Matemática II° medio', 'accion': 'Plan de rescate: nivelación basales, 3 bloques semanales', 'resp': 'UTP / Depto.'},
        {'plazo': '30 días', 'foco': '6° A Matemática', 'accion': 'Reenseñanza focalizada en números, fracciones y decimales', 'resp': 'UTP / Docente'},
        {'plazo': '60 días', 'foco': 'Evaluaciones comunes', 'accion': 'Aplicar evaluación común por nivel en cursos críticos', 'resp': 'UTP'},
        {'plazo': '90 días', 'foco': 'Nuevo ensayo', 'accion': 'Comparar contra línea base de mayo', 'resp': 'Rectoría / UTP'},
    ]

    context = {
        'stats': stats_generales,
        'cursos_labels': json.dumps(cursos_labels),
        'logro_matematica': json.dumps(logro_matematica),
        'logro_lenguaje': json.dumps(logro_lenguaje),
        'riesgo_labels': json.dumps(['En Riesgo (<50%)', 'Estable/Controlado']),
        'riesgo_data': json.dumps([total_riesgo, 206 - total_riesgo if (206 - total_riesgo) > 0 else 0]),
        'cursos_list': Curso.objects.all().order_by('nivel'),
        'curso_seleccionado': int(curso_filtro) if curso_filtro else '',
        'asignatura_seleccionada': asignatura_filtro,
        'tabla_resultados': resultados.order_by('curso__nivel', '-asignatura'),

        # Inyección de datos de pestañas
        'brechas': brechas,
        'alertas': alertas,
        'plan_accion': plan_accion,
    }

    return render(request, 'dashboard/index.html', context)