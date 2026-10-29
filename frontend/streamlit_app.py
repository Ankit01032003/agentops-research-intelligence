
import os

import requests
import streamlit as st


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")
REQUEST_TIMEOUT = 300

st.set_page_config(
    page_title="AgentOps Research Intelligence",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 AgentOps Research Intelligence")
st.write(
    "An AI research workspace combining planning, web search, "
    "document retrieval, evidence review, and report generation."
)


def display_report(result, prefix="research_report"):
    run_id = result.get("run_id", "unknown")
    report = result.get("report", "No report was returned.")

    st.subheader("Research plan")
    for index, task in enumerate(result.get("plan", []), start=1):
        st.write(f"{index}. {task}")

    st.subheader("Evidence review")
    st.markdown(result.get("verification", "No review returned."))

    sources = result.get("sources", [])
    st.subheader(f"Sources ({len(sources)})")

    if not sources:
        st.warning("No supporting sources were retrieved.")
    else:
        for index, source in enumerate(sources, start=1):
            title = source.get("title") or "Untitled source"
            source_type = source.get("source_type", "unknown")

            with st.expander(f"{index}. {title} — {source_type}"):
                url = source.get("url")
                if url:
                    st.markdown(f"[Open source]({url})")
                elif source.get("chunk_index") is not None:
                    st.caption(
                        f"Document chunk: {source['chunk_index']}"
                    )

                st.write(source.get("content", "No content available."))

    st.subheader("Final report")
    st.markdown(report)

    st.download_button(
        "Download research report",
        data=report,
        file_name=f"{prefix}_{run_id[:8]}.md",
        mime="text/markdown",
        key=f"download_{prefix}_{run_id}",
    )


with st.sidebar:
    st.header("System status")

    if st.button("Check API connection"):
        try:
            response = requests.get(
                f"{API_URL}/health",
                timeout=10,
            )
            response.raise_for_status()
            st.success("API is online.")
        except requests.RequestException:
            st.error("API unavailable. Check the API container.")

    st.caption(f"API endpoint: {API_URL}")

    st.divider()
    st.header("Knowledge base")
    st.write("Upload PDF, TXT, or Markdown files.")

    uploaded_files = st.file_uploader(
        "Choose documents",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
    )

    if st.button(
        "Index documents",
        disabled=not uploaded_files,
    ):
        for uploaded_file in uploaded_files:
            try:
                with st.spinner(f"Indexing {uploaded_file.name}..."):
                    response = requests.post(
                        f"{API_URL}/documents",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type
                                or "application/octet-stream",
                            )
                        },
                        timeout=180,
                    )
                    response.raise_for_status()
                    result = response.json()

                st.success(
                    f"{result['filename']}: "
                    f"{result['chunks_added']} chunks indexed."
                )

            except requests.RequestException as exc:
                detail = (
                    exc.response.text
                    if isinstance(exc, requests.HTTPError)
                    and exc.response is not None
                    else str(exc)
                )
                st.error(
                    f"Could not index {uploaded_file.name}: {detail}"
                )


st.divider()
st.header("Research workspace")

question = st.text_area(
    "Research question",
    placeholder=(
        "Compare agentic AI frameworks and explain their "
        "strengths, limitations, and practical use cases."
    ),
    height=120,
    max_chars=2000,
)

if st.button(
    "Start research",
    type="primary",
    disabled=len(question.strip()) < 10,
):
    try:
        with st.spinner(
            "Planning, collecting evidence, reviewing sources, "
            "and generating your report..."
        ):
            response = requests.post(
                f"{API_URL}/research",
                json={"question": question.strip()},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()

        st.success(f"Research run completed: {result['run_id']}")
        display_report(result)

    except requests.HTTPError as exc:
        detail = (
            exc.response.text
            if exc.response is not None
            else str(exc)
        )
        st.error(f"The research API returned an error: {detail}")

    except requests.Timeout:
        st.error(
            "The research request timed out. Check the API logs "
            "to see whether processing is still running."
        )

    except requests.RequestException as exc:
        st.error(f"Cannot reach the API: {exc}")


st.divider()
st.header("Research history")

if st.button("Refresh history"):
    st.rerun()

try:
    response = requests.get(
        f"{API_URL}/runs",
        params={"limit": 20},
        timeout=15,
    )
    response.raise_for_status()
    runs = response.json().get("runs", [])

    if not runs:
        st.info("No saved research runs found yet.")
    else:
        # Use run_id as the unique identifier, not created_at.
        labels = [
            (
                f"{run.get('question', 'Untitled')[:80]} "
                f"| {run.get('created_at', '')} "
                f"| {run['run_id'][:8]}"
            )
            for run in runs
        ]

        selected_index = st.selectbox(
            "Choose a previous research run",
            options=list(range(len(runs))),
            format_func=lambda index: labels[index],
        )

        selected_run = runs[selected_index]
        selected_run_id = selected_run["run_id"]

        st.caption(f"Run ID: {selected_run_id}")

        if st.button("Load saved report"):
            with st.spinner("Loading saved research..."):
                detail = requests.get(
                    f"{API_URL}/runs/{selected_run_id}",
                    timeout=30,
                )
                detail.raise_for_status()
                saved_result = detail.json()

            st.write("**Research question:**")
            st.write(saved_result.get("question", "Not available"))
            display_report(saved_result, prefix="saved_report")

except requests.RequestException as exc:
    st.error(f"Unable to load research history: {exc}")


st.caption(
    "Research results depend on available sources and model output. "
    "Verify important claims against original sources."
)
