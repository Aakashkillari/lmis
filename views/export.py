import streamlit as st

from lmis import api, ui
from lmis.ui import t

result = ui.data()

st.header(t("export_title"))
st.write(t("export_intro"))

frame, chosen = ui.place_filters(result["gaps"], "export")
export = api.gap_records(frame)

st.subheader(t("export_preview", count=len(export)))
ui.table(frame.sort_values("severity", ascending=False), ui.GAP_COLUMNS + [("current_status", "status"), ("demand_lower", "int"), ("demand_upper", "int")], height=380)
ui.source_note()

columns = st.columns(2)
columns[0].download_button(t("download_gaps"), export.to_csv(index=False).encode("utf-8"), file_name="lmis_gap_table.csv", mime="text/csv")
warnings = api.warning_records(result["warnings"])
columns[1].download_button(t("download_warnings"), warnings.to_csv(index=False).encode("utf-8"), file_name="lmis_early_warnings.csv", mime="text/csv")

st.subheader(t("api_title"))
st.write(t("api_intro"))
query = "&".join(f"{key}={value}" for key, value in chosen.items() if key != "sector" and value != ui.all_option())
st.code(f"GET http://localhost:8000/api/gaps{'?' + query if query else ''}", language="text")
st.markdown(t("api_endpoints"))
st.code("uvicorn lmis.api:app --port 8000", language="bash")
