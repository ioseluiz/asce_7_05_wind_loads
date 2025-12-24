import numpy as np

class WindASCE705:
    """
    Lógica de cálculo ASCE 7-05 (MWFRS).
    - Coeficientes Kz según Tabla 6-3 (Formula analítica).
    - Interpolación Bilineal para Cp (Fig 6-6).
    - Soporte para alturas h > 4.6m con pasos detallados.
    """
    def __init__(self):
        self.results = {}

    def calculate(self, data):
        try:
            # --- 1. Inputs ---
            V_kmh = float(data['V'])
            V_ms = V_kmh / 3.6
            exposure = data['exposure']
            I = float(data['I'])
            h = float(data['h'])
            L_geom = float(data['L']) 
            B_geom = float(data['B']) 
            theta = float(data.get('theta', 0.0))
            enclosure = data.get('enclosure', 'Cerrado')

            # Constantes ASCE 7-05
            Kd = 0.85  # Table 6-4 (Edificios)
            Kzt = 1.0  # Sec. 6.5.7.2 (Terreno Plano)
            G = 0.85   # Sec. 6.5.8.1 (Estructura Rígida)
            
            # GCpi (Figure 6-5)
            if enclosure == 'Parcialmente Cerrado': gcpi = 0.55
            elif enclosure == 'Abierto': gcpi = 0.00
            else: gcpi = 0.18

            # --- 2. Coeficientes de Terreno (Tabla 6-2) ---
            # alpha y zg para usar en la fórmula de Kz
            coeffs = {
                'B': (7.0, 365.76),  # zg = 1200 ft
                'C': (9.5, 274.32),  # zg = 900 ft
                'D': (11.5, 213.36)  # zg = 700 ft
            }
            alpha, zg = coeffs[exposure]

            def get_Kz(z_cal):
                """
                Calcula Kz según la Nota 1 y 2 de la Tabla 6-3.
                Formula: Kz = 2.01 * (z / zg)^(2/alpha)
                Restricción: Para z < 4.6m (15 ft), usar Kz calculado a 4.6m.
                """
                z_eff = max(z_cal, 4.6) 
                return 2.01 * ((z_eff / zg) ** (2.0 / alpha))

            # --- 3. Presión Velocidad (qz) ---
            const_metric = 0.613
            # [cite_start]Kh: Se calcula con Kz evaluado a la altura media del techo h [cite: 1]
            Kz_h = get_Kz(h)
            qh = const_metric * Kz_h * Kzt * Kd * (V_ms**2) * I

            calc_details = {
                'Kz_h': Kz_h,
                'formula_qz': f"0.613 * {Kz_h:.3f} (Kh) * {Kzt} * {Kd} * {V_ms:.2f}² * {I}",
                'qh': qh
            }

            # --- 4. Interpolación Fig 6-6 (Cp) ---
            def get_cp_bilinear(angle, h_L_ratio):
                if angle < 10: return 0.8, -0.9, -0.5 

                ww_data = {
                    10: {-1: -0.7, 0.25: -0.7, 0.5: -0.9, 1.0: -1.3},
                    15: {-1: -0.5, 0.25: -0.5, 0.5: -0.7, 1.0: -1.0},
                    20: {-1: -0.3, 0.25: -0.3, 0.5: -0.4, 1.0: -0.7},
                    25: {-1: -0.2, 0.25: -0.2, 0.5: -0.3, 1.0: -0.5},
                    30: {-1: -0.2, 0.25: -0.2, 0.5: -0.2, 1.0: -0.3},
                    35: {-1:  0.0, 0.25:  0.0, 0.5: -0.2, 1.0: -0.2},
                    45: {-1:  0.0, 0.25:  0.0, 0.5:  0.0, 1.0:  0.0},
                }
                lw_data = {
                    10: {-1: -0.3, 0.25: -0.3, 0.5: -0.5, 1.0: -0.7},
                    15: {-1: -0.5, 0.25: -0.5, 0.5: -0.5, 1.0: -0.6},
                    20: {-1: -0.6, 0.25: -0.6, 0.5: -0.6, 1.0: -0.6}
                }
                def interp_1d(val, x_list, y_list): return np.interp(val, x_list, y_list)

                angles_sorted = sorted(ww_data.keys())
                cp_ww, cp_lw = [], []
                for a in angles_sorted:
                    r_ww, r_lw = ww_data[a], lw_data.get(a, lw_data[20])
                    cp_ww.append(interp_1d(h_L_ratio, sorted(r_ww.keys()), [r_ww[k] for k in sorted(r_ww.keys())]))
                    cp_lw.append(interp_1d(h_L_ratio, sorted(r_lw.keys()), [r_lw[k] for k in sorted(r_lw.keys())]))

                return 0.8, interp_1d(angle, angles_sorted, cp_ww), interp_1d(angle, angles_sorted, cp_lw)

            # --- 5. Análisis ---
            def analyze_case(L_bldg, B_bldg, is_transverse):
                rows = []
                L_wind = B_bldg if is_transverse else L_bldg 
                B_wind = L_bldg if is_transverse else B_bldg
                h_L = h / L_wind
                
                if is_transverse:
                    cp_w, cp_r_ww, cp_r_lw = get_cp_bilinear(theta, h_L)
                    tag = f"Perp. Caballete (h/L={h_L:.3f})"
                else:
                    cp_w, cp_r_ww, cp_r_lw = get_cp_bilinear(0, h_L)
                    tag = f"Paral. Caballete (Simulado <10°)"

                # --- GENERACIÓN DE ALTURAS Z PARA PARED BARLOVENTO ---
                # Pasos estándar de Tabla 6-3 en metros:
                # 15'->4.6m, 20'->6.1m, 25'->7.6m, 30'->9.1m, 40'->12.2m, 
                # 50'->15.2m, 60'->18.3m, 70'->21.3m, 80'->24.4m, 90'->27.4m, 100'->30.5m
                steps_table = [4.6, 6.1, 7.6, 9.1, 12.2, 15.2, 18.3, 21.3, 24.4, 27.4, 30.5]
                
                # Filtramos las alturas menores a h y agregamos h al final
                z_list = [z for z in steps_table if z < h] + [h]
                
                # Pared Barlovento (Variable con z)
                for z in z_list:
                    kz = get_Kz(z)
                    qz = const_metric * kz * Kzt * Kd * (V_ms**2) * I
                    
                    rows.append({
                        'elem': f'Pared Barlovento (z={z:.1f})', 
                        'z': f"{z:.1f}", 
                        'q': qz, 
                        'G': G, 
                        'Cp': cp_w, 
                        'p_pos': qz*G*cp_w - qh*gcpi, 
                        'p_neg': qz*G*cp_w - qh*(-gcpi)
                    })

                # [cite_start]Pared Sotavento (Constante a altura media h) [cite: 1]
                ratio_LB = L_wind / B_wind
                cp_lw_wall = -0.5 if ratio_LB <= 1 else (-0.2 if ratio_LB >= 4 else np.interp(ratio_LB, [1, 2, 4], [-0.5, -0.3, -0.2]))
                
                rows.append({'elem': 'Pared Sotavento', 'z': 'All (h)', 'q': qh, 'G': G, 'Cp': cp_lw_wall, 'p_pos': qh*G*cp_lw_wall - qh*gcpi, 'p_neg': qh*G*cp_lw_wall - qh*(-gcpi)})
                
                # [cite_start]Techos (Evaluados a qh) [cite: 1]
                rows.append({'elem': 'Techo Barlovento', 'z': 'h', 'q': qh, 'G': G, 'Cp': cp_r_ww, 'p_pos': qh*G*cp_r_ww - qh*gcpi, 'p_neg': qh*G*cp_r_ww - qh*(-gcpi)})
                rows.append({'elem': 'Techo Sotavento', 'z': 'h', 'q': qh, 'G': G, 'Cp': cp_r_lw, 'p_pos': qh*G*cp_r_lw - qh*gcpi, 'p_neg': qh*G*cp_r_lw - qh*(-gcpi)})
                
                return rows, tag

            res_t, tag_t = analyze_case(L_geom, B_geom, True)
            res_l, tag_l = analyze_case(L_geom, B_geom, False)

            self.results = {
                'meta': {'V': V_kmh, 'exposure': exposure, 'I': I, 'h': h, 'theta': theta, 'qh': qh, 'Kd': Kd, 'G': G, 'gcpi': gcpi},
                'details': calc_details,
                'trans': res_t, 'tag_trans': tag_t, 'long': res_l, 'tag_long': tag_l
            }
            return self.results

        except Exception as e: raise ValueError(f"Error cálculo: {str(e)}")

    def generate_report(self):
        if not self.results: return "<h3>Sin resultados.</h3>"
        m = self.results['meta']
        d = self.results['details']
        
        # --- ESTILOS ---
        STYLE_TD = 'border: 1px solid #bdc3c7; padding: 5px; text-align: center; font-family: Arial, sans-serif; font-size: 10pt; color: #333;'
        STYLE_TH = 'border: 1px solid #bdc3c7; padding: 5px; text-align: center; font-family: Arial, sans-serif; font-size: 10pt; background-color: #ecf0f1; font-weight: bold; color: #2c3e50;'
        STYLE_TD_LEFT = STYLE_TD + ' text-align: left;'
        STYLE_TD_BOLD = STYLE_TD + ' font-weight: bold;'

        html = f"""
        <html>
        <head>
            <style>
                h1 {{ color: #2c3e50; font-family: Arial, sans-serif; font-size: 18pt; margin-bottom: 5px; }}
                h2 {{ color: #2980b9; margin-top: 25px; border-bottom: 2px solid #2980b9; padding-bottom: 3px; font-size: 14pt; font-family: Arial, sans-serif; }}
                p, li {{ font-family: Arial, sans-serif; font-size: 10pt; line-height: 1.4; }}
                .box {{ background-color: #f9f9f9; border-left: 5px solid #2980b9; padding: 10px; margin: 10px 0; font-family: Consolas, monospace; font-size: 10pt; }}
            </style>
        </head>
        <body>
            <h1>Memoria de Cálculo ASCE 7-05</h1>
            <p style="color: #7f8c8d; font-size: 9pt;">Método Analítico (MWFRS) - Capítulo 6</p>
            
            <h2>1. Parámetros de Diseño</h2>
            <table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse; width:100%; border:1px solid #bdc3c7;">
                <thead>
                    <tr>
                        <th style="{STYLE_TH}">V (km/h)</th>
                        <th style="{STYLE_TH}">Exp / I</th>
                        <th style="{STYLE_TH}">h (m)</th>
                        <th style="{STYLE_TH}">Theta (°)</th>
                        <th style="{STYLE_TH}">Kd / G</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="{STYLE_TD}">{m['V']:.1f}</td>
                        <td style="{STYLE_TD}">{m['exposure']} / {m['I']}</td>
                        <td style="{STYLE_TD}">{m['h']}</td>
                        <td style="{STYLE_TD}">{m['theta']}</td>
                        <td style="{STYLE_TD}">{m['Kd']} / {m['G']}</td>
                    </tr>
                </tbody>
            </table>

            <h2>2. Detalle de Cálculos</h2>
            
            <p><strong>A. Coeficientes de Presión de Velocidad (Kz y Kh)</strong><br>
            Se calculan según la Tabla 6-3. Para alturas z &lt; 4.6m, se usa Kz a 4.6m (Nota 2).</p>
            
            <p><strong>B. Presión de Velocidad (qz)</strong><br>
            Ecuación 6-15 (Sistema Métrico):</p>
            <div class="box">qz = 0.613 * Kz * Kzt * Kd * V² * I</div>
            
            <p>Sustitución para altura media h = {m['h']}m (Kh):</p>
            <ul>
                <li><strong>Kz(h):</strong> {d['Kz_h']:.3f}</li>
                <li><strong>V:</strong> {(m['V']/3.6):.2f} m/s</li>
            </ul>
            <div class="box">
                qh = {d['formula_qz']}<br>
                <strong>qh = {d['qh']:.2f} N/m²</strong>
            </div>

            <p><strong>C. Presiones de Diseño (p)</strong><br>
            Ecuación 6-17: <code>p = q * G * Cp - qi * (GCpi)</code></p>

            <h2>3. Resultados: Dirección Transversal</h2>
            <p>Viento perpendicular al caballete. Comportamiento según ángulo real del techo.</p>
            <p style="font-size:9pt; color:#555;"><em>Caso: {self.results['tag_trans']}</em></p>
            {self._make_html_table(self.results['trans'], STYLE_TH, STYLE_TD, STYLE_TD_LEFT, STYLE_TD_BOLD)}
            
            <h2>4. Resultados: Dirección Longitudinal</h2>
            <p>Viento paralelo al caballete. Se asume flujo paralelo (Theta < 10°).</p>
            <p style="font-size:9pt; color:#555;"><em>Caso: {self.results['tag_long']}</em></p>
            {self._make_html_table(self.results['long'], STYLE_TH, STYLE_TD, STYLE_TD_LEFT, STYLE_TD_BOLD)}
            
            <br>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p style="text-align: center; color: #bdc3c7; font-size: 8pt;">Generado por Software ASCE 7-05</p>
        </body>
        </html>
        """
        return html

    def _make_html_table(self, rows, style_th, style_td, style_left, style_bold):
        tbl = '<table border="1" cellspacing="0" cellpadding="0" style="border-collapse: collapse; width: 100%; border: 1px solid #bdc3c7; margin-bottom: 20px;">'
        tbl += '<thead><tr>'
        for h in ["Elemento", "z (m)", "q (N/m²)", "Cp", "P(+GCpi)", "P(-GCpi)"]:
            tbl += f'<th style="{style_th}">{h}</th>'
        tbl += '</tr></thead><tbody>'
        for r in rows:
            tbl += '<tr>'
            tbl += f'<td style="{style_left}">{r["elem"]}</td>'
            tbl += f'<td style="{style_td}">{r["z"]}</td>'
            tbl += f'<td style="{style_td}">{r["q"]:.1f}</td>'
            tbl += f'<td style="{style_td}">{r["Cp"]:.2f}</td>'
            tbl += f'<td style="{style_bold}">{r["p_pos"]:.1f}</td>'
            tbl += f'<td style="{style_bold}">{r["p_neg"]:.1f}</td>'
            tbl += '</tr>'
        tbl += '</tbody></table>'
        return tbl