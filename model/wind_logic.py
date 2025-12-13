import numpy as np

class WindASCE705:
    """
    Lógica de cálculo ASCE 7-05 (MWFRS) actualizada.
    Soporta:
    - Reportes detallados paso a paso.
    - Dirección Longitudinal y Transversal.
    - Cargas en Techo.
    """
    def __init__(self):
        self.results = {}

    def calculate(self, data):
        try:
            # 1. Inputs (Métrico -> Imperial)
            V_kmh = float(data['V'])
            exposure = data['exposure']
            I = float(data['I'])
            h_m = float(data['h'])
            L_m = float(data['L'])
            B_m = float(data['B'])
            theta = float(data.get('theta', 0.0))
            trib_width_m = float(data['trib_width'])
            enclosure = data.get('enclosure', 'Cerrado')

            # Conversiones
            FT_PER_M = 3.28084
            MPH_PER_KMH = 0.621371
            KG_M2_PER_PSF = 4.88243
            
            V_mph = V_kmh * MPH_PER_KMH
            h_ft = h_m * FT_PER_M
            
            # Coeficientes Sitio
            coeffs = {'B': (7.0, 1200.0), 'C': (9.5, 900.0), 'D': (11.5, 700.0)}
            alpha, zg = coeffs[exposure]
            
            # Kz Calculation
            Kz = 2.01 * ((max(h_ft, 15.0) / zg) ** (2.0 / alpha))
            
            # Velocity Pressure (qz) in PSF
            # Eq 6-15: 0.00256 * Kz * Kzt * Kd * V^2 * I
            # Kzt=1.0 (Flat), Kd=0.85 (Building), G=0.85 (Rigid)
            Kzt = 1.0
            Kd = 0.85
            G = 0.85
            qz_psf = 0.00256 * Kz * Kzt * Kd * (V_mph**2) * I
            
            # GCpi Determination
            if enclosure == 'Parcialmente Cerrado': gcpi = 0.55
            elif enclosure == 'Abierto': gcpi = 0.00
            else: gcpi = 0.18

            # --- FUNCION INTERNA PARA CALCULAR UNA DIRECCION ---
            def calc_direction(len_wind, width_cross):
                # Paredes
                cp_wall_ww = 0.8
                ratio = len_wind / width_cross
                if ratio <= 1: cp_wall_lw = -0.5
                elif ratio <= 2: cp_wall_lw = -0.3
                elif ratio >= 4: cp_wall_lw = -0.2
                else: cp_wall_lw = 0.05 * ratio - 0.4
                
                # Techo
                cp_roof_lw = -0.7
                if theta < 10: cp_roof_ww = -0.9
                elif theta < 20: cp_roof_ww = -0.7
                elif theta < 45: cp_roof_ww = 0.3
                else: cp_roof_ww = 0.8
                
                # Cargas Externas (q * G * Cp) en PSF
                # Nota: Calculamos la componente externa principal para el diagrama
                p_ww_psf = qz_psf * G * cp_wall_ww
                p_lw_psf = qz_psf * G * cp_wall_lw
                p_roof_ww_psf = qz_psf * G * cp_roof_ww
                p_roof_lw_psf = qz_psf * G * cp_roof_lw
                
                return {
                    'p_ww': p_ww_psf * KG_M2_PER_PSF,
                    'p_lw': p_lw_psf * KG_M2_PER_PSF,
                    'p_roof_ww': p_roof_ww_psf * KG_M2_PER_PSF,
                    'p_roof_lw': p_roof_lw_psf * KG_M2_PER_PSF,
                    # Guardamos coeficientes para el reporte
                    'cp_wall_ww': cp_wall_ww,
                    'cp_wall_lw': cp_wall_lw,
                    'cp_roof_ww': cp_roof_ww,
                    'cp_roof_lw': cp_roof_lw
                }

            res_long = calc_direction(L_m * FT_PER_M, B_m * FT_PER_M)
            res_trans = calc_direction(B_m * FT_PER_M, L_m * FT_PER_M)

            self.results = {
                'V_kmh': V_kmh, 'V_mph': V_mph,
                'h': h_m, 'L': L_m, 'B': B_m, 'theta': theta,
                'exposure': exposure, 'I': I, 'enclosure': enclosure,
                'Kz': Kz, 'Kzt': Kzt, 'Kd': Kd, 'G': G,
                'qz_psf': qz_psf, 'qz_metric': qz_psf * KG_M2_PER_PSF,
                'gcpi': gcpi,
                'long': res_long,
                'trans': res_trans
            }
            return self.results

        except Exception as e:
            raise ValueError(f"Error cálculo: {str(e)}")

    def generate_report(self):
        r = self.results
        if not r: return "Sin resultados."
        
        # --- BLOQUE 1: DATOS Y FORMULAS DE VELOCIDAD ---
        # Se eliminaron los delimitadores LaTeX ($$) para compatibilidad con QTextEdit
        report = f"""
# Memoria de Cálculo Detallada (ASCE 7-05)

## 1. Parámetros de Diseño
* **Velocidad Básica (V):** {r['V_kmh']:.1f} km/h ({r['V_mph']:.1f} mph)
* **Categoría de Exposición:** {r['exposure']}
* **Factor de Importancia (I):** {r['I']}
* **Dimensiones:** L={r['L']} m, B={r['B']} m, h={r['h']} m
* **Ángulo de Techo (Theta):** {r['theta']}°
* **Clasificación de Cerramiento:** {r['enclosure']}

## 2. Cálculo de Presión de Velocidad (qz)
La presión se calcula según la Ecuación 6-15:
`qz = 0.00256 * Kz * Kzt * Kd * V^2 * I`

### Variables:
* **Kz (Coef. Exposición):** {r['Kz']:.3f} (Calculado para altura h)
* **Kzt (Factor Topográfico):** {r['Kzt']} (Terreno plano asumido)
* **Kd (Factor Direccionalidad):** {r['Kd']} (Edificios)
* **V:** {r['V_mph']:.1f} mph

### Sustitución:
`qz = 0.00256 * ({r['Kz']:.3f}) * ({r['Kzt']}) * ({r['Kd']}) * ({r['V_mph']:.1f})^2 * ({r['I']})`

### Resultado:
`qz = {r['qz_psf']:.2f} psf`
**qz = {r['qz_metric']:.2f} kg/m²**

---

## 3. Presiones de Diseño (p)
Ecuación 6-17 (Sistema MWFRS Edificios Rígidos):
`p = q * G * Cp - qi * (GCpi)`

### Parámetros Comunes:
* **Factor de Ráfaga (G):** {r['G']}
* **Coef. Presión Interna (GCpi):** +/- {r['gcpi']}
  *(Nota: Para el diseño del marco principal resistente a momento, las presiones internas actuando en paredes opuestas se cancelan vectorialmente. A continuación se presentan las Presiones Externas p_ext = q * G * Cp.)*

"""
        # --- BLOQUE 2: ANALISIS POR DIRECCION ---
        def add_direction_block(title, data):
            # Helper para formatear una línea de cálculo en texto plano
            def calc_line(elem, cp, res):
                return f"  - **{elem}:** Cp={cp:.2f} -> p = {r['qz_metric']:.1f} * {r['G']} * ({cp:.2f}) = **{res:.2f} kg/m²**\n"

            block = f"### {title}\n"
            block += calc_line("Pared Barlovento", data['cp_wall_ww'], data['p_ww'])
            block += calc_line("Pared Sotavento", data['cp_wall_lw'], data['p_lw'])
            block += calc_line("Techo Barlovento", data['cp_roof_ww'], data['p_roof_ww'])
            block += calc_line("Techo Sotavento", data['cp_roof_lw'], data['p_roof_lw'])
            return block

        report += add_direction_block("Dirección Longitudinal (Viento // L)", r['long'])
        report += "\n"
        report += add_direction_block("Dirección Transversal (Viento // B)", r['trans'])
        
        return report