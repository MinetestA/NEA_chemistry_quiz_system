from pathlib import Path
import streamlit as st

def render_media(media: dict, base_dir: Path):
    """
    Renders images and videos for a question.
    Supports both local files and external URLs (e.g. YouTube).
    Defensive, reusable, NEA-quality and fully compatilbe with my
    """
    if not media:
        return

    # ----- IMAGE -----
    if media.get("image"):
        image = media["image"]
        if image.startswith("http://") or image.startswith("https://"):
            st.image(image)
        else:
            image_path = base_dir / image
            if image_path.exists():
                st.image(str(image_path))
            else:
                st.warning(f"Image not found: {image}")

    # ----- VIDEO -----
    if media.get("video"):
        video = media["video"]
        if video.startswith("http://") or video.startswith("https://"):  # Simplify to just video.startswith("http")
            st.video(video)  # YouTube / online video
        else:
            video_path = base_dir / video
            if video_path.exists():
                st.video(str(video_path))
            else:
                st.warning(f"Video not found: {video}")


def tolerance_mark(user_answer, correct_answer, tolerance):
    return abs(user_answer - correct_answer) <= tolerance


def apply_penalty(score, retries):
    if retries == 0:
        return score
    return max(0, score - retries)


def initialise_state(st):
    defaults = {
        "started": False,
        "index": 0,
        "attempts": {},
        "results": [],
        "start_time": None,
        "answered": False,
        "last_result": None,
        "advance_question": False,
        "current_qid": None
    }
    for key, value in defaults.items():
        if key not in st:
            st[key] = value


def mark_checkbox(user_answer, correct_answers, tolerance):
    # Defensive: ensure correct_answers is a list
    if isinstance(correct_answers, str):
        correct_answers = [correct_answers]

    #Defensive: handle empty selections safely
    if user_answer is None:
        user_answer = []

    user_set = set(user_answer)
    correct_set = set(correct_answers)

    correct_selected = len(user_set & correct_set)
    incorrect_selected = len(user_set - correct_set)

    total_correct = len(correct_set)

    if total_correct == 0:
        return "incorrect", 0, 0

    # Proportion correct, penalising wrong selections
    net_score = correct_selected - incorrect_selected
    proportion = max(0, net_score) / total_correct

    if proportion == 1.0 and incorrect_selected == 0:
        return "correct", correct_selected, total_correct

    elif proportion >= tolerance:
        return "partial", correct_selected, total_correct

    else:
        return "incorrect", correct_selected, total_correct


def mark_fill_blank(user_inputs, correct_words):
    correct_count = 0
    total = len(correct_words)

    for user, correct in zip(user_inputs, correct_words):
        if user.strip().lower() == correct.lower():
            correct_count += 1

    proportion = correct_count / total

    if proportion == 1:
        return "correct", correct_count, total
    elif proportion >= 0.6:
        return "partial", correct_count, total
    else:
        return "incorrect", correct_count, total
