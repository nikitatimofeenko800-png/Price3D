import json           # Used for parsing and serializing configuration files, cache data, and API responses
import math           # Used for mathematical operations, rounding, and validating finite numbers
import os             # Used for interacting with the operating system (checking file paths, reading environment variables, and clearing the console)
import sys            # Used for handling system-level tasks and exiting the application safely
import urllib.request # Used for sending HTTP GET requests to fetch live currency exchange rates and material prices
from datetime import datetime # Used for generating and handling timestamps when saving and checking cache data

# ====================================================================
#  DEFAULT SETTINGS AND DATA
# ====================================================================

MATERIALS = [
    {"name": "PLA", "pricePerKg": 20.0, "density": 1.24},
    {"name": "PETG", "pricePerKg": 22.0, "density": 1.27},
    {"name": "ABS", "pricePerKg": 21.0, "density": 1.04},
    {"name": "ASA", "pricePerKg": 28.0, "density": 1.07},
    {"name": "TPU", "pricePerKg": 30.0, "density": 1.21},
    {"name": "Resin", "pricePerKg": 35.0, "density": 1.10}
]

CURRENCIES = [
    {"code": "USD", "name": "US Dollar"},
    {"code": "EUR", "name": "Euro"},
    {"code": "PLN", "name": "Polish Zloty"},
    {"code": "GBP", "name": "British Pound"},
    {"code": "CAD", "name": "Canadian Dollar"},
    {"code": "AUD", "name": "Australian Dollar"},
    {"code": "UAH", "name": "Ukrainian Hryvnia"}
]

CHANNELS = [
    {"name": "Direct sale (no fee)", "name_ru": "Прямая продажа (без комиссии)", "feePct": 0.0},
    {"name": "Etsy (approx.)", "name_ru": "Etsy (примерно)", "feePct": 9.5},
    {"name": "eBay (approx.)", "name_ru": "eBay (примерно)", "feePct": 13.0},
    {"name": "Amazon Handmade (approx.)", "name_ru": "Amazon Handmade (примерно)", "feePct": 15.0},
    {"name": "Custom", "name_ru": "Другой", "feePct": 10.0}
]

FINISHES = [
    {"name": "Raw print (supports removed only)", "name_ru": "Без обработки (только удаление поддержек)", "minutes": 10, "consumablesUsd": 0.2},
    {"name": "Sanded", "name_ru": "Шлифовка", "minutes": 30, "consumablesUsd": 0.6},
    {"name": "Sanded + primed", "name_ru": "Шлифовка + грунтовка", "minutes": 60, "consumablesUsd": 1.5},
    {"name": "Painted (basic)", "name_ru": "Покраска (базовая)", "minutes": 120, "consumablesUsd": 3.0},
    {"name": "Painted (detailed / display grade)", "name_ru": "Покраска (детальная / коллекционная)", "minutes": 240, "consumablesUsd": 6.0}
]

settings = {
    "language": "en", # "en" or "ru"
    "currency": "USD",
    "fx": 1.0,
    "material": 0,
    "materialPrice": 20.0,
    "supportPct": 10.0,
    "powerW": 120.0,
    "kwhPrice": 0.20,
    "printerCost": 300.0,
    "printerLifeH": 4000.0,
    "maintPerHour": 0.05,
    "laborRate": 8.0,
    "prepMin": 10.0,
    "packaging": 1.0,
    "shipping": 0.0,
    "failPct": 5.0,
    "profitMoney": 5.0,
    "channel": 1,
    "channelFee": 9.5,
    "royaltyPct": 0.0,
    "vatPct": 0.0,
    "targetHourly": 2.0
}

fx_table = None
online_status = "offline defaults"
sell_mode = False
use_color = "NO_COLOR" not in os.environ
ESC = "\033"

# ====================================================================
#  TRANSLATIONS DICTIONARY
# ====================================================================

TRANSLATIONS = {
    "en": {
        "goodbye": "Goodbye!",
        "info_config": "[Info] Created config.json.",
        "info_rates": "[OK] Exchange rates updated.",
        "warn_rates": "[Warning] Could not parse exchange rates.",
        "warn_rates_unav": "[Warning] Exchange rates unavailable.",
        "info_mats": "[OK] Material prices updated ({} materials).",
        "warn_mats": "[Warning] Could not parse material prices.",
        "info_cached": "[Info] Using cached data from cache.json.",
        "info_default": "[Info] Using built-in default prices.",
        "checking_online": "[Info] Checking online data (once at startup)...",
        "warn_no_rate": "[Warning] No exchange rate for {}.",
        "enter_rate": "Enter rate manually (1 USD = ? {})",
        "ok_rate": "[OK] 1 USD = {} {}",
        "currency_title": "Currency",
        "choose_currency": "Choose currency",
        "purpose_title": "What is this calculation for?",
        "p_self": "For myself / just for fun",
        "p_self_desc": "(cost to make only)",
        "p_sell": "To sell",
        "p_sell_desc": "(full pricing with profit)",
        "choose": "Choose",
        "mode_sell": "-> Selling mode",
        "mode_personal": "-> Personal mode",
        "model_name": "Figurine name",
        "material_title": "Material",
        "choose_material": "Choose material",
        "mat_price": "Material price, {}/kg",
        "model_title": "Model",
        "m_weight": "I know the weight (g) from the slicer",
        "m_vol": "I know the volume (cm3) and infill",
        "mode_label": "Mode",
        "w_grams": "Model weight, g",
        "v_cm3": "Model volume, cm3",
        "infill_pct": "Infill, %",
        "est_weight": "-> estimated weight: {} g",
        "time_unit_title": "Print Time Unit",
        "tu_hours": "Hours",
        "tu_min": "Minutes",
        "tu_sec": "Seconds",
        "choose_tu": "Choose time unit",
        "tu_val": "Print time value",
        "qty": "Quantity (batch size)",
        "finishing_title": "Finishing",
        "choose_fin": "Choose finishing",
        "post_min": "Post-processing time, min",
        "consumables": "Consumables (paint, glue, sandpaper), {}",
        "prep_min": "Prep time (slicing, bed, start), min",
        "labor_rate": "Your labor rate, {}/hour",
        "extras_title": "Extras",
        "paint_glue": "Paint / glue / other materials, {}",
        "count_time": "Count your own time as a cost?",
        "hands_on": "Hands-on time (prep + finishing), min",
        "time_val_cost": "Value of your time, {}/hour",
        "adv_edit": "\nEdit advanced settings (power, printer cost, wear, failure rate)?",
        "adv_title": "Advanced",
        "support_pct": "Extra material for supports/brim, %",
        "power_w": "Printer average power, W",
        "kwh_price": "Electricity price, {}/kWh",
        "printer_cost": "Printer cost, {}",
        "printer_life": "Printer lifetime, hours",
        "maint_hour": "Maintenance reserve, {}/print hour",
        "fail_pct": "Failure rate, %",
        "selling_title": "Selling",
        "packaging": "Packaging, {}",
        "shipping": "Shipping you pay (0 if customer pays), {}",
        "design_cost": "One-off design/model cost for this batch, {}",
        "sales_channel": "Sales channel",
        "channel_fee": "Channel fee, % of sale price",
        "royalty": "Licence/IP royalty, % of sale price",
        "vat": "VAT/sales tax, %",
        "profit_unit": "Profit you want per unit, {}",
        "min_profit_h": "Minimum profit per print hour, {}",
        "err_fees": "[Error] Fees + royalty are too high to price this item.",
        "shop_price": "\nPrice of a similar ready-made figurine in a shop (0 = skip), {}",
        "save_report": "\nSave report to a file?",
        "saved_ok": "[OK] Saved: {}",
        "err_save": "[Error] Could not save file: {}",
        "calc_another": "\nCalculate another figurine?",
        "banner_press": "Press Enter to accept the value in [brackets].\n",
        "lang_title": "Language / Язык",
        "choose_lang": "Choose language / Выберите язык",
        "react_rich": "[!] Wow, a rich person!",
        "react_profit": "[!] Oh wow!",
        "modify_ask": "\nDo you want to change anything before finishing?",
        "modify_title": "What would you like to change?",
        "mod_name": "Model name",
        "mod_mat": "Material / Material price",
        "mod_weight": "Weight / Volume",
        "mod_time": "Print time",
        "mod_profit": "Desired profit",
        "mod_none": "Nothing, proceed to report"
    },
    "ru": {
        "goodbye": "До свидания!",
        "info_config": "[Информация] создан файл config.json.",
        "info_rates": "[ОК] Курсы валют обновлены.",
        "warn_rates": "[Предупреждение] Не удалось разобрать курсы валют.",
        "warn_rates_unav": "[Предупреждение] Курсы валют недоступны.",
        "info_mats": "[ОК] Цены материалов обновлены (материалов: {}).",
        "warn_mats": "[Предупреждение] Не удалось разобрать цены материалов.",
        "info_cached": "[Информация] Используются кэшированные данные из cache.json.",
        "info_default": "[Информация] Используются встроенные цены по умолчанию.",
        "checking_online": "[Информация] Проверка онлайн-данных (один раз при запущенной программе)...",
        "warn_no_rate": "[Предупреждение] Нет курса обмена для валюты {}.",
        "enter_rate": "Введите курс вручную (1 USD = ? {})",
        "ok_rate": "[ОК] 1 USD = {} {}",
        "currency_title": "Валюта",
        "choose_currency": "Выберите валюту",
        "purpose_title": "Для чего выполняется этот расчет?",
        "p_self": "Для себя / просто так",
        "p_self_desc": "(только себестоимость печати)",
        "p_sell": "На продажу",
        "p_sell_desc": "(полный расчет с учетом прибыли)",
        "choose": "Выбор",
        "mode_sell": "-> Режим продаж",
        "mode_personal": "-> Личный режим",
        "model_name": "Название модели",
        "material_title": "Материал",
        "choose_material": "Выберите материал",
        "mat_price": "Цена материала, {}/кг",
        "model_title": "Модель",
        "m_weight": "Я знаю вес (г) из слайсера",
        "m_vol": "Я знаю объем (см3) и заполнение",
        "mode_label": "Режим",
        "w_grams": "Вес модели, г",
        "v_cm3": "Объем модели, см3",
        "infill_pct": "Заполнение, %",
        "est_weight": "-> расчетный вес: {} г",
        "time_unit_title": "Единица времени печати",
        "tu_hours": "Часы",
        "tu_min": "Минуты",
        "tu_sec": "Секунды",
        "choose_tu": "Выберите единицу времени",
        "tu_val": "Значение времени печати",
        "qty": "Количество (размер партии)",
        "finishing_title": "Постобработка",
        "choose_fin": "Выберите вариант отделки",
        "post_min": "Время постобработки, мин",
        "consumables": "Расходники (краска, клей, наждачка), {}",
        "prep_min": "Время подготовки (слайсинг, стол, старт), мин",
        "labor_rate": "Стоимость вашего труда, {}/час",
        "extras_title": "Дополнительно",
        "paint_glue": "Краска / клей / прочие материалы, {}",
        "count_time": "Учитывать ли ваше личное время в затратах?",
        "hands_on": "Затраченное время (подготовка + отделка), мин",
        "time_val_cost": "Ценность вашего времени, {}/час",
        "adv_edit": "\nИзменить расширенные настройки (мощность, стоимость принтера, износ, процент брака)?",
        "adv_title": "Расширенные настройки",
        "support_pct": "Доп. материал на поддержки/область, %",
        "power_w": "Средняя мощность принтера, Вт",
        "kwhPrice": "Цена электроэнергии, {}/кВтч",
        "printer_cost": "Стоимость принтера, {}",
        "printer_life": "Ресурс принтера, часов",
        "maint_hour": "Резерв на обслуживание, {}/час печати",
        "fail_pct": "Процент брака, %",
        "selling_title": "Продажи",
        "packaging": "Упаковка, {}",
        "shipping": "Доставка, которую оплачиваете вы (0, если платит покупатель), {}",
        "design_cost": "Разовые затраты на дизайн/модель для этой партии, {}",
        "sales_channel": "Канал продаж",
        "channel_fee": "Комиссия площадки, % от цены продажи",
        "royalty": "Лицензионные отчисления / роялти, %",
        "vat": "НДС / налог с продаж, %",
        "profit_unit": "Желаемая прибыль с одной единицы, {}",
        "min_profit_h": "Минимальная прибыль за час печати, {}",
        "err_fees": "[Ошибка] Комиссии и роялти слишком высоки для назначения цены.",
        "shop_price": "\nЦена похожей готовой фигурки в магазине (0 = пропустить), {}",
        "save_report": "\nСохранить отчет в файл?",
        "saved_ok": "[ОК] Сохранено: {}",
        "err_save": "[Ошибка] Не удалось сохранить файл: {}",
        "calc_another": "\nРассчитать другую модель?",
        "banner_press": "Нажмите Enter, чтобы принять значение в [скобках].\n",
        "lang_title": "Язык / Language",
        "choose_lang": "Выберите язык / Choose language",
        "react_rich": "[!] Ого, богач!",
        "react_profit": "[!] Ничего себе!",
        "modify_ask": "\nХотите что-то изменить перед завершением?",
        "modify_title": "Что именно вы хотите изменить?",
        "mod_name": "Название модели",
        "mod_mat": "Материал / Цена материала",
        "mod_weight": "Вес / Объем",
        "mod_time": "Время печати",
        "mod_profit": "Желаемая прибыль",
        "mod_none": "Ничего, перейти к отчету"
    }
}

def t(key):
    lang = settings["language"]
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    return TRANSLATIONS["en"].get(key, key)

# ====================================================================
#  COLORS AND TERMINAL UTILITIES
# ====================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def col(code, text):
    return f"{ESC}[{code}m{text}{ESC}[0m" if use_color else text

def cyan(t_text): return col("36", t_text)
def bcyan(t_text): return col("1;36", t_text)
def green(t_text): return col("32", t_text)
def bgreen(t_text): return col("1;32", t_text)
def yellow(t_text): return col("33", t_text)
def red(t_text): return col("31", t_text)
def bred(t_text): return col("1;31", t_text)
def magenta(t_text): return col("1;35", t_text)
def gray(t_text): return col("90", t_text)
def bold(t_text): return col("1", t_text)

def rep(ch, n):
    return ch * max(0, n)

def section(title):
    return f"\n{magenta('=== ' + title + ' ' + rep('=', 40 - len(title)))}"

# ====================================================================
#  NETWORK AND CACHE HANDLING
# ====================================================================

def http_get(url):
    if not url:
        return None
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Price3D/3.2"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as response:
            return response.read().decode("utf-8")
    except Exception:
        return None

def load_config():
    default_cfg = {
        "ratesUrl": "https://open.er-api.com/v6/latest/USD",
        "materialsUrl": "",
        "marketUrl": ""
    }
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "ratesUrl": data.get("ratesUrl", default_cfg["ratesUrl"]),
                    "materialsUrl": data.get("materialsUrl", ""),
                    "marketUrl": data.get("marketUrl", "")
                }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=2)
        print(cyan(t("info_config")))
    except Exception:
        pass
    return default_cfg

def save_cache():
    try:
        data = {
            "fetched": datetime.now().isoformat(),
            "rates": fx_table,
            "materials": MATERIALS
        }
        with open("cache.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_cache():
    global fx_table, MATERIALS
    try:
        if not os.path.exists("cache.json"):
            return False
        with open("cache.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("rates"):
                fx_table = data["rates"]
            if data.get("materials"):
                MATERIALS = data["materials"]
        return True
    except Exception:
        return False

def fetch_startup_data(cfg):
    global fx_table, online_status, MATERIALS
    print(cyan(t("checking_online")))
    got_rates = False
    got_materials = False

    rates_raw = http_get(cfg["ratesUrl"])
    if rates_raw:
        try:
            j = json.loads(rates_raw)
            if j.get("result") == "success" and j.get("rates"):
                fx_table = j["rates"]
                got_rates = True
                print(green(t("info_rates")))
        except Exception:
            print(yellow(t("warn_rates")))
    else:
        print(yellow(t("warn_rates_unav")))

    if cfg["materialsUrl"]:
        mat_raw = http_get(cfg["materialsUrl"])
        if mat_raw:
            try:
                j = json.loads(mat_raw)
                arr = j.get("materials", [])
                if arr:
                    new_mats = []
                    for m in arr:
                        if m.get("name") and m.get("pricePerKg", 0) > 0:
                            new_mats.append({
                                "name": str(m["name"]),
                                "pricePerKg": float(m["pricePerKg"]),
                                "density": float(m.get("density", 1.2))
                            })
                    if new_mats:
                        MATERIALS = new_mats
                        got_materials = True
                        print(green(t("info_mats").format(len(new_mats))))
            except Exception:
                print(yellow(t("warn_mats")))

    if got_rates or got_materials:
        save_cache()
        online_status = "live data" if got_rates else "live materials (rates from cache)"
    elif load_cache():
        online_status = "cached data"
        print(cyan(t("info_cached")))
    else:
        print(cyan(t("info_default")))
    print("")

def get_fx(code):
    if code == "USD":
        return 1.0
    if fx_table and code in fx_table:
        v = float(fx_table[code])
        if v > 0:
            return v
    return -1.0

# ====================================================================
#  INPUT HELPERS
# ====================================================================

def read_line(prompt_text):
    try:
        return input(prompt_text).strip()
    except (KeyboardInterrupt, EOFError):
        print(bgreen("\n" + t("goodbye")))
        sys.exit(0)

def ask_yes_no(question, default_val=False):
    suffix = " (Y/n)" if default_val else " (y/N)"
    ans = read_line(question + gray(suffix) + ": ").lower()
    if not ans:
        return default_val
    return ans in ["y", "yes", "д", "да"]

def prompt_string(label, default_val):
    val = read_line(cyan(label) + f" {gray('[' + default_val + ']')}: ")
    return val if val else default_val

def prompt_float(label, default_val, min_v=0.0, max_v=1e12):
    while True:
        val = read_line(cyan(label) + f" {gray('[' + fmt(default_val) + ']')}: ")
        if not val:
            return default_val
        val = val.replace(",", ".")
        try:
            n = float(val)
            if not math.isfinite(n) or n < min_v or n > max_v:
                print(red(f"  [Error] Allowed range: {fmt(min_v)} to {fmt(max_v)}."))
            else:
                return n
        except ValueError:
            print(red("  [Error] Please enter a valid number."))

def prompt_int(label, default_val, min_v, max_v):
    while True:
        val = read_line(cyan(label) + f" {gray('[' + str(default_val) + ']')}: ")
        if not val:
            return default_val
        try:
            n = int(val)
            if n < min_v or n > max_v:
                print(red(f"  [Error] Allowed range: {min_v} to {max_v}."))
            else:
                return n
        except ValueError:
            print(red("  [Error] Please enter a whole number."))

def fmt(v, decimals=2):
    try:
        if v != v or abs(v) == float('inf'):
            return "n/a"
        return f"{v:.{decimals}f}"
    except Exception:
        return "n/a"

def money(v):
    return f"{fmt(v)} {settings['currency']}"

# ====================================================================
#  CALCULATION LOGIC
# ====================================================================

def choose_language():
    global settings
    print(section(t("lang_title")))
    print(f"  {yellow('1.')} English")
    print(f"  {yellow('2.')} Русский")
    lang_idx = prompt_int(t("choose_lang"), 1, 1, 2)
    settings["language"] = "ru" if lang_idx == 2 else "en"
    print("")

def choose_currency():
    global settings
    print(section(t("currency_title")))
    for i, cur in enumerate(CURRENCIES):
        print(f"  {yellow(str(i + 1))}. {cur['code']} ({cur['name']})")
    
    cur_idx = prompt_int(t("choose_currency"), 1, 1, len(CURRENCIES)) - 1
    cur = CURRENCIES[cur_idx]["code"]
    
    fx = get_fx(cur)
    if fx < 0:
        print(yellow(t("warn_no_rate").format(cur)))
        fx = prompt_float(t("enter_rate").format(cur), 1.0, 0.0001)
    elif cur != "USD":
        print(green(t("ok_rate").format(fmt(fx, 4), cur)) + gray(f"  ({online_status})"))

    conversion = fx / settings["fx"]
    settings["currency"] = cur
    settings["fx"] = fx

    for key in (
        "materialPrice", "kwhPrice", "printerCost", "maintPerHour",
        "laborRate", "packaging", "targetHourly", "profitMoney"
    ):
        settings[key] *= conversion
    print("")

def calculate_costs(job):
    s = settings
    material = job["grams"] * (1 + s["supportPct"] / 100) * s["materialPrice"] / 1000
    electricity = job["hours"] * (s["powerW"] / 1000) * s["kwhPrice"]
    depreciation = job["hours"] * (s["printerCost"] / s["printerLifeH"])
    maintenance = job["hours"] * s["maintPerHour"]
    labor = (job["workMin"] / 60) * job["laborRate"]

    production = material + electricity + depreciation + maintenance + labor + job["consumables"]
    with_failures = production / (1 - s["failPct"] / 100)
    failure_reserve = with_failures - production

    design = job["design"] / job["qty"]
    unit_cost = with_failures + job["packaging"] + job["shipping"] + design
    break_even = unit_cost / (1 - job["feePct"] / 100) * (1 + job["vatPct"] / 100)

    return {
        "material": material,
        "electricity": electricity,
        "depreciation": depreciation,
        "maintenance": maintenance,
        "labor": labor,
        "consumables": job["consumables"],
        "failureReserve": failure_reserve,
        "packaging": job["packaging"],
        "shipping": job["shipping"],
        "design": design,
        "unitCost": unit_cost,
        "breakEven": break_even
    }

def make_tier(name, target_profit, c, j):
    raw = (c["unitCost"] + target_profit) / (1 - j["feePct"] / 100) * (1 + j["vatPct"] / 100)
    price = round_price(raw)
    net = price / (1 + j["vatPct"] / 100)
    profit = net * (1 - j["feePct"] / 100) - c["unitCost"]
    return {
        "name": name,
        "targetProfit": target_profit,
        "price": price,
        "profit": profit,
        "perHour": profit / j["hours"] if j["hours"] > 0 else 0,
        "realMargin": (profit / net * 100) if net > 0 else 0
    }

def build_tiers(c, j):
    target_profit = max(
        settings["profitMoney"],
        settings["targetHourly"] * j["hours"]
    )
    return [
        make_tier("Budget", target_profit * 0.5, c, j),
        make_tier("Recommended", target_profit, c, j),
        make_tier("Premium", target_profit * 1.5, c, j)
    ]

def round_price(v):
    p = int(v) + 0.99
    if p < v:
        p += 1.0
    return p

# ====================================================================
#  REPORTS AND GRAPHICS
# ====================================================================

def cost_bars(c):
    items = [
        ("Material" if settings["language"]=="en" else "Материал", c["material"]),
        ("Electricity" if settings["language"]=="en" else "Электричество", c["electricity"]),
        ("Printer depreciation" if settings["language"]=="en" else "Амортизация принтера", c["depreciation"]),
        ("Maintenance" if settings["language"]=="en" else "Обслуживание", c["maintenance"]),
        ("Your time" if settings["language"]=="en" else "Ваше время", c["labor"]),
        ("Paint / consumables" if settings["language"]=="en" else "Краска / расходники", c["consumables"]),
        ("Failure reserve" if settings["language"]=="en" else "Резерв на брак", c["failureReserve"]),
        ("Packaging" if settings["language"]=="en" else "Упаковка", c["packaging"]),
        ("Shipping" if settings["language"]=="en" else "Доставка", c["shipping"]),
        ("Design (per unit)" if settings["language"]=="en" else "Дизайн (на шт.)", c["design"])
    ]
    b = []
    for label, val in items:
        if val <= 0.0001:
            continue
        share = val / c["unitCost"]
        n = round(share * 20)
        bar = "#" * n + "." * (20 - n)
        if share >= 0.5:
            colored_bar = red(bar)
        elif share >= 0.25:
            colored_bar = yellow(bar)
        else:
            colored_bar = green(bar)
        b.append(f"{label:<22} {fmt(val):>9} {colored_bar} {fmt(share * 100, 0):>3}%\n")
    return "".join(b)

def row_line(label, val_str, color_code=""):
    v = f"{val_str:>20}"
    if color_code:
        v = col(color_code, v)
    return f"{label:<26} {v}\n"

def build_hobby_report(name, mat, j, c, shop_price):
    b = []
    line = bcyan("==============================================")
    thin = gray("----------------------------------------------")

    title_text = "COST TO MAKE (FOR MYSELF)" if settings["language"]=="en" else "СЕБЕСТОИМОСТЬ (ДЛЯ СЕБЯ)"
    money_where = "WHERE THE MONEY GOES" if settings["language"]=="en" else "КУДА УХОДЯТ ДЕНЬГИ"
    model_lbl = "Model" if settings["language"]=="en" else "Модель"
    mat_lbl = "Material" if settings["language"]=="en" else "Материал"
    weight_lbl = "Weight" if settings["language"]=="en" else "Вес"
    time_lbl = "Print time" if settings["language"]=="en" else "Время печати"
    source_lbl = "Data source" if settings["language"]=="en" else "Источник данных"
    tot_cost_lbl = "TOTAL COST TO MAKE" if settings["language"]=="en" else "ИТОГО СЕБЕСТОИМОСТЬ"
    gram_cost = "Cost per gram" if settings["language"]=="en" else "Стоимость за грамм"
    hour_cost = "Cost per print hour" if settings["language"]=="en" else "Стоимость за час печати"
    print_vs_buy = "PRINT vs BUY" if settings["language"]=="en" else "ПЕЧАТЬ против ПОКУПКИ"
    shop_ready = "Ready-made in a shop" if settings["language"]=="en" else "Готовое в магазине"
    save_print = "You save by printing" if settings["language"]=="en" else "Экономия при печати"
    extra_cost = "Extra cost vs buying" if settings["language"]=="en" else "Переплата по сравнению с покупкой"

    b.append(line + "\n")
    b.append(bcyan(f"          {title_text}") + "\n")
    b.append(line + "\n")
    b.append(row_line(model_lbl, name))
    b.append(row_line(mat_lbl, mat["name"]))
    b.append(row_line(weight_lbl, f"{fmt(j['grams'])} g"))
    b.append(row_line(time_lbl, f"{fmt(j['hours'])} h"))
    b.append(row_line(source_lbl, online_status))
    b.append(thin + "\n")
    b.append(bold(money_where) + "\n")
    b.append(cost_bars(c))
    b.append(thin + "\n")
    b.append(row_line(tot_cost_lbl, money(c["unitCost"]), "1;32"))
    b.append(row_line(gram_cost, f"{fmt(c['unitCost'] / j['grams'], 3)} {settings['currency']}"))
    b.append(row_line(hour_cost, money(c["unitCost"] / j["hours"])))
    b.append(line + "\n")

    if shop_price > 0:
        diff = shop_price - c["unitCost"]
        b.append(bold(print_vs_buy) + "\n")
        b.append(row_line(shop_ready, money(shop_price)))
        if diff > 0:
            b.append(row_line(save_print, money(diff), "1;32"))
        else:
            b.append(row_line(extra_cost, money(-diff), "1;31"))
        b.append(thin + "\n")
    return "".join(b)

def build_sell_report(name, mat, j, c, tiers, market):
    b = []
    line = bcyan("==============================================")
    thin = gray("----------------------------------------------")
    rec = tiers[1]

    rep_title = "PRICING REPORT" if settings["language"]=="en" else "ОТЧЕТ ПО ЦЕНООБРАЗОВАНИЮ"
    model_lbl = "Model" if settings["language"]=="en" else "Модель"
    mat_lbl = "Material" if settings["language"]=="en" else "Материал"
    weight_lbl = "Weight" if settings["language"]=="en" else "Вес"
    time_lbl = "Print time" if settings["language"]=="en" else "Время печати"
    batch_lbl = "Batch size" if settings["language"]=="en" else "Размер партии"
    source_lbl = "Data source" if settings["language"]=="en" else "Источник данных"
    unit_cost_lbl = "COST PER UNIT" if settings["language"]=="en" else "ЗАТРАТЫ НА ЕДИНИЦУ"
    tot_cost_lbl = "TOTAL COST" if settings["language"]=="en" else "ИТОГО ЗАТРАТЫ"
    be_lbl = "Break-even price" if settings["language"]=="en" else "Цена безубыточности"
    fees_lbl = "Fees + royalty" if settings["language"]=="en" else "Комиссии + роялти"
    price_opt = "PRICE OPTIONS" if settings["language"]=="en" else "ЦЕНОВЫЕ ВАРИАНТЫ"
    tier_hdr = "Tier                  Price     Profit   Profit/h" if settings["language"]=="en" else "Уровень               Цена      Прибыль  Приб./ч"
    rec_price_lbl = "RECOMMENDED PRICE" if settings["language"]=="en" else "РЕКОМЕНДОВАННАЯ ЦЕНА"
    profit_unit_lbl = "Profit per unit" if settings["language"]=="en" else "Прибыль с единицы"

    b.append(line + "\n")
    b.append(bcyan(f"               {rep_title}") + "\n")
    b.append(line + "\n")
    b.append(row_line(model_lbl, name))
    b.append(row_line(mat_lbl, mat["name"]))
    b.append(row_line(weight_lbl, f"{fmt(j['grams'])} g"))
    b.append(row_line(time_lbl, f"{fmt(j['hours'])} h"))
    b.append(row_line(batch_lbl, f"{j['qty']} pcs"))
    b.append(row_line(source_lbl, online_status))
    b.append(thin + "\n")
    b.append(bold(unit_cost_lbl) + "\n")
    b.append(cost_bars(c))
    b.append(thin + "\n")
    b.append(row_line(tot_cost_lbl, money(c["unitCost"]), "1;33"))
    b.append(row_line(be_lbl, money(c["breakEven"])))
    b.append(row_line(fees_lbl, f"{fmt(j['feePct'], 1)} %"))
    b.append(line + "\n")

    b.append(bold(price_opt) + "\n")
    b.append(tier_hdr + "\n")
    for t in tiers:
        t_name = t["name"]
        if settings["language"] == "ru":
            if t_name == "Budget": t_name = "Бюджетный"
            elif t_name == "Recommended": t_name = "Рекомендуемый"
            elif t_name == "Premium": t_name = "Премиум"
        row_str = f"{t_name:<13} {fmt(t['price']):>11} {fmt(t['profit']):>10} {fmt(t['perHour']):>9}"
        if t["name"] == "Recommended":
            row_str = bgreen(row_str)
        b.append(row_str + "\n")
    b.append(thin + "\n")
    b.append(row_line(rec_price_lbl, money(rec["price"]), "1;32"))
    b.append(row_line(profit_unit_lbl, money(rec["profit"]), "32" if rec["profit"] > 0 else "1;31"))
    b.append(line + "\n")
    return "".join(b)

def safe_file_name(name):
    import re
    clean = re.sub(r'[^a-zA-Z0-9_\-]+', '_', name)
    return clean if clean else "figurine"

# ====================================================================
#  MAIN LOOP
# ====================================================================

def banner():
    print(bcyan("=============================================="))
    print(bcyan("   ") + bold("Price3D") )
    print(bcyan("=============================================="))
    print(gray(t("banner_press")))

def ask_purpose():
    global sell_mode
    print(bold(t("purpose_title")))
    print("  " + yellow("1") + f". {t('p_self')}  " + gray(f"({t('p_self_desc')})"))
    print("  " + yellow("2") + f". {t('p_sell')}                    " + gray(f"({t('p_sell_desc')})"))
    p = prompt_int(t("choose"), 2 if sell_mode else 1, 1, 2)
    sell_mode = (p == 2)
    print(green(t("mode_sell") if sell_mode else t("mode_personal")))
    print("")

def run_calculation():
    name = prompt_string(t("model_name"), "Figurine")

    print(section(t("material_title")))
    for i, m in enumerate(MATERIALS):
        print(f"  {yellow(str(i + 1))}. {m['name']}  " + gray(f"(~{fmt(m['pricePerKg'] * settings['fx'])} {settings['currency']}/kg)"))
    
    mat_idx = prompt_int(t("choose_material"), settings["material"] + 1, 1, len(MATERIALS)) - 1
    if mat_idx != settings["material"]:
        settings["material"] = mat_idx
        settings["materialPrice"] = MATERIALS[mat_idx]["pricePerKg"] * settings["fx"]
    
    mat = MATERIALS[settings["material"]]
    settings["materialPrice"] = prompt_float(t("mat_price").format(settings['currency']), settings["materialPrice"])

    # Реакция на дорогой пластик (> 50)
    if settings["materialPrice"] > 50.0:
        print(red(t("react_rich")))

    print(section(t("model_title")))
    print("  " + yellow("1") + f". {t('m_weight')}")
    print("  " + yellow("2") + f". {t('m_vol')}")
    mode = prompt_int(t("mode_label"), 1, 1, 2)
    
    if mode == 1:
        grams = prompt_float(t("w_grams"), 50.0, 0.01)
    else:
        vol = prompt_float(t("v_cm3"), 40.0, 0.01)
        infill = prompt_float(t("infill_pct"), 20.0, 1.0, 100.0)
        effective = 0.30 + 0.70 * (infill / 100.0)
        grams = vol * effective * mat["density"]
        print(gray(f"  {t('est_weight').format(fmt(grams))}"))
    
    print(section(t("time_unit_title")))
    print("  " + yellow("1") + f". {t('tu_hours')}")
    print("  " + yellow("2") + f". {t('tu_min')}")
    print("  " + yellow("3") + f". {t('tu_sec')}")
    time_unit = prompt_int(t("choose_tu"), 1, 1, 3)
    time_val = prompt_float(t("tu_val"), 5.0, 0.001)

    if time_unit == 1:
        hours = time_val
    elif time_unit == 2:
        hours = time_val / 60.0
    else:
        hours = time_val / 3600.0

    qty = prompt_int(t("qty"), 1, 1, 100000) if sell_mode else 1

    work_min = 0.0
    labor_rate = 0.0
    consumables = 0.0

    if sell_mode:
        print(section(t("finishing_title")))
        for i, fin in enumerate(FINISHES):
            fin_name = fin["name_ru"] if settings["language"] == "ru" else fin["name"]
            print(f"  {yellow(str(i + 1))}. {fin_name}")
        fin_choice = FINISHES[prompt_int(t("choose_fin"), 2, 1, len(FINISHES)) - 1]
        post_min = prompt_float(t("post_min"), fin_choice["minutes"])
        consumables = prompt_float(t("consumables").format(settings['currency']), fin_choice["consumablesUsd"] * settings["fx"])
        settings["prepMin"] = prompt_float(t("prep_min"), settings["prepMin"])
        settings["laborRate"] = prompt_float(t("labor_rate").format(settings['currency']), settings["laborRate"])
        work_min = settings["prepMin"] / qty + post_min
        labor_rate = settings["laborRate"]
    else:
        print(section(t("extras_title")))
        consumables = prompt_float(t("paint_glue").format(settings['currency']), 0.0)
        if ask_yes_no(t("count_time"), False):
            minutes = prompt_float(t("hands_on"), 40.0)
            settings["laborRate"] = prompt_float(t("time_val_cost").format(settings['currency']), settings["laborRate"])
            work_min = minutes
            labor_rate = settings["laborRate"]

    if ask_yes_no(t("adv_edit"), False):
        print(section(t("adv_title")))
        settings["supportPct"] = prompt_float(t("support_pct"), settings["supportPct"])
        settings["powerW"] = prompt_float(t("power_w"), settings["powerW"])
        settings["kwhPrice"] = prompt_float(t("kwh_price").format(settings['currency']), settings["kwhPrice"])
        settings["printerCost"] = prompt_float(t("printer_cost").format(settings['currency']), settings["printerCost"])
        settings["printerLifeH"] = prompt_float(t("printer_life"), settings["printerLifeH"], 1.0)
        settings["maintPerHour"] = prompt_float(t("maint_hour").format(settings['currency']), settings["maintPerHour"])
        settings["failPct"] = prompt_float(t("fail_pct"), settings["failPct"], 0.0, 90.0)

    shop_price = 0.0

    if sell_mode:
        print(section(t("selling_title")))
        packaging_val = prompt_float(t("packaging").format(settings['currency']), settings["packaging"])
        settings["packaging"] = packaging_val
        shipping_val = prompt_float(t("shipping").format(settings['currency']), settings["shipping"])
        settings["shipping"] = shipping_val
        design_val = prompt_float(t("design_cost").format(settings['currency']), 0.0)

        for i, ch in enumerate(CHANNELS):
            ch_name = ch["name_ru"] if settings["language"] == "ru" else ch["name"]
            print(f"  {yellow(str(i + 1))}. {ch_name}  " + gray(f"({fmt(ch['feePct'], 1)}%)"))
        ch_idx = prompt_int(t("sales_channel"), settings["channel"] + 1, 1, len(CHANNELS)) - 1
        if ch_idx != settings["channel"]:
            settings["channel"] = ch_idx
            settings["channelFee"] = CHANNELS[ch_idx]["feePct"]
        
        settings["channelFee"] = prompt_float(t("channel_fee"), settings["channelFee"], 0.0, 60.0)
        settings["royaltyPct"] = prompt_float(t("royalty"), settings["royaltyPct"], 0.0, 50.0)
        settings["vatPct"] = prompt_float(t("vat"), settings["vatPct"], 0.0, 50.0)
        settings["profitMoney"] = prompt_float(t("profit_unit").format(settings['currency']), settings["profitMoney"])
        
        # Реакция на большую прибыль (>= 100)
        if settings["profitMoney"] >= 100.0:
            print(red(t("react_profit")))

        settings["targetHourly"] = prompt_float(t("min_profit_h").format(settings['currency']), settings["targetHourly"])

        fee_pct_val = settings["channelFee"] + settings["royaltyPct"]
        vat_pct_val = settings["vatPct"]

        if fee_pct_val >= 90:
            print(bred(t("err_fees")))
            return
    else:
        shop_price = prompt_float(t("shop_price").format(settings['currency']), 0.0)
        packaging_val = 0.0
        shipping_val = 0.0
        design_val = 0.0
        fee_pct_val = 0.0
        vat_pct_val = 0.0

    # Интерактивный цикл проверки/изменения перед выводом
    while ask_yes_no(t("modify_ask"), False):
        print(section(t("modify_title")))
        print(f"  {yellow('1.')} {t('mod_name')} ({name})")
        print(f"  {yellow('2.')} {t('mod_mat')} ({mat['name']}, {fmt(settings['materialPrice'])} {settings['currency']})")
        print(f"  {yellow('3.')} {t('mod_weight')} ({fmt(grams)} g)")
        print(f"  {yellow('4.')} {t('mod_time')} ({fmt(hours)} h)")
        if sell_mode:
            print(f"  {yellow('5.')} {t('mod_profit')} ({fmt(settings['profitMoney'])} {settings['currency']})")
            print(f"  {yellow('6.')} {t('mod_none')}")
            mod_choice = prompt_int(t("choose"), 6, 1, 6)
        else:
            print(f"  {yellow('5.')} {t('mod_none')}")
            mod_choice = prompt_int(t("choose"), 5, 1, 5)

        if mod_choice == 1:
            name = prompt_string(t("model_name"), name)
        elif mod_choice == 2:
            settings["materialPrice"] = prompt_float(t("mat_price").format(settings['currency']), settings["materialPrice"])
            if settings["materialPrice"] > 50.0:
                print(red(t("react_rich")))
        elif mod_choice == 3:
            grams = prompt_float(t("w_grams"), grams, 0.01)
        elif mod_choice == 4:
            time_val = prompt_float(t("tu_val"), hours, 0.001)
            hours = time_val
        elif mod_choice == 5 and sell_mode:
            settings["profitMoney"] = prompt_float(t("profit_unit").format(settings['currency']), settings["profitMoney"])
            if settings["profitMoney"] >= 100.0:
                print(red(t("react_profit")))
        else:
            break

    job = {
        "grams": grams,
        "hours": hours,
        "qty": qty,
        "workMin": work_min,
        "laborRate": labor_rate,
        "consumables": consumables,
        "design": design_val,
        "packaging": packaging_val,
        "shipping": shipping_val,
        "feePct": fee_pct_val,
        "vatPct": vat_pct_val
    }

    costs = calculate_costs(job)
    tiers = build_tiers(costs, job) if sell_mode else []

    report = build_sell_report(name, mat, job, costs, tiers, None) if sell_mode else build_hobby_report(name, mat, job, costs, shop_price)

    print("\n" + report)

    if ask_yes_no(t("save_report"), False):
        # Автоматическое создание папки all prices для чеков
        os.makedirs("all prices", exist_ok=True)
        file_name = os.path.join("all prices", safe_file_name(name) + "_report.txt")
        try:
            global use_color
            use_color = False
            plain_report = build_sell_report(name, mat, job, costs, tiers, None) if sell_mode else build_hobby_report(name, mat, job, costs, shop_price)
            use_color = "NO_COLOR" not in os.environ
            
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(plain_report)
            print(green(t("saved_ok").format(file_name)))
        except Exception as e:
            print(bred(t("err_save").format(e)))

def main():
    cfg = load_config()
    fetch_startup_data(cfg)
    
    first = True
    while True:
        clear_screen()
        banner()
        if not first:
            pass
        first = False
        choose_language()
        choose_currency()
        ask_purpose()
        run_calculation()
        if not ask_yes_no(t("calc_another"), False):
            break
    print(bgreen("\n" + t("goodbye")))

if __name__ == "__main__":
    main()
