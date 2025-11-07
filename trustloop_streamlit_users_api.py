import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

API_URL = "http://localhost:8000"

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
            return None
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

def get_all_users():
    try:
        resp = requests.get(f"{API_URL}/users")
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Error fetching users: {e}")
    return []

def delete_user(user_id):
    try:
        resp = requests.delete(f"{API_URL}/users/{user_id}")
        return resp.status_code == 204
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False

def update_user(user_id, username=None, email=None, reputation=None):
    data = {}
    if username:
        data["username"] = username
    if email:
        data["email"] = email
    if reputation is not None:
        data["reputation"] = reputation
    try:
        resp = requests.put(f"{API_URL}/users/{user_id}", params=data)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(resp.json().get("detail", "Failed to update user."))
    except Exception as e:
        st.error(f"Error updating user: {e}")
    return None

# ...existing UI code, but add a new section for user management...
