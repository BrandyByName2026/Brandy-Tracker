import streamlit as st
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Basahin mula sa Streamlit Secrets (fall back sa hardcoded kung wala)
try:
    REDMINE_URL = st.secrets["REDMINE_URL"]
    API_KEY = st.secrets["API_KEY"]
except Exception:
    REDMINE_URL = "https://matrix.philsys.gov.ph"
    API_KEY = "cb664261700fd411bfda36fc14ea8d46bad4fbc7"

# Page Configuration
st.set_page_config(page_title="PSA FindMyTRN Tracker", page_icon="🔍", layout="centered")

st.title("🔍 PSA FindMyTRN & Ticket Status Lookup")
st.write("I-type ang **TRN** o **Pangalan** para hanapin ang status at response sa Redmine tickets.")

# Search Input Box sa Web
query = st.text_input("Mag-search ng TRN o Pangalan:", placeholder="Halimbawa: 7530020729027092...")

def search_redmine_by_keyword(keyword):
    headers = {
        "X-Redmine-API-Key": API_KEY
    }
    search_url = f"{REDMINE_URL}/search.json?q={keyword}&issues=1"
    
    try:
        response = requests.get(search_url, headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])
            matched_issues = []
            
            for item in results:
                if item.get("type") == "issue":
                    issue_id = item.get("id")
                    issue_url = f"{REDMINE_URL}/issues/{issue_id}.json?include=journals"
                    issue_resp = requests.get(issue_url, headers=headers, verify=False, timeout=10)
                    
                    if issue_resp.status_code == 200:
                        data = issue_resp.json().get("issue", {})
                        
                        notes_list = []
                        for journal in data.get("journals", []):
                            note = journal.get("notes", "")
                            if note:
                                notes_list.append(note)
                        
                        latest_response = " | ".join(notes_list) if notes_list else "Wala pang response / notes"
                        
                        matched_issues.append({
                            "id": issue_id,
                            "subject": data.get("subject", ""),
                            "status": data.get("status", {}).get("name", ""),
                            "assignee": data.get("assigned_to", {}).get("name", "Unassigned"),
                            "response": latest_response,
                            "updated_on": data.get("updated_on", "")
                        })
            return matched_issues
        else:
            return None
    except Exception as e:
        return None

if query:
    with st.spinner("Hinahanap sa Redmine database... Sandali lang."):
        results = search_redmine_by_keyword(query)
        
    if results is None:
        st.error("May naganap na error sa pag-connect sa Redmine server.")
    elif not results:
        st.warning(f"Walang nakitang ticket na may kaugnayan sa '{query}'.")
    else:
        st.success(f"May nakitang {len(results)} na resultang tumutugma!")
        
        for res in results:
            with st.container():
                st.markdown(f"### Ticket ID: `#{res['id']}`")
                st.write(f"**Subject:** {res['subject']}")
                st.write(f"**Status:** {res['status']}")
                st.write(f"**Assignee:** {res['assignee']}")
                st.write(f"**Updated On:** {res['updated_on']}")
                
                st.info(f"**Response / Notes:**\n\n{res['response']}")
                st.markdown("---")
