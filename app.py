# A program that implements a chemistry quiz application using Streamlit.
# Made by Josiah Anderson between 1st Jan '26 and 2nd March '26.
# NEA_chemistry_quiz_app/app.py

import streamlit as st
import json
import time
import pandas as pd
from utils import (
    tolerance_mark,
    apply_penalty,
    initialise_state,
    mark_checkbox,
    mark_fill_blank,
    render_media
)
# import os #removed os as it becomes unused after refactoring
from pathlib import Path
BASE_DIR = Path(__file__).parent
# =========================

st.set_page_config(page_title="Chemistry Quiz", layout="centered")
initialise_state(st.session_state)

# 🔒 Ensure title-page flag exists before use
# Defensive session-state initialisation
if "started" not in st.session_state:
    st.session_state.started = False

# Handle question advancement cleanly
if st.session_state.advance_question:
    st.session_state.index += 1
    st.session_state.start_time = time.time()
    st.session_state.answered = False
    st.session_state.advance_question = False

# =========================
# TITLE PAGE
# =========================

if not st.session_state.started:
    st.title("GCSE Chemistry Required Practical Quiz")
    st.subheader("Assess your understanding of core experimental chemistry")

    st.markdown(
        """
        ### Instructions
        - Answer each question carefully.
        - Some questions may include images or videos.
        - Numerical answers allow a small tolerance.
        - Your score may decrease with repeated attempts.
        - Click **Submit** to check your answer, then **Continue** to move on.
        """
    )

    # ---- Title image ----
    title_img = {
        # "image":"Media/temperature_image_title_page.png",
        # "image":"Media/schoolkids_sweaters_image_title_page.png",
        "image":"Media/schoolkids_labcoats_image_title_page.png"
        # OR you could use:
        # "video":"https://www.youtube.com/watch?v=/....."
    }
    render_media(title_img, BASE_DIR)

    # ---- Begin button ----
    if st.button("▶ Click to begin"):
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.rerun()

    st.stop()


# Load questions
with open("questions.json", "r") as f:
    QUESTIONS = json.load(f)

TOTAL_QUESTIONS = len(QUESTIONS)

# Guard against index overflow
if st.session_state.index >= TOTAL_QUESTIONS:
    current_q = None
else:
    current_q = QUESTIONS[st.session_state.index]

st.title("GCSE Chemistry RP Quiz")

# =========================
# QUIZ FINISHED
# =========================
if current_q is None:
    st.title("🎉 Quiz Complete")

    total_score = sum(r["score"] for r in st.session_state.results)
    percentage = (total_score / TOTAL_QUESTIONS) * 100

    st.write(f"Final score: **{percentage:.1f}%**")

    if percentage >= 80:
        st.balloons()

    # ----- Feedback breakdown table -----
    st.markdown("### Feedback Breakdown")

    df = pd.DataFrame(st.session_state.results)

    # Add 1-indexed question numbers
    df.insert(0, "Question", range(1, len(df) + 1))

    # Friendly display correctness values
    df["Correct"] = df["correct"].map({True: "✅", False: "❌"})

    # Rename question column properly
    df = df.rename(columns={"question": "Question Text"})

    # Select and order columns for display
    df = df[["Question", "Question Text", "Correct", "attempts", "score", "time"]]

    # Display without Pandas' 0-indexed row labels
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.stop()

# =========================
# QUESTION DISPLAY
# =========================

if st.session_state.start_time is None:
    st.session_state.start_time = time.time()

st.subheader(f"Question {st.session_state.index + 1} of {TOTAL_QUESTIONS}")
st.write(current_q["prompt"])

# ------- Media -------
# Only show media for question types that support it
# Follows my question-type design.
if current_q["type"] in ["numerical", "radio", "checkbox", "graph"]:
    render_media(current_q.get("media"), BASE_DIR)


# =========================
# ANSWER INPUT
# =========================

user_answer = None
user_answers = None

if current_q["type"] == "numerical":
    user_answer = st.number_input("Your answer", step=0.01)

elif current_q["type"] == "radio":
    user_answer = st.radio("Choose one:", current_q["choices"])

elif current_q["type"] == "checkbox":
    user_answers = []
    for i, choice in enumerate(current_q["choices"]):
        if st.checkbox(choice):
            user_answers.append(i)

elif current_q["type"] == "fill_blank":
    user_answers = []
    st.write(current_q["text"])
    for i in range(len(current_q["blanks"])):
        user_answers.append(
            st.text_input(f"Blank {i + 1}")
        )

elif current_q["type"] == "graph":
    user_answer = st.radio(
        "Select the correct graph:",
        range(len(current_q["graphs"])),
        format_func=lambda x: f"Graph {x + 1}"
    )
    st.image(current_q["graphs"][user_answer])

# =========================
# SUBMIT ANSWER
# =========================

submitted = st.button("Submit")

if submitted:
    qid = current_q["id"]
    st.session_state.current_qid = qid # Storing the qid safely

    st.session_state.attempts.setdefault(qid, 0)
    st.session_state.attempts[qid] += 1

    correct = False
    status = None
    correct_count = None
    total = None

    # Marking logic
    if current_q["type"] == "numerical":
        correct = tolerance_mark(
            user_answer,
            current_q["answer"]["value"],
            current_q["answer"]["tolerance"]
        )

    elif current_q["type"] == "radio":
        correct = (
            current_q["choices"].index(user_answer)
            == current_q["correct_index"]
        )

    elif current_q["type"] == "checkbox":
        correct = mark_checkbox(
            user_answers,
            current_q["correct_indices"]
        )

    elif current_q["type"] == "fill_blank":
        status, correct_count, total = mark_fill_blank(
            user_answers,
            current_q["blanks"]
        )
        correct = (status == "correct")

    elif current_q["type"] == "graph":
        correct = user_answer == current_q["correct_index"]

    # Store result temporarily
    st.session_state.answered = True
    st.session_state.last_result = {
        "correct": correct,
        "status": status,
        "correct_count": correct_count,
        "total": total,
        "user_answer": user_answer if user_answer is not None else user_answers
    }

# =========================
# FEEDBACK + CONTINUE
# =========================

if st.session_state.answered:
    # Feedback
    if current_q["type"] == "fill_blank":
        if st.session_state.last_result["status"] == "correct":
            st.success("Correct ✅")
        elif st.session_state.last_result["status"] == "partial":
            st.warning(
                f"Nearly correct ⚠️ ({st.session_state.last_result['correct_count']}/"
                f"{st.session_state.last_result['total']} blanks correct)"
            )
        else:
            st.error("Incorrect ❌")
    else:
        if st.session_state.last_result["correct"]:
            st.success("Correct ✅")
        else:
            st.error("Incorrect ❌")

    # Continue button
    if st.button("Continue"):
        # Calculate time taken
        time_taken = round(time.time() - st.session_state.start_time, 1)

        qid = st.session_state.get("current_qid")
        if qid is None: # Defensive check
            st.error("Internal error: Question ID missing.")
            st.stop()
        retries = st.session_state.attempts[qid] - 1

        # Scoring
        if current_q["type"] == "fill_blank":
            if st.session_state.last_result["status"] == "correct":
                score = 1
            elif st.session_state.last_result["status"] == "partial":
                score = 0.5
            else:
                score = 0
        else:
            score = apply_penalty(1, retries)

        # ✅ STORE RESULT BEFORE RERUN
        st.session_state.results.append({
            "question": current_q["prompt"],
            "user_answer": st.session_state.last_result["user_answer"],
            "correct": st.session_state.last_result["correct"],
            "attempts": retries + 1,
            "score": score,
            "time": time_taken,
            "explanation": current_q["explanation"]
        })

        # Advance question safely
        st.session_state.advance_question = True
        st.rerun()
