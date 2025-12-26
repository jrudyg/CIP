# components/workflow_animation.py
"""
CIP Workflow Animation Component
Animated visualization of the CIP workflow process.

Usage:
    from components.workflow_animation import render_workflow_animation
    render_workflow_animation()
"""

import streamlit as st
import streamlit.components.v1 as components


WORKFLOW_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: transparent;
            color: #E2E8F0;
        }
        
        .workflow-container {
            padding: 8px 0 4px 0;
        }
        
        .workflow-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #E2E8F0;
            margin-bottom: 12px;
            opacity: 0;
            transform: translateY(-10px);
            transition: opacity 0.8s ease, transform 0.8s ease;
            cursor: pointer;
            display: inline-block;
        }
        
        .workflow-title:hover {
            color: #3B82F6;
        }
        
        .workflow-title.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .workflow-row {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
            min-height: 58px;
        }
        
        .row-label {
            width: 80px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #8B5CF6;
            text-transform: uppercase;
            flex-shrink: 0;
        }
        
        .row-content {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0;
        }
        
        .node {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            opacity: 0;
            transform: scale(0.8);
            transition: opacity 0.8s ease, transform 0.8s ease;
            flex-shrink: 0;
            width: 70px;
        }
        
        .node.visible {
            opacity: 1;
            transform: scale(1);
        }
        
        .node-icon {
            font-size: 1.6rem;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1E293B;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: box-shadow 0.3s ease, border-color 0.3s ease;
        }
        
        .node.visible .node-icon {
            box-shadow: 0 3px 10px rgba(59, 130, 246, 0.15);
        }
        
        .node-label {
            font-size: 0.55rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            color: #94A3B8;
            text-transform: uppercase;
        }
        
        .arrow-container {
            width: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        
        .arrow {
            display: flex;
            align-items: center;
            opacity: 0;
            transition: opacity 0.6s ease;
        }
        
        .arrow.visible {
            opacity: 1;
        }
        
        .arrow-line {
            height: 2px;
            background: linear-gradient(90deg, #3B82F6, #8B5CF6);
            border-radius: 1px;
            width: 16px;
        }
        
        .arrow.visible .arrow-line {
            animation: arrowPulse 2s ease-in-out infinite, arrowGrow 2s ease-in-out infinite;
        }
        
        .arrow-head {
            width: 0;
            height: 0;
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
            border-left: 6px solid #8B5CF6;
            filter: drop-shadow(0 0 2px rgba(139, 92, 246, 0.5));
            flex-shrink: 0;
        }
        
        .arrow.visible .arrow-head {
            animation: arrowHeadPulse 2s ease-in-out infinite;
        }
        
        /* Tagline styling */
        .workflow-tagline {
            text-align: center;
            margin-top: 8px;
            min-height: 28px;
        }
        
        .tagline-text {
            font-size: 0.9rem;
            font-weight: 600;
            font-style: italic;
            color: #A78BFA;
            opacity: 0;
            transition: opacity 0.6s ease;
            text-shadow: 0 0 15px rgba(139, 92, 246, 0.3);
        }
        
        .tagline-text.visible {
            opacity: 1;
        }
        
        .tagline-text.pulse {
            animation: taglinePulse 1.5s ease-in-out 3;
        }
        
        .tagline-text.bright {
            color: #C4B5FD;
            text-shadow: 0 0 20px rgba(139, 92, 246, 0.5);
        }
        
        @keyframes arrowPulse {
            0%, 100% {
                box-shadow: 0 0 3px rgba(59, 130, 246, 0.4);
            }
            50% {
                box-shadow: 0 0 10px rgba(139, 92, 246, 0.8);
            }
        }
        
        @keyframes arrowGrow {
            0%, 100% {
                width: 16px;
            }
            50% {
                width: 28px;
            }
        }
        
        @keyframes arrowHeadPulse {
            0%, 100% {
                filter: drop-shadow(0 0 2px rgba(139, 92, 246, 0.4));
            }
            50% {
                filter: drop-shadow(0 0 6px rgba(139, 92, 246, 0.9));
            }
        }
        
        @keyframes taglinePulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="workflow-container" id="workflowContainer">
        <div class="workflow-title" id="workflowTitle" onclick="restartAnimation()">CIP Workflow</div>
        
        <!-- Row 1: INTAKE -->
        <div class="workflow-row">
            <div class="row-label">Intake</div>
            <div class="row-content">
                <div class="node" data-index="0">
                    <div class="node-icon">📄</div>
                    <div class="node-label">Contract</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="0">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="1">
                    <div class="node-icon">🧠</div>
                    <div class="node-label">CIP</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="1">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="2">
                    <div class="node-icon">🏷️</div>
                    <div class="node-label">Metadata</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="2">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="3">
                    <div class="node-icon">💾</div>
                    <div class="node-label">Store</div>
                </div>
            </div>
        </div>
        
        <!-- Row 2: ANALYZE -->
        <div class="workflow-row">
            <div class="row-label">Analyze</div>
            <div class="row-content">
                <div class="node" data-index="4">
                    <div class="node-icon">🚦</div>
                    <div class="node-label">Risk</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="3">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="5">
                    <div class="node-icon">📝</div>
                    <div class="node-label">Redlines</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="4">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="6">
                    <div class="node-icon">⚖️</div>
                    <div class="node-label">Compare</div>
                </div>
            </div>
        </div>
        
        <!-- Row 3: LEARN -->
        <div class="workflow-row">
            <div class="row-label">Learn</div>
            <div class="row-content">
                <div class="node" data-index="7">
                    <div class="node-icon">📋</div>
                    <div class="node-label">Report</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="5">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="8">
                    <div class="node-icon">🤝</div>
                    <div class="node-label">Negotiate</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="6">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="9">
                    <div class="node-icon">📤</div>
                    <div class="node-label">Handoff</div>
                </div>
                <div class="arrow-container">
                    <div class="arrow" data-index="7">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                </div>
                <div class="node" data-index="10">
                    <div class="node-icon">🔄</div>
                    <div class="node-label">Feedback</div>
                </div>
            </div>
        </div>
        
        <!-- Tagline area -->
        <div class="workflow-tagline">
            <span class="tagline-text" id="taglineText"></span>
        </div>
    </div>

    <script>
        const nodes = document.querySelectorAll('.node');
        const arrows = document.querySelectorAll('.arrow');
        const title = document.getElementById('workflowTitle');
        const taglineText = document.getElementById('taglineText');
        
        // Row taglines
        const rowTaglines = [
            "Every contract, captured and cataloged",
            "Manage and mitigate risks",
            "Insights that drive performance"
        ];
        
        // Final tagline
        const finalTagline = "Building contract management as a core competency";
        
        let animationTimeout = null;
        
        function resetAnimation() {
            if (animationTimeout) {
                clearTimeout(animationTimeout);
            }
            
            title.classList.remove('visible');
            nodes.forEach(node => node.classList.remove('visible'));
            arrows.forEach(arrow => arrow.classList.remove('visible'));
            taglineText.classList.remove('visible', 'pulse', 'bright');
            taglineText.textContent = '';
        }
        
        function showTagline(text) {
            taglineText.classList.remove('visible', 'pulse', 'bright');
            setTimeout(() => {
                taglineText.textContent = text;
                taglineText.classList.add('visible');
            }, 200);
        }
        
        function runAnimation() {
            resetAnimation();
            
            let delay = 200;
            
            // Timing (2x slower)
            const nodeDelay = 600;
            const arrowDelay = 400;
            const rowPause = 400;
            
            // Show title first
            setTimeout(() => {
                title.classList.add('visible');
            }, delay);
            delay += 1000;
            
            // Row 1: INTAKE (4 nodes, 3 arrows)
            for (let i = 0; i <= 3; i++) {
                const nodeIndex = i;
                const arrowIndex = i;
                
                setTimeout(() => {
                    const node = document.querySelector(`.node[data-index="${nodeIndex}"]`);
                    if (node) node.classList.add('visible');
                }, delay);
                delay += nodeDelay;
                
                if (i < 3) {
                    setTimeout(() => {
                        const arrow = document.querySelector(`.arrow[data-index="${arrowIndex}"]`);
                        if (arrow) arrow.classList.add('visible');
                    }, delay);
                    delay += arrowDelay;
                }
            }
            
            // Show INTAKE tagline
            setTimeout(() => {
                showTagline(rowTaglines[0]);
            }, delay);
            delay += rowPause + 800;
            
            // Row 2: ANALYZE (3 nodes, 2 arrows)
            for (let i = 4; i <= 6; i++) {
                const nodeIndex = i;
                const arrowIndex = i - 1;
                
                setTimeout(() => {
                    const node = document.querySelector(`.node[data-index="${nodeIndex}"]`);
                    if (node) node.classList.add('visible');
                }, delay);
                delay += nodeDelay;
                
                if (i < 6) {
                    setTimeout(() => {
                        const arrow = document.querySelector(`.arrow[data-index="${arrowIndex}"]`);
                        if (arrow) arrow.classList.add('visible');
                    }, delay);
                    delay += arrowDelay;
                }
            }
            
            // Show ANALYZE tagline
            setTimeout(() => {
                showTagline(rowTaglines[1]);
            }, delay);
            delay += rowPause + 800;
            
            // Row 3: LEARN (4 nodes, 3 arrows)
            for (let i = 7; i <= 10; i++) {
                const nodeIndex = i;
                const arrowIndex = i - 2;
                
                setTimeout(() => {
                    const node = document.querySelector(`.node[data-index="${nodeIndex}"]`);
                    if (node) node.classList.add('visible');
                }, delay);
                delay += nodeDelay;
                
                if (i < 10) {
                    setTimeout(() => {
                        const arrow = document.querySelector(`.arrow[data-index="${arrowIndex}"]`);
                        if (arrow) arrow.classList.add('visible');
                    }, delay);
                    delay += arrowDelay;
                }
            }
            
            // Show LEARN tagline
            setTimeout(() => {
                showTagline(rowTaglines[2]);
            }, delay);
            delay += 1500;
            
            // Show final tagline
            setTimeout(() => {
                showTagline(finalTagline);
            }, delay);
            delay += 800;
            
            // Pulse final tagline
            setTimeout(() => {
                taglineText.classList.add('pulse');
            }, delay);
            delay += 4500; // 3 pulses × 1.5s
            
            // Stay bright
            setTimeout(() => {
                taglineText.classList.remove('pulse');
                taglineText.classList.add('bright');
            }, delay);
        }
        
        function restartAnimation() {
            runAnimation();
        }
        
        // Start animation on load
        document.addEventListener('DOMContentLoaded', runAnimation);
        
        // Also start immediately in case DOM is already loaded
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(runAnimation, 100);
        }
    </script>
</body>
</html>
'''


def render_workflow_animation(height: int = 320) -> None:
    """
    Render the CIP workflow animation.
    
    Args:
        height: Height of the animation container in pixels
    """
    components.html(WORKFLOW_HTML, height=height, scrolling=False)
