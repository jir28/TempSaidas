import sys
import win32clipboard
import customtkinter as ctk
from PIL import Image, ImageGrab
from customtkinter import CTkImage
import json
import os
from datetime import datetime
import io

# CONFIGURACIÓN INICIAL
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Cálculo de Temperatura de Salidas")
app.geometry("680x980")

# CARGA DE IMÁGENES (Asegúrate de tener estos archivos en la misma carpeta)
try:
    img_sem = CTkImage(Image.open("SemBlindagem.JPG"), size=(300, 240))
    img_com = CTkImage(Image.open("ComBlindagem.JPG"), size=(300, 240))
    # img_b es opcional si no tienes el archivo, puedes comentar la línea
    if os.path.exists("cotaB.png"):
        img_b = CTkImage(Image.open("cotaB.png"), size=(300, 240))
    else:
        img_b = img_com  # Fallback

    flag_mex = CTkImage(Image.open("mexico.png"), size=(24, 24))
    flag_bra = CTkImage(Image.open("brasil.png"), size=(24, 24))
except Exception as e:
    print(f"Error cargando imágenes: {e}")
    # Crear placeholders si fallan las imagenes para que la app no crashee
    img_sem = None
    img_com = None
    img_b = None
    flag_mex = None
    flag_bra = None

# VARIABLES GLOBALES
inputs = {}
result_labels = {}
lang = "es"  # Idioma inicial
texts = {
    "es": {
        "title": "Cálculo de Temperatura de Salidas",
        "lang_btn": flag_mex,
        "labels": ["A (mm)", "B (mm)", "S (mm)", "L (mm)", "Sección Transversal (mm²)",
                   "Densidad Corriente(A/mm²)", "Temperatura Ambiente (°C)", "Temp. Oleo [ONAF2] (°C)"],
        "disp": "Disposición:",
        "options": ["Vertical", "Horizontal"],
        "mat": "Material:",
        "materials": ["Cobre", "Aluminio"],
        "oil": "Aceite:",
        "oils": ["Mineral", "Vegetal"],
        "aisl": "Aislamiento:",
        "aisl_opts": ["Kraft Termo.", "Nomex"],
        "ctc": "CTC (Transposto)",
        "blind": "Cable Blindado",
        "calc": "Calcular",
        "shot": "Captura",
        "result": ["Área Conducción", "Área Convección", "Pérdidas (W)",
                   "Pérdidas / Área", "ΔT", "Temperatura Total"],
        "ok": "✅ Temperatura dentro del margen permitido",
        "alert": "⚠️ Temperatura excedida (Máx: {max_t}°C)",
        "error": "⚠️ Verifica entradas numéricas"
    },
    "pt": {
        "title": "Cálculo da Temperatura de Saídas",
        "lang_btn": flag_bra,
        "labels": ["A (mm)", "B (mm)", "S (mm)", "L (mm)", "Seção Transversal (mm²)",
                   "Densidade Corrente(A/mm²)", "Temperatura Ambiente (°C)", "Temp. Óleo [ONAF2] (°C)"],
        "disp": "Disposição:",
        "options": ["Vertical", "Horizontal"],
        "mat": "Material:",
        "materials": ["Cobre", "Alumínio"],
        "oil": "Óleo:",
        "oils": ["Mineral", "Vegetal"],
        "aisl": "Isolamento:",
        "aisl_opts": ["Kraft Termo.", "Nomex"],
        "ctc": "CTC (Transposto)",
        "blind": "Cabo Blindado",
        "calc": "Calcular",
        "shot": "Captura",
        "result": ["Área Condução", "Área Convecção", "Perdas (W)",
                   "Perdas / Área", "ΔT", "Temperatura Total"],
        "ok": "✅ Temperatura dentro do limite permitido",
        "alert": "⚠️ Temperatura excedida (Máx: {max_t}°C)",
        "error": "⚠️ Verifique as entradas"
    }
}

HISTORIAL_FILE = "historial.json"
historial_calculos = []


# Funciones

def actualizar_textos():
    t = texts[lang]
    app.title(t["title"])
    if t["lang_btn"]:
        lang_btn.configure(image=t["lang_btn"])

    for i, key in enumerate(t["labels"]):
        entrada_frame.grid_slaves(row=i, column=0)[0].configure(text=key)

    dispo_label.configure(text=t["disp"])
    dispo_menu.configure(values=t["options"])
    mat_label.configure(text=t["mat"])
    mat_menu.configure(values=t["materials"])
    oil_label.configure(text=t["oil"])
    oil_menu.configure(values=t["oils"])
    aisl_label.configure(text=t["aisl"])
    aisl_menu.configure(values=t["aisl_opts"])
    ctc_check.configure(text=t["ctc"])
    blind_check.configure(text=t["blind"])
    calc_btn.configure(text=t["calc"])
    shot_btn.configure(text=t["shot"])

    # Mantener selecciones actuales si cambiamos idioma
    current_disp = dispo_var.get()
    # Mapeo simple para mantener consistencia visual si cambia idioma
    if lang == "es":
        if current_disp == "Horizontal": dispo_var.set("Horizontal")
        # Material
        if mat_menu.get() == "Alumínio": mat_menu.set("Aluminio")
    else:
        if mat_menu.get() == "Aluminio": mat_menu.set("Alumínio")

    for i, lbl in enumerate(t["result"]):
        result_frame.grid_slaves(row=i, column=0)[0].configure(text=lbl + ":")


def cambiar_idioma():
    global lang
    lang = "pt" if lang == "es" else "es"
    actualizar_textos()


def obtener_constantes(material_str, aceite_str, aisl_str, transposto_bool):
    # Definición de Constantes según VBA

    # MATERIAL
    # En VBA Alumínio tenía Coef 9999999 (error). 
    # Calculando proporcionalmente: (Rho_Al / Rho_Cu) * (Dens_Cu / Dens_Al) * 2.4 ~= 13.0
    if material_str in ["Cobre"]:
        peso_especifico = 8.92
        coef_cond = 2.4
    else:  # Aluminio
        peso_especifico = 2.7
        coef_cond = 13.0  # Valor estimado ingenieril para ajustar la fórmula

    # FACTOR DE PERDIDAS ADICIONALES
    # Si es CTC (Transposto), no hay pérdidas adicionales (factor 1.0)
    # Si es sólido, hay pérdidas adicionales (factor 1.3)
    factor_perdas = 1.0 if transposto_bool else 1.3

    # K CONDUCCION
    k_cond = 55

    # TEMPERATURA MÁXIMA PERMITIDA (Matriz del VBA)
    temp_max = 120  # Default
    if aceite_str == "Mineral":
        if aisl_str == "Kraft Termo.":
            temp_max = 120
        elif aisl_str == "Nomex":
            temp_max = 140
    elif aceite_str in ["Vegetal", "Vegetal "]:  # A veces quedan espacios
        if aisl_str == "Kraft Termo.":
            temp_max = 140
        elif aisl_str == "Nomex":
            temp_max = 180

    return peso_especifico, coef_cond, factor_perdas, k_cond, temp_max


def calcular():
    try:
        # Obtener valores de UI
        A = float(inputs["A (mm)"].get().replace(',', '.'))
        B = float(inputs["B (mm)"].get().replace(',', '.'))
        S = float(inputs["S (mm)"].get().replace(',', '.'))
        L = float(inputs["L (mm)"].get().replace(',', '.'))
        ST = float(inputs["Sección Transversal (mm²)"].get().replace(',', '.'))
        J = float(inputs["Densidad Corriente(A/mm²)"].get().replace(',', '.'))
        TA = float(inputs["Temperatura Ambiente (°C)"].get().replace(',', '.'))
        TTO = float(inputs["Temp. Oleo [ONAF2] (°C)"].get().replace(',', '.'))

        # Opciones Lógicas
        transposto = transposto_var.get()
        blindado = blindado_var.get()
        divb = dividirb_var.get()

        # Recuperar strings de los menús
        mat_sel = mat_menu.get()  # Cobre / Aluminio
        oil_sel = oil_menu.get()  # Mineral / Vegetal
        aisl_sel = aisla_var.get()  # Kraft / Nomex
        disp_sel = dispo_var.get()  # Vertical / Horizontal

        # Obtener Constantes Físicas
        peso_esp, coef_cond, perdas_adic, KCond, TempMax = obtener_constantes(mat_sel, oil_sel, aisl_sel, transposto)

        # H Convección (Según Initialize del VBA)
        # Horizontal = 120, Vertical = 85
        # NOTA: En app.py original tenías Vertical=85 y Horizontal=120, coincide con VBA Initialize.
        is_vertical = (disp_sel == "Vertical")
        HConv = 85 if is_vertical else 120

        # CÁLCULO DE ÁREAS (Geometría)
        B_efectiva = B / 2 if (blindado and divb) else B

        SDisCond = 0.0
        SDisConv = 0.0

        if not blindado:
            # Sin blindaje (Transposto o no, la geometria es igual, solo cambia el factor de pérdidas)
            SDisCond = (A + B + 2 * S) * 2 * L / 100
            SDisConv = ((A + 2 * S) + (B + 2 * S)) * 2 * L / 100
        else:
            # Con Blindaje
            if divb:
                SDisCond = ((A + B_efectiva) * L * 2) / 100
            else:
                SDisCond = (A * L * 2) / 100

            SDisConv = SDisCond  # En blindado Convección = Conducción según VBA

        # CÁLCULO DE PESO Y PÉRDIDAS
        PesoSaida = ST * L * peso_esp * 1e-6

        # Fórmula VBA: PerdaSaida = CoefCond * Peso * J^2 * (FactorAdicional si aplica)
        PerdaSaida = coef_cond * PesoSaida * (J ** 2) * perdas_adic

        # CÁLCULO TÉRMICO
        PerdaPorAreaCond = PerdaSaida / SDisCond
        PerdaPorAreaConv = PerdaSaida / SDisConv

        DeltaT = (PerdaPorAreaCond * S * KCond) + (PerdaPorAreaConv * HConv)
        TTotal = DeltaT + TA + TTO

        # Mostrar Resultados
        res_vals = {
            "Área Conducción": f"{SDisCond:.2f} cm²",
            "Área Convección": f"{SDisConv:.2f} cm²",
            "Pérdidas (W)": f"{PerdaSaida:.2f} W",
            "Pérdidas / Área": f"{PerdaPorAreaCond:.4f} + {PerdaPorAreaConv:.4f} W/cm²",
            "ΔT": f"{DeltaT:.2f} °C",
            "Temperatura Total": f"{TTotal:.2f} °C"
        }

        llaves = texts[lang]["result"]  # Usar las llaves del idioma actual para buscar en result_labels
        llaves_base = texts["es"]["result"]  # Llaves base para mapear el diccionario res_vals

        for i, key_base in enumerate(llaves_base):
            key_ui = llaves[i]
            result_labels[key_ui].configure(text=res_vals[key_base])

        # Mensaje de Alerta Dinámico
        if TTotal >= TempMax:
            msg_txt = texts[lang]["alert"].format(max_t=TempMax)
            msg_label.configure(text=msg_txt, text_color="red")
        else:
            msg_label.configure(text=texts[lang]["ok"], text_color="green")

        # Guardar en historial
        entrada = {
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "A": A, "B": B, "S": S, "L": L, "ST": ST, "J": J,
            "Material": mat_sel,
            "Aceite": oil_sel,
            "Temp. Total": round(TTotal, 2),
            "Max Permitida": TempMax,
            "Estado": "OK" if TTotal < TempMax else "ALERTA"
        }
        guardar_historial(entrada)

    except ValueError:
        msg_label.configure(text=texts[lang]["error"], text_color="orange")
    except Exception as e:
        msg_label.configure(text=f"Error inesperado: {e}", text_color="red")


def capturar_y_guardar(app):
    carpeta_capturas = os.path.join(os.getcwd(), "capturas")
    os.makedirs(carpeta_capturas, exist_ok=True)

    nombre_archivo = f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    ruta_archivo = os.path.join(carpeta_capturas, nombre_archivo)

    try:
        x = app.winfo_rootx()
        y = app.winfo_rooty()
        w = x + app.winfo_width()
        h = y + app.winfo_height()

        imagen = ImageGrab.grab(bbox=(x, y, w, h))
        imagen.save(ruta_archivo, "JPEG")

        output = io.BytesIO()
        imagen.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        msg_label.configure(text="Screenshot guardado y copiado", text_color="blue")
    except Exception as e:
        print(f"Error screenshot: {e}")


def actualizar_imagen(*args):
    if img_sem is None: return  # Evitar error si no hay imagen

    if blindado_var.get() and dividirb_var.get():
        img_label.configure(image=img_b)
        divb_check.grid()
    elif blindado_var.get():
        img_label.configure(image=img_com)
        divb_check.grid()
    else:
        img_label.configure(image=img_sem)
        divb_check.grid_remove()


def guardar_historial(entrada):
    global historial_calculos
    historial_calculos.append(entrada)
    if len(historial_calculos) > 20:
        historial_calculos = historial_calculos[-20:]

    with open(HISTORIAL_FILE, "w", encoding='utf-8') as f:
        json.dump(historial_calculos, f, indent=4, ensure_ascii=False)


def cargar_historial():
    global historial_calculos
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                historial_calculos = json.load(f)
        except:
            historial_calculos = []


def mostrar_historial():
    ventana = ctk.CTkToplevel(app)
    ventana.title("Historial de Cálculos")
    ventana.geometry("900x500")

    frame_tabla = ctk.CTkScrollableFrame(ventana, width=880, height=460)
    frame_tabla.pack(padx=10, pady=10)

    encabezados = ["Fecha", "Mat", "Oil", "A", "B", "J", "T.Total", "Máx", "Estado"]

    # Header
    for j, h in enumerate(encabezados):
        ctk.CTkLabel(frame_tabla, text=h, font=("Arial", 12, "bold")).grid(row=0, column=j, padx=5, pady=5)

    # Data (Invertido para ver lo más reciente arriba)
    for i, entrada in enumerate(reversed(historial_calculos), start=1):
        valores = [
            entrada.get("Fecha", ""),
            entrada.get("Material", ""),
            entrada.get("Aceite", ""),
            entrada.get("A", ""),
            entrada.get("B", ""),
            entrada.get("J", ""),
            f"{entrada.get('Temp. Total', 0)}°C",
            f"{entrada.get('Max Permitida', 0)}°C",
            entrada.get("Estado", "")
        ]

        color = "red" if entrada.get("Estado") == "ALERTA" else "black"

        for j, val in enumerate(valores):
            lbl = ctk.CTkLabel(frame_tabla, text=str(val), font=("Arial", 11), text_color=color if j == 8 else "black")
            lbl.grid(row=i, column=j, padx=5, pady=3)


# GUI SETUP
entrada_frame = ctk.CTkFrame(app)
entrada_frame.pack(pady=10)

# Generar Inputs
for i, label in enumerate(texts["es"]["labels"]):
    ctk.CTkLabel(entrada_frame, text=label).grid(row=i, column=0, padx=5, pady=3, sticky="e")
    entry = ctk.CTkEntry(entrada_frame)
    entry.grid(row=i, column=1, padx=5, pady=3)
    inputs[label] = entry

# Dropdowns y Opciones
dispo_label = ctk.CTkLabel(entrada_frame, text="Disposición:")
dispo_label.grid(row=0, column=2, padx=5, pady=3, sticky="e")
dispo_var = ctk.StringVar(value="Horizontal")  # Default VBA Horizontal
dispo_menu = ctk.CTkOptionMenu(entrada_frame, variable=dispo_var, values=texts["es"]["options"])
dispo_menu.grid(row=0, column=3)

mat_label = ctk.CTkLabel(entrada_frame, text="Material:")
mat_label.grid(row=1, column=2, padx=5, pady=3, sticky="e")
mat_menu = ctk.CTkOptionMenu(entrada_frame, values=texts["es"]["materials"])
mat_menu.grid(row=1, column=3)

oil_label = ctk.CTkLabel(entrada_frame, text="Aceite:")
oil_label.grid(row=2, column=2, padx=5, pady=3, sticky="e")
oil_menu = ctk.CTkOptionMenu(entrada_frame, values=texts["es"]["oils"])
oil_menu.grid(row=2, column=3)

aisl_label = ctk.CTkLabel(entrada_frame, text="Aislamiento:")
aisl_label.grid(row=3, column=2, padx=5, pady=3, sticky="e")
aisla_var = ctk.StringVar(value="Kraft Termo.")
aisl_menu = ctk.CTkOptionMenu(entrada_frame, variable=aisla_var, values=texts["es"]["aisl_opts"])
aisl_menu.grid(row=3, column=3)

transposto_var = ctk.BooleanVar()
ctc_check = ctk.CTkCheckBox(entrada_frame, text="CTC", variable=transposto_var)
ctc_check.grid(row=4, column=3, pady=5)

blindado_var = ctk.BooleanVar()
blind_check = ctk.CTkCheckBox(entrada_frame, text="Cable Blindado", variable=blindado_var, command=actualizar_imagen)
blind_check.grid(row=5, column=3, pady=5)

dividirb_var = ctk.BooleanVar()
divb_check = ctk.CTkCheckBox(entrada_frame, text="B/2", variable=dividirb_var, command=actualizar_imagen)
divb_check.grid(row=6, column=3, pady=5)
divb_check.grid_remove()

calc_btn = ctk.CTkButton(app, text="Calcular", command=calcular, font=("Arial", 14, "bold"))
calc_btn.pack(pady=10)

# Idioma Boton
if flag_mex:
    lang_btn = ctk.CTkButton(app, image=flag_mex, width=30, height=30, text="", command=cambiar_idioma,
                             fg_color="transparent")
    lang_btn.place(x=10, y=10)

msg_label = ctk.CTkLabel(app, text="", font=("Arial", 14, "bold"))
msg_label.pack(pady=5)

img_label = ctk.CTkLabel(app, text="")
if img_sem:
    img_label.configure(image=img_sem)
img_label.pack(pady=5)

result_frame = ctk.CTkFrame(app)
result_frame.pack(pady=10)

# Resultados
for i, label in enumerate(texts["es"]["result"]):
    ctk.CTkLabel(result_frame, text=label + ":").grid(row=i, column=0, padx=5, pady=3, sticky="e")
    result = ctk.CTkLabel(result_frame, text="---", font=("Arial", 14, "bold") if "Total" in label else None)
    result.grid(row=i, column=1, padx=5, pady=3, sticky="w")
    result_labels[label] = result

shot_btn = ctk.CTkButton(app, text="Screenshot", command=lambda: capturar_y_guardar(app))
shot_btn.pack(pady=5)

hist_btn = ctk.CTkButton(app, text="Historial", command=mostrar_historial, fg_color="gray")
hist_btn.pack(pady=5)

# Inicializar
cargar_historial()
actualizar_imagen()
actualizar_textos()
app.mainloop()