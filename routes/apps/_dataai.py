"""Data AI backend — natural-language querying / reshaping of uploaded tabular data.

Flow: uploaded file(s) -> pandas DataFrame(s) -> registered as DuckDB tables ->
an LLM writes ONE read-only SQL SELECT for the user's question -> DuckDB runs it ->
the result (always a DataFrame, even a single value) is returned.
"""

import io
import os
import re
import json
import base64
import threading

import duckdb
import pandas as pd

from myapp import app
from openai import OpenAI

# PDF ingestion is optional — if pdfplumber isn't installed we simply can't read PDFs.
try:
    import pdfplumber
    _PDF_OK = True
except Exception:
    _PDF_OK = False


PYFLASKI_VERSION = str(os.environ.get("PYFLASKI_VERSION", ""))

# ── LLM client ──────────────
api_key = app.config.get("MAGE_LLM_KEY", "")
base_url = app.config.get("MAGE_LLM_URL", "")

client = OpenAI(api_key=api_key, base_url=base_url, max_retries=0)

# Coder model would be better.
LLM_MODEL = "qwen3-coder-30b"

# Hard cap on how long a single generated query may run.
QUERY_TIMEOUT = 60

# Cap on text sent to the LLM when structuring free text / PDF into a table
MAX_TEXT_CHARS = 25000

# Accepted upload formats (whitelist)
_STRUCTURED_EXTS = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".json", ".ndjson",
                    ".parquet", ".feather", ".html", ".xml"}
_TEXT_EXTS = {".pdf", ".md", ".txt"}            # routed to the LLM text->table path
ALLOWED_EXTS = _STRUCTURED_EXTS | _TEXT_EXTS


# ── File ingestion (self-contained) ────────────────────────────────────────
def _file_to_dataframe(contents, filename):
    """Parse a Dash-uploaded file into a DataFrame. Returns (df, None) or (None, err)."""
    try:
        if not contents or not filename:
            return None, "No data to parse."
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        ext = os.path.splitext(filename)[-1].lower()

        if ext == ".csv":
            return pd.read_csv(io.StringIO(decoded.decode("utf-8"))), None
        elif ext == ".tsv":
            return pd.read_csv(io.StringIO(decoded.decode("utf-8")), sep="\t"), None
        elif ext == ".txt":
            try:
                return pd.read_csv(io.StringIO(decoded.decode("utf-8")), sep="\t"), None
            except Exception:
                return pd.read_csv(io.StringIO(decoded.decode("utf-8"))), None
        elif ext in (".xlsx", ".xls"):
            return pd.read_excel(io.BytesIO(decoded)), None
        elif ext == ".json":
            try:
                return pd.read_json(io.StringIO(decoded.decode("utf-8"))), None
            except Exception:
                return pd.read_json(io.StringIO(decoded.decode("utf-8")), lines=True), None
        elif ext == ".ndjson":
            return pd.read_json(io.StringIO(decoded.decode("utf-8")), lines=True), None
        elif ext == ".parquet":
            return pd.read_parquet(io.BytesIO(decoded)), None
        elif ext == ".feather":
            return pd.read_feather(io.BytesIO(decoded)), None
        elif ext == ".html":
            dfs = pd.read_html(io.StringIO(decoded.decode("utf-8")))
            return (dfs[0], None) if dfs else (None, "No tables found in HTML file.")
        elif ext == ".xml":
            return pd.read_xml(io.StringIO(decoded.decode("utf-8"))), None
        else:
            return None, f"Unsupported file extension: {ext}"
    except Exception as e:
        return None, f"Failed to parse file: {e}"


def _extract_text_from_pdf(decoded_bytes):
    """Extract text from a PDF (<=5MB). Returns text, or '' if too large / unreadable."""
    if not _PDF_OK or len(decoded_bytes) > 5 * 1024 * 1024:
        return ""
    with pdfplumber.open(io.BytesIO(decoded_bytes)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def _text_to_dataframe(text_content, model=LLM_MODEL, max_retries=3):
    """LLM turns messy/semi-structured text into a DataFrame. Returns (df, err)."""
    text_content = (text_content or "")[:MAX_TEXT_CHARS]      # keep within context window
    prompt = (
        "Convert the content below into a valid JSON object usable by pd.DataFrame(...).\n"
        "- Return ONLY the JSON (no markdown, no comments, no explanation).\n"
        "- Do NOT invent or hallucinate data.\n"
        "- Respond exactly as:\nJSONBlock:\n{ your_json_here }\n\n"
        f"Content:\n{text_content}"
    )
    last_error = "Unknown error."
    for _ in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}],
                temperature=0, timeout=90,
            )
            text = resp.choices[0].message.content or ""
            match = re.search(r"JSONBlock:\s*(\{.*\}|\[.*\])", text, re.DOTALL)
            if not match:
                last_error = "Could not extract structured data from the text."
                continue
            df = pd.DataFrame(json.loads(match.group(1)))
            return df, None
        except Exception as e:
            last_error = f"Failed to build a table from the text: {e}"
    return None, last_error


def _prepare_dataframe(contents, filename):
    """One upload -> DataFrame. Only whitelisted formats."""
    ext = os.path.splitext(filename)[-1].lower()
    if ext not in ALLOWED_EXTS:
        return None, (f"Unsupported format ({ext or 'no extension'}). Accepted: CSV, TSV, "
                      "TXT, MD, Excel, JSON, Parquet, Feather, HTML, XML, or PDF.")

    df, err = _file_to_dataframe(contents, filename)
    if df is not None:
        return df, None
    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
    except Exception as e:
        return None, f"Failed to decode file: {e}"

    if ext == ".pdf":
        text = _extract_text_from_pdf(decoded)
        if not text.strip():
            return None, "No extractable text in PDF (or PDF too large)."
        return _text_to_dataframe(text)

    # Text formats only -> let the LLM structure them.
    if ext in (".md", ".txt"):
        try:
            file_text = decoded.decode("utf-8", errors="ignore")
            if not file_text.strip():
                return None, f"Could not read file. ({err})"
            return _text_to_dataframe(file_text)
        except Exception as e:
            return None, f"Could not read file: {e} ({err})"

    return None, f"Could not read the file as a table. ({err})"


def prepare_tables(contents_list, filenames):
    """Multiple uploads -> ({unique_table_name: df}, [errors])."""
    tables, errors, used = {}, [], set()
    for contents, filename in zip(contents_list or [], filenames or []):
        df, err = _prepare_dataframe(contents, filename)
        if err:
            errors.append(f"{filename}: {err}")
        if df is None:
            continue
        name = _safe_name(filename)
        base, i = name, 2
        while name in used:            # keep table names unique across files
            name = f"{base}_{i}"; i += 1
        used.add(name)
        tables[name] = df
    return tables, errors


# ── Text-to-SQL engine (DuckDB) ─────────────────────────────────────────────
def _safe_name(filename):
    """A SQL-safe table name derived from a filename."""
    base = os.path.splitext(os.path.basename(str(filename)))[0]
    safe = re.sub(r"\W+", "_", base).strip("_") or "data"
    return ("t_" + safe) if safe[0].isdigit() else safe


def _extract_sql(text):
    """Pull SQL out of an LLM reply (strip ``` fences / a leading 'sql' token)."""
    text = (text or "").strip()
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    if m:
        text = m.group(1).strip()
    return re.sub(r"^sql\s+", "", text, flags=re.I).strip()


_DISALLOWED = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|install|load|"
    r"pragma|export|import|call|set)\b", re.I)


def _is_safe_select(sql):
    """Allow a single read-only SELECT/WITH statement only. (ok, reason)."""
    if not sql.strip():
        return False, "Empty query."
    s = sql.strip().rstrip(";")
    if ";" in s:
        return False, "Only a single statement is allowed."
    if not re.match(r"^\s*(with|select)\b", s, re.I):
        return False, "Only SELECT / WITH queries are allowed."
    if _DISALLOWED.search(s):
        return False, "Query contains a disallowed (data-modifying) keyword."
    return True, ""


def _schema_text(tables):
    """Compact schema + sample rows to ground the model."""
    blocks = []
    for name, df in tables.items():
        cols = ", ".join(f'"{c}" ({df[c].dtype})' for c in df.columns)
        blocks.append(
            f'Table "{name}" ({len(df)} rows):\nColumns: {cols}\n'
            f"Sample rows (CSV):\n{df.head(3).to_csv(index=False)}")
    return "Available tables:\n\n" + "\n\n".join(blocks)


SYSTEM_PROMPT = (
    "You translate a question into ONE read-only DuckDB SQL SELECT over the tables "
    "below, and nothing else.\n"
    "- Output ONLY the SQL — no prose, no markdown fences.\n"
    "- Use ONLY SELECT / WITH; never modify data or the database.\n"
    "- Put EVERY column name in double quotes, exactly as given — e.g. \"a.b\". An "
    "unquoted name containing a dot (a.b) is read as table.column and will fail.\n"
    "- Always return a result set; for a single value, still SELECT it as one row.\n"
    "- Write DuckDB-dialect SQL — e.g. use string_agg(expr, ', ') to concatenate grouped "
    "values (DuckDB has no LISTAGG or WITHIN GROUP).\n\n"
)


def _execute_with_timeout(con, sql, timeout=QUERY_TIMEOUT):
    """Run sql on con with a hard time limit; interrupt and raise TimeoutError if exceeded."""
    box = {}

    def _work():
        try:
            box["df"] = con.execute(sql).df()
        except Exception as e:                     # e.g. interrupt, SQL error
            box["err"] = e

    t = threading.Thread(target=_work, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        try:
            con.interrupt()                        # cancel the running query
        except Exception:
            pass
        t.join(5)
        raise TimeoutError(f"query exceeded {timeout}s")
    if "err" in box:
        raise box["err"]
    return box["df"]


def run_dataai(tables, query, default_table=None, model=LLM_MODEL, max_retries=2):
    """dict[name->df] + NL query -> (result_df, sql, error). Result is always a DataFrame.

    default_table: when the question doesn't name a table, the model is told to operate
    on this one (used to default follow-ups to the last result)."""
    if not tables:
        return None, None, "No data provided."

    con = duckdb.connect()                       # in-memory, ephemeral per request
    for name, df in tables.items():
        con.register(name, df)
    # Sandbox: block all file/URL/extension access (read_csv on disk, COPY, ATTACH, INSTALL…).
    try:
        con.execute("SET enable_external_access=false")
    except Exception:
        pass

    system = SYSTEM_PROMPT + _schema_text(tables)
    if default_table and default_table in tables:
        system += (
            f'\n\nIMPORTANT: If the question does not explicitly name a table, operate on '
            f'the table "{default_table}" — it is the user\'s current working result. Only '
            f'use the other tables when the question names them or clearly needs them '
            f'(e.g. "merge with ...", "join ... on ...").')
    sql, err = None, None
    for _ in range(max_retries):
        # If the last error looks like an unquoted column read as table.column, nudge
        # the model to quote — the raw "table X not found" message alone doesn't say so.
        hint = ""
        if err and ("not found" in err.lower() or "binder error" in err.lower()):
            hint = ' Put every column name in double quotes exactly as given (e.g. "a.b").'
        user = query if err is None else (
            f"{query}\n\nThe previous SQL failed with:\n{err}\nReturn corrected SQL only.{hint}")
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=0, timeout=90,
            )
            sql = _extract_sql(resp.choices[0].message.content or "")
        except Exception as e:
            err = f"Model call failed: {e}"
            continue

        ok, reason = _is_safe_select(sql)
        if not ok:
            err = reason
            continue
        try:
            return _execute_with_timeout(con, sql), sql, None
        except TimeoutError:
            err = f"Query timed out (over {QUERY_TIMEOUT}s) — try narrowing it."
        except Exception as e:
            err = f"SQL error: {e}"

    return None, sql, err
