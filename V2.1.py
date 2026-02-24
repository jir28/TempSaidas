import customtkinter as ctk
from PIL import Image, ImageGrab
import os
import json
from datetime import datetime
import win32clipboard
import io

# --- CONFIGURACIÓN ESTÉTICA ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class EngineeringApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración Ventana Principal
        self.title("Cálculo de Temperatura de Salidas - WEG")
        # Ajustamos el tamaño ya que quitamos la barra lateral, puede ser menos ancha
        self.geometry("950x720")
        self.minsize(900, 650)

        # --- VARIABLES DE ESTADO (Persistentes) ---
        self.inputs = {}
        self.result_labels = {}
        self.historial_calculos = []

        # Variables de Checkbox/Radios
        self.var_transposto = ctk.BooleanVar(value=False)
        self.var_blindado = ctk.BooleanVar(value=False)
        self.var_divb = ctk.BooleanVar(value=False)
        self.var_dispo = ctk.StringVar(value="Horizontal")
        self.var_mat = ctk.StringVar(value="Cobre")
        self.var_oil = ctk.StringVar(value="Mineral")
        self.var_aisl = ctk.StringVar(value="Kraft Termo.")

        # --- LAYOUT PRINCIPAL (FILAS) ---
        # Fila 0: Header (Botones arriba)
        # Fila 1: Contenido Principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. HEADER SUPERIOR (Navegación)
        self.header_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))

        # Logo / Título a la izquierda
        self.lbl_logo = ctk.CTkLabel(self.header_frame, text="Temperatura | WEG", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_logo.pack(side="left", padx=(0, 30))

        # Botones de Navegación (Arriba, estilo Pestaña)
        self.btn_calc = ctk.CTkButton(self.header_frame, text="Calculadora", width=120, height=35,
                                      font=("Arial", 13, "bold"), command=self.mostrar_calculadora)
        self.btn_calc.pack(side="left", padx=5)

        self.btn_hist = ctk.CTkButton(self.header_frame, text="Historial", width=120, height=35,
                                      font=("Arial", 13, "bold"), fg_color="transparent", border_width=0,
                                      text_color=("gray10", "#DCE4EE"), command=self.mostrar_historial)
        self.btn_hist.pack(side="left", padx=5)

        # 2. ÁREA DE CONTENIDO (CONTENEDOR PRINCIPAL)
        # Ahora está en row=1
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # --- INICIALIZACIÓN DE VISTAS ---
        self.frame_calc_view = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_hist_view = None

        # Construimos la calculadora UNA SOLA VEZ al iniciar
        self.construir_interfaz_calculadora()

        # Mostramos la calculadora por defecto
        self.mostrar_calculadora()

    def construir_interfaz_calculadora(self):
        # Configurar Grid
        self.frame_calc_view.grid_columnconfigure(0, weight=1)  # Inputs
        self.frame_calc_view.grid_columnconfigure(1, weight=1)  # Resultados
        self.frame_calc_view.grid_rowconfigure(0, weight=1)

        # === SECCIÓN IZQUIERDA: INPUTS ===
        self.frame_inputs = ctk.CTkFrame(self.frame_calc_view)
        self.frame_inputs.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        self.frame_inputs.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self.frame_inputs, text="PARÁMETROS DE ENTRADA", font=("Arial", 14, "bold")).grid(row=0, column=0,
                                                                                                       columnspan=2,
                                                                                                       pady=(10, 5))

        # Geometría
        self.crear_subgrupo(self.frame_inputs, "Geometría", 1, [
            ("A (mm)", "A"), ("B (mm)", "B"),
            ("S (mm)", "S"), ("L (mm)", "L")
        ])

        # Eléctricos
        self.crear_subgrupo(self.frame_inputs, "Datos Eléctricos y Térmicos", 5, [
            ("Sección Trans. (mm²)", "ST"), ("Densidad (A/mm²)", "J"),
            ("Temp. Amb. (°C)", "TA"), ("Temp. Oleo (°C)", "TO")
        ])

        # Combos
        frame_conf = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        frame_conf.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(frame_conf, text="Configuración Materiales", font=("Arial", 12, "bold"), text_color="gray").pack(
            anchor="w")
        conf_grid = ctk.CTkFrame(frame_conf, fg_color="transparent")
        conf_grid.pack(fill="x", pady=2)

        self.crear_combo(conf_grid, "Disposición", self.var_dispo, ["Vertical", "Horizontal"], 0, 0)
        self.crear_combo(conf_grid, "Material", self.var_mat, ["Cobre", "Aluminio"], 0, 1)
        self.crear_combo(conf_grid, "Aceite", self.var_oil, ["Mineral", "Vegetal"], 1, 0)
        self.crear_combo(conf_grid, "Aislamiento", self.var_aisl, ["Kraft Termo.", "Nomex"], 1, 1)

        # Checkboxes
        frame_chk = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        frame_chk.grid(row=10, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        ctk.CTkCheckBox(frame_chk, text="Cable Transposto (CTC)", variable=self.var_transposto).pack(side="left",
                                                                                                     padx=10)
        ctk.CTkCheckBox(frame_chk, text="Blindado", variable=self.var_blindado,
                        command=self.actualizar_imagen_check).pack(side="left", padx=10)
        self.chk_divb = ctk.CTkCheckBox(frame_chk, text="Dividir B/2", variable=self.var_divb,
                                        command=self.actualizar_imagen_check)

        # Botón Calcular
        self.btn_run = ctk.CTkButton(self.frame_inputs, text="CALCULAR TEMPERATURA", height=50,
                                     font=("Arial", 15, "bold"), fg_color="#0066CC", hover_color="#0055AA",
                                     command=self.calcular)
        self.btn_run.grid(row=11, column=0, columnspan=2, sticky="ew", padx=20, pady=20)

        # === SECCIÓN DERECHA: RESULTADOS ===
        self.frame_results = ctk.CTkFrame(self.frame_calc_view, fg_color="white")
        self.frame_results.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.frame_results.grid_columnconfigure(0, weight=1)

        # Imagen
        self.img_container = ctk.CTkLabel(self.frame_results, text="[ Imagen del Esquema ]",
                                          fg_color="#EBEBEB", height=250, corner_radius=6)
        self.img_container.pack(fill="x", padx=10, pady=10)
        self.cargar_imagenes()

        # Resultados Texto
        ctk.CTkLabel(self.frame_results, text="Resultados del Análisis", font=("Arial", 16, "bold"),
                     text_color="black").pack(pady=(10, 5))
        self.res_container = ctk.CTkFrame(self.frame_results, fg_color="transparent")
        self.res_container.pack(fill="both", expand=True, padx=10)

        self.crear_fila_res("Área Conducción:", "---", "res_cond")
        self.crear_fila_res("Área Convección:", "---", "res_conv")
        self.crear_fila_res("Pérdidas Totales:", "--- W", "res_loss")
        self.crear_fila_res("Pérdidas / Área:", "--- W/cm²", "res_area")
        ctk.CTkFrame(self.res_container, height=2, fg_color="gray").pack(fill="x", pady=10)
        self.crear_fila_res("Elevación (ΔT):", "--- °C", "res_dt")
        self.crear_fila_res("Temperatura Total:", "--- °C", "res_total", font_size=22, is_bold=True)

        self.lbl_status = ctk.CTkLabel(self.frame_results, text="Esperando cálculo...", font=("Arial", 12),
                                       text_color="gray")
        self.lbl_status.pack(pady=10)

        ctk.CTkButton(self.frame_results, text="Captura de Pantalla", fg_color="gray",
                      command=lambda: self.capturar(self)).pack(pady=10)



    # --- NAVEGACIÓN (TOP BAR) ---
    def mostrar_calculadora(self):
        if self.frame_hist_view is not None:
            self.frame_hist_view.pack_forget()

        # Botones Top Bar: Calculadora Activa (Azul), Historial Inactivo (Transparente)
        self.btn_calc.configure(fg_color=["#3B8ED0", "#1F6AA5"], text_color=("white", "white"))
        self.btn_hist.configure(fg_color="transparent", text_color=("gray10", "gray80"))

        self.frame_calc_view.pack(fill="both", expand=True)

    def dibujar_esquema_dinamico(self, A, B, S):
        """
        Dibuja la geometría real de la salida basada en los inputs A y B.
        """
        # Crear un Canvas si no existe (puedes ponerlo donde iba self.img_container)
        if not hasattr(self, 'canvas_dibujo'):
            self.canvas_dibujo = ctk.CTkCanvas(self.frame_results, width=300, height=200, bg="#EBEBEB",
                                               highlightthickness=0)
            self.canvas_dibujo.pack(fill="x", padx=10, pady=10, before=self.res_container)
            # Ocultar la imagen estática anterior si existe
            if hasattr(self, 'img_container'):
                self.img_container.pack_forget()

        c = self.canvas_dibujo
        c.delete("all")  # Limpiar dibujo anterior

        # Escalar para que quepa en el canvas (300x200)
        # Margen de 20px
        w_canvas = 300
        h_canvas = 200
        padding = 40

        # Relación de aspecto
        max_dim = max(A, B)
        scale = (min(w_canvas, h_canvas) - padding * 2) / max_dim

        w_rect = A * scale
        h_rect = B * scale

        # Coordenadas centradas
        x1 = (w_canvas - w_rect) / 2
        y1 = (h_canvas - h_rect) / 2
        x2 = x1 + w_rect
        y2 = y1 + h_rect

        # Dibujar Aislamiento (S) - Un rectángulo más grande y claro
        s_pixel = S * scale  # Escalar el espesor S
        c.create_rectangle(x1 - s_pixel, y1 - s_pixel, x2 + s_pixel, y2 + s_pixel,
                           outline="#A0A0A0", fill="#D0E0E3", width=1, dash=(2, 2))

        # Dibujar Conductor (Cobre/Aluminio)
        color_fill = "#B87333" if self.var_mat.get() == "Cobre" else "#A9A9A9"  # Cobre vs Aluminio
        c.create_rectangle(x1, y1, x2, y2, outline="black", fill=color_fill, width=2)

        # Dibujar Cotas (Texto)
        # Cota A
        c.create_line(x1, y2 + 15, x2, y2 + 15, arrow=ctk.LAST, fill="black")  # Flecha simulada
        c.create_text((x1 + x2) / 2, y2 + 25, text=f"A={A}mm", fill="black", font=("Arial", 10, "bold"))

        # Cota B
        c.create_line(x2 + 15, y1, x2 + 15, y2, arrow=ctk.LAST, fill="black")
        c.create_text(x2 + 35, (y1 + y2) / 2, text=f"B={B}mm", fill="black", font=("Arial", 10, "bold"))

    def mostrar_historial(self):
        self.frame_calc_view.pack_forget()

        # Botones Top Bar: Calculadora Inactiva (Transparente), Historial Activo (Azul)
        self.btn_calc.configure(fg_color="transparent", text_color=("gray10", "gray80"))
        self.btn_hist.configure(fg_color=["#3B8ED0", "#1F6AA5"], text_color=("white", "white"))

        if self.frame_hist_view is not None:
            self.frame_hist_view.destroy()

        self.frame_hist_view = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_hist_view.pack(fill="both", expand=True)

        ctk.CTkLabel(self.frame_hist_view, text="Historial de Sesión", font=("Arial", 20)).pack(pady=20)

        scroll = ctk.CTkScrollableFrame(self.frame_hist_view)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        headers = ctk.CTkFrame(scroll, fg_color="transparent")
        headers.pack(fill="x", pady=5)
        ctk.CTkLabel(headers, text="Hora", width=60, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Material", width=80, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Temp. Total", width=100, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Estado", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        if not self.historial_calculos:
            ctk.CTkLabel(scroll, text="No hay cálculos aún.", text_color="gray").pack(pady=20)

        for item in reversed(self.historial_calculos):
            card = ctk.CTkFrame(scroll, fg_color=("gray90", "gray20"))
            card.pack(fill="x", padx=5, pady=2)

            ctk.CTkLabel(card, text=item["hora"], width=60).pack(side="left", padx=5)
            ctk.CTkLabel(card, text=item["mat"], width=80).pack(side="left", padx=5)

            t_lbl = ctk.CTkLabel(card, text=f"{item['total']}°C", width=100, font=("Arial", 12, "bold"))
            t_lbl.pack(side="left", padx=5)

            status_color = "red" if "PELIGRO" in item["estado"] else "green"
            ctk.CTkLabel(card, text=item["estado"], text_color=status_color).pack(side="left", padx=5)

    # --- HELPERS UI ---
    def crear_subgrupo(self, parent, titulo, start_row, campos):
        ctk.CTkLabel(parent, text=titulo, font=("Arial", 11, "bold"), text_color="gray").grid(row=start_row, column=0,
                                                                                              columnspan=2, sticky="w",
                                                                                              padx=15, pady=(10, 2))
        row = start_row + 1
        col = 0
        for label_text, key in campos:
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, sticky="ew", padx=10, pady=2)
            lbl = ctk.CTkLabel(f, text=label_text, width=100, anchor="w", font=("Arial", 12))
            lbl.pack(side="left")
            entry = ctk.CTkEntry(f, height=28, width=80)
            entry.pack(side="right", fill="x", expand=True)
            self.inputs[key] = entry
            col += 1
            if col > 1:
                col = 0
                row += 1

    def crear_combo(self, parent, label, variable, values, r, c):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=r, column=c, sticky="ew", padx=5, pady=2)
        ctk.CTkLabel(f, text=label, anchor="w", font=("Arial", 11)).pack(anchor="w")
        ctk.CTkOptionMenu(f, variable=variable, values=values, height=25).pack(fill="x")

    def crear_fila_res(self, label, val_inicial, key, font_size=14, is_bold=False):
        f = ctk.CTkFrame(self.res_container, fg_color="transparent")
        f.pack(fill="x", pady=4)
        ctk.CTkLabel(f, text=label, font=("Arial", 12), text_color="gray").pack(side="left")
        font_w = "bold" if is_bold else "normal"
        lbl_val = ctk.CTkLabel(f, text=val_inicial, font=("Arial", font_size, font_w), text_color="black")
        lbl_val.pack(side="right")
        self.result_labels[key] = lbl_val

    # --- LÓGICA DE NEGOCIO ---
    def cargar_imagenes(self):
        try:
            if os.path.exists("SemBlindagem.JPG"):
                self.img_sem = ctk.CTkImage(Image.open("SemBlindagem.JPG"), size=(350, 200))
                self.img_container.configure(image=self.img_sem, text="")
            if os.path.exists("ComBlindagem.JPG"):
                self.img_com = ctk.CTkImage(Image.open("ComBlindagem.JPG"), size=(350, 200))
            if os.path.exists("cotaB.png"):
                self.img_b = ctk.CTkImage(Image.open("cotaB.png"), size=(350, 200))
        except:
            pass

    def actualizar_imagen_check(self):
        if self.var_blindado.get():
            self.chk_divb.pack(side="left", padx=10)
            if hasattr(self, 'img_com'):
                img = self.img_b if self.var_divb.get() and hasattr(self, 'img_b') else self.img_com
                self.img_container.configure(image=img)
        else:
            self.chk_divb.pack_forget()
            if hasattr(self, 'img_sem'):
                self.img_container.configure(image=self.img_sem)

    def calcular(self):
        try:
            vals = {k: float(v.get().replace(',', '.')) for k, v in self.inputs.items() if v.get()}
            if len(vals) < 8: raise ValueError("Faltan campos")

            A, B, S, L = vals["A"], vals["B"], vals["S"], vals["L"]
            ST, J, TA, TO = vals["ST"], vals["J"], vals["TA"], vals["TO"]

            is_alum = self.var_mat.get() == "Aluminio"
            peso_esp = 2.7 if is_alum else 8.92
            coef_cond = 13.0 if is_alum else 2.4
            factor_perdas = 1.0 if self.var_transposto.get() else 1.3
            k_cond = 55

            oil = self.var_oil.get()
            aisl = self.var_aisl.get()
            temp_max = 120
            if oil == "Mineral" and aisl == "Nomex": temp_max = 140
            if oil == "Vegetal": temp_max = 140 if aisl == "Kraft Termo." else 180

            h_conv = 85 if self.var_dispo.get() == "Vertical" else 120
            blindado = self.var_blindado.get()

            if not blindado:
                s_dis_cond = (A + B + 2 * S) * 2 * L / 100
                s_dis_conv = ((A + 2 * S) + (B + 2 * S)) * 2 * L / 100
            else:
                b_efectiva = B / 2 if self.var_divb.get() else B
                base_calc = (A + b_efectiva) if (self.var_divb.get() and blindado) else A
                s_dis_cond = (base_calc * L * 2) / 100
                s_dis_conv = s_dis_cond

            peso_saida = ST * L * peso_esp * 1e-6
            perda_saida = coef_cond * peso_saida * (J ** 2) * factor_perdas
            perda_area_cond = perda_saida / s_dis_cond
            perda_area_conv = perda_saida / s_dis_conv
            delta_t = (perda_area_cond * S * k_cond) + (perda_area_conv * h_conv)
            t_total = delta_t + TA + TO

            self.result_labels["res_cond"].configure(text=f"{s_dis_cond:.2f} cm²")
            self.result_labels["res_conv"].configure(text=f"{s_dis_conv:.2f} cm²")
            self.result_labels["res_loss"].configure(text=f"{perda_saida:.2f} W")
            self.result_labels["res_area"].configure(text=f"{perda_area_cond:.3f} W/cm²")
            self.result_labels["res_dt"].configure(text=f"{delta_t:.2f} °C")
            self.result_labels["res_total"].configure(text=f"{t_total:.2f} °C")

            estado_msg = "OK"
            if t_total < temp_max:
                self.lbl_status.configure(text=f" APROBADO (Máx {temp_max}°C)", text_color="green")
                self.result_labels["res_total"].configure(text_color="green")
            else:
                estado_msg = "PELIGRO"
                self.lbl_status.configure(text=f" PELIGRO - SUPERA LÍMITE ({temp_max}°C)", text_color="red")
                self.result_labels["res_total"].configure(text_color="red")

            # Guardar en estructura para historial
            nuevo_registro = {
                "hora": datetime.now().strftime('%H:%M'),
                "mat": self.var_mat.get(),
                "total": f"{t_total:.1f}",
                "estado": estado_msg
            }
            self.historial_calculos.append(nuevo_registro)

            self.dibujar_esquema_dinamico(A, B, S)

        except ValueError:
            self.lbl_status.configure(text="⚠️ Error: Revise que todos los campos sean numéricos", text_color="orange")
        except Exception as e:
            self.lbl_status.configure(text=f"⚠️ Error: {str(e)}", text_color="red")

    def capturar(self, app):
        try:
            x = app.winfo_rootx()
            y = app.winfo_rooty()
            w = x + app.winfo_width()
            h = y + app.winfo_height()
            imagen = ImageGrab.grab(bbox=(x, y, w, h))
            output = io.BytesIO()
            imagen.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            self.lbl_status.configure(text="Screenshot copiado al portapapeles", text_color="blue")
        except:
            pass

        # Agrega esto dentro de tu clase EngineeringApp



if __name__ == "__main__":
    app = EngineeringApp()
    app.mainloop()