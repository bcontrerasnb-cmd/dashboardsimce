import pandas as pd
import os
from django.core.management.base import BaseCommand
from dashboard.models import Curso, ResultadoSimce

class Command(BaseCommand):
    help = 'Carga masiva de resultados SIMCE desde un archivo Excel'

    def add_arguments(self, parser):
        # Ahora pedimos la ruta del archivo Excel
        parser.add_argument('ruta_excel', type=str, help='Ruta al archivo Excel (Tablero_SIMCE_Estrategico.xlsx)')

    def handle(self, *args, **kwargs):
        ruta_excel = kwargs['ruta_excel']

        if not os.path.exists(ruta_excel):
            self.stderr.write(self.style.ERROR(f'No se encontró el archivo: {ruta_excel}'))
            return

        try:
            # Leemos directamente el Excel y apuntamos a la hoja 'Resumen SIMCE'
            df = pd.read_excel(ruta_excel, sheet_name='Resumen SIMCE', engine='openpyxl')

            # Limpiamos filas vacías
            df = df.dropna(subset=['Curso', 'Asignatura'])

            registros_creados = 0
            registros_actualizados = 0

            for index, row in df.iterrows():
                nombre_curso = str(row['Curso']).strip()
                asignatura_raw = str(row['Asignatura']).strip()

                codigo_asignatura = 'MAT' if 'Matemática' in asignatura_raw else 'LEN'

                # 1. Buscar o Crear el Curso
                curso_obj, creado = Curso.objects.get_or_create(nivel=nombre_curso)

                # 2. Actualizar o Crear el Resultado Simce
                resultado, fue_creado = ResultadoSimce.objects.update_or_create(
                    curso=curso_obj,
                    asignatura=codigo_asignatura,
                    defaults={
                        'porcentaje_logro': float(row['Logro %']),
                        'puntaje_simce': float(row['SIMCE']),
                        'estudiantes_riesgo': int(row['N Est <50%']),
                        'preguntas_criticas': int(row['Preguntas <40%']),
                    }
                )

                if fue_creado:
                    registros_creados += 1
                else:
                    registros_actualizados += 1

            self.stdout.write(self.style.SUCCESS(
                f'Carga exitosa: {registros_creados} registros nuevos, {registros_actualizados} actualizados.'
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error al procesar el archivo: {str(e)}'))