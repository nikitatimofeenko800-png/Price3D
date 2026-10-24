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
    {"name": "Direct sale (no fee)", "feePct": 0.0},
    {"name": "Etsy (approx.)", "feePct": 9.5},
    {"name": "eBay (approx.)", "feePct": 13.0},
    {"name": "Amazon Handmade (approx.)", "feePct": 15.0},
    {"name": "Custom", "feePct": 10.0}
]

FINISHES = [
    {"name": "Raw print (supports removed only)", "minutes": 10, "consumablesUsd": 0.2},
    {"name": "Sanded", "minutes": 30, "consumablesUsd": 0.6},
    {"name": "Sanded + primed", "minutes": 60, "consumablesUsd": 1.5},
    {"name": "Painted (basic)", "minutes": 120, "consumablesUsd": 3.0},
    {"name": "Painted (detailed / display grade)", "minutes": 240, "consumablesUsd": 6.0}
]

settings = {
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
#  COLORS AND TERMINAL UTILITIES
# ====================================================================

def clear_screen():
    # Clear console screen based on operating system to save resources and clean old output
    os.system('cls' if os.name == 'nt' else 'clear')

def col(code, text):
    return f"{ESC}[{code}m{text}{ESC}[0m" if use_color else text

def cyan(t): return col("36", t)
def bcyan(t): return col("1;36", t)
def green(t): return col("32", t)
def bgreen(t): return col("1;32", t)
def yellow(t): return col("33", t)
def red(t): return col("31", t)
def bred(t): return col("1;31", t)
def magenta(t): return col("1;35", t)
def gray(t): return col("90", t)
def bold(t): return col("1", t)

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
        print(cyan("[Info] Created config.json."))
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
    print(cyan("[Info] Checking online data (once at startup)..."))
    got_rates = False
    got_materials = False

    rates_raw = http_get(cfg["ratesUrl"])
    if rates_raw:
        try:
            j = json.loads(rates_raw)
            if j.get("result") == "success" and j.get("rates"):
                fx_table = j["rates"]
                got_rates = True
                print(green("[OK] Exchange rates updated."))
        except Exception:
            print(yellow("[Warning] Could not parse exchange rates."))
    else:
        print(yellow("[Warning] Exchange rates unavailable."))

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
                        print(green(f"[OK] Material prices updated ({len(new_mats)} materials)."))
            except Exception:
                print(yellow("[Warning] Could not parse material prices."))

    if got_rates or got_materials:
        save_cache()
        online_status = "live data" if got_rates else "live materials (rates from cache)"
    elif load_cache():
        online_status = "cached data"
        print(cyan("[Info] Using cached data from cache.json."))
    else:
        print(cyan("[Info] Using built-in default prices."))
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
        print(bgreen("\nGoodbye!"))
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

def choose_currency():
    global settings
    print(section("Currency"))
    for i, cur in enumerate(CURRENCIES):
        print(f"  {yellow(str(i + 1))}. {cur['code']} ({cur['name']})")
    
    cur_idx = prompt_int("Choose currency", 1, 1, len(CURRENCIES)) - 1
    cur = CURRENCIES[cur_idx]["code"]
    
    fx = get_fx(cur)
    if fx < 0:
        print(yellow(f"[Warning] No exchange rate for {cur}."))
        fx = prompt_float(f"Enter rate manually (1 USD = ? {cur})", 1.0, 0.0001)
    elif cur != "USD":
        print(green(f"[OK] 1 USD = {fmt(fx, 4)} {cur}") + gray(f"  ({online_status})"))

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
        ("Material", c["material"]),
        ("Electricity", c["electricity"]),
        ("Printer depreciation", c["depreciation"]),
        ("Maintenance", c["maintenance"]),
        ("Your time", c["labor"]),
        ("Paint / consumables", c["consumables"]),
        ("Failure reserve", c["failureReserve"]),
        ("Packaging", c["packaging"]),
        ("Shipping", c["shipping"]),
        ("Design (per unit)", c["design"])
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

    b.append(line + "\n")
    b.append(bcyan("          COST TO MAKE (FOR MYSELF)") + "\n")
    b.append(line + "\n")
    b.append(row_line("Model", name))
    b.append(row_line("Material", mat["name"]))
    b.append(row_line("Weight", f"{fmt(j['grams'])} g"))
    b.append(row_line("Print time", f"{fmt(j['hours'])} h"))
    b.append(row_line("Data source", online_status))
    b.append(thin + "\n")
    b.append(bold("WHERE THE MONEY GOES") + "\n")
    b.append(cost_bars(c))
    b.append(thin + "\n")
    b.append(row_line("TOTAL COST TO MAKE", money(c["unitCost"]), "1;32"))
    b.append(row_line("Cost per gram", f"{fmt(c['unitCost'] / j['grams'], 3)} {settings['currency']}"))
    b.append(row_line("Cost per print hour", money(c["unitCost"] / j["hours"])))
    b.append(line + "\n")

    if shop_price > 0:
        diff = shop_price - c["unitCost"]
        b.append(bold("PRINT vs BUY") + "\n")
        b.append(row_line("Ready-made in a shop", money(shop_price)))
        if diff > 0:
            b.append(row_line("You save by printing", money(diff), "1;32"))
        else:
            b.append(row_line("Extra cost vs buying", money(-diff), "1;31"))
        b.append(thin + "\n")
    return "".join(b)

def build_sell_report(name, mat, j, c, tiers, market):
    b = []
    line = bcyan("==============================================")
    thin = gray("----------------------------------------------")
    rec = tiers[1]

    b.append(line + "\n")
    b.append(bcyan("               PRICING REPORT") + "\n")
    b.append(line + "\n")
    b.append(row_line("Model", name))
    b.append(row_line("Material", mat["name"]))
    b.append(row_line("Weight", f"{fmt(j['grams'])} g"))
    b.append(row_line("Print time", f"{fmt(j['hours'])} h"))
    b.append(row_line("Batch size", f"{j['qty']} pcs"))
    b.append(row_line("Data source", online_status))
    b.append(thin + "\n")
    b.append(bold("COST PER UNIT") + "\n")
    b.append(cost_bars(c))
    b.append(thin + "\n")
    b.append(row_line("TOTAL COST", money(c["unitCost"]), "1;33"))
    b.append(row_line("Break-even price", money(c["breakEven"])))
    b.append(row_line("Fees + royalty", f"{fmt(j['feePct'], 1)} %"))
    b.append(line + "\n")

    b.append(bold("PRICE OPTIONS") + "\n")
    b.append("Tier                  Price     Profit   Profit/h\n")
    for t in tiers:
        row_str = f"{t['name']:<13} {fmt(t['price']):>11} {fmt(t['profit']):>10} {fmt(t['perHour']):>9}"
        if t["name"] == "Recommended":
            row_str = bgreen(row_str)
        b.append(row_str + "\n")
    b.append(thin + "\n")
    b.append(row_line("RECOMMENDED PRICE", money(rec["price"]), "1;32"))
    b.append(row_line("Profit per unit", money(rec["profit"]), "32" if rec["profit"] > 0 else "1;31"))
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
    print(gray("Press Enter to accept the value in [brackets].\n"))

def ask_purpose():
    global sell_mode
    print(bold("What is this calculation for?"))
    print("  " + yellow("1") + ". For myself / just for fun  " + gray("(cost to make only)"))
    print("  " + yellow("2") + ". To sell                    " + gray("(full pricing with profit)"))
    p = prompt_int("Choose", 2 if sell_mode else 1, 1, 2)
    sell_mode = (p == 2)
    print(green("-> Selling mode" if sell_mode else "-> Personal mode"))
    print("")

def run_calculation():
    name = prompt_string("Figurine name", "Figurine")

    print(section("Material"))
    for i, m in enumerate(MATERIALS):
        print(f"  {yellow(str(i + 1))}. {m['name']}  " + gray(f"(~{fmt(m['pricePerKg'] * settings['fx'])} {settings['currency']}/kg)"))
    
    mat_idx = prompt_int("Choose material", settings["material"] + 1, 1, len(MATERIALS)) - 1
    if mat_idx != settings["material"]:
        settings["material"] = mat_idx
        settings["materialPrice"] = MATERIALS[mat_idx]["pricePerKg"] * settings["fx"]
    
    mat = MATERIALS[settings["material"]]
    settings["materialPrice"] = prompt_float(f"Material price, {settings['currency']}/kg", settings["materialPrice"])

    print(section("Model"))
    print("  " + yellow("1") + ". I know the weight (g) from the slicer")
    print("  " + yellow("2") + ". I know the volume (cm3) and infill")
    mode = prompt_int("Mode", 1, 1, 2)
    
    if mode == 1:
        grams = prompt_float("Model weight, g", 50.0, 0.01)
    else:
        vol = prompt_float("Model volume, cm3", 40.0, 0.01)
        infill = prompt_float("Infill, %", 20.0, 1.0, 100.0)
        effective = 0.30 + 0.70 * (infill / 100.0)
        grams = vol * effective * mat["density"]
        print(gray(f"  -> estimated weight: {fmt(grams)} g"))
    
    # Time unit selection (Hours, Minutes, Seconds support)
    print(section("Print Time Unit"))
    print("  " + yellow("1") + ". Hours")
    print("  " + yellow("2") + ". Minutes")
    print("  " + yellow("3") + ". Seconds")
    time_unit = prompt_int("Choose time unit", 1, 1, 3)
    time_val = prompt_float("Print time value", 5.0, 0.001)

    if time_unit == 1:
        hours = time_val
    elif time_unit == 2:
        hours = time_val / 60.0
    else:
        hours = time_val / 3600.0

    qty = prompt_int("Quantity (batch size)", 1, 1, 100000) if sell_mode else 1

    work_min = 0.0
    labor_rate = 0.0
    consumables = 0.0

    if sell_mode:
        print(section("Finishing"))
        for i, fin in enumerate(FINISHES):
            print(f"  {yellow(str(i + 1))}. {fin['name']}")
        fin_choice = FINISHES[prompt_int("Choose finishing", 2, 1, len(FINISHES)) - 1]
        post_min = prompt_float("Post-processing time, min", fin_choice["minutes"])
        consumables = prompt_float(f"Consumables (paint, glue, sandpaper), {settings['currency']}", fin_choice["consumablesUsd"] * settings["fx"])
        settings["prepMin"] = prompt_float("Prep time (slicing, bed, start), min", settings["prepMin"])
        settings["laborRate"] = prompt_float(f"Your labor rate, {settings['currency']}/hour", settings["laborRate"])
        work_min = settings["prepMin"] / qty + post_min
        labor_rate = settings["laborRate"]
    else:
        print(section("Extras"))
        consumables = prompt_float(f"Paint / glue / other materials, {settings['currency']}", 0.0)
        if ask_yes_no("Count your own time as a cost?", False):
            minutes = prompt_float("Hands-on time (prep + finishing), min", 40.0)
            settings["laborRate"] = prompt_float(f"Value of your time, {settings['currency']}/hour", settings["laborRate"])
            work_min = minutes
            labor_rate = settings["laborRate"]

    if ask_yes_no("\nEdit advanced settings (power, printer cost, wear, failure rate)?", False):
        print(section("Advanced"))
        settings["supportPct"] = prompt_float("Extra material for supports/brim, %", settings["supportPct"])
        settings["powerW"] = prompt_float("Printer average power, W", settings["powerW"])
        settings["kwhPrice"] = prompt_float(f"Electricity price, {settings['currency']}/kWh", settings["kwhPrice"])
        settings["printerCost"] = prompt_float(f"Printer cost, {settings['currency']}", settings["printerCost"])
        settings["printerLifeH"] = prompt_float("Printer lifetime, hours", settings["printerLifeH"], 1.0)
        settings["maintPerHour"] = prompt_float(f"Maintenance reserve, {settings['currency']}/print hour", settings["maintPerHour"])
        settings["failPct"] = prompt_float("Failure rate, %", settings["failPct"], 0.0, 90.0)

    job = {
        "grams": grams,
        "hours": hours,
        "qty": qty,
        "workMin": work_min,
        "laborRate": labor_rate,
        "consumables": consumables,
        "design": 0.0,
        "packaging": 0.0,
        "shipping": 0.0,
        "feePct": 0.0,
        "vatPct": 0.0
    }

    shop_price = 0.0
    tiers = []

    if sell_mode:
        print(section("Selling"))
        job["packaging"] = prompt_float(f"Packaging, {settings['currency']}", settings["packaging"])
        settings["packaging"] = job["packaging"]
        job["shipping"] = prompt_float(f"Shipping you pay (0 if customer pays), {settings['currency']}", settings["shipping"])
        settings["shipping"] = job["shipping"]
        job["design"] = prompt_float(f"One-off design/model cost for this batch, {settings['currency']}", 0.0)

        for i, ch in enumerate(CHANNELS):
            print(f"  {yellow(str(i + 1))}. {ch['name']}  " + gray(f"({fmt(ch['feePct'], 1)}%)"))
        ch_idx = prompt_int("Sales channel", settings["channel"] + 1, 1, len(CHANNELS)) - 1
        if ch_idx != settings["channel"]:
            settings["channel"] = ch_idx
            settings["channelFee"] = CHANNELS[ch_idx]["feePct"]
        
        settings["channelFee"] = prompt_float("Channel fee, % of sale price", settings["channelFee"], 0.0, 60.0)
        settings["royaltyPct"] = prompt_float("Licence/IP royalty, % of sale price", settings["royaltyPct"], 0.0, 50.0)
        settings["vatPct"] = prompt_float("VAT/sales tax, %", settings["vatPct"], 0.0, 50.0)
        settings["profitMoney"] = prompt_float(f"Profit you want per unit, {settings['currency']}", settings["profitMoney"])
        settings["targetHourly"] = prompt_float(f"Minimum profit per print hour, {settings['currency']}", settings["targetHourly"])

        job["feePct"] = settings["channelFee"] + settings["royaltyPct"]
        job["vatPct"] = settings["vatPct"]

        if job["feePct"] >= 90:
            print(bred("[Error] Fees + royalty are too high to price this item."))
            return
    else:
        shop_price = prompt_float(f"\nPrice of a similar ready-made figurine in a shop (0 = skip), {settings['currency']}", 0.0)

    costs = calculate_costs(job)
    if sell_mode:
        tiers = build_tiers(costs, job)

    report = build_sell_report(name, mat, job, costs, tiers, None) if sell_mode else build_hobby_report(name, mat, job, costs, shop_price)

    print("\n" + report)

    if ask_yes_no("\nSave report to a file?", False):
        file_name = safe_file_name(name) + "_report.txt"
        try:
            global use_color
            use_color = False
            plain_report = build_sell_report(name, mat, job, costs, tiers, None) if sell_mode else build_hobby_report(name, mat, job, costs, shop_price)
            use_color = "NO_COLOR" not in os.environ
            
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(plain_report)
            print(green(f"[OK] Saved: {file_name}"))
        except Exception as e:
            print(bred(f"[Error] Could not save file: {e}"))

def main():
    cfg = load_config()
    fetch_startup_data(cfg)
    
    first = True
    while True:
        clear_screen()  # Clean up terminal window completely before new calculation
        banner()
        if not first:
            pass
        first = False
        choose_currency()
        ask_purpose()
        run_calculation()
        if not ask_yes_no("\nCalculate another figurine?", False):
            break
    print(bgreen("\nGoodbye!"))

if __name__ == "__main__":
    main()
