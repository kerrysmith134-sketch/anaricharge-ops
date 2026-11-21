#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-locale-cases.py — 生成 RU / ES 的 9 个案例详情页规格

设计取舍（写进页面，不隐瞒）：
  - 本地化：标题、概要、三个要点（约束 / 做法 / 结果）、字段标签
  - 保留原位：参数表里的**技术值与型号**（工程惯例）
  - 长文分析仍在英文页：本地化页明确写「完整分析见英文页」并给链接
    —— 技术长文机翻错误代价高，宁可不译也不译错
"""
import json
import os

PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")
EN = json.load(open("/tmp/cases-en.json", encoding="utf-8"))

# AC 产品已下架（2026-11-08 用户决策"只保留直流"）→ 这个 AC 案例不再生成本地化页
SKIP_SLUGS = {"ac-wallbox-deployments"}

IMG = {
    "bus-depot-czechia": "scene-fleet-1280.webp",
    "jordan-160kw": "case-jordan-640.webp",
    "cambodia-240kw": "case-cambodia-640.webp",
    "romania-highway": "case-romania-640.webp",
    "hot-climate": "scene-hotclimate-640.webp",
    "cold-climate": "case-cold-640.webp",
    "off-grid-pv-ess": "scene-offgrid-640.webp",
    "ac-wallbox-deployments": "scene-destination-640.webp",
    "emerging-markets": "scene-commercial-640.webp",
}

# 每个案例：标题 / 概要 / 三个要点（约束、做法、结果）
C = {
 "bus-depot-czechia": {
  "ru": ("Депо на 12 постов: проверка в 06:40, а не по кВт·ч в сутки",
         "Оператор регулярных автобусных перевозок заказал двенадцать двухпостовых DC-зарядок 120 кВт в мае 2026 года и получил их под напряжением в июле. Это 24 разъёма DC с 12 вводов — достаточно, чтобы пройти утренний пик по расписанию без платы за расширение подключения.",
         "Пик расписания: двенадцать автобусов должны уехать утром одновременно.",
         "Распределение мощности между постами вместо наращивания ввода.",
         "24 разъёма DC от 12 вводов; утренний пик закрыт без расширения подключения."),
  "es": ("Cochera de 12 puestos: se juzga a las 06:40, no por kWh al día",
         "Un operador de servicios regulares de autobús encargó doce cargadores DC de 120 kW de dos pistolas en mayo de 2026 y los tuvo energizados en julio. Son 24 conectores DC desde 12 acometidas: suficiente para cubrir el pico de la mañana sin pagar una ampliación de conexión.",
         "Pico de horario: doce autobuses deben salir a la vez por la mañana.",
         "Reparto de potencia entre pistolas en lugar de ampliar la acometida.",
         "24 conectores DC desde 12 acometidas; pico de la mañana cubierto sin ampliar la conexión."),
 },
 "jordan-160kw": {
  "ru": ("Коридорная зарядка в Иордании: инженерия загрузки, работающая при 45 °C",
         "Ведущий ближневосточный CPO построил с нами скоростную зарядку на трассе: станции Vulco DC 160 кВт в двух- и трёхпостовом исполнении, рассчитанные на номинал при летней температуре выше 45 °C. Площадка вошла в число крупнейших зарядных станций страны.",
         "Жара выше 45 °C: после обеда оборудование теряет мощность первым.",
         "Тепловой запас + интеллектуальное распределение мощности между постами.",
         "Стабильный номинал в летний пик; одна из крупнейших станций Иордании."),
  "es": ("Carga de corredor en Jordania: ingeniería de utilización que aguanta a 45 °C",
         "Un CPO líder de Oriente Medio construyó con nosotros carga rápida de autopista: estaciones Vulco DC de 160 kW en configuraciones de dos y tres pistolas, diseñadas para mantener la potencia nominal con verano por encima de 45 °C. El sitio quedó entre los mayores de Jordania.",
         "Calor por encima de 45 °C: la potencia cae por la tarde si no hay margen térmico.",
         "Margen térmico + reparto inteligente de potencia entre pistolas.",
         "Potencia nominal estable en el pico de verano; uno de los mayores sitios del país."),
 },
 "cambodia-240kw": {
  "ru": ("2 × 180 кВт + 1 × 240 кВт на национальной трассе Камбоджи",
         "Оператор из Пномпеня, уже работавший на наших Vulco после первой поставки, вернулся с более жёстким бюджетом и нулевой терпимостью к простоям. Мы поставили три Pales DC вдоль национальной трассы: 2 × 180 кВт и 1 × 240 кВт, двухпостовые GB/T.",
         "Сезон муссонов и ограниченная мощность сети плюс требование нулевого простоя.",
         "Три моноблока Pales с двумя GB/T каждый, без отдельного силового шкафа.",
         "Повторный заказ: клиент вернулся после первого объекта."),
  "es": ("2 × 180 kW + 1 × 240 kW en la carretera nacional de Camboya",
         "Un operador de Phnom Penh que ya usaba nuestros Vulco tras un primer despliegue volvió con un presupuesto más ajustado y tolerancia cero a paradas. Instalamos tres cargadores Pales DC en la carretera nacional: 2 × 180 kW y 1 × 240 kW, de dos pistolas GB/T.",
         "Monzón, red limitada y exigencia de cero tiempo de parada.",
         "Tres monobloques Pales con dos GB/T cada uno, sin armario de potencia separado.",
         "Pedido repetido: el cliente volvió después del primer sitio."),
 },
 "romania-highway": {
  "ru": ("Первая поставка в Румынию: пуск 180 кВт в эпоху AFIR",
         "Румынский CPO выбрал нас для расширения сети на трассах. Мы поставили зарядки Vulco DC 180 кВт в двух- и трёхпостовом исполнении на площадках сервиса и провели весь пуск с собственными инженерами на месте.",
         "Требования AFIR и сроки согласований — до того как оборудование вообще включат.",
         "Инженеры Anari на месте в ходе пуска, а не дистанционные консультации.",
         "Первая поставка в стране стала для нас шаблоном пуска в регионе ЕС."),
  "es": ("Primer despliegue en Rumanía: puesta en marcha de 180 kW en la era AFIR",
         "Un CPO rumano nos eligió para expandir su red de autopista. Suministramos cargadores Vulco DC de 180 kW en configuraciones de dos y tres pistolas en áreas de servicio y ejecutamos toda la puesta en marcha con ingenieros propios en sitio.",
         "Requisitos AFIR y plazos de aprobación antes de energizar.",
         "Ingenieros de Anari en sitio durante la puesta en marcha, no soporte remoto.",
         "El primer despliegue del país se volvió nuestro patrón de puesta en marcha en la UE."),
 },
 "hot-climate": {
  "ru": ("DC-зарядка в жару: номинал держится за 45 °C",
         "Публичные сети Ближнего Востока отказывают в одной и той же точке — в пиковое лето. Наши DC 120–180 кВт развёрнуты в сети израильского партнёра с 2025 года и в Саудовской Аравии в трёхпостовом исполнении.",
         "Летний пик: температура снаружи выше, чем рассчитано оборудование.",
         "Термоуправление и интеллектуальное распределение мощности вместо снижения номинала.",
         "Работа на номинале в самые жаркие часы, а не «снижение мощности» в отчёте."),
  "es": ("Carga DC en clima cálido: mantiene la potencia nominal por encima de 45 °C",
         "Las redes públicas de Oriente Medio fallan en el mismo punto: el pico del verano. Nuestros cargadores DC de 120–180 kW están desplegados en la red de un socio israelí desde 2025 y en Arabia Saudí en configuración de tres pistolas.",
         "Pico de verano: la temperatura ambiente supera lo previsto en el diseño.",
         "Gestión térmica y reparto inteligente en lugar de reducir potencia.",
         "Potencia nominal en las horas más calurosas, no «derating» en el informe."),
 },
 "cold-climate": {
  "ru": ("DC-зарядка в холод: запуск при минус 30 °C",
         "Северный и центральный Казахстан держит минус 30 °C неделями. Мы ввели в эксплуатацию шесть двухпостовых DC 120 кВт на коммерческой парковке в августе 2026 года; в Грузии оператор сети взял двухпостовые DC 120 и 180 кВт.",
         "Минус 30 °C неделями: обычный шкаф просто не запускается.",
         "Подогрев корпуса и пусковой резерв, рассчитанные на длительный холод.",
         "6 × 120 кВт (12 разъёмов) в Казахстане + сеть в Грузии."),
  "es": ("Carga DC en frío: arranca a menos 30 °C",
         "El norte y el centro de Kazajistán mantienen −30 °C durante semanas. Pusimos en servicio seis cargadores DC de 120 kW de dos pistolas en un aparcamiento comercial en agosto de 2026; en Georgia, el segundo operador de red del país tomó DC de 120 y 180 kW.",
         "−30 °C durante semanas: un armario convencional no arranca.",
         "Calefacción de envolvente y margen de arranque para frío prolongado.",
         "6 × 120 kW (12 conectores) en Kazajistán + red en Georgia."),
 },
 "off-grid-pv-ess": {
  "ru": ("Автономная СЭС, накопитель и зарядка как одна система, а не три закупки",
         "Промышленный парк в Китае работает на связке СЭС — накопитель — зарядка: панели над парковкой, батарейная система и AC 22 кВт плюс DC 80/120 кВт, спроектированные как одна автономная система генерации.",
         "Нет пригодного подключения к сети для нужной мощности.",
         "Генерация, хранение и зарядка считаются вместе, а не покупаются по частям.",
         "Площадка работает автономно; накопитель определяет, сколько постов можно включить."),
  "es": ("FV aislada, almacenamiento y carga como un sistema, no tres compras",
         "Un parque industrial en China opera un conjunto FV-almacenamiento-carga: paneles sobre el aparcamiento, un sistema de baterías y carga AC de 22 kW más DC de 80/120 kW, diseñados como una sola instalación de generación aislada.",
         "No hay conexión de red utilizable para la potencia requerida.",
         "Generación, almacenamiento y carga se dimensionan juntos, no por partes.",
         "El sitio opera aislado; el almacenamiento decide cuántos puestos se pueden encender."),
 },
 "ac-wallbox-deployments": {
  "ru": ("AC 22 кВт: от трасс Омана до полицейского участка в Италии",
         "Один продукт, пять рынков. Наша AC-станция 22 кВт Type 2 напольного исполнения развёрнута на трассах Омана, на парковках Кипра и Перу, у полицейского участка в Италии и в Турции рядом с центром локализации.",
         "Пять разных площадок с одной и той же задачей — долгая стоянка.",
         "Одно изделие, разные ответы на управление доступом и учёт.",
         "Пять рынков без изменения продукта."),
  "es": ("AC de 22 kW: de las carreteras de Omán a una comisaría en Italia",
         "Un producto, cinco mercados. Nuestra estación AC de 22 kW Type 2 de suelo está desplegada en corredores de Omán, aparcamientos de Chipre y Perú, una comisaría en Italia y en Türkiye junto a un centro de localización.",
         "Cinco sitios distintos con la misma premisa: estancia larga.",
         "Un solo producto con respuestas distintas en control de acceso y medición.",
         "Cinco mercados sin cambiar el producto."),
 },
 "emerging-markets": {
  "ru": ("Когда политика приходит раньше зарядной сети",
         "Общее у этих рынков не борьба за долю, а отсутствие инфраструктуры. Эфиопия ограничила ввоз бензиновых и дизельных машин до появления сети: мы ввели в эксплуатацию 3 двухпостовых DC 180 кВт (6 разъёмов, 540 кВт) на одной коммерческой площадке. Болгария: 4 шкафа Castor.",
         "Спрос создан политикой, а инфраструктуры ещё нет.",
         "Быстрый ввод там, где конкуренты ждут «зрелости рынка».",
         "3 × 180 кВт DC (540 кВт) в Эфиопии; 4 × Castor в Болгарии; Сальвадор."),
  "es": ("Cuando la política llega antes que la red de carga",
         "Lo que comparten estos mercados no es competencia por cuota, sino ausencia de infraestructura. Etiopía restringió la importación de vehículos diésel y gasolina antes de que existiera la red: pusimos en servicio 3 cargadores DC de 180 kW de dos pistolas (6 conectores, 540 kW) en un sitio comercial. Bulgaria: 4 armarios Castor.",
         "La demanda la creó la política; la infraestructura aún no existe.",
         "Puesta en servicio rápida donde otros esperan a que el mercado madure.",
         "3 × 180 kW DC (540 kW) en Etiopía; 4 × Castor en Bulgaria; El Salvador."),
 },
}

# 案例页字段标签翻译（复用产品页词表 + 案例特有）
LBL = {
 "Product": ("Изделие", "Producto"),
 "Power": ("Мощность", "Potencia"),
 "Configurations": ("Конфигурации", "Configuraciones"),
 "Site type": ("Тип площадки", "Tipo de sitio"),
 "Climate design point": ("Расчётный климат", "Punto de diseño climático"),
 "Operator": ("Оператор", "Operador"),
 "Support model": ("Модель поддержки", "Modelo de soporte"),
 "Size for the average": ("Расчёт под средний день", "Dimensionar para la media"),
 "Dispensers per cabinet": ("Постов на шкаф", "Dispensadores por armario"),
 "Photovoltaic array": ("Фотоэлектрическая система", "Campo fotovoltaico"),
 "Battery energy storage": ("Накопитель энергии", "Almacenamiento de energía"),
 "AC charging": ("AC-зарядка", "Carga AC"),
 "DC charging": ("DC-зарядка", "Carga DC"),
 "System architecture": ("Архитектура системы", "Arquitectura del sistema"),
}

NOTE_RU = ("Полный технический разбор с формулами и таблицами — на английской странице.")
NOTE_ES = ("El análisis técnico completo, con fórmulas y tablas, está en la página en inglés.")


def build(slug, loc):
    title, lede, k1, k2, k3 = C[slug][loc]
    en = EN[slug]
    rows = []
    for a, b in en["specs"]:
        rows.append({"k": LBL.get(a, (a, a))[0 if loc == "ru" else 1], "v": b})
    if not rows:
        rows = [{"k": ("Площадка" if loc == "ru" else "Sitio"), "v": en["tldr"][:120]}]

    facts = []
    for num, lab in en["stats"][:4]:
        if num:
            facts.append({"value": num, "label": lab if loc == "en" else (
                "см. параметры ниже" if loc == "ru" else "ver especificaciones")})

    if loc == "ru":
        bulb = [("Ограничение", k1), ("Что сделали", k2), ("Результат", k3)]
        eyebrow, h2 = "Разбор", "Ограничение → решение → результат"
        spec_eyebrow = "Параметры площадки"
        cta_h2 = "Похожая площадка? Пришлите вводные."
        more = "Полный разбор (EN)"
        lang_label = "Полная версия анализа — на английском"
        note = NOTE_RU
    else:
        bulb = [("Restricción", k1), ("Qué hicimos", k2), ("Resultado", k3)]
        eyebrow, h2 = "Análisis", "Restricción → solución → resultado"
        spec_eyebrow = "Parámetros del sitio"
        cta_h2 = "¿Un sitio parecido? Envíe los datos."
        more = "Análisis completo (EN)"
        lang_label = "La versión completa del análisis está en inglés"
        note = NOTE_ES

    return {
        "slug": f"{loc}/cases/{slug}",
        "url": f"/{loc}/cases/{slug}.html",
        "breadcrumb": title[:48],
        "locale": loc,
        "title": (title[:56] + " | Anari")[:60],
        "meta": ((lede[:140] + (" Подробности и параметры — на странице." if loc == "ru"
                                else " Detalles y especificaciones en la página.")))[:160],
        "hreflangs": [
            {"lang": "en", "href": f"https://www.anaricharge.com/cases/{slug}"},
            {"lang": "ru", "href": f"https://www.anaricharge.com/ru/cases/{slug}"},
            {"lang": "es", "href": f"https://www.anaricharge.com/es/cases/{slug}"},
        ],
        "sections": [
            {"type": "hero", "eyebrow": ("Кейс" if loc == "ru" else "Caso"), "h1": title, "lede": lede,
             "image": f"/assets/img/v2/{IMG[slug]}",
             "credit": lang_label,
             "facts": facts or None,
             "actions": [{"label": ("Все проекты" if loc == "ru" else "Todos los proyectos"),
                          "href": f"/{loc}/cases/"},
                         {"label": more, "href": f"/cases/{slug}"}]},
            {"type": "steps", "alt": True, "eyebrow": eyebrow, "h2": h2, "lede": note,
             "items": [{"no": f"0{i+1}", "title": t, "text": x} for i, (t, x) in enumerate(bulb)]},
            {"type": "specTable", "eyebrow": spec_eyebrow,
             "h2": (f"{title[:34]} — {'параметры' if loc=='ru' else 'parámetros'}"),
             "rows": rows, "caption": title[:50]},
            {"type": "cta", "eyebrow": ("Следующий шаг" if loc == "ru" else "Siguiente paso"),
             "h2": cta_h2,
             "lede": ("Достаточно страны, доступной мощности и того, как площадка будет работать."
                      if loc == "ru" else
                      "Basta con el país, la potencia disponible y cómo operará el sitio."),
             "actions": [{"label": ("Обсудить проект" if loc == "ru" else "Hablar del proyecto"),
                          "href": f"/{loc}/inquiry"},
                         {"label": more, "href": f"/cases/{slug}"}]},
        ],
    }


n = 0
for slug in C:
    if slug in SKIP_SLUGS:
        continue
    for loc in ("ru", "es"):
        d = build(slug, loc)
        out = os.path.join(PAGES, loc, "cases", f"{slug}.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        n += 1
        print(f"  {loc}/cases/{slug}.json  title={len(d['title'])}")
print(f"\n写出 {n} 个本地化案例页规格")
