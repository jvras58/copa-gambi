"""Streamlit render functions — every section of the page in one place."""

import streamlit as st
from agno.run.team import TeamRunOutput

from copa_gambi.core.capabilities import Capabilities
from copa_gambi.core.schemas import DebateReport
from copa_gambi.ui.debate import DebateSetup
from copa_gambi.ui.report import guess_score, parse_report, strip_report_blocks


def _caps_badges(caps: Capabilities) -> str:
    if not caps.research_capable:
        return "🧠 só conhecimento"
    badges = ["🛠 tools"] if caps.use_tools else []
    if caps.use_skills:
        badges.append("📚 skills")
    return " · ".join(badges)


def render_participants(setup: DebateSetup) -> None:
    st.subheader("Participantes da room")
    columns = st.columns(min(len(setup.views), 4))
    for i, view in enumerate(setup.views):
        with columns[i % len(columns)].container(border=True):
            crown = "👑 " if view.is_moderator else ""
            st.markdown(f"{crown}**{view.participant.participant_id}**")
            st.caption(view.participant.model)
            if view.is_moderator:
                st.caption(f"moderador · {view.participant.specs.gpu_vram_gb:g} GB VRAM")
            else:
                st.caption(_caps_badges(view.caps))


def render_members(output: TeamRunOutput, setup: DebateSetup) -> None:
    if not output.member_responses:
        return
    st.subheader("Previsões dos debatedores")
    for member in output.member_responses:
        name = getattr(member, "agent_name", None) or "debatedor"
        content = str(member.content or "")
        score = guess_score(content)
        title = f"{name} — {score}" if score else name
        with st.expander(title):
            caps = setup.caps_for(name)
            if caps is not None:
                st.caption(_caps_badges(caps))
            st.markdown(content)


def _render_groups(report: DebateReport) -> None:
    for group in sorted(report.groups, key=lambda g: g.percentage, reverse=True):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{group.score}**")
            right.markdown(f"**{group.percentage:g}%**")
            st.progress(min(max(group.percentage / 100, 0.0), 1.0))
            if group.models:
                st.caption(" · ".join(group.models))
            for argument in group.arguments:
                st.markdown(f"- {argument}")


def render_report(output: TeamRunOutput) -> None:
    st.subheader("Relatório do moderador")
    content = str(output.content or "")
    report = parse_report(content)

    if report is None:
        st.info("O moderador não estruturou o relatório — exibindo o texto original.")
        st.markdown(content)
        return

    st.metric("Previsão final do debate", report.final_score)
    if report.rationale:
        st.caption(report.rationale)
    _render_groups(report)

    markdown = strip_report_blocks(content)
    if markdown:
        with st.expander("Relatório completo"):
            st.markdown(markdown)
