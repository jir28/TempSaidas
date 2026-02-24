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
        self.geometry("1000x750")  # Un poco más alto para que quepa el dibujo
        self.minsize(950, 700)

        # --- VARIABLES DE ESTADO ---
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

        # Triggers para actualizar dibujo al cambiar combos
        self.var_mat.trace_add("write", self.actualizar_dibujo_evento)
        self.var_dispo.trace_add("write", self.actualizar_dibujo_evento)
        self.var_blindado.trace_add("write", self.actualizar_dibujo_evento)

        # --- LAYOUT PRINCIPAL ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. HEADER
        self.header_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))

        self.lbl_logo = ctk.CTkLabel(self.header_frame, text="Temperatura | WEG",
                                     font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_logo.pack(side="left", padx=(0, 30))

        self.btn_calc = ctk.CTkButton(self.header_frame, text="Calculadora", width=120, height=35,
                                      font=("Arial", 13, "bold"), command=self.mostrar_calculadora)
        self.btn_calc.pack(side="left", padx=5)

        self.btn_hist = ctk.CTkButton(self.header_frame, text="Historial", width=120, height=35,
                                      font=("Arial", 13, "bold"), fg_color="transparent", border_width=0,
                                      text_color=("gray10", "#DCE4EE"), command=self.mostrar_historial)
        self.btn_hist.pack(side="left", padx=5)

        # 2. CONTENIDO
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # --- VISTAS ---
        self.frame_calc_view = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_hist_view = None

        self.construir_interfaz_calculadora()
        self.mostrar_calculadora()

    def construir_interfaz_calculadora(self):
        # Grid: Col 0 (Inputs + Dibujo Dinámico), Col 1 (Resultados + Imagen Estática)
        self.frame_calc_view.grid_columnconfigure(0, weight=1)
        self.frame_calc_view.grid_columnconfigure(1, weight=1)
        self.frame_calc_view.grid_rowconfigure(0, weight=1)

        # === SECCIÓN IZQUIERDA ===
        self.frame_inputs = ctk.CTkFrame(self.frame_calc_view)
        self.frame_inputs.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        self.frame_inputs.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self.frame_inputs, text="PARÁMETROS DE ENTRADA", font=("Arial", 14, "bold")).grid(row=0, column=0,
                                                                                                       columnspan=2,
                                                                                                       pady=(10, 5))

        # Inputs (A, B, S, L...)
        # Nota: Pasamos 'bind_keys=True' para que al escribir se actualice el dibujo
        self.crear_subgrupo(self.frame_inputs, "Geometría", 1,
                            [("A (mm)", "A"), ("B (mm)", "B"), ("S (mm)", "S"), ("L (mm)", "L")], bind_keys=True)
        self.crear_subgrupo(self.frame_inputs, "Datos Eléctricos y Térmicos", 5,
                            [("Sección Trans. (mm²)", "ST"), ("Densidad (A/mm²)", "J"), ("Temp. Amb. (°C)", "TA"),
                             ("Temp. Oleo (°C)", "TO")])

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
        frame_chk.grid(row=10, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        ctk.CTkCheckBox(frame_chk, text="Cable Transposto (CTC)", variable=self.var_transposto).pack(side="left",
                                                                                                     padx=10)
        ctk.CTkCheckBox(frame_chk, text="Blindado", variable=self.var_blindado,
                        command=self.actualizar_imagen_check).pack(side="left", padx=10)
        self.chk_divb = ctk.CTkCheckBox(frame_chk, text="Dividir B/2", variable=self.var_divb,
                                        command=self.actualizar_imagen_check)

        # --- AQUÍ ESTÁ LA MEJORA: DIBUJO DINÁMICO ---
        # Lo colocamos en la Fila 11 (antes del botón)
        self.frame_preview = ctk.CTkFrame(self.frame_inputs, fg_color="#F0F0F0", corner_radius=6)
        self.frame_preview.grid(row=11, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        ctk.CTkLabel(self.frame_preview, text="Vista Previa (Sección Transversal)", font=("Arial", 10, "bold"),
                     text_color="gray").pack(pady=(5, 0))

        self.canvas_dibujo = ctk.CTkCanvas(self.frame_preview, width=280, height=140, bg="#F0F0F0",
                                           highlightthickness=0)
        self.canvas_dibujo.pack(pady=5)

        # Botón Calcular (Fila 12)
        self.btn_run = ctk.CTkButton(self.frame_inputs, text="CALCULAR TEMPERATURA", height=45,
                                     font=("Arial", 15, "bold"), fg_color="#0066CC", hover_color="#0055AA",
                                     command=self.calcular)
        self.btn_run.grid(row=12, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 20))

        # === SECCIÓN DERECHA ===
        self.frame_results = ctk.CTkFrame(self.frame_calc_view, fg_color="white")
        self.frame_results.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.frame_results.grid_columnconfigure(0, weight=1)

        # Imagen Estática (Referencia)
        self.img_container = ctk.CTkLabel(self.frame_results, text="[ Imagen Referencia ]",
                                          fg_color="#EBEBEB", height=200, corner_radius=6)
        self.img_container.pack(fill="x", padx=10, pady=10)
        self.cargar_imagenes()

        # Resultados
        ctk.CTkLabel(self.frame_results, text="Resultados del Análisis", font=("Arial", 16, "bold"),
                     text_color="black").pack(pady=(5, 5))
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

    # --- LÓGICA DE DIBUJO DINÁMICO ---
    def actualizar_dibujo_evento(self, *args):
        self.dibujar_dinamico()

    def dibujar_dinamico(self, event=None):
        c = self.canvas_dibujo
        c.delete("all")

        try:
            # Obtener valores (si están vacíos o error, salimos silenciosamente)
            txt_a = self.inputs["A"].get().replace(',', '.')
            txt_b = self.inputs["B"].get().replace(',', '.')
            txt_s = self.inputs["S"].get().replace(',', '.')

            if not txt_a or not txt_b: return  # No dibujar si falta A o B

            A_val = float(txt_a)
            B_val = float(txt_b)
            S_val = float(txt_s) if txt_s else 0.0

            # Lógica de Rotación Visual
            is_vertical = self.var_dispo.get() == "Vertical"

            # Si es vertical, visualmente intercambiamos ancho y alto en el canvas
            # (Aunque A sigue siendo la dimensión "A" física)
            draw_w = B_val if is_vertical else A_val
            draw_h = A_val if is_vertical else B_val

            # Escala para ajustar al canvas (280x140)
            canvas_w = 280
            canvas_h = 140
            padding = 20

            max_dim_w = draw_w + (2 * S_val)
            max_dim_h = draw_h + (2 * S_val)

            # Evitar división por cero
            if max_dim_w == 0: max_dim_w = 1
            if max_dim_h == 0: max_dim_h = 1

            scale_w = (canvas_w - padding * 2) / max_dim_w
            scale_h = (canvas_h - padding * 2) / max_dim_h
            scale = min(scale_w, scale_h)  # Usar la escala más restrictiva para mantener proporción

            # Dimensiones en pixeles
            rect_w = draw_w * scale
            rect_h = draw_h * scale
            iso_px = S_val * scale

            # Centro del canvas
            cx = canvas_w / 2
            cy = canvas_h / 2

            # Coordenadas Rectángulo
            x1 = cx - (rect_w / 2)
            y1 = cy - (rect_h / 2)
            x2 = cx + (rect_w / 2)
            y2 = cy + (rect_h / 2)

            # Dibujar Aislamiento (S) - Rectángulo externo punteado
            c.create_rectangle(x1 - iso_px, y1 - iso_px, x2 + iso_px, y2 + iso_px,
                               outline="#888", dash=(3, 2), width=1)

            # Dibujar Conductor (Relleno)
            color_mat = "#B87333" if self.var_mat.get() == "Cobre" else "#A9A9A9"
            c.create_rectangle(x1, y1, x2, y2, fill=color_mat, outline="black", width=2)

            # Etiquetas (Texto)
            # Mostramos qué dimensión es cual. Si rotamos, las etiquetas deben seguir la lógica.
            label_bottom = f"B={B_val}" if is_vertical else f"A={A_val}"
            label_side = f"A={A_val}" if is_vertical else f"B={B_val}"

            c.create_text(cx, y2 + iso_px + 8, text=label_bottom, font=("Arial", 9), fill="#444")
            c.create_text(x2 + iso_px + 5, cy, text=label_side, anchor="w", font=("Arial", 9), fill="#444")

            # Indicador de Orientación
            orient_text = "⬆ Vertical" if is_vertical else "➡ Horizontal"
            c.create_text(10, 10, text=orient_text, anchor="nw", font=("Arial", 8, "bold"), fill="blue")

        except ValueError:
            pass  # Ignorar errores mientras escribe

    # --- HELPERS UI ---
    def crear_subgrupo(self, parent, titulo, start_row, campos, bind_keys=False):
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

            # BINDING PARA DIBUJO EN TIEMPO REAL
            if bind_keys and key in ["A", "B", "S"]:
                entry.bind("<KeyRelease>", self.dibujar_dinamico)

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

    # --- NAVEGACIÓN ---
    def mostrar_calculadora(self):
        if self.frame_hist_view is not None: self.frame_hist_view.pack_forget()
        self.btn_calc.configure(fg_color=["#3B8ED0", "#1F6AA5"], text_color=("white", "white"))
        self.btn_hist.configure(fg_color="transparent", text_color=("gray10", "gray80"))
        self.frame_calc_view.pack(fill="both", expand=True)

    def mostrar_historial(self):
        self.frame_calc_view.pack_forget()
        self.btn_calc.configure(fg_color="transparent", text_color=("gray10", "gray80"))
        self.btn_hist.configure(fg_color=["#3B8ED0", "#1F6AA5"], text_color=("white", "white"))

        if self.frame_hist_view is not None: self.frame_hist_view.destroy()
        self.frame_hist_view = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_hist_view.pack(fill="both", expand=True)
        # (Aquí iría el código del historial, igual que en la v3...)
        # Para ahorrar espacio en la respuesta asumo que copias el bloque del historial de la v3,
        # pero si lo necesitas completo avísame.
        self.construir_historial_interno()  # Helper simple para llenar

    def construir_historial_interno(self):
        # ... Copia exacta de tu lógica de historial ...
        pass  # Rellena con el código de la v3

    # --- LÓGICA DE NEGOCIO ---
    def cargar_imagenes(self):
        try:
            if os.path.exists("SemBlindagem.JPG"):
                self.img_sem = ctk.CTkImage(Image.open("SemBlindagem.JPG"), size=(300, 180))
                self.img_container.configure(image=self.img_sem, text="")
            if os.path.exists("ComBlindagem.JPG"):
                self.img_com = ctk.CTkImage(Image.open("ComBlindagem.JPG"), size=(300, 180))
            if os.path.exists("cotaB.png"):
                self.img_b = ctk.CTkImage(Image.open("cotaB.png"), size=(300, 180))
        except:
            pass

    def actualizar_imagen_check(self, *args):
        self.dibujar_dinamico()  # Actualizar también el canvas
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
        # ... (Lógica de cálculo exacta a la v3) ...
        # Solo asegúrate de copiar el método calcular() completo de la versión anterior
        # No cambia nada en la matemática
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
                self.lbl_status.configure(text=f"APROBADO (Máx {temp_max}°C)", text_color="green")
                self.result_labels["res_total"].configure(text_color="green")
            else:
                estado_msg = "PELIGRO"
                self.lbl_status.configure(text=f" PELIGRO - SUPERA LÍMITE ({temp_max}°C)", text_color="red")
                self.result_labels["res_total"].configure(text_color="red")

            nuevo_registro = {
                "hora": datetime.now().strftime('%H:%M'),
                "mat": self.var_mat.get(),
                "total": f"{t_total:.1f}",
                "estado": estado_msg
            }
            self.historial_calculos.append(nuevo_registro)
        except ValueError:
            pass
        except Exception:
            pass

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
            self.lbl_status.configure(text="Screenshot copiado", text_color="blue")
        except:
            pass


if __name__ == "__main__":
    app = EngineeringApp()
    app.mainloop()