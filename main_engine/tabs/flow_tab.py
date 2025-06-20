import json
from pathlib import Path
import streamlit as st


def render(root: Path) -> None:
    """Render UI for flow configuration."""
    st.subheader("Xây dựng flow")
    st.markdown("**1. Chọn flow có sẵn hoặc upload file**")
    config_dir = root / "config"
    flows = [f.name for f in config_dir.glob("*.json") if f.name.endswith("flow_config.json")] or ["flow_config.json"]
    selected = st.selectbox("Chọn flow đã có:", options=flows)
    flow_file = config_dir / selected
    upload = st.file_uploader("Hoặc upload file flow JSON", type=["json"])
    if upload:
        flow_text = upload.getvalue().decode('utf-8')
    else:
        flow_text = flow_file.read_text(encoding='utf-8') if flow_file.exists() else '[]'

    st.markdown("**2. Chỉnh sửa hoặc tự tạo flow**")
    flow_text = st.text_area("Flow JSON (node: {id,label,next})", value=flow_text, height=200, key="flow_json")
    if st.button("Tạo flow từ modules"):
        mods = [p.stem for p in (root / 'modules').glob('*.py') if p.is_file()]
        gen = []
        for i, m in enumerate(mods):
            nxt = [mods[i+1]] if i+1 < len(mods) else []
            gen.append({"id": m, "label": m, "next": nxt})
        st.session_state["flow_json"] = json.dumps(gen, indent=2)

    cols = st.columns(2)
    with cols[0]:
        if st.button("Xem sơ đồ flow"):
            try:
                nodes = json.loads(flow_text)
                if not isinstance(nodes, list):
                    raise ValueError("Flow phải là mảng list của node dict")
                normalized = [
                    {"id": e, "label": e, "next": []} if isinstance(e, str) else e
                    for e in nodes
                ]
                dot = ['digraph G {', '  rankdir=LR;']
                for n in normalized:
                    nid = n.get('id')
                    label = n.get('label', nid)
                    dot.append('  "{}" [label="{}"];'.format(nid, label))
                for n in normalized:
                    nid = n.get('id')
                    for nxt in n.get('next', []):
                        dot.append('  "{}" -> "{}";'.format(nid, nxt))
                dot.append('}')
                st.graphviz_chart('\n'.join(dot))
            except Exception as e:
                st.error(f"Lỗi phân tích flow: {e}")
    with cols[1]:
        if st.button("Lưu flow.json"):
            try:
                parsed = json.loads(flow_text)
                flow_path = config_dir / selected
                flow_path.write_text(json.dumps(parsed, indent=2), encoding='utf-8')
                st.success(f"Đã lưu vào {flow_path.name}")
            except Exception as e:
                st.error(f"Lỗi lưu: {e}")
