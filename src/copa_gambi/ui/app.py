"""Streamlit entry point: `uv run --group ui streamlit run src/copa_gambi/ui/app.py`."""

import streamlit as st

from copa_gambi.core.config import settings
from copa_gambi.core.hub import HubError
from copa_gambi.ui.components import render_members, render_participants, render_report
from copa_gambi.ui.debate import load_setup, run_debate

st.set_page_config(page_title="copa-gambi", page_icon="⚽", layout="wide")
st.title("⚽ copa-gambi — debate de placar")

with st.sidebar:
    st.markdown(f"**Hub:** {settings.hub_base}")
    st.markdown(f"**Room:** {settings.room_code}")
    if st.button("Atualizar participantes"):
        st.session_state.pop("setup", None)
        st.session_state.pop("run_output", None)

if "setup" not in st.session_state:
    try:
        with st.spinner("Consultando a room no Gambi Hub…"):
            st.session_state["setup"] = load_setup(settings)
    except HubError as exc:
        st.error(f"Não consegui falar com o Hub: {exc}")
        st.stop()

setup = st.session_state["setup"]
render_participants(setup)

matchup = st.text_input(
    "Confronto",
    placeholder='ex.: "Brasil x Argentina — Copa do Mundo 2026, semifinal"',
)
if st.button("Rodar debate", type="primary", disabled=not matchup.strip()):
    with st.spinner("Debatedores pesquisando e o moderador consolidando…"):
        st.session_state["run_output"] = run_debate(matchup.strip(), setup, settings)

output = st.session_state.get("run_output")
if output is not None:
    render_members(output, setup)
    render_report(output)
