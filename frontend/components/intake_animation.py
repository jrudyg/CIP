# components/intake_animation.py
"""
CIP Intake Animation Component v2.1
Minimal vertical steps - success merged into steps

Usage:
    from components.intake_animation import render_intake_progress
    render_intake_progress(stage="extract", contract_id=None)
"""

import streamlit as st


def render_intake_progress(stage: str = "idle", contract_id: int = None) -> None:
    """
    Render vertical progress steps with integrated success state.
    
    Args:
        stage: Current stage - "idle", "upload", "extract", "analyze", "complete"
        contract_id: If complete, show contract ID in final step
    """
    
    complete = (stage == "complete" or contract_id is not None)
    
    stages = [
        ("upload", "Upload", "File received"),
        ("extract", "Extract", "Metadata extracted"),
        ("analyze", "Analyze", "Validating..."),
    ]
    
    # Add final step with dynamic text
    if complete and contract_id:
        stages.append(("complete", f"Stored (ID: {contract_id})", "Ready"))
    else:
        stages.append(("complete", "Complete", "Save to database"))
    
    stage_order = ["idle", "upload", "extract", "analyze", "complete"]
    current_idx = stage_order.index(stage) if stage in stage_order else 0
    
    if complete:
        current_idx = 5
    
    st.markdown("**Progress**")
    
    for i, (stage_key, label, desc) in enumerate(stages):
        stage_num = i + 1
        
        if complete or current_idx > stage_num:
            # Completed
            st.markdown(f'''
                <div style="display: flex; align-items: center; gap: 8px; padding: 5px 0; border-left: 2px solid #10B981; padding-left: 10px; margin-left: 6px;">
                    <span style="color: #10B981; font-size: 0.9rem;">✓</span>
                    <span style="color: #10B981; font-size: 0.8rem; font-weight: 500;">{label}</span>
                </div>
            ''', unsafe_allow_html=True)
        elif current_idx == stage_num:
            # Active
            st.markdown(f'''
                <div style="display: flex; align-items: center; gap: 8px; padding: 5px 0; border-left: 2px solid #8B5CF6; padding-left: 10px; margin-left: 6px; background: rgba(139, 92, 246, 0.1); border-radius: 0 6px 6px 0;">
                    <span style="color: #8B5CF6; font-size: 0.9rem;">●</span>
                    <div>
                        <span style="color: #A78BFA; font-size: 0.8rem; font-weight: 600;">{label}</span>
                        <span style="color: #7C3AED; font-size: 0.65rem; margin-left: 6px;">{desc}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            # Pending
            st.markdown(f'''
                <div style="display: flex; align-items: center; gap: 8px; padding: 5px 0; border-left: 2px solid #334155; padding-left: 10px; margin-left: 6px;">
                    <span style="color: #475569; font-size: 0.9rem;">○</span>
                    <span style="color: #475569; font-size: 0.8rem;">{label}</span>
                </div>
            ''', unsafe_allow_html=True)


def render_upload_another_link() -> bool:
    """
    Render subtle "Upload Another" link.
    Returns True if clicked.
    """
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    clicked = st.button("↻ Upload Another", key="btn_upload_another", type="secondary")
    
    if clicked:
        for key in list(st.session_state.keys()):
            if key.startswith("intake_"):
                del st.session_state[key]
        st.rerun()
    
    return clicked


def render_system_health() -> None:
    """Render compact system health indicator."""
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 6px; justify-content: flex-end;">
            <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%;"></span>
            <span style="color: #64748B; font-size: 0.7rem;">System Online</span>
        </div>
    ''', unsafe_allow_html=True)
