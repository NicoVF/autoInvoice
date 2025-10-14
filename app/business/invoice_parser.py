import json
import re
import textwrap
from app.logger import loggerCloudVision, loggerOpenAI
from app.services.cloud_vision import extract_text_from_file
from app.services.openAI import interpret_with_gpt


FIELDS = [
    "bank", "amount", "date", "time",
    "sender_name", "sender_cuit", "sender_cvu",
    "receiver_name", "receiver_cuit", "receiver_cvu", "operation_id"
]
BANKS = [
    "Banco Nación",
    "Banco Provincia",
    "Banco Santander Río",
    "Banco Galicia",
    "Banco BBVA",
    "Banco Macro",
    "Banco HSBC",
    "Banco ICBC",
    "Banco Patagonia",
    "Banco Supervielle",
    "Banco Credicoop",
    "Brubank",
    "Ualá",
    "Mercado Pago",
    "Personal Pay",
    "Naranja X",
    "Lemon Cash",
    "Prex",
    "Copter",
    "Pomelo",
    "Telepagos"
]


def ask_gpt_to_parse(text):
    prompt = textwrap.dedent(f"""
    Analizá el siguiente texto obtenido por OCR y determiná si corresponde a un **comprobante bancario argentino real** 
    (por ejemplo, un comprobante de transferencia, depósito, pago o acreditación).
    Si NO parece un comprobante (por ejemplo, si es una tabla, planilla, captura de Excel, mensaje, texto genérico o sin datos financieros reales),
    devolvé todos los campos con **null** y el campo "bank" con "null".

    Devolvé solo JSON con las claves exactas: {FIELDS}

    ### Reglas:
    - *bank*: uno de estos posibles valores: {BANKS}
    - *amount*: número sin símbolo ni separadores. Si tiene punto entre miles (260.00000), interpretalo como separador de miles. Usá punto decimal con dos dígitos (260000.00).
    - *date*: formato ISO YYYY-MM-DD
    - *time*: formato HH:MM (24h)
    - *CUIT/CUIL*: 11 dígitos (XX-XXXXXXXX-X o sin guiones)
    - *CVU/CBU*: 22 dígitos
    - *operation_id*: número o GUID (relacionado con operación o comprobante)
    - Si un campo no aparece o el texto claramente **no es un comprobante**, poné null.
    - No agregues texto fuera del JSON.
    - Evitá interpretar planillas, reportes, listados de transacciones o texto con títulos como "Saldo", "Comisión", "Fecha", "Importe", etc. como comprobantes.

    Texto OCR:
    ---
    {text}
    ---
    """)
    system_message = "Sos experto en interpretar comprobantes bancarios argentinos y devolver datos estructurados."
    try:
        content = interpret_with_gpt(prompt, system_message)
        if not content:
            return None
        json_text = re.search(r"\{.*\}", content, re.S)
        return json.loads(json_text.group()) if json_text else None
    except Exception as e:
        loggerOpenAI.error(f"Error in ChatGPT parse: {e}")
        return None


def normalize_amount(raw_value):
    if not raw_value:
        return None
    val = str(raw_value).replace(" ", "").replace("$", "")
    if re.match(r"^\d{1,3}(\.\d{3})*,\d{2}$", val):
        return float(val.replace(".", "").replace(",", "."))
    if re.match(r"^\d+,\d{1,2}$", val):
        return float(val.replace(",", "."))
    if re.match(r"^\d+\.\d{4,}$", val):
        return float(val.replace(".", ""))
    if re.match(r"^\d{1,3}(\.\d{3})+$", val):
        return float(val.replace(".", ""))
    if val.isdigit():
        return float(val)
    try:
        return float(val.replace(",", "."))
    except Exception:
        return None


def parse_invoice(file_url, file_type="image"):
    try:
        text = extract_text_from_file(file_url, file_type=file_type)
        if not text:
            loggerCloudVision.warning(f"No text detected in {file_url}")
            return None
        parsed = ask_gpt_to_parse(text)
        if not parsed:
            loggerOpenAI.error(f"ChatGPT parsing failed for {file_url}")
            return None
        if parsed.get("amount"):
            parsed["amount"] = normalize_amount(parsed["amount"])
        loggerOpenAI.info(f"Extracted: {parsed}")
        return parsed
    except Exception as e:
        loggerCloudVision.error(f"Error parsing invoice {file_url}: {e}")
        return None


def format_arg_amount(amount):
    if amount is None:
        return "-"
    try:    # 260000.0 → "260.000,00"
        formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except Exception:
        return str(amount)


def build_summary(data):
    def fmt(v): return str(v).strip() if v not in [None, "null", ""] else "-"
    amount = data.get("amount")
    amount_fmt = format_arg_amount(amount)
    parts = [
        f"💸 Monto: *${amount_fmt}*",
        f"📅 Fecha: {fmt(data.get('date'))}",
        f"🕒 Hora: {fmt(data.get('time'))}",
    ]
    return "\n".join([p for p in parts if p])
