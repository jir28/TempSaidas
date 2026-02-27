import femm


def crear_geometria_femm(cilindros, devanados):
    # 1. Iniciar FEMM y configurar problema Axisimétrico
    femm.openfemm()
    femm.newdocument(1)  # 1 = Axisimétrico
    # Unidades: mm, Tipo: axisimétrico, Precisión: 1e-8
    femm.ei_probdef('millimeters', 'axisymmetric', 1e-8, 10, 30)

    # 2. Definir Materiales Base
    femm.ei_addmaterial('Aceite', 2.2, 0)
    femm.ei_addmaterial('Pressboard', 3.8, 0)
    femm.ei_addmaterial('Cobre', 1, 0)  # Para los devanados

    # ==========================================
    # 3. DIBUJAR CILINDROS (Barreras aislantes)
    # ==========================================
    for i, cil in enumerate(cilindros):
        r_in = cil['diametro_interno'] / 2.0  # Convertir diámetro a radio (eje X)
        espesor = cil['espesor']
        r_out = r_in + espesor
        z_min = cil['z_min']  # Elevación inferior (eje Y)
        z_max = cil['z_max']  # Elevación superior (eje Y)

        # Dibujar rectángulo
        femm.ei_drawrectangle(r_in, z_min, r_out, z_max)

        # Poner etiqueta de material en el centro del cilindro
        r_centro = r_in + (espesor / 2.0)
        z_centro = (z_min + z_max) / 2.0

        femm.ei_addblocklabel(r_centro, z_centro)
        femm.ei_selectlabel(r_centro, z_centro)
        femm.ei_setblockprop('Pressboard', 1, 0, 0)
        femm.ei_clearselected()

    # ==========================================
    # 4. DIBUJAR DEVANADOS CON REDONDEO
    # ==========================================
    for i, dev in enumerate(devanados):
        r_in = dev['diametro_interno'] / 2.0
        espesor = dev['espesor']
        r_out = r_in + espesor
        z_min = dev['z_min']
        z_max = dev['z_max']
        radio_esquina = dev.get('redondeo', 1.0)  # 1mm por defecto
        voltaje = dev.get('voltaje', 0)  # Si tiene voltaje asignado

        # Dibujar rectángulo inicial
        femm.ei_drawrectangle(r_in, z_min, r_out, z_max)

        # Aplicar Redondeo (Fillet) en las 4 esquinas
        # FEMM tiene la función ei_createradius(x, y, r) para redondear nodos
        femm.ei_createradius(r_in, z_min, radio_esquina)
        femm.ei_createradius(r_out, z_min, radio_esquina)
        femm.ei_createradius(r_out, z_max, radio_esquina)
        femm.ei_createradius(r_in, z_max, radio_esquina)

        # Etiqueta de material en el centro del devanado
        r_centro = r_in + (espesor / 2.0)
        z_centro = (z_min + z_max) / 2.0

        femm.ei_addblocklabel(r_centro, z_centro)
        femm.ei_selectlabel(r_centro, z_centro)
        femm.ei_setblockprop('Cobre', 1, 0, 0)
        femm.ei_clearselected()

        # (Opcional) Si quieres aplicar voltaje a todo el bloque del devanado
        # Aquí crearíamos una condición de frontera y la asignaríamos a los bordes.

    # 5. Zoom para ver todo
    femm.ei_zoomnatural()
    print("Geometría generada exitosamente.")


# ==========================================
# DATOS DE ENTRADA DEL USUARIO
# ==========================================
# Aquí es donde cambias los parámetros para cada diseño diferente
# Puedes poner 1, 3 o 20 cilindros, el programa se adaptará solo.

lista_cilindros = [
    {'diametro_interno': 600, 'espesor': 3, 'z_min': 100, 'z_max': 2000},  # Cilindro 1
    {'diametro_interno': 630, 'espesor': 4, 'z_min': 100, 'z_max': 2000},  # Cilindro 2
    {'diametro_interno': 900, 'espesor': 5, 'z_min': 50, 'z_max': 2100}  # Barrera entre fases
]

lista_devanados = [
    # Devanado Baja Tensión (LV)
    {'diametro_interno': 650, 'espesor': 50, 'z_min': 200, 'z_max': 1800, 'redondeo': 1.0, 'voltaje': 0},
    # Devanado Alta Tensión (HV)
    {'diametro_interno': 750, 'espesor': 80, 'z_min': 200, 'z_max': 1800, 'redondeo': 1.0, 'voltaje': 431000}
]

# Ejecutar el programa
crear_geometria_femm(lista_cilindros, lista_devanados)