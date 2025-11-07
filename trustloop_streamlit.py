import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

API_URL = "http://localhost:8000"

# --- Session State for Auth ---
def is_logged_in():
    return "access_token" in st.session_state and st.session_state.get("access_token")

def login(username, password):
    resp = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    if resp.status_code == 200:
        data = resp.json()
        st.session_state["access_token"] = data["access_token"]
        st.session_state["user"] = data["user"]
        return True, "Login successful!"
    else:
        return False, resp.json().get("detail", "Login failed.")

def register(username, email, password):
    resp = requests.post(f"{API_URL}/register", json={"username": username, "email": email, "password": password})
    if resp.status_code == 201:
        return True, "Registration successful! Please log in."
    else:
        return False, resp.json().get("detail", "Registration failed.")
def get_profile():
    if not is_logged_in():
        return None
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        resp = requests.get(f"{API_URL}/users/me", headers=headers)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            st.session_state.pop("access_token", None)
            st.session_state.pop("user", None)
    except Exception as e:
        return None
    return None

def get_help_requests():
    try:
        resp = requests.get(f"{API_URL}/requests")
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Error fetching help requests: {e}")
    return []

def create_help_request(title, description):
    if not is_logged_in():
        return None
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        resp = requests.post(f"{API_URL}/requests", json={"title": title, "description": description}, headers=headers)
        return resp
    except Exception as e:
        st.error(f"Error creating help request: {e}")
        return None
# --- Streamlit UI ---

st.set_page_config(
    page_title="TrustLoop",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("TrustLoop: Community Help Exchange Platform")


menu = ["Dashboard", "Home", "Login", "Register", "Profile", "Help Requests", "Help Someone", "User Management"]
if is_logged_in():
    menu.remove("Login")
    menu.remove("Register")
    menu.insert(2, "Logout")




choice = st.sidebar.selectbox("Navigation", menu)
# --- Help Someone Section ---
if choice == "Help Someone":
    st.header(":handshake: Help Someone")
    help_requests = get_help_requests()
    if not help_requests:
        st.info("No help requests available.")
    else:
        # Only show requests not created by current user (if logged in)
        current_user = st.session_state.get("user", {})
        filtered_requests = [r for r in help_requests if not current_user or r["creator"]["username"] != current_user.get("username")]
        if not filtered_requests:
            st.info("No help requests from other users.")
        else:
            df = pd.DataFrame([
                {
                    "ID": r["id"],
                    "Title": r["title"],
                    "Description": r["description"],
                    "User": r["creator"]["username"],
                    "Created At": r["created_at"]
                }
                for r in filtered_requests
            ])
            st.dataframe(df)
            selected_id = st.selectbox("Select a request to help", df["ID"])
            selected_request = next((r for r in filtered_requests if r["id"] == selected_id), None)
            if selected_request:
                st.write(f"**Title:** {selected_request['title']}")
                st.write(f"**Description:** {selected_request['description']}")
                st.write(f"**Requested by:** {selected_request['creator']['username']}")
                if st.button("Help this user!"):
                    # Simulate sending a message (in real app, would trigger notification)
                    st.success(f"You have offered to help {selected_request['creator']['username']}! They have been notified.")

# ...existing UI code...

if choice == "User Management":
    st.header(":busts_in_silhouette: User Management")
    users = []
    try:
        resp = requests.get(f"{API_URL}/users")
        if resp.status_code == 200:
            users = resp.json()
    except Exception as e:
        st.error(f"Error fetching users: {e}")
    if users:
        df = pd.DataFrame(users)
        st.dataframe(df)
        st.subheader("Edit or Delete User")
        user_ids = [u['id'] for u in users]
        selected_id = st.selectbox("Select User ID", user_ids)
        selected_user = next((u for u in users if u['id'] == selected_id), None)
        if selected_user:
            with st.form("edit_user_form"):
                new_username = st.text_input("Username", value=selected_user['username'])
                new_email = st.text_input("Email", value=selected_user['email'])
                new_reputation = st.number_input("Reputation", value=selected_user['reputation'], step=1)
                submitted = st.form_submit_button("Update User")
                if submitted:
                    params = {}
                    if new_username != selected_user['username']:
                        params['username'] = new_username
                    if new_email != selected_user['email']:
                        params['email'] = new_email
                    if new_reputation != selected_user['reputation']:
                        params['reputation'] = int(new_reputation)
                    if params:
                        try:
                            resp = requests.put(f"{API_URL}/users/{selected_id}", params=params)
                            if resp.status_code == 200:
                                st.success("User updated!")
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Failed to update user."))
                        except Exception as e:
                            st.error(f"Error updating user: {e}")
                    else:
                        st.info("No changes to update.")
            if st.button("Delete User", key=f"delete_{selected_id}"):
                try:
                    resp = requests.delete(f"{API_URL}/users/{selected_id}")
                    if resp.status_code == 204:
                        st.success("User deleted!")
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Failed to delete user."))
                except Exception as e:
                    st.error(f"Error deleting user: {e}")
    else:
        st.info("No users found.")


if choice == "Dashboard":
    st.header(":bar_chart: Dashboard")
    help_requests = get_help_requests()
    if help_requests:
        # Simulate "helped" status: even IDs are helped, odd IDs are not
        for r in help_requests:
            r["status"] = "Helped" if r["id"] % 2 == 0 else "Unhelped"
        df = pd.DataFrame([
            {
                "Title": r["title"],
                "User": r["creator"]["username"],
                "Status": r["status"],
                "Created At": r["created_at"]
            }
            for r in help_requests
        ])
        st.dataframe(df)
        # Pie chart: Helped vs Unhelped
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig = px.pie(status_counts, names="Status", values="Count", title="Helped vs Unhelped Requests")
        st.plotly_chart(fig, use_container_width=True)
        # Bar chart: Requests per user
        user_counts = df["User"].value_counts().reset_index()
        user_counts.columns = ["User", "Requests"]
        fig2 = px.bar(user_counts, x="User", y="Requests", title="Requests by User")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No help requests yet.")

elif choice == "Home":
    st.header("Welcome to TrustLoop!")
    st.write("A platform to request and offer help, and build your reputation.")
    help_requests = get_help_requests()
    if help_requests:
        df = pd.DataFrame([
            {
                "Title": r["title"],
                "Description": r["description"],
                "User": r["creator"]["username"],
                "Reputation": r["creator"]["reputation"],
                "Created At": r["created_at"]
            }
            for r in help_requests
        ])
        st.subheader("Recent Help Requests")
        st.dataframe(df)
        # Pie chart: requests per user
        user_counts = df["User"].value_counts().reset_index()
        user_counts.columns = ["User", "Requests"]
        fig = px.pie(user_counts, names="User", values="Requests", title="Help Requests by User")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No help requests yet.")

elif choice == "Login":
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            success, msg = login(username, password)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

elif choice == "Register":
    st.header("Register New Account")
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")
        if submitted:
            success, msg = register(username, email, password)
            if success:
                st.success(msg)
            else:
                st.error(msg)

elif choice == "Logout":
    st.session_state.pop("access_token", None)
    st.session_state.pop("user", None)
    st.success("Logged out successfully.")
    st.rerun()

elif choice == "Profile":
    st.header("User Profile")
    if not is_logged_in():
        st.warning("You must be logged in to view your profile.")
    else:
        profile = get_profile()
        if profile:
            st.write(f"**Username:** {profile['username']}")
            st.write(f"**Email:** {profile['email']}")
            st.write(f"**Reputation:** {profile['reputation']}")
            st.write(f"**Joined:** {profile['created_at']}")
            # Pie chart: user's help requests vs others
            help_requests = get_help_requests()
            user_requests = [r for r in help_requests if r["creator"]["username"] == profile["username"]]
            others = len(help_requests) - len(user_requests)
            pie_df = pd.DataFrame({
                "Type": ["Your Requests", "Others' Requests"],
                "Count": [len(user_requests), others]
            })
            fig = px.pie(pie_df, names="Type", values="Count", title="Your Requests vs Others")
            st.plotly_chart(fig, use_container_width=True)
            # Bar chart: Helped vs Unhelped for this user
            for r in user_requests:
                r["status"] = "Helped" if r["id"] % 2 == 0 else "Unhelped"
            status_counts = pd.Series([r["status"] for r in user_requests]).value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig2 = px.bar(status_counts, x="Status", y="Count", title="Your Helped vs Unhelped Requests")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.error("Could not load profile. Please log in again.")

elif choice == "Help Requests":
    st.header("Help Requests")
    if is_logged_in():
        with st.form("help_request_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            submitted = st.form_submit_button("Create Request")
            if submitted:
                if not title or not description:
                    st.warning("Title and description are required.")
                else:
                    resp = create_help_request(title, description)
                    if resp and resp.status_code == 201:
                        st.success("Help request created!")
                        st.rerun()
                    elif resp is not None:
                        st.error(resp.json().get("detail", "Failed to create help request."))
    else:
        st.info("Login to create a help request.")
    help_requests = get_help_requests()
    if help_requests:
        for r in help_requests:
            r["status"] = "Helped" if r["id"] % 2 == 0 else "Unhelped"
        df = pd.DataFrame([
            {
                "Title": r["title"],
                "Description": r["description"],
                "User": r["creator"]["username"],
                "Reputation": r["creator"]["reputation"],
                "Status": r["status"],
                "Created At": r["created_at"]
            }
            for r in help_requests
        ])
        st.dataframe(df)
        # Bar chart: requests per user
        user_counts = df["User"].value_counts().reset_index()
        user_counts.columns = ["User", "Requests"]
        fig = px.bar(user_counts, x="User", y="Requests", title="Help Requests by User")
        st.plotly_chart(fig, use_container_width=True)
        # Pie chart: Helped vs Unhelped
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig2 = px.pie(status_counts, names="Status", values="Count", title="Helped vs Unhelped Requests")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No help requests yet.")
