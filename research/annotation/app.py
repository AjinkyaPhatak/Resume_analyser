"""Streamlit annotation app: rate how well a candidate bio fits a job description (0-3).

    streamlit run research/annotation/app.py
    streamlit run research/annotation/app.py -- --config configs/annotation.yaml

Annotators see only the job description and the bio: no model scores, gender, occupation
or relevance labels. Each annotator works through all pairs in their own random order;
ratings are saved immediately to research/annotation/labels/<annotator>.csv, so the app
can be closed and reopened at any time. Read research/annotation/GUIDELINES.md first.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.annotation.storage import (  # noqa: E402
    annotator_order, labels_path, load_ratings, save_rating,
)
from research.common.config import load_config, repo_path  # noqa: E402

SCALE_HELP = {
    3: "3 - Strong fit: same occupation, core requirements evident",
    2: "2 - Partial fit: same/closely related occupation, notable gaps",
    1: "1 - Weak fit: related field or transferable skills, different occupation",
    0: "0 - No fit: unrelated occupation",
}


@st.cache_data
def load_sample(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=os.environ.get("RESEARCH_ANNOTATION_CONFIG", "configs/annotation.yaml"))
    args, _ = p.parse_known_args()
    cfg = load_config(args.config)["annotation"]
    sample = load_sample(str(repo_path(cfg["sample_csv"]))).set_index("pair_id")

    st.set_page_config(page_title="Resume-job fit annotation", layout="wide")
    st.title("Resume-job fit annotation")
    st.caption("Read GUIDELINES.md before starting. Rate professional fit only; ignore names, "
               "pronouns and any other personal characteristics.")

    name = st.sidebar.text_input("Your name (used for your ratings file)", key="annotator")
    if not name.strip():
        st.info("Enter your name in the sidebar to start.")
        return
    path = labels_path(repo_path(cfg["labels_dir"]), name)
    done = load_ratings(path).set_index("pair_id") if path.exists() else pd.DataFrame()
    order = annotator_order(list(sample.index), name)
    remaining = [pid for pid in order if pid not in done.index]

    st.sidebar.progress(len(done) / len(order), text=f"{len(done)} / {len(order)} rated")
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    st.sidebar.markdown(f"Ratings file: `{shown}`")
    mode = st.sidebar.radio("Show", ["Next unrated pair", "Revisit a rated pair"])
    if mode == "Revisit a rated pair":
        if done.empty:
            st.sidebar.write("Nothing rated yet.")
            return
        pid = st.sidebar.selectbox("Pair", [p for p in order if p in done.index])
    else:
        if not remaining:
            st.success("All pairs rated - thank you! You can revisit pairs from the sidebar.")
            return
        pid = remaining[0]

    row = sample.loc[pid]
    left, right = st.columns(2)
    with left:
        st.subheader("Job description")
        st.markdown(f"**{row['jd_title']}**")
        st.text_area("JD", row["jd_text"], height=460, disabled=True, label_visibility="collapsed")
    with right:
        st.subheader("Candidate bio")
        st.text_area("Bio", row["bio_text"], height=460, disabled=True, label_visibility="collapsed")

    prev = done.loc[pid] if pid in done.index else None
    with st.form(f"rate_{pid}", clear_on_submit=True):
        labels = list(SCALE_HELP.values())
        choice = st.radio("How well does this candidate fit this job?", labels, horizontal=False, key=f"rating_{pid}",
                          index=None if prev is None else list(SCALE_HELP).index(int(prev["rating"])))
        rating = None if choice is None else int(choice[0])     # labels start with the digit
        comment = st.text_input("Comment (optional; e.g. 'bio too vague', 'unsure')",
                                value="" if prev is None else str(prev["comment"]))
        if st.form_submit_button("Save and continue", type="primary"):
            if rating is None:
                st.error("Pick a rating first.")
            else:
                save_rating(path, pid, int(rating), comment, tuple(cfg["scale"]))
                st.rerun()
    st.caption(f"Pair {pid}")


if __name__ == "__main__":
    main()
