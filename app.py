import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import griddata

st.title("Расчет тройниковых (штуцерных) сварных соединений")
st.header("В соответствии с РД 10-249-98")

# Создаем таблицу допускаемых напряжений для стали 12Х1МФ
st.subheader("Таблица допускаемых напряжений для стали 12Х1МФ")

# Данные из таблицы для стали 12Х1МФ
temperature_ranges = [20, 250, 300, 350, 400, 420, 440, 450, 460, 480, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600, 610, 620]
stress_data_12x1mf = {
    1e4: [None, None, None, None, None, None, None, None, None, 133, 130, 120, 112, 100, 88, 80, 72, 65, 59, 53, 47, 41, 35],
    1e5: [173, 166, 159, 152, 145, 142, 139, 138, 136, 133, 113, 101, 90, 81, 73, 66, 59, 53, 47, 41, 37, 33, None],
    2e5: [None, None, None, None, None, None, None, 138, 136, 120, 96, 86, 77, 69, 62, 56, 50, 44, 39, 35, 31, None, None],
    3e5: [None, None, None, None, None, None, None, 138, 130, 107, 88, 79, 72, 65, 58, 52, 46, 41, 36, 32, 29, None, None],
    4e5: [None, None, None, None, None, None, None, 138, 125, 103, 83, 76, 66, 59, 53, 48, 43, 38, 34, 30, 27, None, None]
}

# Создаем DataFrame для отображения
df_stress = pd.DataFrame(stress_data_12x1mf, index=temperature_ranges)
df_stress.index.name = 'Температура, °C'
st.dataframe(df_stress)

# Функция для линейной интерполяции допускаемого напряжения
def interpolate_stress(temperature, operating_hours):
    points = []
    values = []
    
    for temp_idx, temp in enumerate(temperature_ranges):
        for hours_idx, hours in enumerate([1e4, 1e5, 2e5, 3e5, 4e5]):
            stress = stress_data_12x1mf[hours][temp_idx]
            if stress is not None:
                points.append([temp, hours])
                values.append(stress)
    
    if not points:
        return None
    
    # Интерполяция
    try:
        interpolated_value = griddata(points, values, [[temperature, operating_hours]], method='linear')[0]
        return float(interpolated_value) if not np.isnan(interpolated_value) else None
    except:
        return None

# Боковая панель для ввода данных
st.sidebar.header("Исходные данные")

# Ввод основных параметров
D_a = st.sidebar.number_input("Наружный диаметр основной трубы (коллектора) D_a, мм", min_value=0.0, value=325.0, step=1.0)
s = st.sidebar.number_input("Толщина стенки основной трубы s, мм", min_value=0.0, value=38.0, step=0.1)
d_a = st.sidebar.number_input("Наружный диаметр штуцера d_a, мм", min_value=0.0, value=93.0, step=1.0)
s_s = st.sidebar.number_input("Толщина стенки штуцера s_s, мм", min_value=0.0, value=21.5, step=0.1)
p = st.sidebar.number_input("Давление P, МПа", min_value=0.0, value=14.0, step=0.1)
T = st.sidebar.number_input("Температура T, °C", min_value=0.0, value=545.0, step=1.0)
operating_hours = st.sidebar.number_input("Наработка на момент обследования, ч", min_value=0, value=219142, step=1000)
planned_hours = st.sidebar.number_input("Планируемое время дальнейшей эксплуатации, ч", min_value=0, value=50000, step=1000)

# Дополнительные параметры
st.sidebar.subheader("Дополнительные параметры")
c = st.sidebar.number_input("Прибавка на коррозию c, мм", min_value=0.0, value=0.0, step=0.1, 
                           help="Обычно принимается 0-2 мм в зависимости от агрессивности среды")

st.sidebar.info("""
**Обозначения:**
- D_a - наружный диаметр основной трубы
- s - толщина стенки основной трубы  
- d_a - наружный диаметр штуцера
- s_s - толщина стенки штуцера
- s_os - минимальная толщина стенки штуцера
- c - прибавка на коррозию
""")

# Расчет
if st.button("Выполнить расчет"):
    st.header("Результаты расчета")
    
    # 1. Определение допускаемого напряжения
    total_hours = operating_hours + planned_hours
    sigma_allowable = interpolate_stress(T, total_hours)
    
    if sigma_allowable is None:
        st.error("Невозможно определить допускаемое напряжение для заданных параметров")
        st.stop()
    
    st.subheader(f"1. Допускаемое напряжение [σ] = {sigma_allowable:.2f} МПа")
    st.write(f"При температуре {T}°C и суммарной наработке {total_hours:.0f} ч")
    
    # 2. Конструктивный размер штуцера h_s
    h_s = np.sqrt(1.25 * (d_a - s_s) * (s_s - c))
    st.subheader(f"2. Конструктивный размер штуцера h_s = {h_s:.2f} мм")
    st.write(f"h_s = √[1.25 * ({d_a} - {s_s}) * ({s_s} - {c})] = √[1.25 * {d_a - s_s:.1f} * {s_s - c:.1f}]")
    
    # 3. Минимальная толщина стенки штуцера s_os
    # Для расчета s_os нужен коэффициент прочности, принимаем φ = 1 для первого приближения
    phi_temp = 1.0
    s_os = (p * d_a) / (2 * sigma_allowable * phi_temp + p)
    st.subheader(f"3. Минимальная толщина стенки штуцера s_os = {s_os:.2f} мм")
    st.write(f"s_os = ({p} * {d_a}) / (2 * {sigma_allowable:.1f} * {phi_temp} + {p})")
    
    # 4. Компенсирующая площадь штуцера f_s
    f_s = 2 * h_s * ((s_s - c) - s_os)
    st.subheader(f"4. Компенсирующая площадь штуцера f_s = {f_s:.2f} мм²")
    st.write(f"f_s = 2 * {h_s:.2f} * (({s_s} - {c}) - {s_os:.2f})")
    
    # 5. Коэффициент прочности для неукрепленного отверстия φ_od
    D_m = D_a - s  # Средний диаметр основной трубы
    z = d_a / np.sqrt(D_m * (s - c))
    phi_od = 2 / (z + 1.75) if (z + 1.75) != 0 else 0
    
    st.subheader(f"5. Коэффициент прочности для неукрепленного отверстия φ_od = {phi_od:.3f}")
    st.write(f"z = {d_a} / √({D_m:.1f} * ({s} - {c})) = {z:.3f}")
    st.write(f"D_m = {D_a} - {s} = {D_m:.1f} мм")
    
    # 6. Коэффициент прочности для укрепленного отверстия φ_oc
    sum_f = f_s  # Сумма компенсирующих площадей
    denominator = 2 * (s - c) * np.sqrt(D_m * (s - c))
    phi_oc = phi_od * (1 + sum_f / denominator) if denominator != 0 else phi_od
    
    st.subheader(f"6. Коэффициент прочности для укрепленного отверстия φ_oc = {phi_oc:.3f}")
    st.write(f"φ_oc = {phi_od:.3f} * [1 + {sum_f:.1f} / (2 * ({s} - {c}) * √({D_m:.1f} * ({s} - {c})))]")
    
    # 7. Приведенное напряжение σ
    sigma = p * (D_a - (s - c)) / (2 * phi_oc * (s - c))
    
    st.subheader(f"7. Приведенное напряжение σ = {sigma:.2f} МПа")
    st.write(f"σ = {p} * [{D_a} - ({s} - {c})] / (2 * {phi_oc:.3f} * ({s} - {c}))")
    
    # 8. Оценка прочности
    safety_factor = sigma_allowable / sigma if sigma != 0 else 0
    
    st.header("Оценка прочности")
    st.subheader(f"Запас прочности: {safety_factor:.2f}")
    
    if sigma <= sigma_allowable:
        st.success("✅ Условие прочности ВЫПОЛНЯЕТСЯ")
        st.write(f"σ = {sigma:.2f} МПа ≤ [σ] = {sigma_allowable:.2f} МПа")
    else:
        st.error("❌ Условие прочности НЕ ВЫПОЛНЯЕТСЯ")
        st.write(f"σ = {sigma:.2f} МПа > [σ] = {sigma_allowable:.2f} МПа")
    
    # Сводная таблица результатов
    st.header("Сводная таблица результатов")
    results_data = {
        'Параметр': ['Допускаемое напряжение [σ], МПа', 'Приведенное напряжение σ, МПа', 
                     'Коэффициент прочности φ_oc', 'Запас прочности'],
        'Значение': [f"{sigma_allowable:.2f}", f"{sigma:.2f}", 
                     f"{phi_oc:.3f}", f"{safety_factor:.2f}"],
        'Статус': ['-', 'В норме' if sigma <= sigma_allowable else 'Превышено', 
                   '-', 'В норме' if safety_factor >= 1.0 else 'Недостаточный']
    }
    st.table(pd.DataFrame(results_data))

else:
    st.info("Введите исходные данные в боковой панели и нажмите 'Выполнить расчет'")

st.markdown("---")
st.caption("Расчет выполнен в соответствии с РД 10-249-98 'Нормы расчета на прочность стационарных котлов и трубопроводов пара и горячей воды'")