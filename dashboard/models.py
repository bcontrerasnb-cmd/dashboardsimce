from django.db import models

class Curso(models.Model):
    nivel = models.CharField(max_length=50) # Ej: "2° Medio B"

    def __str__(self):
        return self.nivel

class ResultadoSimce(models.Model):
    ASIGNATURAS = [('MAT', 'Matemática'), ('LEN', 'Lenguaje')]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    asignatura = models.CharField(max_length=3, choices=ASIGNATURAS)
    porcentaje_logro = models.FloatField()
    puntaje_simce = models.FloatField()
    estudiantes_riesgo = models.IntegerField(help_text="Estudiantes bajo 50% de logro")
    preguntas_criticas = models.IntegerField(help_text="Preguntas bajo 40% de acierto")

    def __str__(self):
        return f"{self.curso} - {self.get_asignatura_display()}"