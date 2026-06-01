# dashboard/views.py
from django.shortcuts import render
from django.db.models import Avg, Sum
from .models import ResultadoSimce, Curso
from .datos_cualitativos import INFORMES_CURSOS, FALLBACK_CURSO, ESTUDIANTES, BRECHAS, ALERTAS, PLAN_ACCION
import json

def dashboard_estrategico(request):
    curso_filtro = request.GET.get('curso', '')
    asignatura_filtro = request.GET.get('asignatura', '')
    estudiante_filtro = request.GET.get('estudiante', '')

    resultados = ResultadoSimce.objects.all()

    # Filtro Dinámico de Alumnos
    if curso_filtro:
        curso_obj_para_filtro = Curso.objects.get(id=curso_filtro)
        nombre_nivel = curso_obj_para_filtro.nivel
        lista_estudiantes = [k for k, v in ESTUDIANTES.items() if v['curso'] == nombre_nivel]
    else:
        lista_estudiantes = list(ESTUDIANTES.keys())
    lista_estudiantes.sort()

    if curso_filtro:
        resultados = resultados.filter(curso__id=curso_filtro)
    if asignatura_filtro:
        resultados = resultados.filter(asignatura=asignatura_filtro)

    # KPIs Generales
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

    mostrar_detalle_curso = False
    detalle_curso = {}
    mostrar_estudiante = False
    detalle_estudiante = {}

    # Lógica de Vistas Múltiples
    if estudiante_filtro and estudiante_filtro in ESTUDIANTES:
        mostrar_estudiante = True
        detalle_estudiante = ESTUDIANTES[estudiante_filtro]
        detalle_estudiante['nombre'] = estudiante_filtro

    elif curso_filtro and asignatura_filtro:
        mostrar_detalle_curso = True
        curso_obj = Curso.objects.get(id=curso_filtro)
        llave_informe = f"{curso_obj.nivel}_{asignatura_filtro}"

        detalle_curso = INFORMES_CURSOS.get(llave_informe, FALLBACK_CURSO)

        res_especifico = resultados.first()
        if res_especifico:
            detalle_curso['preg_criticas_val'] = res_especifico.preguntas_criticas
            detalle_curso['preg_resto_val'] = 35 - res_especifico.preguntas_criticas if (35 - res_especifico.preguntas_criticas) > 0 else 0
        else:
            detalle_curso['preg_criticas_val'] = 0
            detalle_curso['preg_resto_val'] = 0

    else:
        # Modo Institucional Global
        if curso_filtro:
            cursos_labels = list(Curso.objects.filter(id=curso_filtro).values_list('nivel', flat=True))
        else:
            cursos_labels = list(Curso.objects.values_list('nivel', flat=True).distinct())

        logro_matematica, logro_lenguaje = [], []
        preg_criticas_mat, preg_criticas_len = [], []

        for curso_nombre in cursos_labels:
            res_mat = resultados.filter(curso__nivel=curso_nombre, asignatura='MAT').first()
            res_len = resultados.filter(curso__nivel=curso_nombre, asignatura='LEN').first()

            logro_matematica.append(res_mat.porcentaje_logro if res_mat else 0)
            preg_criticas_mat.append(res_mat.preguntas_criticas if res_mat else 0)

            logro_lenguaje.append(res_len.porcentaje_logro if res_len else 0)
            preg_criticas_len.append(res_len.preguntas_criticas if res_len else 0)

        detalle_curso = {
            'cursos_labels': json.dumps(cursos_labels),
            'logro_matematica': json.dumps(logro_matematica),
            'logro_lenguaje': json.dumps(logro_lenguaje),
            'preg_criticas_mat': json.dumps(preg_criticas_mat),
            'preg_criticas_len': json.dumps(preg_criticas_len),
            'riesgo_labels': json.dumps(['En Riesgo (<50%)', 'Estable/Controlado']),
            'riesgo_data': json.dumps([total_riesgo, 206 - total_riesgo if (206 - total_riesgo) > 0 else 0]),
            'brechas_labels': json.dumps([f"{b['nivel']} ({b['asignatura'][:3]})" for b in BRECHAS]),
            'brechas_data': json.dumps([b['brecha'] for b in BRECHAS]),
        }

    # Armado final del Contexto
    context = {
        'stats': stats_generales,
        'cursos_list': Curso.objects.all().order_by('nivel'),
        'curso_seleccionado': int(curso_filtro) if curso_filtro else '',
        'asignatura_seleccionada': asignatura_filtro,

        'lista_estudiantes': lista_estudiantes,
        'estudiante_seleccionado': estudiante_filtro,
        'mostrar_estudiante': mostrar_estudiante,
        'perfil_estudiante': detalle_estudiante,

        'tabla_resultados': resultados.order_by('curso__nivel', '-asignatura'),
        'brechas': BRECHAS,
        'alertas': ALERTAS,
        'plan_accion': PLAN_ACCION,

        'mostrar_detalle': mostrar_detalle_curso,
        'detalle_informe': detalle_curso,

        # Data extraída de los Word para los gráficos
        'hab_labels': json.dumps(detalle_curso.get('habilidades_labels', [])) if mostrar_detalle_curso else "[]",
        'hab_data': json.dumps(detalle_curso.get('habilidades_data', [])) if mostrar_detalle_curso else "[]",
        'cont_labels': json.dumps(detalle_curso.get('contenidos_labels', [])) if mostrar_detalle_curso else "[]",
        'cont_data': json.dumps(detalle_curso.get('contenidos_data', [])) if mostrar_detalle_curso else "[]",
        'est_nombres': json.dumps(detalle_curso.get('estudiantes_nombres', [])) if mostrar_detalle_curso else "[]",
        'est_puntajes': json.dumps(detalle_curso.get('estudiantes_puntajes', [])) if mostrar_detalle_curso else "[]",
    }

    return render(request, 'dashboard/index.html', context)