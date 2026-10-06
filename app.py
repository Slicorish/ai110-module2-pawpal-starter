from datetime import date

import streamlit as st

from pawpal_systems import Owner, Pet, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.caption("A pet care planner: add your pets and their tasks, then build today's plan.")

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

st.divider()

# The Owner lives in session_state so it survives Streamlit's reruns
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_time=120)
owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_time = int(
        st.number_input(
            "Time available today (minutes)", min_value=0, max_value=1440, value=owner.available_time
        )
    )

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        pet_name = st.text_input("Pet name", value="Mochi")
        birthday = st.date_input("Birthday", value=date(2020, 1, 1))
    with c2:
        species = st.selectbox("Species", ["dog", "cat", "bird", "other"])
        weight = st.number_input("Weight (kg)", min_value=0.1, value=5.0)
    with c3:
        gender = st.selectbox("Gender", ["F", "M"])
        color = st.text_input("Color", value="white")
    if st.form_submit_button("Add pet") and pet_name.strip():
        owner.add_pet(Pet(pet_name.strip(), species, birthday, float(weight), gender, color))
        st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    st.table(
        [
            {"name": p.name, "species": p.species, "age": p.age, "weight": p.weight, "color": p.color}
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.subheader("Tasks")
PRIORITIES = {"high": 1, "medium": 2, "low": 3}  # 1 is the most urgent

if owner.pets:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        pet_index = st.selectbox(
            "Pet", range(len(owner.pets)), format_func=lambda i: owner.pets[i].name
        )
    with col3:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col4:
        priority = st.selectbox("Priority", list(PRIORITIES), index=0)

    if st.button("Add task"):
        owner.add_task(
            Task(task_title, int(duration), date.today(), PRIORITIES[priority], owner.pets[pet_index])
        )
        st.success(f"Added task '{task_title}' for {owner.pets[pet_index].name}.")
else:
    st.info("Add a pet before adding tasks.")

if owner.schedule.tasks:
    st.table(
        [
            {
                "task": t.description,
                "pet": t.pet.name,
                "minutes": t.duration,
                "priority": t.priority,
                "done": t.completed,
            }
            for t in owner.schedule.tasks
        ]
    )
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Most urgent tasks first, as many as fit in the time available.")

if st.button("Generate schedule"):
    scheduler = owner.schedule
    scheduler.prioritize()
    plan = scheduler.fit_to_time()
    if plan:
        total = sum(t.duration for t in plan)
        st.success(f"{len(plan)} tasks planned, {total} of {owner.available_time} minutes used.")
        st.table(
            [
                {"order": i, "task": t.description, "pet": t.pet.name, "minutes": t.duration, "priority": t.priority}
                for i, t in enumerate(plan, start=1)
            ]
        )
    else:
        st.warning("Nothing fits in the time available.")
    left_out = scheduler.unscheduled()
    if left_out:
        st.warning(
            "Not enough time for: " + ", ".join(f"{t.description} ({t.pet.name})" for t in left_out)
        )
