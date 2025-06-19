import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="GTM Workspace Inspector", layout="wide")

st.title("GTM Workspace Inspector")
uploaded_file = st.file_uploader("Upload your GTM workspace JSON", type="json")

def format_filter(f):
    op = f.get('type')
    params = f.get('parameter', [])
    args = {p['key']: p['value'] for p in params}
    
    arg0 = args.get('arg0')
    arg1 = args.get('arg1')
    ignore_case = args.get('ignore_case')
    negate = args.get('negate')

    if not arg0 or not arg1:
        return op + " (invalid or missing args)"

    expression = f"{arg0} {op.lower()} '{arg1}'"
    extras = []
    if ignore_case == 'true':
        extras.append("ignore_case=True")
    if negate == 'true':
        extras.append("negate=True")
    if extras:
        expression += f" ({', '.join(extras)})"
    return expression

if uploaded_file:
    data = json.load(uploaded_file)
    tags = data['containerVersion']['tag']
    triggers_dict = {t['triggerId']: t for t in data['containerVersion']['trigger']}
    
    rows = []

    for tag in tags:
        tag_name = tag.get('name')
        tag_type = tag.get('type')
        trigger_ids = tag.get('firingTriggerId', [])

        trigger_info_list = []
        first_trigger_name = ""
        first_trigger_type = ""

        for idx, tid in enumerate(trigger_ids):
            trigger = triggers_dict.get(tid)
            if not trigger:
                continue

            trig_name = trigger.get('name', '')
            trig_type = trigger.get('type', '')
            filters = trigger.get('filter', []) + trigger.get('customEventFilter', [])
            flat_filters = [format_filter(f) for f in filters]

            trigger_info_list.append(f"Name: {trig_name} | Type: {trig_type} | Filter: {flat_filters}")

            if idx == 0:
                first_trigger_name = trig_name
                first_trigger_type = trig_type

        # Get parameters
        parameters = {p['key']: p.get('value') for p in tag.get('parameter', [])}
        param_list = [f"{k}: {v}" for k, v in parameters.items()]
        param_conversion_label = parameters.get('conversionLabel', '')
        param_event_name = parameters.get('eventName', '')

        rows.append({
            "Tag Name": tag_name,
            "Type": tag_type,
            "Triggers": "\n".join(trigger_info_list),
            "Trigger.Name": first_trigger_name,
            "Trigger.Type": first_trigger_type,
            "Parameters": "\n".join(param_list),
            "Parameters.conversionLabel": param_conversion_label,
            "Parameters.eventName": param_event_name
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "gtm_tags_export.csv", "text/csv")
