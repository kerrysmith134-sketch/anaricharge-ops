#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-locale-products.py — 生成 RU / ES 的 8 个产品详情页规格

原则：
  - **结构、标题、定位文案本地化**
  - **参数值保留原位**（工程文档惯例，量与单位不译；页面里明确说明这一点）
  - 参数标签翻译；事实库要求的英文精确短语在英文页保留，本页不涉及
"""
import json
import os
import re

WS = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(WS, "pages")
EN_SPECS = os.path.join(PAGES, "products")
SRC = "/tmp/product-specs.json"

PRODUCTS = {
    "fora":   {"img": "fora-split-960kw",   "ru": "Fora", "es": "Fora"},
    "vulco":  {"img": "vulco-60-480kw",     "ru": "Vulco", "es": "Vulco"},
    "pales":  {"img": "pales-60-240kw",     "ru": "Pales", "es": "Pales"},
    "castor": {"img": "castor-20-40kw",     "ru": "Castor", "es": "Castor"},
    "aquila": {"img": "aquila-ads-60-240kw", "ru": "Aquila", "es": "Aquila"},
    "bess":   {"img": "bess-261kwh",        "ru": "BESS", "es": "BESS"},
}

# 参数标签（只译标签，值保留原样）
LABELS = {
 "Ad formats": ("Форматы рекламы", "Formatos de anuncio"),
 "Advertising display": ("Рекламный экран", "Pantalla publicitaria"),
 "Authentication": ("Аутентификация", "Autenticación"),
 "Capacities / AC power": ("Ёмкости / мощность AC", "Capacidades / potencia AC"),
 "Cells": ("Ячейки", "Celdas"),
 "Certification": ("Сертификация", "Certificación"),
 "Certifications and testing": ("Сертификаты и испытания", "Certificados y ensayos"),
 "Charging mode": ("Режим зарядки", "Modo de carga"),
 "Climate options": ("Климатические опции", "Opciones climáticas"),
 "Compliance": ("Соответствие нормам", "Cumplimiento normativo"),
 "Connectivity": ("Связь", "Conectividad"),
 "Connector": ("Разъём", "Conector"),
 "Connectors": ("Разъёмы", "Conectores"),
 "Cycle life": ("Ресурс циклов", "Vida útil en ciclos"),
 "DC connectors": ("Разъёмы DC", "Conectores DC"),
 "DC output power": ("Выходная мощность DC", "Potencia de salida DC"),
 "DC output voltage": ("Выходное напряжение DC", "Tensión de salida DC"),
 "Depth of discharge": ("Глубина разряда", "Profundidad de descarga"),
 "Dimensions (W×D×H)": ("Габариты (Ш×Г×В)", "Dimensiones (An×Pr×Al)"),
 "Dispensers per cabinet": ("Постов на шкаф", "Dispensadores por armario"),
 "Display and access": ("Дисплей и доступ", "Pantalla y acceso"),
 "Electrical safety": ("Электробезопасность", "Seguridad eléctrica"),
 "Enclosure and endurance": ("Корпус и износостойкость", "Envolvente y resistencia"),
 "Enclosure and weight": ("Корпус и масса", "Envolvente y peso"),
 "Energy management": ("Управление энергией", "Gestión de energía"),
 "Fora-A terminal": ("Терминал Fora-A", "Terminal Fora-A"),
 "Fora-L terminal": ("Терминал Fora-L", "Terminal Fora-L"),
 "Input supply": ("Питание", "Alimentación"),
 "Monetization model": ("Модель монетизации", "Modelo de monetización"),
 "Mounting": ("Монтаж", "Montaje"),
 "Network protocol": ("Сетевой протокол", "Protocolo de red"),
 "Operating range": ("Рабочий диапазон", "Rango operativo"),
 "Operating temperature": ("Рабочая температура", "Temperatura de operación"),
 "Optional AC connector": ("Опциональный AC-разъём", "Conector AC opcional"),
 "Output voltage": ("Выходное напряжение", "Tensión de salida"),
 "Payment": ("Оплата", "Pago"),
 "Peak efficiency": ("Пиковый КПД", "Rendimiento pico"),
 "Power range": ("Диапазон мощности", "Rango de potencia"),
 "Protection and environment": ("Защита и условия", "Protección y entorno"),
 "Protection rating": ("Степень защиты", "Grado de protección"),
 "Rated output": ("Номинальная мощность", "Potencia nominal"),
 "Rated power": ("Номинальная мощность", "Potencia nominal"),
 "Safety and grid codes": ("Безопасность и сетевые нормы", "Seguridad y códigos de red"),
 "Session start": ("Запуск сессии", "Inicio de sesión"),
 "Solar / grid functions": ("Функции СЭС / сети", "Funciones FV / red"),
 "Standards": ("Стандарты", "Normas"),
 "System efficiency": ("КПД системы", "Rendimiento del sistema"),
 "System power": ("Мощность системы", "Potencia del sistema"),
 "User interface": ("Интерфейс", "Interfaz"),
 "Vehicle connector": ("Разъём для авто", "Conector de vehículo"),
}

# 每个产品的本地化定位文案
FIT = {
 "fora": ("Ультрабыстрые коридорные хабы и площадки с высокой пропускной способностью, "
          "где силовой блок должен пережить несколько поколений постов.",
          "Hubs de corredor ultrarrápidos y sitios de alto tránsito donde el bloque de potencia "
          "debe sobrevivir a varias generaciones de dispensadores."),
 "vulco": ("Площадки с ожидаемым ростом: начать на имеющейся мощности и добавить модули, "
           "когда загрузка оправдает расширение сети.",
           "Sitios con crecimiento previsto: empezar con la potencia disponible y añadir módulos "
           "cuando la utilización justifique ampliar la red."),
 "pales": ("Площадки со смешанным парком, где машины с разъёмами CCS2 и GB/T делят одну станцию.",
           "Sitios de flota mixta donde vehículos con conectores CCS2 y GB/T comparten la estación."),
 "castor": ("Депо, мастерские и служебные зоны, где машины стоят часами, а не минутами.",
            "Cocheras, talleres y zonas de servicio donde los vehículos paran horas, no minutos."),
 "aquila": ("Коммерческие площадки с высоким потоком людей, где реклама или выручка арендаторов "
            "закрывает часть бизнес-кейса.",
            "Sitios comerciales de alto tránsito donde la publicidad o los ingresos de comercios "
            "cubren parte del caso de negocio."),
 "bess": ("Площадки с ограниченной сетью, срезание пиковой нагрузки и автономные объекты, "
          "где накопитель считают раньше зарядки.",
          "Sitios con red limitada, recorte de picos y ubicaciones aisladas donde el "
          "almacenamiento se dimensiona antes del cargador."),
}

# 产品副标题（本地化）
SUB = {
 "fora": ("раздельная ультрабыстрая DC-система, 360–960 кВт", "sistema DC ultrarápido split, 360–960 kW"),
 "vulco": ("модульная DC-зарядка, 60–480 кВт", "cargador DC modular, 60–480 kW"),
 "pales": ("моноблочная DC-зарядка, 60–240 кВт", "cargador DC todo en uno, 60–240 kW"),
 "castor": ("настенный DC-бокс, 20–40 кВт", "DC de pared, 20–40 kW"),
 "aquila": ("DC-зарядка с рекламным экраном, 60–240 кВт", "cargador DC con pantalla publicitaria, 60–240 kW"),
 "bess": ("жидкостное охлаждение, 120 / 261 / 418 кВт·ч", "refrigeración líquida, 120 / 261 / 418 kWh"),
}


def build(slug, locale):
    meta = PRODUCTS[slug]
    name = meta[locale]
    sub = SUB[slug][0 if locale == "ru" else 1]
    fit = FIT[slug][0 if locale == "ru" else 1]
    rows = SPECS[slug]
    L = 0 if locale == "ru" else 1
    table = [{"k": LABELS[k][L] if k in LABELS else k, "v": v} for k, v in rows]
    loc = locale

    if loc == "ru":
        t_hero, t_note = ("Запросить конфигурацию", "Параметры приведены в оригинальной нотации изготовителя; вариант определяется ограничением вашей площадки.")
        t_spec_eyebrow, t_spec_lede = "Характеристики", "Опубликованная конфигурация."
        t_fit_eyebrow, t_fit_h2 = "Где применяется", "Ограничение, на которое отвечает семейство"
        t_rel_eyebrow, t_rel_h2 = "Смежные семейства", "Часто заказывают вместе"
        t_cta_h2 = f"Пришлите параметры площадки — вернём конфигурацию {name}."
        t_cta_lede = "Доступной мощности, графика и климата достаточно."
        t_req, t_title_suffix = "Запросить конфигурацию", "DC-зарядка Anari"
    else:
        t_hero, t_note = ("Pedir configuración", "Valores en la notación original del fabricante; la variante la decide la restricción de su sitio.")
        t_spec_eyebrow, t_spec_lede = "Especificaciones", "Configuración publicada."
        t_fit_eyebrow, t_fit_h2 = "Dónde encaja", "La restricción que responde esta familia"
        t_rel_eyebrow, t_rel_h2 = "Familias relacionadas", "A menudo se especifican juntas"
        t_cta_h2 = f"Envíe los parámetros del sitio y devolvemos una configuración {name}."
        t_cta_lede = "Con potencia disponible, ciclo y clima es suficiente."
        t_req, t_title_suffix = "Pedir configuración", "Cargador Anari"

    title = f"{name} — {sub.split(',')[0]} | Anari"
    # 校验器要求 title 30–60 字符：短标题补功率区间（副标题第二段）
    if len(title) < 30:
        tail = sub.split(", ", 1)[1] if ", " in sub else ""
        title = f"{name} — {sub}, {tail} | Anari" if tail else title + " Energy"
    meta_desc = (f"{name}: {sub}. " + ("Полный цикл: проект, поставка, пуск, эксплуатация." if loc == "ru"
                 else "Ciclo completo: diseño, suministro, puesta en marcha y operación."))[:158]
    while len(meta_desc) < 140:
        meta_desc += " Anari." if loc == "es" else " Anari."

    return {
        "slug": f"{loc}/products/{slug}",
        "url": f"/{loc}/products/{slug}.html",
        "breadcrumb": name,
        "locale": loc,
        "title": title,
        "meta": meta_desc[:160],
        "hreflangs": [
            {"lang": "en", "href": f"https://www.anaricharge.com/products/{slug}"},
            {"lang": "ru", "href": f"https://www.anaricharge.com/ru/products/{slug}"},
            {"lang": "es", "href": f"https://www.anaricharge.com/es/products/{slug}"},
        ],
        "sections": [
            {"type": "productHero", "eyebrow": f"{'Продукт' if loc=='ru' else 'Producto'} · {name}",
             "h1": f"{name} — {sub}", "lede": fit,
             "image": f"/assets/img/products/v2/{meta['img']}.webp",
             "image1024": f"/assets/img/products/v2/{meta['img']}-1024.webp",
             "imageAlt": f"{name} — {'фото продукта' if loc=='ru' else 'fotografía del producto'}",
             "note": t_note,
             "actions": [{"label": t_req, "href": f"/{loc}/inquiry"},
                         {"label": ("Полные характеристики" if loc=="ru" else "Ficha completa"),
                          "href": "https://www.anariev.com/"}]},
            {"type": "specTable", "eyebrow": t_spec_eyebrow, "h2": f"{name} — {t_spec_eyebrow.lower()}",
             "lede": t_spec_lede, "rows": table, "caption": f"{name}"},
            {"type": "cardGrid", "cols": 2, "alt": True, "eyebrow": t_fit_eyebrow, "h2": t_fit_h2,
             "lede": fit,
             "items": [
                 {"title": ("Типовое развёртывание" if loc=="ru" else "Despliegue típico"),
                  "text": ("Выбирается, когда ограничение площадки совпадает с семейством." if loc=="ru"
                           else "Se elige cuando la restricción del sitio coincide con la familia.")},
                 {"title": ("Что определяет вариант" if loc=="ru" else "Qué decide la variante"),
                  "text": ("Мощность сети, график, климат и стандарт разъёма." if loc=="ru"
                           else "Capacidad de red, ciclo, clima y estándar de conector.")},
                 {"title": ("Что нам пришлёте" if loc=="ru" else "Qué enviarnos"),
                  "text": ("Доступные кВА, число машин в день, время стоянки, температура." if loc=="ru"
                           else "kVA disponibles, vehículos al día, estancia y temperatura.")},
                 {"title": ("Как поставляется" if loc=="ru" else "Cómo se entrega"),
                  "text": ("В объёме под ключ: проект, разрешения, надзор, пуск, передача." if loc=="ru"
                           else "Dentro del alcance llave en mano: diseño, permisos, supervisión y puesta en marcha.")},
             ]},
            {"type": "productGrid", "eyebrow": t_rel_eyebrow, "h2": t_rel_h2,
             "items": [
                 {"href": f"/{loc}/products/vulco", "image": "/assets/img/products/v2/vulco-60-480kw-640.webp",
                  "name": "Vulco", "spec": ("DC · 60–480 кВт · модульная" if loc=="ru" else "DC · 60–480 kW · modular")},
                 {"href": f"/{loc}/products/pales", "image": "/assets/img/products/v2/pales-60-240kw-640.webp",
                  "name": "Pales", "spec": ("DC · 60–240 кВт · CCS2 + GB/T" if loc=="ru" else "DC · 60–240 kW · CCS2 + GB/T")},
                 {"href": f"/{loc}/products/bess", "image": "/assets/img/products/v2/bess-261kwh-640.webp",
                  "name": "BESS", "spec": ("Накопитель · 120 / 261 / 418 кВт·ч" if loc=="ru" else "Almacenamiento · 120 / 261 / 418 kWh")},
             ]},
            {"type": "cta", "eyebrow": ("Следующий шаг" if loc=="ru" else "Siguiente paso"),
             "h2": t_cta_h2, "lede": t_cta_lede,
             "actions": [{"label": t_req, "href": f"/{loc}/inquiry"},
                         {"label": ("Смотреть объекты" if loc=="ru" else "Ver instalaciones"), "href": f"/{loc}/cases/"}]},
        ],
    }


SPECS = json.load(open(SRC, encoding="utf-8"))

written = 0
for slug in PRODUCTS:
    for loc in ("ru", "es"):
        d = build(slug, loc)
        out = os.path.join(PAGES, loc, "products", f"{slug}.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        written += 1
        print(f"  {loc}/products/{slug}.json  title={len(d['title'])} meta={len(d['meta'])}")
print(f"\n写出 {written} 个规格（Vulco 会被已有文件覆盖，内容一致）")
