# streamlit_app.py
# Streamlit app for The Met Museum Open Access API (English-only UI)
# Ready for GitHub → Streamlit Cloud deployment, or local `streamlit run streamlit_app.py`

import requests
import streamlit as st

API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"

st.set_page_config(page_title="Explore Artworks — MET Open API", page_icon="🖼️", layout="wide")

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_departments():
    """Fetch department list from The Met API."""
    try:
        r = requests.get(f"{API_BASE}/departments", timeout=20)
        r.raise_for_status()
        js = r.json() or {}
        depts = js.get("departments", [])
        options = ["All Departments"]
        mapping = {"All Departments": None}
        for d in depts:
            label = f"{d.get('displayName','Unknown')} ({d.get('departmentId')})"
            options.append(label)
            mapping[label] = d.get("departmentId")
        return options, mapping
    except Exception:
        return ["All Departments"], {"All Departments": None}

@st.cache_data(show_spinner=True, ttl=60)
def search_ids(q, has_images=True, department_id=None):
    """Search artworks and return object IDs and total count."""
    params = {"q": q, "hasImages": has_images}
    if department_id:
        params["departmentId"] = int(department_id)
    r = requests.get(f"{API_BASE}/search", params=params, timeout=25)
    r.raise_for_status()
    data = r.json() or {}
    return data.get("objectIDs") or [], int(data.get("total", 0))

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_object(oid: int):
    """Fetch detailed object info by ID."""
    r = requests.get(f"{API_BASE}/objects/{oid}", timeout=20)
    if r.status_code == 200:
        return r.json()
    return None

# ------------------ UI ------------------
st.title("🖼️ Explore Artworks with The MET Museum Open API")
st.caption("Powered by The Metropolitan Museum of Art — Open Access Collection (No API Key Required)")

with st.sidebar:
    st.header("Search Settings")
    q = st.text_input("Keyword", value="flower", help="Example: flower, china, landscape, portrait, bronze…")
    max_n = st.slider("Maximum Results to Display", 1, 60, 18)
    has_images = st.toggle("Show Only Items with Images", value=True)

    options, mapping = fetch_departments()
    choice = st.selectbox("Department (optional)", options, index=0)
    dept_id = mapping.get(choice)

    search_btn = st.button("Search Artworks", type="primary", use_container_width=True)

if search_btn:
    if not q.strip():
        st.warning("Please enter a keyword before searching.")
        st.stop()

    with st.spinner("Searching artworks..."):
        ids, total = search_ids(q.strip(), has_images=has_images, department_id=dept_id)

    st.subheader(f'Results for "{q}"')
    st.caption(f"Total found: {total} items — Displaying top {min(max_n, len(ids))} results")

    if not ids:
        st.info("No results found. Try another keyword or remove filters.")
        st.stop()

    cols = st.columns(3)
    for i, oid in enumerate(ids[:max_n]):
        obj = fetch_object(oid)
        if not obj:
            continue
        with cols[i % 3]:
            st.image(obj.get("primaryImageSmall") or obj.get("primaryImage") or "", use_column_width=True)
            st.markdown(f"**{obj.get('title') or 'Untitled'}**")
            artist = obj.get("artistDisplayName") or "Unknown"
            date = obj.get("objectDate") or ""
            st.caption(f"{artist} · {date}")
            if obj.get("medium"):
                st.write(f"**Medium:** {obj.get('medium')}")
            if obj.get("objectURL"):
                st.link_button("View on The Met Website", obj.get("objectURL"), use_container_width=True)
else:
    st.info("Enter a keyword in the sidebar and click **Search Artworks** to explore the collection.")
    st.divider()
    st.markdown(
        """
        ### Quick Tips
        - Use **English keywords** for better results (e.g., *flower*, *portrait*, *bronze*).
        - Department list is loaded from The Met’s `/departments` API.
        - Results include high-quality public domain artworks.
        """
    )

st.markdown("---")
st.caption("Data Source: The Met Museum Open Access — https://metmuseum.github.io/")
