import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="GTM Workspace Inspector", layout="wide")
st.title("📊 GTM Workspace Inspector")

uploaded_file = st.file_uploader("Lade deine GTM JSON-Datei hoch", type="json")

# Format filters for triggers
def format_filter(f):
    op = f.get("type")
    params = f.get("parameter", [])
    args = {p["key"]: p.get("value", "") for p in params}

    arg0 = args.get("arg0", "")
    arg1 = args.get("arg1", "")
    ignore_case = args.get("ignore_case")
    negate = args.get("negate")

    if not arg0 or not arg1:
        return f"{op} (ungültig)"

    result = f"{arg0} {op.lower()} '{arg1}'"
    extras = []
    if ignore_case == "true":
        extras.append("ignore_case=True")
    if negate == "true":
        extras.append("negate=True")
    if extras:
        result += f" ({', '.join(extras)})"
    return result

if uploaded_file:
    try:
        data = json.load(uploaded_file)
        tags = data.get("containerVersion", {}).get("tag", [])
        triggers = data.get("containerVersion", {}).get("trigger", [])
        trigger_dict = {t["triggerId"]: t for t in triggers}

        results = []

        for tag in tags:
            if not isinstance(tag, dict):
                continue

            tag_name = tag.get("name", "")
            tag_type = tag.get("type", "")
            tag_paused = tag.get("paused", False)
            trigger_ids = tag.get("firingTriggerId", []) or []

            all_trigger_info = []
            first_trigger_name = ""
            first_trigger_type = ""

            for idx, tid in enumerate(trigger_ids):
                trigger = trigger_dict.get(tid)
                if not trigger:
                    continue

                trig_name = trigger.get("name", "")
                trig_type = trigger.get("type", "")
                filters = trigger.get("filter", []) + trigger.get("customEventFilter", [])
                flat_filters = [format_filter(f) for f in filters]

                all_trigger_info.append(f"Name: {trig_name} | Type: {trig_type} | Filter: {flat_filters}")

                if idx == 0:
                    first_trigger_name = trig_name
                    first_trigger_type = trig_type

            parameters = {p.get("key"): p.get("value") for p in tag.get("parameter", [])}
            param_list = [f"{k}: {v}" for k, v in parameters.items()]
            param_conversion_label = parameters.get("conversionLabel", "")
            param_event_name = parameters.get("eventName", "")

            results.append({
                "Tag Name": tag_name,
                "Type": tag_type,
                "Tag Paused": tag_paused,
                "Triggers": "\n".join(all_trigger_info),
                "Trigger.Name": first_trigger_name,
                "Trigger.Type": first_trigger_type,
                "Parameters": "\n".join(param_list),
                "Parameters.conversionLabel": param_conversion_label,
                "Parameters.eventName": param_event_name
            })

        df = pd.DataFrame(results)
        st.success(f"{len(df)} Tags gefunden.")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV herunterladen", csv, "gtm_tags_export.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Fehler beim Verarbeiten der Datei: {e}")

