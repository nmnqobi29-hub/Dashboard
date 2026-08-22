import streamlit as st
import requests
import pandas as pd
import io

API_URL = "https://dashboard-production-6b0b.up.railway.app"  # same deployed API as Isthixo

st.set_page_config(page_title="City Edge — Residents", layout="wide")
st.title("City Edge Resident Dashboard")



with st.expander("Add new resident", icon="➕"):
    with st.form("add_resident_form", clear_on_submit=True):
        new_col1, new_col2 = st.columns(2)

        new_student_number = new_col1.text_input("Student number")
        new_student_name = new_col2.text_input("Student name")

        new_room_number = new_col1.text_input("Room number")
        new_academic_year = new_col2.selectbox(
            "Academic year",
            ["1st Year", "2nd Year", "3rd Year", "Advanced Diploma", "Postgraduate"],
        )

        new_lease_status = st.selectbox(
            "Lease status", ["Renewed", "Expired", "Unknown"]
        )

        submitted = st.form_submit_button("Add resident")

        if submitted:
            if not new_student_number or not new_student_name or not new_room_number:
                st.error("Student number, name, and room number are all required.")
            elif not new_student_number.isdigit():
                st.error("Student number must be numeric.")
            else:
                try:
                    resp = requests.post(
                        f"{API_URL}/residents",
                        json={
                            "student_number": int(new_student_number),
                            "student_name": new_student_name,
                            "room_number": new_room_number,
                            "academic_year": new_academic_year,
                            "lease_status": new_lease_status,
                        },
                        timeout=10,
                    )
                    resp.raise_for_status()
                    st.success(f"Added {new_student_name} to room {new_room_number}.")
                    st.rerun()
                except requests.HTTPError as e:
                    if e.response is not None and e.response.status_code == 409:
                        st.error(e.response.json().get("detail", "This student number already exists."))
                    else:
                        st.error(f"Could not add resident: {e}")
                except requests.RequestException as e:
                    st.error(f"Could not add resident: {e}")



def fetch_residents(filters: dict):
    params = {k: v for k, v in filters.items() if v}
    try:
        response = requests.get(f"{API_URL}/residents", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Could not reach the API: {e}")
        st.stop()
    except ValueError:
        st.error("API returned invalid JSON.")
        st.stop()



with st.container():
    col1, col2, col3, col4 = st.columns(4)

    search = col1.text_input("Search name or student number")
    lease_status = col2.selectbox(
        "Lease status", ["", "Renewed", "Expired", "Unknown"]
    )
    academic_year = col3.selectbox(
        "Academic year",
        ["", "1st Year", "2nd Year", "3rd Year", "Advanced Diploma", "Postgraduate"],
    )
    room_number = col4.text_input("Room number")

filters = {
    "search": search,
    "lease_status": lease_status,
    "academic_year": academic_year,
    "room_number": room_number,
}

residents = fetch_residents(filters)

if not isinstance(residents, list):
    st.error(f"Unexpected response: {residents}")
    st.stop()

st.caption(f"{len(residents)} resident(s) match the current filters.")

if not residents:
    st.info("No residents match these filters.")
    st.stop()

df = pd.DataFrame(residents)



dl_col1, dl_col2, _ = st.columns([1, 1, 4])

csv_bytes = df.to_csv(index=False).encode("utf-8")
dl_col1.download_button(
    "Download CSV", csv_bytes, "residents.csv", "text/csv"
)

excel_buffer = io.BytesIO()
df.to_excel(excel_buffer, index=False, engine="openpyxl")
dl_col2.download_button(
    "Download Excel",
    excel_buffer.getvalue(),
    "residents.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.divider()



st.subheader("Residents")
st.caption("Edit any cell, then click 'Save changes' to update the database.")

editable_df = df[
    ["id", "student_number", "student_name", "room_number", "academic_year", "lease_status"]
].copy()

edited_df = st.data_editor(
    editable_df,
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "student_number": st.column_config.NumberColumn("Student Number", disabled=True),
        "lease_status": st.column_config.SelectboxColumn(
            "Lease Status", options=["Renewed", "Expired", "Unknown"]
        ),
        "academic_year": st.column_config.SelectboxColumn(
            "Academic Year",
            options=["1st Year", "2nd Year", "3rd Year", "Advanced Diploma", "Postgraduate"],
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="residents_editor",
)

if st.button("Save changes"):
    changes_made = 0
    errors = []

    original_by_id = editable_df.set_index("id")
    edited_by_id = edited_df.set_index("id")

    for resident_id in edited_by_id.index:
        original_row = original_by_id.loc[resident_id]
        edited_row = edited_by_id.loc[resident_id]

        diff = {}
        for col in ["student_name", "room_number", "academic_year", "lease_status"]:
            if original_row[col] != edited_row[col]:
                diff[col] = edited_row[col]

        if diff:
            try:
                resp = requests.patch(
                    f"{API_URL}/residents/{int(resident_id)}", json=diff, timeout=10
                )
                resp.raise_for_status()
                changes_made += 1
            except requests.RequestException as e:
                errors.append(f"Resident {resident_id}: {e}")

    if errors:
        for err in errors:
            st.error(err)
    if changes_made:
        st.success(f"Saved {changes_made} change(s).")
        st.rerun()
    if not changes_made and not errors:
        st.info("No changes to save.")
