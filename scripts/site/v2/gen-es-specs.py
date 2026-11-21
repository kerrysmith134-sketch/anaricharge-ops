#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 ES 本地化 v2 页面规格（西语文案，结构对齐英文 v2 页面）。"""
import json
import os

OUT = "scripts/site/v2/pages/es"
os.makedirs(OUT, exist_ok=True)
IMG = "/assets/img/"
PIMG = IMG + "products/v2/"
PAD = " Entrega llave en mano: estudio de emplazamiento, diseño, equipos, permisos y operación."


def w(name, d):
    if len(d["meta"]) < 140:
        d["meta"] = (d["meta"] + PAD).strip()[:160]
    slug = d["url"].strip("/").split("/")[-1]
    en_path = "/" if name == "index" else "/%s/" % slug
    d["locale"] = "es"
    d["hreflangs"] = [
        {"lang": "en", "href": "https://www.anaricharge.com" + en_path},
        {"lang": "ru", "href": "https://www.anaricharge.com/ru/" + ("" if name == "index" else slug + "/")},
        {"lang": "es", "href": "https://www.anaricharge.com" + d["url"]},
    ]
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"  {name}.json  title={len(d['title'])} meta={len(d['meta'])}")


def cta(h2, lede):
    return {"type": "cta", "eyebrow": "Siguiente paso", "h2": h2, "lede": lede,
            "actions": [{"label": "Hablar del proyecto", "href": "/es/inquiry"},
                        {"label": "Ver proyectos", "href": "/es/cases/"}]}


w("index", {
    "slug": "es/index", "url": "/es/", "breadcrumb": "Inicio",
    "title": "Infraestructura de carga llave en mano | Anari",
    "meta": "Diseñamos, construimos y operamos estaciones de carga en 22 países: desde la decisión del emplazamiento hasta la operación de la red.",
    "sections": [
        {"type": "hero", "eyebrow": "Carga llave en mano · sistemas de energía · operación",
         "h1": "Un negocio de carga listo para operar.",
         "lede": "Desde la decisión del emplazamiento y el diseño del sistema hasta el equipo, el montaje y la operación inteligente: un único socio responsable en 22 países.",
         "image": IMG + "v2/hero-solutions-1920.webp",
         "credit": "Instalación en servicio · cochera de 12 unidades, Chequia",
         "actions": [{"label": "Planificar el proyecto", "href": "/journey/"},
                     {"label": "Ver instalaciones", "href": "/es/cases/"}],
         "facts": [{"value": "22", "label": "países atendidos"},
                   {"value": "100+", "label": "clientes desde 2021"},
                   {"value": "20–960 kW", "label": "rango DC"},
                   {"value": "120–418 kWh", "label": "BESS refrigerado por líquido"}]},
        {"type": "sceneGrid", "eyebrow": "Elija el escenario", "h2": "¿Qué está construyendo?",
         "lede": "Cuatro contextos operativos, cuatro restricciones distintas. De ellas se deriva todo el diseño.",
         "items": [
             {"href": "/es/solutions/", "image": IMG + "v2/scene-commercial-640.webp", "title": "Carga comercial", "text": "Corredores y emplazamientos urbanos: el plazo lo marca la conexión, no el cargador."},
             {"href": "/es/solutions/", "image": IMG + "v2/scene-fleet-640.webp", "title": "Flotas y cocheras", "text": "Ventanas nocturnas y ciclos de servicio: el sitio debe aguantar la peor noche del año."},
             {"href": "/es/solutions/", "image": IMG + "v2/scene-offgrid-640.webp", "title": "FV, almacenamiento y aislado", "text": "Cuando la red no entrega la potencia, primero se almacena."},
             {"href": "/es/solutions/", "image": IMG + "v2/scene-destination-640.webp", "title": "Destino y oficina", "text": "La estancia larga cambia la decisión: importa el control de acceso, no los kW."}]},
        {"type": "steps", "alt": True, "eyebrow": "Un solo responsable", "h2": "Cinco etapas desde el terreno hasta la red operativa",
         "lede": "Cinco etapas, cada una con un responsable y un entregable. No hay que coordinar cinco proveedores.",
         "items": [
             {"no": "01", "title": "Emplazamiento y mercado", "text": "Si el sitio y el mercado sostienen el caso de negocio."},
             {"no": "02", "title": "Diseño del sistema", "text": "Potencia, almacenamiento, layout y esquema unifilar."},
             {"no": "03", "title": "Equipos", "text": "Familias y potencias elegidas contra la restricción real."},
             {"no": "04", "title": "Permisos y puesta en marcha", "text": "Tramitación, aprobación de la utility, montaje y pruebas."},
             {"no": "05", "title": "Operación y crecimiento", "text": "Monitorización, mantenimiento y generación de demanda."}],
         "action": {"label": "Cómo funciona la entrega llave en mano", "href": "/es/turnkey/"}},
        {"type": "productGrid", "eyebrow": "Equipos", "h2": "Hardware para cada parte de la red",
         "lede": "DC de 60 a 960 kW, AC de 7,4 a 22 kW y almacenamiento refrigerado por líquido.",
         "items": [
             {"href": "/es/products/fora", "image": PIMG + "fora-split-960kw-640.webp", "name": "Fora", "spec": "DC · 360–960 kW · split"},
             {"href": "/es/products/vulco", "image": PIMG + "vulco-60-480kw-640.webp", "name": "Vulco", "spec": "DC · 60–480 kW · modular"},
             {"href": "/es/products/pales", "image": PIMG + "pales-60-240kw-640.webp", "name": "Pales", "spec": "DC · 60–240 kW · CCS2 + GB/T"},
             {"href": "/es/products/castor", "image": PIMG + "castor-20-40kw-640.webp", "name": "Castor", "spec": "DC de pared · 20–40 kW"},
             {"href": "/es/products/bess", "image": PIMG + "bess-261kwh-640.webp", "name": "BESS", "spec": "Almacenamiento · 120 / 261 / 418 kWh"},
            ],
         "action": {"label": "Comparar familias", "href": "/es/products/"}},
        cta("Cuéntenos el emplazamiento. Le diremos qué es realmente construible.",
            "La capacidad disponible, el clima, el ciclo de servicio y el modelo de negocio bastan para una primera evaluación."),
    ]})

w("solutions", {
    "slug": "es/solutions", "url": "/es/solutions/", "breadcrumb": "Soluciones",
    "title": "Soluciones de carga por tipo de sitio | Anari Energy",
    "meta": "Cuatro soluciones ordenadas por la restricción que decide el diseño: corredores públicos, flotas y cocheras, FV con almacenamiento, destino y oficina.",
    "sections": [
        {"type": "hero", "eyebrow": "Soluciones", "h1": "El emplazamiento decide el diseño, no el catálogo.",
         "lede": "Un corredor, una cochera de autobuses y un aparcamiento de hotel fallan por motivos distintos. Cada solución parte de la restricción que de verdad va a condicionar el proyecto.",
         "image": IMG + "v2/hero-solutions-1920.webp",
         "credit": "Instalación de corredor · DC de dos pistolas, Asia Central",
         "actions": [{"label": "Elegir escenario", "href": "/es/solutions/#contexts"},
                     {"label": "Ver proyectos", "href": "/es/cases/"}]},
        {"type": "steps", "alt": True, "eyebrow": "Cómo se elige la solución", "h2": "Cuatro preguntas antes de elegir equipo",
         "lede": "Todas las páginas de solución las responden en el mismo orden, para que dos emplazamientos se comparen por restricciones y no por marketing.",
         "items": [
             {"no": "01", "title": "Potencia disponible", "text": "Los kVA que el sitio puede tomar y lo que aprobará la utility."},
             {"no": "02", "title": "Estancia y ciclo", "text": "Cuánto tiempo paran los vehículos y cuántas sesiones exige el pico."},
             {"no": "03", "title": "Clima", "text": "Calor, monzón, polvo o frío: qué componente pierde potencia primero."},
             {"no": "04", "title": "Modelo operativo", "text": "Quién opera, quién repara y qué ocurre en la peor noche."}],
         "action": {"label": "Alcance llave en mano", "href": "/es/turnkey/"}},
        {"type": "cardGrid", "cols": 2, "eyebrow": "Lo que no prometemos", "h2": "Límites del alcance, por escrito",
         "lede": "El valor de una entrega llave en mano es que el límite se escribe antes de empezar, no se negocia cuando aparece el problema.",
         "items": [
             {"title": "Incluido", "text": "Estudio de sitio y mercado, diseño y esquema unifilar, suministro, permisos y trámites, supervisión de montaje, puesta en marcha y traspaso."},
             {"title": "No incluido", "text": "Compra del suelo, decisiones comerciales de tarifa y financiación a largo plazo: quedan con usted, y lo decimos antes del anticipo."},
             {"title": "Aparte", "text": "La generación de demanda posterior es un programa separado, no una promesa dentro del alcance."},
             {"title": "Control de cambios", "text": "Si cambia la restricción, el diseño cambia con un delta escrito, no con una sustitución silenciosa."}]},
        cta("Cuéntenos el sitio y le diremos cuál de los cuatro escenarios es el suyo.",
            "Con la capacidad disponible, el patrón de estancia y el clima basta para situar el proyecto."),
    ]})

w("products", {
    "slug": "es/products", "url": "/es/products/", "breadcrumb": "Productos",
    "title": "Equipos de carga DC, AC y BESS | Anari Energy",
    "meta": "Carga rápida DC de 20 a 960 kW, cargadores AC de 3,5 a 22 kW y almacenamiento refrigerado por líquido de 120 a 418 kWh.",
    "sections": [
        {"type": "hero", "eyebrow": "Equipos", "h1": "Equipos para cada parte de la red de carga.",
         "lede": "Nueve familias de DC, AC y almacenamiento. La familia se elige por la restricción del sitio — margen de crecimiento, ciclo, clima o potencia disponible — no por la cifra de kW.",
         "image": IMG + "v2/hero-products-1920.webp", "credit": "Línea de producción ANARI antes de embarque",
         "actions": [{"label": "Comparar familias", "href": "#families"},
                     {"label": "Pedir configuración", "href": "/es/inquiry"}],
         "facts": [{"value": "20–960 kW", "label": "rango DC"},
                   {"value": "3,5–22 kW", "label": "rango AC"},
                   {"value": "120–418 kWh", "label": "BESS líquido"},
                   {"value": "≥96%", "label": "rendimiento pico DC modular"}]},
        {"type": "productGrid", "eyebrow": "Familias", "h2": "Primero la restricción, después la familia",
         "lede": "Los rangos se solapan a propósito: cuatro familias cubren 60–240 kW porque la decisión entre ellas es margen, estándar de conector y envolvente.",
         "items": [
             {"href": "/es/products/fora", "image": PIMG + "fora-split-960kw-640.webp", "name": "Fora", "spec": "DC · 360–960 kW · ultracarga"},
             {"href": "/es/products/vulco", "image": PIMG + "vulco-60-480kw-640.webp", "name": "Vulco", "spec": "DC · 60–480 kW · modular"},
             {"href": "/es/products/pales", "image": PIMG + "pales-60-240kw-640.webp", "name": "Pales", "spec": "DC · 60–240 kW · CCS2 y GB/T"},
             {"href": "/es/products/castor", "image": PIMG + "castor-20-40kw-640.webp", "name": "Castor", "spec": "DC de pared · 20–40 kW"},
             {"href": "/es/products/aquila", "image": PIMG + "aquila-ads-60-240kw-640.webp", "name": "Aquila", "spec": "DC + pantalla publicitaria · 60–240 kW"}],
         "action": {"label": "Ver catálogo", "href": "/es/products/vulco"}},
        {"type": "steps", "eyebrow": "Lógica de selección", "h2": "Cómo se elige la familia",
         "lede": "Es el orden que usamos en proyectos y el que modela la calculadora de ROI.",
         "items": [
             {"no": "01", "title": "Margen de crecimiento", "text": "Si la flota crecerá, una plataforma modular supera a un armario fijo."},
             {"no": "02", "title": "Estándar de conector", "text": "CCS2, GB/T o ambos: las flotas mixtas reducen la elección rápido."},
             {"no": "03", "title": "Envolvente y clima", "text": "Calor, polvo y monzón definen refrigeración y sellado."},
             {"no": "04", "title": "Capacidad de red", "text": "Si el transformador no crece, el almacenamiento entra antes que el cargador."},
             {"no": "05", "title": "Modelo operativo", "text": "Los sitios remotos necesitan módulos reparables, no armarios sellados."}],
         "action": {"label": "Calculadora de ROI", "href": "/tools/charging-station-roi"}},
        cta("Envíe los parámetros del sitio y devolvemos una configuración.",
            "Con la potencia disponible, el ciclo y el clima se reduce la familia en un solo intercambio."),
    ]})

w("cases", {
    "slug": "es/cases", "url": "/es/cases/", "breadcrumb": "Proyectos",
    "title": "Proyectos de carga ejecutados y verificables | Anari",
    "meta": "Proyectos en servicio con contexto de sitio, configuración y resultado: cocheras, corredores, clima cálido y frío en 22 países.",
    "sections": [
        {"type": "hero", "eyebrow": "Proyectos", "h1": "Cada afirmación del sitio debe poder comprobarse con una instalación.",
         "lede": "9 casos documentados: contexto del sitio, configuración instalada y qué ocurrió tras la puesta en marcha, incluidas las condiciones que el equipo tuvo que soportar.",
         "image": IMG + "v2/hero-cases-1920.webp", "credit": "Corredor · DC de dos pistolas, Asia Central",
         "actions": [{"label": "Ver casos", "href": "#cases"}, {"label": "Hablar de un sitio similar", "href": "/es/inquiry"}],
         "facts": [{"value": "22", "label": "países atendidos"}, {"value": "100+", "label": "clientes desde 2021"},
                   {"value": "45 °C+", "label": "ambiente más exigente"}, {"value": "−30 °C", "label": "sitio más frío"}]},
        {"type": "sceneGrid", "eyebrow": "Filtrar por dificultad", "h2": "Qué fue difícil en cada proyecto",
         "lede": "Los casos se agrupan por el problema que había que resolver, porque eso es lo que los hace comparables con su sitio.",
         "items": [
             {"href": "/es/cases/bus-depot-czechia", "image": IMG + "v2/scene-fleet-640.webp", "title": "Cochera de 12 unidades", "text": "Chequia · ciclo nocturno, 12 unidades DC, marquesina."},
             {"href": "/es/cases/jordan-160kw", "image": IMG + "v2/case-jordan-640.webp", "title": "160 kW a 45 °C+", "text": "Jordania · potencia nominal sostenida con calor extremo."},
             {"href": "/es/cases/cambodia-240kw", "image": IMG + "v2/case-cambodia-640.webp", "title": "240 kW en monzón", "text": "Camboya · control de entrada de agua y dimensionado limitado por red."},
             {"href": "/es/cases/romania-highway", "image": IMG + "v2/case-romania-640.webp", "title": "Área de servicio", "text": "Rumanía · primera entrega, puesta en marcha con soporte en sitio."},
             {"href": "/es/cases/cold-climate", "image": IMG + "v2/case-cold-640.webp", "title": "Clima frío", "text": "Hasta −30 °C · comportamiento de carga y calefacción de envolvente."},
             {"href": "/es/cases/off-grid-pv-ess", "image": IMG + "v2/scene-offgrid-640.webp", "title": "FV + almacenamiento aislado", "text": "Sin conexión utilizable · almacenamiento dimensionado antes del cargador."}]},
        {"type": "cardGrid", "cols": 2, "alt": True, "eyebrow": "Cómo leer un caso", "h2": "Los mismos cuatro hechos en cada proyecto",
         "lede": "Un caso solo sirve si declara las condiciones: qué necesitaba el sitio, qué se instaló, qué restricción decidió el diseño y el resultado medido. Las páginas de caso detalladas están en inglés.",
         "items": [
             {"title": "Contexto del sitio", "text": "País, tipo de sitio y capacidad de red disponible."},
             {"title": "Configuración", "text": "Familias, potencias, estándar de conector y almacenamiento."},
             {"title": "Restricción", "text": "El único factor que decidió el diseño."},
             {"title": "Resultado", "text": "Qué ocurrió tras la puesta en marcha, incluidos los límites."}]},
        cta("¿Tiene un sitio como estos?", "Envíe país, capacidad disponible y cómo se operará el sitio: responderemos con el caso comparable más cercano."),
    ]})

w("turnkey", {
    "slug": "es/turnkey", "url": "/es/turnkey/", "breadcrumb": "Llave en mano",
    "title": "Entrega de carga llave en mano | Anari Energy",
    "meta": "Un alcance responsable desde el terreno hasta un operador en marcha: estudio de sitio, diseño, equipos, permisos, puesta en marcha y operación.",
    "sections": [
        {"type": "hero", "eyebrow": "Llave en mano", "h1": "Del terreno a un negocio de carga en operación.",
         "lede": "Siete líneas de trabajo y ocho etapas de entrega con un solo equipo, para que el estudio del sitio, el diseño eléctrico, el equipo y los permisos no se señalen entre sí cuando algo se retrasa.",
         "image": IMG + "v2/hero-turnkey-1920.webp", "credit": "Soporte de puesta en marcha · sitio DC de 180 kW, Etiopía",
         "actions": [{"label": "Las ocho etapas", "href": "#stages"}, {"label": "Pedir evaluación", "href": "/es/inquiry"}],
         "facts": [{"value": "7", "label": "líneas de trabajo"}, {"value": "8", "label": "etapas de entrega"},
                   {"value": "22", "label": "países atendidos"}, {"value": "100+", "label": "clientes desde 2021"}]},
        {"type": "steps", "eyebrow": "Las ocho etapas", "h2": "Cada etapa tiene un responsable y un entregable",
         "lede": "Una etapa termina cuando su resultado existe y se acepta, no cuando se emite la factura. Es el mismo orden en el que un proyecto falla si se salta una etapa.",
         "items": [
             {"no": "01", "title": "Mercado y sitio", "text": "Si el mercado y el sitio sostienen el caso de negocio."},
             {"no": "02", "title": "Red y capacidad", "text": "Los kVA que la utility aprobará y lo que cuesta conseguirlos."},
             {"no": "03", "title": "Diseño del sistema", "text": "Potencia, almacenamiento, layout y esquema unifilar."},
             {"no": "04", "title": "Selección de equipos", "text": "Familias y potencias contra la restricción que condiciona."},
             {"no": "05", "title": "Permisos y aprobación", "text": "Solicitudes, inspecciones y documentación que abre la obra."}],
         "action": {"label": "Cómo se elige el sitio", "href": "/turnkey/ai-site-selection"}},
        {"type": "steps", "alt": True, "eyebrow": "Las ocho etapas (continuación)", "h2": "Construir, energizar, entregar, operar",
         "lede": "Las últimas etapas son donde los proyectos pierden dinero en silencio: calidad del montaje, primera energización y quién responde la primera mala noche.",
         "items": [
             {"no": "06", "title": "Obra civil y eléctrica", "text": "Cimentaciones, cableado, trabajos de transformador y supervisión de montaje."},
             {"no": "07", "title": "Puesta en marcha", "text": "Energización, pruebas de protocolo, bucle de pago y primeras sesiones."},
             {"no": "08", "title": "Traspaso a operación", "text": "Monitorización, modelo de mantenimiento, repuestos y escalado."},
             {"no": "→", "title": "Operación", "text": "Monitorización con ANARI OS y mantenimiento N-Tech tras el traspaso."}],
         "action": {"label": "Cómo ANARI OS opera el sitio", "href": "/turnkey/anari-os"}},
        {"type": "cardGrid", "cols": 2, "eyebrow": "Límites del alcance", "h2": "Qué está incluido y qué no",
         "lede": "El valor del alcance llave en mano es que el límite se escribe antes de empezar y no se negocia cuando aparece el problema.",
         "items": [
             {"title": "Incluido", "text": "Estudio de sitio y mercado, diseño y unifilar, suministro de equipos, permisos y trámites, supervisión de montaje, puesta en marcha y traspaso."},
             {"title": "No incluido", "text": "Compra de suelo, decisiones comerciales de tarifa y financiación: quedan de su lado y lo decimos antes del anticipo."},
             {"title": "Aparte", "text": "La generación de demanda posterior es un programa separado, para no inflar el alcance con promesas."},
             {"title": "Control de cambios", "text": "Si cambia la restricción — red, clima, ciclo — el diseño cambia con un delta escrito."}]},
        cta("Envíe el sitio. Le diremos qué etapa será la difícil.",
            "Una evaluación corta identifica la etapa que probablemente retrase el proyecto: casi siempre la conexión de red."),
    ]})

w("agents", {
    "slug": "es/agents", "url": "/es/agents/", "breadcrumb": "Plataforma e IA",
    "title": "ANARI OS y el ecosistema de agentes IA | Anari",
    "meta": "ANARI OS opera sitios de carga reales. Alrededor, 18 agentes en cuatro capas, etiquetados como en producción, piloto o plan.",
    "sections": [
        {"type": "hero", "eyebrow": "Plataforma e IA", "h1": "Una operación, no un vendedor de hardware.",
         "lede": "El hardware es lo que se puede fotografiar. Lo que mantiene un sitio generando ingresos es la capa que está por encima: monitorización, triaje de fallos, despacho de mantenimiento y el trabajo comercial posterior.",
         "image": IMG + "v2/hero-agents-1920.webp", "credit": "Unidad en servicio · clima frío, Finlandia",
         "actions": [{"label": "Qué funciona hoy", "href": "#status"}, {"label": "Hablar con nosotros", "href": "/es/inquiry"}],
         "facts": [{"value": "18", "label": "agentes en el ecosistema"},
                   {"value": "4 h → 90 s", "label": "respuesta de soporte, N-Tech"},
                   {"value": "5×", "label": "eficiencia de filtrado, N-SDR"},
                   {"value": "desde Q4 2025", "label": "N-Tech en producción"}]},
        {"type": "cardGrid", "cols": 2, "eyebrow": "Estado antes que promesas", "h2": "Lo que realmente funciona hoy",
         "lede": "Casi todas las webs describen su ecosistema como si todo estuviera activo. Aquí el reparto honesto: en producción, en piloto y en plan.",
         "items": [
             {"status": "Live", "title": "Monitorización y soporte remoto", "text": "Telemetría de flota, triaje de alarmas e intervención remota; respuesta medida en segundos, no en horas."},
             {"status": "Live", "title": "Mantenimiento N-Tech", "text": "Diagnóstico y despacho en producción desde Q4 2025 — respuesta de soporte 4 hours to 90 seconds."},
             {"status": "Live", "title": "N-SDR generación de demanda", "text": "Filtrado de salientes para operadores tras la puesta en marcha: 5x lead-screening efficiency."},
             {"status": "Pilot", "title": "Agentes de diseño", "text": "Apoyo al estudio de sitio y al diseño, con firma humana de la especificación final."},
             {"status": "Pilot", "title": "Formación y conocimiento", "text": "Formación de operadores y generación de documentación, en prueba con nuevos traspasos."},
             {"status": "Planned", "title": "Comercio autónomo de energía", "text": "Arbitraje tarifario y respuesta a la demanda. Diseñado, no desplegado: hoy no lo vendemos como función."}]},
        {"type": "steps", "alt": True, "eyebrow": "Cómo encajan las cuatro capas", "h2": "Captar → entregar → operar → crecer",
         "lede": "Los agentes se agrupan por función de negocio, no por tecnología. Una capa solo sirve si la anterior produjo algo real.",
         "items": [
             {"no": "01", "title": "Captar", "text": "Análisis de mercado, filtrado de oportunidades y estudio comercial."},
             {"no": "02", "title": "Entregar", "text": "Estudio de sitio, apoyo al diseño y seguimiento de permisos."},
             {"no": "03", "title": "Operar", "text": "Monitorización, triaje, despacho y formación de operadores."},
             {"no": "04", "title": "Crecer", "text": "Generación de demanda y aumento de utilización."},
             {"no": "05", "title": "Orquestar", "text": "Planificación entre agentes con aprobación humana en todo lo irreversible."}]},
        cta("Vea la capa de operación contra su propio sitio.",
            "Si ya opera cargadores, la comparación útil no es una lista de funciones, sino el tiempo de fallo a reparación."),
    ]})

w("who-we-serve", {
    "slug": "es/who-we-serve", "url": "/es/who-we-serve/", "breadcrumb": "A quién servimos",
    "title": "A quién servimos: contratistas, flotas y CPO | Anari",
    "meta": "Cuatro tipos de cliente en mercados emergentes: contratistas de ingeniería, operadores de flota, energía e inmobiliario y CPO independientes.",
    "sections": [
        {"type": "hero", "eyebrow": "A quién servimos", "h1": "Usted aporta el sitio, la flota, el capital o el plan.",
         "lede": "Cuatro puntos de partida y un destino: un negocio de carga propio y operado. El alcance es el mismo; cambia el activo que ya tiene.",
         "image": IMG + "v2/hero-serving-1920.webp", "credit": "Corredor · DC de dos pistolas, Asia Central",
         "actions": [{"label": "Encontrar su perfil", "href": "#profiles"}, {"label": "Hablar con nosotros", "href": "/es/inquiry"}],
         "facts": [{"value": "35–40%", "label": "de demanda · ingeniería"},
                   {"value": "25–30%", "label": "de demanda · flotas"},
                   {"value": "15–20%", "label": "de demanda · energía"},
                   {"value": "10–15%", "label": "de demanda · CPO independientes"}]},
        {"type": "sceneGrid", "eyebrow": "Los cuatro perfiles", "h2": "Un destino, distintas líneas de salida",
         "lede": "Los porcentajes son la mezcla de demanda del programa llave en mano en mercados emergentes, no un ranking de importancia.",
         "items": [
             {"href": "/who-we-serve/engineering-contractors", "image": IMG + "v2/scene-offgrid-640.webp", "title": "Contratistas de ingeniería", "text": "Usted construye y sabe ejecutar obra: necesita línea de producto, permisos y capa de operación."},
             {"href": "/who-we-serve/fleet-operators", "image": IMG + "v2/scene-fleet-640.webp", "title": "Operadores de flota", "text": "Usted controla vehículos y patio: necesita el diseño que aguante su peor noche."},
             {"href": "/who-we-serve/energy-real-estate", "image": IMG + "v2/scene-destination-640.webp", "title": "Energía e inmobiliario", "text": "Usted tiene suelo, potencia o inquilinos: necesita el modelo que haga rentable construir."},
             {"href": "/who-we-serve/cpo-entrepreneurs", "image": IMG + "v2/scene-commercial-640.webp", "title": "CPO independientes", "text": "Usted tiene el plan y el mercado: necesita todo lo que hay entre decidir el sitio y operar."}]},
        {"type": "cardGrid", "cols": 2, "alt": True, "eyebrow": "Qué cambia por perfil", "h2": "La brecha es distinta, el alcance no",
         "lede": "Las siete líneas de trabajo siguen en alcance. Cambia dónde fallará primero el proyecto y, por tanto, qué etapa recibe más atención.",
         "items": [
             {"title": "Contratistas", "text": "Fuerte en obra civil y eléctrica. Brecha habitual: especificación de producto, permisos y operación tras el traspaso."},
             {"title": "Flotas", "text": "Fuerte en vehículos y patrón operativo. Brecha: capacidad de red para el pico y ruta de migración cuando cambia la flota."},
             {"title": "Energía e inmobiliario", "text": "Fuerte en suelo, potencia e inquilinos. Brecha: supuestos de utilización y modelo comercial, que deciden el retorno."},
             {"title": "CPO independientes", "text": "Fuerte en conocimiento de mercado y relaciones. Brecha: todas las etapas técnicas a la vez — para eso existe el alcance llave en mano."}]},
        cta("Díganos cuál de los cuatro es y qué tiene ya.",
            "La conversación útil empieza por el activo que controla: sitio, flota, capital o plan."),
    ]})

print("ES 规格生成完成")

# ------------------------------------------------------------------ Herramientas (índice localizado)
w("tools", {
    "slug": "es/tools",
    "url": "/es/tools/",
    "breadcrumb": "Herramientas",
    "title": "Calculadoras de carga y almacenamiento | Anari",
    "meta": "Cuatro calculadoras gratuitas en el navegador sin registro: retorno de la estación, coste del almacenamiento, selección de clase y TCO a la vida útil.",
    "sections": [
        {
            "type": "hero",
            "eyebrow": "Herramientas",
            "h1": "Haga los números antes de hablar con nosotros.",
            "lede": "Cuatro calculadoras funcionan en el navegador, sin registro y sin enviar datos. Los supuestos están abiertos y el resultado se puede revisar; si quiere una lectura de ingeniero, se pide aparte.",
            "image": IMG + "v2/scene-commercial-1280.webp",
            "credit": "Cálculo en el navegador · sin registro",
            "facts": [
                {"value": "4", "label": "calculadoras"},
                {"value": "0", "label": "registros"},
                {"value": "—", "label": "los datos no salen del dispositivo"},
            ],
            "actions": [
                {"label": "Abrir calculadora de ROI", "href": "/tools/charging-station-roi"},
                {"label": "Hablar del proyecto", "href": "/es/inquiry"},
            ],
        },
        {
            "type": "cardGrid",
            "cols": 2,
            "eyebrow": "Qué calcula cada una",
            "h2": "Cuatro preguntas distintas, cuatro herramientas",
            "lede": "La interfaz de las calculadoras está en inglés: no traducimos las etiquetas técnicas de los campos para no deformar el significado. Las fórmulas y los supuestos son los mismos en todos los idiomas.",
            "items": [
                {"title": "Retorno de la estación", "text": "Ingresos, costes operativos y plazo de retorno con su utilización y tarifa. Responde sobre todo a «¿tiene sentido?»."},
                {"title": "Coste de propiedad del almacenamiento", "text": "Arbitraje pico/valle, ciclos y vida útil: cuánto cuesta cada kWh que pasa por el sistema."},
                {"title": "Selección de clase de equipo", "text": "Tres preguntas sobre escenario, tiempo de estancia y presupuesto dan una banda de potencia y una clase de equipo — como primer filtro, no como decisión final."},
                {"title": "TCO a la vida útil", "text": "Coste completo a 5–15 años: equipo, electricidad, mantenimiento y sustitución, para comparar opciones con honestidad."},
            ],
        },
        {
            "type": "steps",
            "eyebrow": "Cómo usarlas",
            "h2": "Primero sus cifras, después nuestra revisión",
            "lede": "La herramienta sirve para llegar con datos, no con intuiciones. Eso acelera también nuestra respuesta.",
            "items": [
                {"no": "01", "title": "Reúna tres números", "text": "Tarifa y estructura de demanda, utilización esperada y capacidad disponible en el sitio."},
                {"no": "02", "title": "Calcule y mire los supuestos", "text": "La calculadora muestra qué supuestos producen el resultado — son los que conviene discutir."},
                {"no": "03", "title": "Pida revisión de ingeniero", "text": "El botón «Send these numbers to an engineer» traslada su cálculo a la consulta junto con los datos de entrada."},
            ],
        },
        cta("Envíe el cálculo y le añadimos revisión de ingeniero.",
            "No vendemos cifras. Si los supuestos no aguantan la revisión, lo decimos antes de firmar."),
    ],
})

# ------------------------------------------------------------------ Mercados (índice localizado)
w("markets", {
    "slug": "es/markets",
    "url": "/es/markets/",
    "breadcrumb": "Mercados",
    "title": "22 países con estaciones ya operando | Anari Energy",
    "meta": "22 países con proyectos de carga entregados en seis regiones: calor, red débil, frío, monzón. Los mercados objetivo no se dibujan en el mapa: solo lo entregado.",
    "sections": [
        {
            "type": "hero",
            "eyebrow": "Cobertura",
            "h1": "22 países donde las estaciones ya funcionan.",
            "lede": "El mapa muestra solo proyectos entregados y transferidos. Los países de la lista objetivo no aparecen hasta que la obra está entregada — si no, el mapa se convierte en una promesa.",
            "image": IMG + "v2/hero-markets-1920.webp",
            "credit": "Base: Natural Earth (dominio público); la misma proyección coloca los puntos de país",
            "facts": [
                {"value": "22", "label": "países con proyectos"},
                {"value": "6", "label": "regiones"},
                {"value": "45 °C+", "label": "calor de diseño"},
                {"value": "−30 °C", "label": "frío de diseño"},
            ],
            "actions": [
                {"label": "Ver casos", "href": "/es/cases/"},
                {"label": "Hablar del mercado", "href": "/es/inquiry"},
            ],
        },
        {
            "type": "cardGrid",
            "cols": 2,
            "eyebrow": "Seis regiones",
            "h2": "La región la define la restricción, no la distancia",
            "lede": "En cada región el diseño resuelve la misma restricción limitante — de ella dependen especificación y plazo.",
            "items": [
                {"title": "Oriente Medio · 6 países", "text": "Jordania, Líbano, Israel, Arabia Saudí, EAU, Omán. Calor por encima de 45 °C y sitios limitados por el transformador."},
                {"title": "Cáucaso y Asia Central · 6", "text": "Georgia, Armenia, Kazajistán y otros. Frío hasta −30 °C y redes que hay que calcular antes de elegir equipo."},
                {"title": "Europa · 4", "text": "Rumanía, Chequia, Bulgaria, Italia. Requisitos AFIR y secuencia de aprobaciones antes de energizar."},
                {"title": "Asia · 2", "text": "Camboya, China. Monzón, polvo y necesidad de mantener la potencia nominal con red limitada."},
                {"title": "África · 3", "text": "Etiopía, Kenia, El Salvador — mercados donde la política creó demanda antes de que existiera la infraestructura."},
                {"title": "Latinoamérica · 1", "text": "Perú. Aparcamientos públicos con estancia larga y potencia de red limitada."},
            ],
        },
        {
            "type": "steps",
            "eyebrow": "Cómo elegimos mercado",
            "h2": "Cuatro condiciones sin las cuales no tomamos el país",
            "lede": "Un país entra en la lista cuando se cumplen las cuatro; si no, el proyecto acaba con equipos parados.",
            "items": [
                {"no": "01", "title": "Demanda", "text": "¿Hay vehículos reales y propietarios dispuestos a pagar, y no solo un objetivo político?"},
                {"no": "02", "title": "Red", "text": "¿Se puede aprobar la potencia y cuánto cuesta la conexión?"},
                {"no": "03", "title": "Servicio", "text": "¿Quién acude la primera mala noche y en cuántas horas?"},
                {"no": "04", "title": "Certificación", "text": "Conectores y normas que el país acepta sin excepciones."},
            ],
        },
        cta("Díganos país y sitio y revisamos las condiciones.",
            "Si el mercado no está en la lista, la respuesta es honesta: diremos qué debe aparecer para que aparezca."),
    ],
})
