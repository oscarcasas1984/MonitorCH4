# -*- coding: utf-8 -*-
"""
Comparador de Modelos SNC (VPN/BPN + Carbono) — MVP05 en Streamlit
------------------------------------------------------------------
Roles: SNC + Finanzas + Diseño Web (UI ejecutiva)

Cambios radicales (MVP05):
- Entrada única: una sola hoja Excel tipo MATRIZ por proyecto.
- Cada proyecto tiene dos filas obligatorias: CASHFLOW (USD) y CO2 (tCO2e).
- CO2 es obligatorio y va como fila (no como columna). Lo pintamos y validamos.
- Tabs automáticas por proyecto (sin selectores). Cada tab trae sus propios sliders:
  tasa de descuento y factor de precio del carbono.
- Tasa de descuento por proyecto desde columna `tasa` (por fila); el slider de cada tab se inicializa con ese valor.
- Eliminada la convención de mitad de año (α=0.5). Solo VPN clásico (fin de año).
- Validaciones al final: continuidad/NaN/huecos.
- Soporta p0..p30 (o más).

Formato esperado (una sola hoja):
- Columnas: project_id, project_title, row_label, unit, notes, p0, p1, p2, ... , pN
- Filas por proyecto (mínimo):
  - row_label = CASHFLOW  (unit: USD o MUSD)
  - row_label = CO2       (unit: tCO2e o MtCO2e)
Ejemplo:
project_id,project_title,row_label,unit,notes,p0,p1,p2,p3
A,Sumideros 2021,CASHFLOW,USD,capex inicial,-2000000,-545540,653058,1306171
A,Sumideros 2021,CO2,tCO2e,,0,109100,208650,398200
B,OMC 2024,CASHFLOW,MUSD,,-300,-264,-225,-184
B,OMC 2024,CO2,MtCO2e,,0,4.0,4.8,5.3

Cómo ejecutar:
1) pip install streamlit pandas plotly
2) streamlit run MISNC_MVP03.py
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import unicodedata
import plotly.graph_objects as go
import streamlit.components.v1 as components

# -----------------------------
# Utilidades
# -----------------------------

def npv(rate: float, cashflows: List[float]) -> float:
    """VPN clásico (fin de año). cashflows[0] = año 0."""
    total = 0.0
    for t, cf in enumerate(cashflows):
        total += cf / ((1.0 + rate) ** t)
    return total

def normalize_currency(value: float, unit: str) -> float:
    """USD por defecto; MUSD → USD."""
    if isinstance(unit, str) and unit.strip().upper().startswith("M"):
        return float(value) * 1_000_000.0
    return float(value)

def normalize_carbon(value: float, unit: str) -> float:
    """tCO2e por defecto; MtCO2e → tCO2e."""
    if not isinstance(unit, str):
        return float(value)
    u = unit.strip().lower().replace(" ", "")
    if u in ("mtco2e", "mtco₂e"):
        return float(value) * 1_000_000.0
    return float(value)

def _is_period_col(col: str) -> bool:
    # Detecta columnas p0..pN (soporta p0..p30 o más sin cambios)
    col = str(col).strip().lower()
    return col.startswith("p") and col[1:].isdigit()

def apply_price_factor(cash: List[float], factor: float) -> List[float]:
    """Escala solo flujos positivos (simulación de precio del carbono en capa presentación)."""
    return [(cf * factor if cf > 0 else cf) for cf in cash]

def effective_horizon_years(cash: List[float], carb: List[float], eps: float = 1e-9) -> int:
    """Devuelve el horizonte en años contando realmente los periodos con datos.
    Se considera que hay "dato" si en el periodo existe flujo de caja distinto de ~0 o CO2 distinto de ~0.
    Regla: si el último periodo con datos es pK, el horizonte es K (p0→0 años, p1→1 año, ...).
    """
    if not cash and not carb:
        return 0
    n = max(len(cash), len(carb))
    # pad a la misma longitud
    cash2 = (cash or []) + [0.0] * (n - len(cash or []))
    carb2 = (carb or []) + [0.0] * (n - len(carb or []))
    last_idx = 0
    for i in range(n):
        cf = cash2[i]
        co2 = carb2[i]
        if (cf is not None and abs(cf) > eps) or (co2 is not None and abs(co2) > eps):
            last_idx = i
    return int(last_idx)

# -----------------------------
# Parser de MATRIZ única (Excel)
# -----------------------------

def parse_matrix(df_raw: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Convierte la hoja matriz en { project_id: {title, cashflow, carbon, units, notes, period_cols} }.
    """
    df = df_raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    required = {"project_id", "project_title", "row_label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {missing}")

    if "unit" not in df.columns:
        df["unit"] = ""
    if "notes" not in df.columns:
        df["notes"] = ""

    # tasa/rate por proyecto (opcional). Puede venir como 'tasa' ("10%" o 0.10) o 'rate'.
    rate_col = None
    for cand in ("tasa", "rate", "discount_rate", "drate"):
        if cand in df.columns:
            rate_col = cand
            break

    period_cols = [c for c in df.columns if _is_period_col(c)]
    if not period_cols:
        raise ValueError("No se encontraron columnas de periodo (p0, p1, ...)")
    period_cols = sorted(period_cols, key=lambda c: int(c[1:]))

    projects: Dict[str, Dict[str, Any]] = {}
    for pid, g in df.groupby("project_id"):
        title = str(g["project_title"].dropna().iloc[0]) if not g.empty else str(pid)
        # Inicializa series de expansión (se poblarán si existen filas *_EXP)
        cashflow_exp_series = None
        carbon_exp_series = None

        # -----------------------------
        # 1) Detectar componentes (si existen) y agrupar por component_id
        # -----------------------------
        components = []
        has_components = ("component_id" in g.columns) and ("component_title" in g.columns)
        if has_components and g["component_id"].notna().any():
            for cid, cg in g.groupby("component_id"):
                cname = str(cg["component_title"].dropna().iloc[0]) if not cg.empty else str(cid)

                cf_rows_c = cg[cg["row_label"].str.strip().str.upper().isin(["CASHFLOW", "CF"])]
                co2_rows_c = cg[cg["row_label"].str.strip().str.upper().isin(["CO2", "CARBON", "CARBONO"])]
                if cf_rows_c.empty or co2_rows_c.empty:
                    # si un componente no está completo, lo saltamos
                    continue

                cf_row_c  = cf_rows_c.iloc[0]
                co2_row_c = co2_rows_c.iloc[0]

                unit_cf_c  = str(cf_row_c.get("unit", "USD"))
                unit_co2_c = str(co2_row_c.get("unit", "tCO2e"))

                cf_series_c  = [normalize_currency(0.0 if pd.isna(cf_row_c[c])  else float(cf_row_c[c]),  unit_cf_c)  for c in period_cols]
                co2_series_c = [normalize_carbon (0.0 if pd.isna(co2_row_c[c]) else float(co2_row_c[c]), unit_co2_c) for c in period_cols]

                comp_rate = None
                if rate_col is not None and rate_col in cg.columns:
                    val = cg[rate_col].dropna()
                    if len(val) > 0:
                        raw = val.iloc[0]
                        try:
                            if isinstance(raw, (int, float)):
                                v = float(raw)
                            else:
                                v = float(str(raw).strip().replace('%',''))
                            comp_rate = v/100.0 if v > 1.0 else v
                        except Exception:
                            comp_rate = None

                components.append({
                    "component_id": str(cid),
                    "component_title": cname,
                    "cashflow": cf_series_c,
                    "carbon":   co2_series_c,
                    "units": {"cf": unit_cf_c, "co2": unit_co2_c},
                    "rate": comp_rate,
                })

        # -----------------------------
        # 2) Series agregadas a nivel proyecto para KPIs (si hay componentes)
        # -----------------------------
        def _sum_series(list_of_series: List[List[float]]) -> List[float]:
            if not list_of_series:
                return []
            L = max(len(s) for s in list_of_series)
            acc = [0.0]*L
            for s in list_of_series:
                s = s + [0.0]*(L - len(s))
                acc = [a+b for a,b in zip(acc,s)]
            return acc

        if components:
            agg_cf  = _sum_series([c["cashflow"] for c in components])
            agg_co2 = _sum_series([c["carbon"]   for c in components])
            # tasa de proyecto = primera tasa válida encontrada en componentes (si existe)
            proj_rate = next((c.get("rate") for c in components if c.get("rate") is not None), None)
            unit_cf = components[0]["units"]["cf"]
            unit_co2 = components[0]["units"]["co2"]
            cashflow_exp_series = None
            carbon_exp_series   = None
        else:
            # Sin componentes: comportamiento estándar (toma las filas CASHFLOW/CO2 del grupo)
            cf_rows = g[g["row_label"].str.strip().str.upper().isin(["CASHFLOW", "CF"])]
            co2_rows = g[g["row_label"].str.strip().str.upper().isin(["CO2", "CARBON", "CARBONO"])]
            if cf_rows.empty:
                raise ValueError(f"Proyecto {pid}: falta fila CASHFLOW")
            if co2_rows.empty:
                raise ValueError(f"Proyecto {pid}: falta fila CO2 (obligatoria)")
            cf_row = cf_rows.iloc[0]
            co2_row = co2_rows.iloc[0]
            unit_cf  = str(cf_row.get("unit", "USD"))
            unit_co2 = str(co2_row.get("unit", "tCO2e"))
            agg_cf  = [normalize_currency(0.0 if pd.isna(cf_row[c])  else float(cf_row[c]),  unit_cf)  for c in period_cols]
            agg_co2 = [normalize_carbon (0.0 if pd.isna(co2_row[c]) else float(co2_row[c]), unit_co2) for c in period_cols]
            proj_rate = None
            if rate_col is not None:
                val = g[rate_col].dropna()
                if len(val) > 0:
                    raw = val.iloc[0]
                    try:
                        if isinstance(raw, (int, float)):
                            v = float(raw)
                        else:
                            v = float(str(raw).strip().replace('%',''))
                        proj_rate = v/100.0 if v > 1.0 else v
                    except Exception:
                        proj_rate = None

            # --- Series opcionales de EXPANSIÓN (si existen en la hoja 'modelos') ---
            # Acepta alias comunes de etiquetas
            exp_cf_labels  = ["CASHFLOW_EXP", "CF_EXP", "CASHFLOW EXP", "CF EXP", "CASHFLOW_EXPANSION", "CF_EXPANSION"]
            exp_co2_labels = ["CO2_EXP", "CO₂_EXP", "CO2 EXP", "CO₂ EXP", "CARBON_EXP", "CARBONO_EXP", "CO2_EXPANSION"]

            exp_cf_rows  = g[g["row_label"].str.strip().str.upper().isin([s.upper() for s in exp_cf_labels])]
            exp_co2_rows = g[g["row_label"].str.strip().str.upper().isin([s.upper() for s in exp_co2_labels])]

            cashflow_exp_series = None
            carbon_exp_series   = None

            if not exp_cf_rows.empty:
                exp_cf_row = exp_cf_rows.iloc[0]
                unit_exp_cf = str(exp_cf_row.get("unit", unit_cf))
                cashflow_exp_series = [normalize_currency(0.0 if pd.isna(exp_cf_row[c]) else float(exp_cf_row[c]), unit_exp_cf) for c in period_cols]

            if not exp_co2_rows.empty:
                exp_co2_row = exp_co2_rows.iloc[0]
                unit_exp_co2 = str(exp_co2_row.get("unit", unit_co2))
                carbon_exp_series = [normalize_carbon(0.0 if pd.isna(exp_co2_row[c]) else float(exp_co2_row[c]), unit_exp_co2) for c in period_cols]

        # Notas del proyecto (primera no nula)
        notes_vals = g.get("notes")
        notes = "" if notes_vals is None else str(notes_vals.dropna().iloc[0])

        projects[str(pid)] = {
            "title": title,
            "cashflow": agg_cf,
            "carbon":   agg_co2,
            "cashflow_exp": cashflow_exp_series,
            "carbon_exp":   carbon_exp_series,
            "units": {"cf": unit_cf, "co2": unit_co2},
            "notes": notes,
            "period_cols": period_cols,
            "rate": proj_rate,
            "components": components,
        }

    return projects

# -----------------------------
# Render de tabs
# -----------------------------
def render_oportunidades_section(df_particiones: pd.DataFrame, use_expander: bool = True, key_prefix: str = ""):
    """
    Renderiza Sunburst, Barras apiladas (abs/%), y Mapa de casos (puntos) dentro de un expander.
    Espera un DataFrame con columnas al menos: ecosistema, nivel, area_ha.
    Opcionales: region, lat, lon, total_ha, pct (si no están, se calculan).
    Niveles esperados: 'Restricciones', 'Potencial no usado', 'Caso de estudio'.
    """
    # Validación mínima
    req = {"ecosistema", "nivel", "area_ha"}
    if not req.issubset(set(df_particiones.columns)):
        st.info("Faltan columnas para 'Análisis de Oportunidades' (se requieren: ecosistema, nivel, area_ha).")
        return

    df = df_particiones.copy()
    # Normalizaciones
    for c in ("ecosistema", "nivel"):
        df[c] = df[c].astype(str)
    df["area_ha"] = pd.to_numeric(df["area_ha"], errors="coerce").fillna(0.0)

    # total_ha y pct si no existen
    if "total_ha" not in df.columns:
        totales = df.groupby("ecosistema")["area_ha"].sum().rename("total_ha").reset_index()
        df = df.merge(totales, on="ecosistema", how="left")
    if "pct" not in df.columns:
        df["pct"] = df["area_ha"] / df["total_ha"] * 100.0

    # --- Alias y etiquetas canónicas para niveles (visualización) ---
    # Mapea textos de Excel a etiquetas mostradas en los gráficos.
    LEVEL_ALIAS = {
        # etiquetas históricas -> nuevas etiquetas
        "restricciones": "Potencial por evaluar + Restricciones",
        "potencial no usado": "Área potencial SNC",
        "caso de estudio": "Caso de estudio",
    }
    def _canon_label_level(s: str) -> str:
        s0 = str(s).strip().lower().replace("_", " ").replace("-", " ")
        s0 = unicodedata.normalize("NFD", s0).encode("ascii", "ignore").decode("utf-8")
        s0 = " ".join(s0.split())
        return LEVEL_ALIAS.get(s0, str(s))  # si ya viene con la etiqueta nueva u otra, se respeta

    # columna derivada solo para display
    df["nivel_disp"] = df["nivel"].apply(_canon_label_level)

    # Orden y colores fijos según nuevas etiquetas
    LEVEL_ORDER = [
        LEVEL_ALIAS["restricciones"],
        LEVEL_ALIAS["potencial no usado"],
        LEVEL_ALIAS["caso de estudio"],
    ]
    LEVEL_COLORS = {
        LEVEL_ALIAS["restricciones"]: "#9AA0A6",      # gris
        LEVEL_ALIAS["potencial no usado"]: "#6ECF68", # verde claro
        LEVEL_ALIAS["caso de estudio"]: "#1E8E3E",    # verde oscuro
    }
    def _render_body(df: pd.DataFrame):
        st.caption("Estudio de Portafolio por ecosistema: restricciones, zona natural por evaluar, casos de estudio y su proyección factible. Se priorizan 3 ecosistemas: Manglares, Bosques de Galería y Bosques Húmedos; detalle de priorización, en sección posterior.")

        # --- Filtro por ecosistemas (similar al selector de componentes) ---
        eco_all = list(dict.fromkeys(df["ecosistema"].astype(str).tolist()))  # mantiene orden de llegada
        selected_eco = st.multiselect(
            "Ecosistemas a incluir",
            options=eco_all,
            default=eco_all,
            key=f"{key_prefix}_opp_ecos_filter"
        )
        if not selected_eco:
            st.info("Selecciona al menos un ecosistema para visualizar el análisis de oportunidades.")
            return
        df = df[df["ecosistema"].isin(selected_eco)].copy()

        # Recalcular total_ha y pct dentro del subconjunto seleccionado
        df["_total_ha_local"] = df.groupby("ecosistema")["area_ha"].transform("sum")
        df["_pct_local"] = (df["area_ha"] / df["_total_ha_local"] * 100.0).replace([np.inf, -np.inf], 0.0).fillna(0.0)

        # ---- 1) Sunburst ----
        st.subheader("Análisis de Potenciales por regiones")
        st.caption("Para leer la gráfica. El centro rojo es la totalidad de área del ecosistema en Colombia y su porcentaje respecto a las áreas de los demás ecosistemas estudiados. Haciendo click en el ecosistema, se abre el ecosistema y su capa externa lee: Verde Oscuro: Caso de Estudio en Escala Mínima; Verde Claro: Potencial a su expansión; gris: restante por evaluar, incluyendo restricciones. Colocando el puntero, se leen las áreas.")
        fig_sun = px.sunburst(
            df,
            path=["ecosistema", "nivel_disp"],
            values="area_ha",
            color="nivel_disp",
            color_discrete_map=LEVEL_COLORS,
        )
        fig_sun.update_traces(textinfo="label+percent parent")
        fig_sun.update_traces(
            hovertemplate=(
                "<b>%{label}</b>"
                "<br>Área: %{value:,.0f} ha"
                "<br>% del ecosistema: %{percentParent:.1%}"
                "<extra></extra>"
            )
        )
        fig_sun.update_layout(
            height=650,
            margin=dict(t=10, l=10, r=10, b=10)
        )
        st.plotly_chart(fig_sun, use_container_width=True, key=f"{key_prefix}_sunburst")

        st.divider()

        # ---- 2) Barras apiladas (abs / %) ----
        st.subheader("Áreas totales: Casos de Estudio y su Potencial de Escalado")
        mode_pct = st.checkbox(
            "Mostrar en 100% (porcentaje del total del ecosistema)",
            value=False,
            key=f"{key_prefix}_pct_toggle"
        )

        df_bar = df.copy()
        df_bar["nivel_disp"] = df_bar["nivel"].apply(_canon_label_level)
        if mode_pct:
            # usar el % local recalculado tras el filtro de ecosistemas
            if "_pct_local" in df_bar.columns:
                df_bar["valor"] = df_bar["_pct_local"]
            else:
                df_bar["valor"] = df_bar.get("pct", 0.0)
            y_title = "% del total"
        else:
            df_bar["valor"] = df_bar["area_ha"]
            y_title = "Área (ha)"

        if "region" not in df_bar.columns:
            df_bar["region"] = ""

        fig_bar = px.bar(
            df_bar,
            x="ecosistema",
            y="valor",
            color="nivel_disp",
            barmode="stack",
            category_orders={"Disponibilidad": LEVEL_ORDER},
            color_discrete_map=LEVEL_COLORS,
        )
        fig_bar.update_layout(yaxis_title=y_title)
        try:
            hover_cols = ["area_ha"]
            if "_pct_local" in df_bar.columns:
                hover_cols.append("_pct_local")
            else:
                hover_cols.append("pct" if "pct" in df_bar.columns else "area_ha")
            if "region" in df_bar.columns:
                hover_cols.append("region")
            fig_bar.update_traces(
                customdata=df_bar[hover_cols].values,
                hovertemplate=(
                    "<b>%{x}</b> — %{fullData.name}<br>"
                    "Área: %{customdata[0]:,.0f} ha"
                    "<br>% del ecosistema: %{customdata[1]:.1f}%"
                    + ("<br>Región: %{customdata[2]}" if "region" in df_bar.columns and df_bar["region"].notna().any() else "")
                    + "<extra></extra>"
                )
            )
        except Exception:
            pass

        # Recuadro lateral para texto ejecutivo (gris claro)
        # Ajustamos margen derecho para que haya espacio suficiente
        fig_bar.update_layout(
            margin=dict(
                t=40,
                l=40,
                b=40,
                r=220,  # espacio para el recuadro y el texto
            )
        )


        st.plotly_chart(
            fig_bar,
            use_container_width=True,
            key=f"{key_prefix}_bar_{'pct' if mode_pct else 'abs'}"
        )

        # Texto de referencia colocado debajo de la gráfica para evitar problemas de alineación
        st.markdown(
            """
            **Referencias de orden de magnitud de áreas:**

            - Valle del Cauca: ~250.000 ha de caña en pie. Meta: ~195.000 ha de palma de aceite.  
            - Risaralda: ≈0,5 millones de hectáreas. Casanare: ≈4,46 millones de hectáreas.
            """,
        )

        st.divider()

        # ---- 2.bis) Priorización de Oportunidades (histograma por ecosistema) ----
        st.subheader("Priorización de Oportunidades")
        st.caption("Priorización de Casos de Estudio, según 7 criterios (Potencial de Carbono, Activos Estratégicos, Lectura Social, Lectura Institucional, Potencial de Extensión, Complejidad Técnica y Acciones País) y Juicio de Expertos. Ver resultados completos en: SP Estudio.")

        if "priorizacion" in df.columns:
            # Nos quedamos con una fila por ecosistema/proyecto para evitar duplicados por nivel
            df_prio = (
                df[["project_id", "ecosistema", "priorizacion"]]
                .dropna(subset=["priorizacion"])
                .drop_duplicates(subset=["project_id", "ecosistema"])
                .copy()
            )
            df_prio["priorizacion"] = pd.to_numeric(df_prio["priorizacion"], errors="coerce")
            df_prio = df_prio.dropna(subset=["priorizacion"])

            if df_prio.empty:
                st.info("No hay datos numéricos de 'priorizacion' disponibles para los ecosistemas seleccionados.")
            else:
                fig_prio = px.bar(
                    df_prio,
                    x="ecosistema",
                    y="priorizacion",
                    text="priorizacion",
                )
                fig_prio.update_layout(
                    yaxis_title="Nivel de priorización",
                    xaxis_title="Ecosistema",
                )
                fig_prio.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                st.plotly_chart(
                    fig_prio,
                    use_container_width=True,
                    key=f"{key_prefix}_prio_hist"
                )
        else:
            st.info("La hoja 'coords' no trae columna 'priorizacion'; no se puede graficar la priorización de oportunidades.")

        # ---- 3) Mapa (solo puntos de Caso de estudio) ----
        st.subheader("Visor geoespacial — Casos de estudio y Ecosistemas")

        # --- REEMPLAZO: Visor ArcGIS embebido ---
        arcgis_url = "https://ias-unipaz.maps.arcgis.com/apps/instant/sidebar/index.html?appid=26dea924d5854b488cf73af1753bc495"

        components.html(
            f"""
            <iframe
                src="{arcgis_url}"
                width="100%"
                height="650"
                style="border:none;"
                allowfullscreen
            ></iframe>
            """,
            height=660,
            scrolling=True,
        )

    if use_expander:
        with st.expander("Análisis de Oportunidades", expanded=False):
            _render_body(df)
    else:
        st.markdown("### Análisis de Oportunidades")
        _render_body(df)
def render_project_tab(pid: str, proj: Dict[str, Any]):
    st.markdown(f"**Proyecto:** {proj['title']} ")
    st.caption(proj.get("notes", ""))

    c1, c2 = st.columns(2)
    with c1:
        default_rate = proj.get("rate", 0.10)
        # asegura límites sensatos
        if default_rate <= 0: default_rate = 0.10
        if default_rate > 0.5: default_rate = default_rate/100.0  # si vino como 10 ó 12
        rate_local = st.slider(f"Tasa de descuento — {pid}", 0.02, 0.30, float(default_rate), 0.01, format="%.2f")
    with c2:
        price_factor_local = st.slider(f"Factor precio carbono — {pid}", 0.50, 2.00, 1.00, 0.05)

    cash_sim = apply_price_factor(proj["cashflow"], price_factor_local)
    vpn_val = npv(rate_local, cash_sim)

    k1, k2, k3 = st.columns(3)
    with k1: st.metric("VPN (USD)", f"{vpn_val:,.0f}")
    horizon = effective_horizon_years(proj['cashflow'], proj['carbon'])
    with k2: st.metric("Horizonte (años)", f"{horizon}")
    with k3: st.metric("CO₂ total (tCO₂e)", f"{sum(proj['carbon']):,.0f}")

    years = list(range(len(proj["cashflow"])))
    st.subheader("Flujo de caja anual")
    df_cf = pd.DataFrame({"Año": years, "Flujo (USD)": cash_sim})
    fig_cf = px.bar(df_cf, x="Año", y="Flujo (USD)")
    # Si hay serie de expansión, la superponemos como línea
    cf_exp = proj.get("cashflow_exp")
    if isinstance(cf_exp, list) and len(cf_exp) > 0:
        # recorta/igualar longitud a la serie base
        L = max(len(cash_sim), len(cf_exp))
        xs = list(range(L))
        cf_exp2 = cf_exp + [0.0]*(L - len(cf_exp))
        fig_cf.add_trace(
            go.Scatter(x=xs, y=cf_exp2, mode="lines", name="Expansión", line=dict(width=2))
        )
    st.plotly_chart(fig_cf, use_container_width=True, key=f"cf_chart_{pid}")
    # Expander de Supuestos Principales (alimentado por hoja 'detail')
    with st.expander("Supuestos"):
        details_rows = proj.get("details", [])
        if details_rows:
            try:
                df_det = pd.DataFrame(details_rows, columns=["Supuesto", "Valor"])
            except Exception:
                df_det = pd.DataFrame(details_rows)
                if set(df_det.columns) == set(["key", "value"]):
                    df_det = df_det.rename(columns={"key": "Supuesto", "value": "Valor"})
            html_table = df_det.to_html(index=False, header=False)
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.info("No se encontraron detalles para este proyecto en la hoja 'detail'.")
    # Importante: graficamos CO2 solo hasta el último periodo con dato para evitar la "caída a cero" visual
    st.subheader("CO₂ anual")

    def _last_idx(series):
        for i in reversed(range(len(series))):
            if series[i] is not None and abs(series[i]) > 1e-9:
                return i
        return 0

    last_co2_idx = _last_idx(proj["carbon"])
    years_co2 = list(range(last_co2_idx + 1))
    co2_trim = proj["carbon"][: last_co2_idx + 1]

    fig_co2 = px.line(pd.DataFrame({"Año": years_co2, "CO₂ (tCO₂e)": co2_trim}), x="Año", y="CO₂ (tCO₂e)")
    fig_co2.update_xaxes(range=[0, last_co2_idx])

    # Agregar serie de expansión si existe
    co2_exp = proj.get("carbon_exp")
    if isinstance(co2_exp, list) and len(co2_exp) > 0:
        last_co2_exp_idx = _last_idx(co2_exp)
        xs_exp = list(range(last_co2_exp_idx + 1))
        co2_exp_trim = co2_exp[: last_co2_exp_idx + 1]
        fig_co2.add_trace(
            go.Scatter(x=xs_exp, y=co2_exp_trim, mode="lines", name="Expansión", line=dict(width=2))
        )

    st.plotly_chart(fig_co2, use_container_width=True, key=f"co2_chart_{pid}")
    # Diagnóstico de componentes (ayuda a verificar parser y render)
    with st.expander("De ecosistemas de investigación a Portafolio de Proyectos."):
        comps_dbg = proj.get("components", [])
        st.write("N° componentes detectados:", len(comps_dbg))
        if comps_dbg:
            rows_dbg = [{
                "component_id": c.get("component_id"),
                "component_title": c.get("component_title"),
                "len_CF": len(c.get("cashflow", [])),
                "len_CO2": len(c.get("carbon", [])),
                "CO2_total": float(sum(c.get("carbon", []))),
                "rate": c.get("rate")
            } for c in comps_dbg]
            st.table(pd.DataFrame(rows_dbg))
        else:
            st.info("Este proyecto no trae 'components' o solo se detectó el componente por defecto.")

    # --- Composición por componentes (apilado CO2 y VPN) ---
    comps = proj.get("components", [])
    # Mostrar sección si hay más de un componente o si no es solo el default
    has_components = len(comps) > 1 or (len(comps) == 1 and comps[0].get("component_id") != "__default__")
    if has_components:
        st.subheader("Portafolio de Oportunidades")

        # Filtro manteniendo orden de llegada
        seen = set()
        comp_labels = []
        for c in comps:
            label = c.get("component_title")
            if label not in seen:
                comp_labels.append(label)
                seen.add(label)

        selected = st.multiselect(
            "Componentes a mostrar",
            comp_labels,
            default=comp_labels,
            key=f"comp_filter_{pid}"
        )
        percent_mode = st.checkbox("Mostrar en 100%", value=False, key=f"comp_pct_{pid}")

        # Construir totales por componente
        rows_c = []
        for c in comps:
            if c.get("component_title") not in selected:
                continue
            co2_tot = float(sum(c.get("carbon", [])))
            rate_c = c.get("rate")
            # Si no hay tasa por componente, usar la del slider local
            if rate_c is None or rate_c <= 0:
                rate_c = rate_local
            elif rate_c > 1.0:
                rate_c = rate_c/100.0
            vpn_c = npv(rate_c, apply_price_factor(c.get("cashflow", []), price_factor_local))
            rows_c.append({"Componente": c.get("component_title"), "CO2_total": co2_tot, "VPN": vpn_c})

        df_c = pd.DataFrame(rows_c)
        if df_c.empty:
            st.info("No hay componentes seleccionados.")
        else:
            # CO2 apilado
            st.markdown("**CO₂ total por componentes**")
            dfp = df_c.copy(); dfp["Proyecto"] = proj["title"]
            ycol, ytitle = ("CO2_total", "tCO₂e")
            if percent_mode:
                total = dfp["CO2_total"].sum()
                dfp["Valor"] = (dfp["CO2_total"]/total*100.0) if total != 0 else dfp["CO2_total"]
                ycol, ytitle = ("Valor", "%")
            fig_c = px.bar(dfp, x="Proyecto", y=ycol, color="Componente")
            fig_c.update_layout(barmode="stack", yaxis_title=ytitle)
            st.plotly_chart(fig_c, use_container_width=True, key=f"co2stack_{pid}")

            # VPN apilado
            st.markdown("**VPN por componentes (USD)**")
            dfp2 = df_c.copy(); dfp2["Proyecto"] = proj["title"]
            y2, y2title = ("VPN", "USD")
            if percent_mode:
                total_v = dfp2["VPN"].sum()
                dfp2["Valor"] = (dfp2["VPN"]/total_v*100.0) if total_v != 0 else dfp2["VPN"]
                y2, y2title = ("Valor", "%")
            fig_v = px.bar(dfp2, x="Proyecto", y=y2, color="Componente")
            fig_v.update_layout(barmode="stack", yaxis_title=y2title)
            st.plotly_chart(fig_v, use_container_width=True, key=f"vpnstack_{pid}")

    # --- Análisis de Oportunidades (por proyecto) ---
    _df_opp_local = proj.get("oportunidades_df", None)
    if isinstance(_df_opp_local, pd.DataFrame) and not _df_opp_local.empty:
        # La función ya contiene su propio expander
        render_oportunidades_section(_df_opp_local, use_expander=True, key_prefix=f"proj_{pid}")

# -----------------------------
# UI — Streamlit
# -----------------------------

st.set_page_config(page_title="Comparador SNC (VPN + Carbono) — MVP07", layout="wide")

st.sidebar.title("Matriz de Análisis")
file = st.sidebar.file_uploader("Subir archivo para interacción", type=["xlsx", "xls"])
st.sidebar.caption("Prot.07")

st.title("Oportunidades de Valor en las Soluciones Naturales del Clima (SNC)")

if not file:
    st.info("Carga de Data para inicio de análisis integrado ")
else:
    try:
        xls = pd.ExcelFile(file)
        # Hoja principal: primera hoja
        sheet = pd.read_excel(xls, sheet_name=0)

        # Intentar leer hoja de detalles (case-insensitive: 'detail' o 'detalles')
        details_sheet_name = None
        for sn in xls.sheet_names:
            if str(sn).strip().lower() in ("detail", "detalles"):
                details_sheet_name = sn
                break
        details_df = None
        if details_sheet_name is not None:
            try:
                details_df = pd.read_excel(xls, sheet_name=details_sheet_name)
            except Exception:
                details_df = None
        # >>> HOOK A — Lectura de hojas 'particiones' y 'coords' (opcional)
        part_df = None
        coords_df = None
        try:
            sheet_names_lc = [str(s).strip().lower() for s in xls.sheet_names]
            if "particiones" in sheet_names_lc:
                part_df = pd.read_excel(xls, sheet_name=xls.sheet_names[sheet_names_lc.index("particiones")])
            if "coords" in sheet_names_lc:
                coords_df = pd.read_excel(xls, sheet_name=xls.sheet_names[sheet_names_lc.index("coords")])
        except Exception as _hook_a_err:
            st.warning(f"No se pudieron leer 'particiones'/'coords': {_hook_a_err}")
        # <<< HOOK A    
    except Exception as e:
        st.error(f"No se pudo leer el Excel: {e}")
        st.stop()

    try:
        projects = parse_matrix(sheet)
        # Mapear detalles por proyecto si existe la hoja 'detail'
        if 'details_df' in locals() and details_df is not None:
            ddf = details_df.copy()
            ddf.columns = [str(c).strip().lower() for c in ddf.columns]
            # Esquema mínimo esperado: project_id, key, value (opcional: orden)
            if all(c in ddf.columns for c in ("project_id", "key", "value")):
                if "orden" in ddf.columns:
                    try:
                        ddf = ddf.sort_values(by=["project_id", "orden"])  # respeta orden por proyecto
                    except Exception:
                        pass
                details_map = {}
                for pid, grp in ddf.groupby("project_id"):
                    rows = []
                    for _, r in grp.iterrows():
                        k = str(r.get("key", "")).strip()
                        v = r.get("value", "")
                        rows.append({"Supuesto": k, "Valor": v})
                    details_map[str(pid)] = rows
                # Adjuntar al diccionario de proyectos
                for pid in projects.keys():
                    if pid in details_map:
                        projects[pid]["details"] = details_map[pid]
    except Exception as e:
        st.error(f"Error en el formato de la matriz: {e}")
        st.stop()
    # >>> HOOK B — Construcción de 'oportunidades_df' por proyecto desde 'particiones'/'coords'
    def _normalize_cols_lower(df_in: pd.DataFrame) -> pd.DataFrame:
        d = df_in.copy()
        d.columns = [str(c).strip().lower() for c in d.columns]
        return d

    def _slug_ecosystem(s: str) -> str:
        # quita tildes, pasa a minúsculas, normaliza separadores (espacios/guiones/_)
        if s is None:
            return ""
        s0 = str(s).strip().lower()
        s0 = "".join(c for c in unicodedata.normalize("NFD", s0) if unicodedata.category(c) != "Mn")
        s0 = s0.replace("_", " ").replace("-", " ")
        s0 = " ".join(s0.split())
        return s0

    def _to_float_dot(x):
        # convierte "11,3" -> 11.3; deja NaN si no se puede
        if pd.isna(x):
            return np.nan
        try:
            return float(str(x).replace(",", "."))
        except Exception:
            return np.nan

    if 'part_df' in locals() and part_df is not None:
        part_df = _normalize_cols_lower(part_df)
        needed = {"project_id", "ecosistema", "nivel", "area_ha"}
        if not needed.issubset(set(part_df.columns)):
            st.warning("La hoja 'particiones' no trae las columnas requeridas: project_id, ecosistema, nivel, area_ha")
        else:
            # normaliza llaves y series
            part_df["project_id"] = part_df["project_id"].astype(str)
            part_df["ecosistema_key"] = part_df["ecosistema"].apply(_slug_ecosystem)
            part_df["nivel"] = part_df["nivel"].astype(str)
            part_df["area_ha"] = pd.to_numeric(part_df["area_ha"], errors="coerce").fillna(0.0)

            # totales y porcentaje por ecosistema
            tot = part_df.groupby("ecosistema_key", as_index=False)["area_ha"].sum().rename(columns={"area_ha": "total_ha"})
            part_df = part_df.merge(tot, on="ecosistema_key", how="left")
            part_df["pct"] = (part_df["area_ha"] / part_df["total_ha"] * 100.0).replace([np.inf, -np.inf], 0.0).fillna(0.0)

            # coords opcionales
            coords_norm = None
            if 'coords_df' in locals() and coords_df is not None:
                coords_norm = _normalize_cols_lower(coords_df)
                # renombra si vinieron como Latitud/Longitud
                coords_norm = coords_norm.rename(columns={"latitud": "lat", "longitud": "lon"})
                if "ecosistema" not in coords_norm.columns:
                    st.warning("La hoja 'coords' no trae columna 'ecosistema'.")
                    coords_norm = None
                else:
                    coords_norm["project_id"] = coords_norm["project_id"].astype(str)
                    coords_norm["ecosistema_key"] = coords_norm["ecosistema"].apply(_slug_ecosystem)
                    if "lat" in coords_norm.columns and "lon" in coords_norm.columns:
                        coords_norm["lat"] = coords_norm["lat"].apply(_to_float_dot)
                        coords_norm["lon"] = coords_norm["lon"].apply(_to_float_dot)
                        # Prioridad (puede venir con coma decimal)
                        if "priorizacion" in coords_norm.columns:
                            coords_norm["priorizacion"] = coords_norm["priorizacion"].apply(_to_float_dot)
                    else:
                        coords_norm = None

            for _pid in projects.keys():
                sub = part_df[part_df["project_id"] == str(_pid)].copy()
                if sub.empty:
                    continue
                if coords_norm is not None:
                    merge_cols = ["project_id", "ecosistema_key"]
                    for opt_col in ["lat", "lon", "region", "priorizacion"]:
                        if opt_col in coords_norm.columns:
                            merge_cols.append(opt_col)
                    sub = sub.merge(coords_norm[merge_cols], on=["project_id", "ecosistema_key"], how="left")
                projects[_pid]["oportunidades_df"] = sub
    # <<< HOOK B        
    tab_names = list(projects.keys()) + ["Análisis Integrado", "Visor Geoespacial"]  # "Validaciones" desactivado temporalmente
    tabs = st.tabs(tab_names)

    # Tabs por proyecto
    for i, pid in enumerate(projects.keys()):
        with tabs[i]:
            render_project_tab(pid, projects[pid])

    # Replaced Portafolio tab with comparative implementation
    with tabs[-2]:
        st.subheader("Análisis Comparativo")
        all_ids = list(projects.keys())
        sel = st.multiselect("Estudios a comparar:", all_ids, default=all_ids)
        c1, c2 = st.columns(2)
        with c1:
            rate_cmp = st.slider("Tasa de descuento — Comparativo", 0.02, 0.20, 0.10, 0.01, format="%.2f")
        with c2:
            price_factor_cmp = st.slider("Factor precio carbono — Comparativo", 0.50, 2.00, 1.00, 0.05)

        if sel:
            # Construir KPIs por proyecto con los controles de este tab (sin sumar)
            rows = []
            for pid in sel:
                proj = projects[pid]
                cf_sim = apply_price_factor(proj["cashflow"], price_factor_cmp)
                rate_used = proj.get("rate", None)
                if rate_used is None or rate_used <= 0:
                    rate_used = rate_cmp
                elif rate_used > 1.0:
                    rate_used = rate_used/100.0
                vpn_val = npv(rate_used, cf_sim)
                rows.append({
                    "project_id": pid,
                    "Proyecto": proj["title"],
                    "Tasa usada": rate_used,
                    "VPN (USD)": vpn_val,
                    "CO₂ total (tCO₂e)": sum(proj["carbon"]),
                    "Horizonte (años)": effective_horizon_years(proj["cashflow"], proj["carbon"]),
                })

            df_cmp = pd.DataFrame(rows)
            st.dataframe(
                df_cmp.style.format({
                    "Tasa usada": "{:.2%}",
                    "VPN (USD)": "{:,.0f}",
                    "CO₂ total (tCO₂e)": "{:,.0f}",
                }),
                use_container_width=True,
            )
            st.caption("Comparación de métricas principales; se mantiene la lógica de cada modelo.")

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("VPN por proyecto (USD)")
                st.plotly_chart(
                    px.bar(df_cmp, x="Proyecto", y="VPN (USD)"),
                    use_container_width=True,
                    key=f"cmp_vpn_{'-'.join(sel)}_{len(df_cmp)}"
                )
            with col_b:
                st.subheader("CO₂ total por proyecto (tCO₂e)")
                st.plotly_chart(
                    px.bar(df_cmp, x="Proyecto", y="CO₂ total (tCO₂e)"),
                    use_container_width=True,
                    key=f"cmp_co2_{'-'.join(sel)}_{len(df_cmp)}"
                )

            st.caption("Análisis de Portafolio construido con base en resultados de investigación:")

            # --- Portafolio: composición por componentes (opcional, a demanda) ---
            with st.expander("📦 Portafolio de Oportunidades — desplegable"):
                # Lista de proyectos que realmente tienen componentes > 1 (o distinto de default)
                proj_ids_with_comps = []
                for _pid, _proj in projects.items():
                    comps_ = _proj.get("components", [])
                    if len(comps_) > 1 or (len(comps_) == 1 and comps_[0].get("component_id") != "__default__"):
                        proj_ids_with_comps.append(_pid)

                if not proj_ids_with_comps:
                    st.info("Ningún proyecto trae componentes definidos en la matriz.")
                else:
                    pid_sel = st.selectbox(
                        "Selección de proyecto",
                        options=proj_ids_with_comps,
                        format_func=lambda _pid: projects[_pid]["title"],
                        key="portafolio_comp_project_select"
                    )
                    proj_comp = projects[pid_sel]

                    comps = proj_comp.get("components", [])
                    # Filtro de componentes y modo porcentaje (100%) como en los tabs
                    seen_lb = set()
                    comp_labels = []
                    for c in comps:
                        lb = c.get("component_title")
                        if lb not in seen_lb:
                            comp_labels.append(lb); seen_lb.add(lb)

                    selected_comp = st.multiselect(
                        "Ecosistemas o Caso de Estudio",
                        comp_labels,
                        default=comp_labels,
                        key=f"portafolio_comp_filter_{pid_sel}"
                    )
                    percent_mode_pf = st.checkbox(
                        "Mostrar en 100%",
                        value=False,
                        key=f"portafolio_comp_pct_{pid_sel}"
                    )

                    # Usar los mismos controles del comparativo para tasa y factor, o la tasa del componente si existe
                    rows_pc = []
                    for c in comps:
                        if c.get("component_title") not in selected_comp:
                            continue
                        co2_tot = float(sum(c.get("carbon", [])))
                        rate_c = c.get("rate")
                        if rate_c is None or rate_c <= 0:
                            rate_c = rate_cmp  # usa la tasa del tab Portafolio si el componente no trae una
                        elif rate_c > 1.0:
                            rate_c = rate_c/100.0
                        vpn_c = npv(rate_c, apply_price_factor(c.get("cashflow", []), price_factor_cmp))
                        rows_pc.append({"Componente": c.get("component_title"), "CO2_total": co2_tot, "VPN": vpn_c})

                    df_pc = pd.DataFrame(rows_pc)
                    if df_pc.empty:
                        st.info("No hay componentes seleccionados para este proyecto.")
                    else:
                        # CO2 apilado (portafolio)
                        st.markdown("**CO₂ total por componentes — Portafolio**")
                        dfp_pf = df_pc.copy(); dfp_pf["Proyecto"] = proj_comp["title"]
                        ycol_pf, ytitle_pf = ("CO2_total", "tCO₂e")
                        if percent_mode_pf:
                            total_pf = dfp_pf["CO2_total"].sum()
                            dfp_pf["Valor"] = (dfp_pf["CO2_total"]/total_pf*100.0) if total_pf != 0 else dfp_pf["CO2_total"]
                            ycol_pf, ytitle_pf = ("Valor", "%")
                        fig_c_pf = px.bar(dfp_pf, x="Proyecto", y=ycol_pf, color="Componente")
                        fig_c_pf.update_layout(barmode="stack", yaxis_title=ytitle_pf)
                        st.plotly_chart(fig_c_pf, use_container_width=True, key=f"pf_co2stack_{pid_sel}")

                        # VPN apilado (portafolio)
                        st.markdown("**VPN por componentes (USD) — Portafolio**")
                        dfp2_pf = df_pc.copy(); dfp2_pf["Proyecto"] = proj_comp["title"]
                        y2_pf, y2title_pf = ("VPN", "USD")
                        if percent_mode_pf:
                            total_v_pf = dfp2_pf["VPN"].sum()
                            dfp2_pf["Valor"] = (dfp2_pf["VPN"]/total_v_pf*100.0) if total_v_pf != 0 else dfp2_pf["VPN"]
                            y2_pf, y2title_pf = ("Valor", "%")
                        fig_v_pf = px.bar(dfp2_pf, x="Proyecto", y=y2_pf, color="Componente")
                        fig_v_pf.update_layout(barmode="stack", yaxis_title=y2title_pf)
                        st.plotly_chart(fig_v_pf, use_container_width=True, key=f"pf_vpnstack_{pid_sel}")
                        # --- Análisis de Oportunidades (por proyecto) ---
                        # >>> HOOK B — Invocar visualización de Oportunidades
                        _df_opp = proj_comp.get("oportunidades_df", None)
                        if isinstance(_df_opp, pd.DataFrame) and not _df_opp.empty:
                            # Importante: estamos DENTRO de un expander; por eso desactivamos expander interno
                            render_oportunidades_section(_df_opp, use_expander=False, key_prefix=f"pf_{pid_sel}")
                        else:
                            st.info("Este proyecto no trae filas en 'particiones'/'coords' para 'Análisis de Oportunidades'.")
                        # <<< HOOK B
        else:
            st.info("Selecciona al menos un proyecto para comparar.")

    # --- Visor externo (embed ArcGIS u otros) ---
    with tabs[-1]:
        st.subheader("Visor Geoespacial — Mapa de Casos de Estudio, Oportunidades y Ecosistemas")
        st.caption("Visualizador dinámico de áreas de interés: Potenciales, Áreas de Investigación y Casos de Estudio.")

        arcgis_url = "https://ias-unipaz.maps.arcgis.com/apps/instant/sidebar/index.html?appid=26dea924d5854b488cf73af1753bc495"


        components.html(
            f"""
            <iframe
                src="{arcgis_url}"
                width="100%"
                height="800"
                style="border:none;"
                allowfullscreen
            ></iframe>
            """,
            height=820,
            scrolling=True,
        )

    # --- Validaciones (desactivado temporalmente) ---
    # with tabs[-1]:
    #     st.subheader("Validaciones de calidad de datos")
    #     issues = []
    #
    #     for pid, pj in projects.items():
    #         cash, carb = pj["cashflow"], pj["carbon"]
    #         # NaN
    #         if any(pd.isna(x) for x in cash) or any(pd.isna(x) for x in carb):
    #             issues.append({"project_id": pid, "issue": "Valores NaN en flujo o CO₂"})
    #         # longitudes
    #         if len(cash) != len(carb):
    #             issues.append({"project_id": pid, "issue": "Longitudes distintas: CASHFLOW vs CO₂"})
    #         # huecos internos: detecta grandes huecos (cambios bruscos NaN->valores)
    #         # Aquí un check simple: todos p0..pN existen por parseo; si todo ok, no marca.
    #         # (Se puede ampliar a reglas específicas tuyas.)
    #
    #     if issues:
    #         st.warning("Se encontraron observaciones en los datos:")
    #         st.dataframe(pd.DataFrame(issues), use_container_width=True)
    #     else:
    #         st.success("Validaciones OK: sin NaN ni desalineación de longitudes.")