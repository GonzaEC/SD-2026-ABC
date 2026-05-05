import json
 
MAX_INTENTOS = 4
DELAYS = [1, 2, 4, 8]
 
def simular_flujo(exito_en_intento):
    """Simula el ciclo retry hasta éxito o DLQ."""
    msg = {"id": 1, "intentos": 0}
    resultado = None
 
    for intento in range(1, MAX_INTENTOS + 1):
        if intento == exito_en_intento:
            resultado = "ok"
            break
        elif intento == MAX_INTENTOS:
            resultado = "dlq"
        else:
            msg["intentos"] = intento
            resultado = f"retry_{DELAYS[intento - 1]}s"
 
    return resultado
 
def test_exito_en_primer_intento():
    assert simular_flujo(exito_en_intento=1) == "ok"
 
def test_exito_en_tercer_intento():
    assert simular_flujo(exito_en_intento=3) == "ok"
 
def test_fallo_total_va_a_dlq():
    assert simular_flujo(exito_en_intento=None) == "dlq"
 