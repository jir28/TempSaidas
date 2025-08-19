import customtkinter as ctk
from PIL import Image, ImageGrab
from customtkinter import CTkImage
import io
import win32clipboard


#CONFIGURACIÓN INICIAL
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Cálculo de Temperatura de Salidas")
app.geometry("680x920")

#CARGA DE IMÁGENES
img_sem = CTkImage(Image.open("SemBlindagem.JPG"), size=(300, 240))
img_com = CTkImage(Image.open("ComBlindagem.JPG"), size=(300, 240))
img_b = CTkImage(Image.open("cotaB.png"), size=(300, 240))
flag_mex = CTkImage(Image.open("mexico.png"), size=(24, 24))
flag_bra = CTkImage(Image.open("brasil.png"), size=(24, 24))

#VARIABLES GLOBALES
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
        "ctc": "CTC",
        "blind": "Cable Blindado",
        "calc": "Calcular",
        "shot": "Captura",
        "result": ["Área Conducción", "Área Convección", "Pérdidas (W)",
                   "Pérdidas / Área", "ΔT", "Temperatura Total"],
        "ok": "✅ Temperatura dentro del margen permitido",
        "alert_kraft": "⚠️ Temperatura excedida para Kraft Termo. (máx 120 °C)",
        "alert_nomex": "⚠️ Temperatura excedida para Nomex (máx 140 °C)",
        "error": "⚠️ Verifica entradas"
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
        "ctc": "CTC",
        "blind": "Cabo Blindado",
        "calc": "Calcular",
        "shot": "Captura",
        "result": ["Área Condução", "Área Convecção", "Perdas (W)",
                   "Perdas / Área", "ΔT", "Temperatura Total"],
        "ok": "✅ Temperatura dentro do limite permitido",
        "alert_kraft": "⚠️ Temperatura excedida para Kraft Termo. (máx 120 °C)",
        "alert_nomex": "⚠️ Temperatura excedida para Nomex (máx 140 °C)",
        "error": "⚠️ Verifique as entradas"
    }
}

#Funciones

def actualizar_textos():
    t = texts[lang]
    app.title(t["title"])
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
    for i, lbl in enumerate(t["result"]):
        result_frame.grid_slaves(row=i, column=0)[0].configure(text=lbl + ":")


def cambiar_idioma():
    global lang
    lang = "pt" if lang == "es" else "es"
    actualizar_textos()


def calcular():
    try:
        A = float(inputs["A (mm)"].get())
        B = float(inputs["B (mm)"].get())
        S = float(inputs["S (mm)"].get())
        L = float(inputs["L (mm)"].get())
        ST = float(inputs["Sección Transversal (mm²)"].get())
        J = float(inputs["Densidad Corriente(A/mm²)"].get())
        TA = float(inputs["Temperatura Ambiente (°C)"].get())
        TTO = float(inputs["Temp. Oleo [ONAF2] (°C)"].get())
        transposto = transposto_var.get()
        blindado = blindado_var.get()
        divb = dividirb_var.get()
        vertical = dispo_var.get() == texts[lang]["options"][0]
        aislamiento = aisla_var.get()

        peso_cobre = 8.92
        cond_cobre = 2.4
        perdas_adic = 1.3
        KCond = 55
        HConv = 85 if vertical else 120

        if not blindado and not transposto:
            SDisCond = (A + B + 2 * S) * 2 * L / 100
            SDisConv = ((A + 2 * S) + (B + 2 * S)) * 2 * L / 100
            PesoSaida = ST * L * peso_cobre * 1e-6
            PerdaSaida = cond_cobre * PesoSaida * J**2 * perdas_adic
        elif not blindado and transposto:
            SDisCond = (A + B + 2 * S) * 2 * L / 100
            SDisConv = ((A + 2 * S) + (B + 2 * S)) * 2 * L / 100
            PesoSaida = ST * L * peso_cobre * 1e-6
            PerdaSaida = cond_cobre * PesoSaida * J**2

        elif blindado and not transposto and not divb:
            SDisCond = (A * L * 2) / 100
            SDisConv = SDisCond
            PesoSaida = ST * L * peso_cobre * 1e-6
            PerdaSaida = cond_cobre * PesoSaida * J**2 * perdas_adic

        elif blindado and transposto and not divb:
            SDisCond = (A * L * 2) / 100
            SDisConv = SDisCond
            PesoSaida = ST * L * peso_cobre * 1e-6
            PerdaSaida = cond_cobre * PesoSaida * J**2

        B_efectiva = B / 2 if dividirb_var.get() else B

        if blindado and not transposto and divb:
            SDisCond = ((A + B_efectiva) * L * 2) /100
            SDisConv = SDisCond
            PesoSaida = ST * L * peso_cobre * 1e-6
            PerdaSaida = cond_cobre * PesoSaida * J ** 2 * perdas_adic

        elif blindado and transposto and divb:
            SDisCond = ((A + B_efectiva)* L * 2) / 100
            SDisConv = SDisCond
            PesoSaida = ST * L * peso_cobre * 1e-6
            PerdaSaida = cond_cobre * PesoSaida * J ** 2

        PerdaPorAreaCond = PerdaSaida / SDisCond
        PerdaPorAreaConv = PerdaSaida / SDisConv
        DeltaT = (PerdaPorAreaCond * S * KCond) + (PerdaPorAreaConv * HConv)
        TTotal = DeltaT + TA + TTO

        for key, val in zip(["Área Conducción", "Área Convección", "Pérdidas (W)",
                             "Pérdidas / Área", "ΔT", "Temperatura Total"],
                            [f"{SDisCond:.2f} cm²", f"{SDisConv:.2f} cm²", f"{PerdaSaida:.2f} W",
                             f"{PerdaPorAreaCond:.4f} + {PerdaPorAreaConv:.4f} W/cm²",
                             f"{DeltaT:.2f} °C", f"{TTotal:.2f} °C"]):
            result_labels[key].configure(text=val)

        # Mensaje de alerta
        if aislamiento == "Kraft Termo." and TTotal >= 120:
            msg_label.configure(text=texts[lang]["alert_kraft"], text_color="red")
        elif aislamiento == "Nomex" and TTotal >= 140:
            msg_label.configure(text=texts[lang]["alert_nomex"], text_color="red")
        else:
            msg_label.configure(text=texts[lang]["ok"], text_color="green")

    except ValueError:
        msg_label.configure(text=texts[lang]["error"], text_color="orange")


def capturar_y_copiar():
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    output = io.BytesIO()
    img.convert("RGB").save(output, "JPG")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def actualizar_imagen(*args):

    if blindado_var.get() and dividirb_var.get():
        img_label.configure(image=img_b)
        divb_check.grid()

    elif blindado_var.get():
        img_label.configure(image=img_com)
        divb_check.grid()
    else:
        img_label.configure(image=img_sem)
        divb_check.grid_remove()



# INTERFAZ
entrada_frame = ctk.CTkFrame(app)
entrada_frame.pack(pady=10)

for i, label in enumerate(texts["es"]["labels"]):
    ctk.CTkLabel(entrada_frame, text=label).grid(row=i, column=0, padx=5, pady=3, sticky="e")
    entry = ctk.CTkEntry(entrada_frame)
    entry.grid(row=i, column=1, padx=5, pady=3)
    inputs[label] = entry

# Opciones
dispo_label = ctk.CTkLabel(entrada_frame, text="Disposición:")
dispo_label.grid(row=0, column=2, padx=5, pady=3, sticky="e")
dispo_var = ctk.StringVar(value="Vertical")
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

calc_btn = ctk.CTkButton(app, text="Calcular", command=calcular)
calc_btn.pack(pady=15)

# Selector de idioma (botón de imagen)
lang_btn = ctk.CTkButton(app, image=flag_mex, width=24, height=24, text="", command=cambiar_idioma, fg_color="transparent")
lang_btn.place(x=10, y=10)

msg_label = ctk.CTkLabel(app, text="", font=("Arial", 13))
msg_label.pack(pady=5)

img_label = ctk.CTkLabel(app, text="", image=img_sem)
img_label.pack(pady=5)

result_frame = ctk.CTkFrame(app)
result_frame.pack(pady=10)

for i, label in enumerate(texts["es"]["result"]):
    ctk.CTkLabel(result_frame, text=label + ":").grid(row=i, column=0, padx=5, pady=3, sticky="e")
    result = ctk.CTkLabel(result_frame, text="---", font=("Arial", 14, "bold") if "Total" in label else None)
    result.grid(row=i, column=1, padx=5, pady=3, sticky="w")
    result_labels[label] = result

shot_btn = ctk.CTkButton(app, text="Screenshot", command=capturar_y_copiar)
shot_btn.pack(pady=10)

actualizar_imagen()
actualizar_textos()
app.mainloop()
