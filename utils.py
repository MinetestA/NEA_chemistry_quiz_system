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

def mark_checkbox(user_answers, correct_indices):
    return set(user_answers) == set(correct_indices)


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
