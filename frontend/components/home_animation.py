# components/home_animation.py
"""
CIP Unified Home Animation v1.0
Combines CIP Workflow + CIP Learning + ALIGNED Trophy + Times Square Celebration

Animation Sequence:
1. CIP Workflow (left) - ~17s
2. CIP Learning (right) - starts at 15s, ~20s duration
3. ALIGNED Trophy appears in Workflow Row 2 Col 4
4. Times Square Drop - full screen celebration finale

Usage:
    from components.home_animation import render_home_animation
    render_home_animation()
"""

import streamlit as st
import streamlit.components.v1 as components


HOME_ANIMATION_HTML = '''
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
            overflow: hidden;
        }
        
        .home-container {
            display: flex;
            gap: 20px;
            padding: 8px 0;
            position: relative;
        }
        
        /* ============================================
           LEFT ZONE: CIP WORKFLOW
           ============================================ */
        .workflow-zone {
            flex: 1;
            min-width: 0;
        }
        
        .workflow-container {
            padding: 8px 0 4px 0;
        }
        
        .workflow-title, .learning-title {
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
        
        .workflow-title:hover, .learning-title:hover {
            color: #3B82F6;
        }
        
        .workflow-title.visible, .learning-title.visible {
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
            width: 70px;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #8B5CF6;
            text-transform: uppercase;
            flex-shrink: 0;
        }
        
        .row-content {
            display: flex;
            align-items: center;
            flex-wrap: nowrap;
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
            width: 60px;
        }
        
        .node.visible {
            opacity: 1;
            transform: scale(1);
        }
        
        .node-icon {
            font-size: 1.4rem;
            width: 40px;
            height: 40px;
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
            font-size: 0.5rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            color: #94A3B8;
            text-transform: uppercase;
        }
        
        .arrow-container {
            width: 30px;
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
            width: 14px;
        }
        
        .arrow.visible .arrow-line {
            animation: arrowPulse 2s ease-in-out infinite, arrowGrow 2s ease-in-out infinite;
        }
        
        .arrow-head {
            width: 0;
            height: 0;
            border-top: 3px solid transparent;
            border-bottom: 3px solid transparent;
            border-left: 5px solid #8B5CF6;
            filter: drop-shadow(0 0 2px rgba(139, 92, 246, 0.5));
            flex-shrink: 0;
        }
        
        .arrow.visible .arrow-head {
            animation: arrowHeadPulse 2s ease-in-out infinite;
        }
        
        /* Workflow Tagline */
        .workflow-tagline {
            text-align: center;
            margin-top: 8px;
            min-height: 28px;
        }
        
        .tagline-text {
            font-size: 0.85rem;
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
        
        /* ============================================
           ALIGNED TROPHY - Row 2 Col 4
           ============================================ */
        .trophy-node {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            opacity: 0;
            transform: scale(0.3);
            transition: opacity 1s ease, transform 1s cubic-bezier(0.34, 1.56, 0.64, 1);
            flex-shrink: 0;
            width: 60px;
        }
        
        .trophy-node.visible {
            opacity: 1;
            transform: scale(1);
        }
        
        .trophy-icon {
            font-size: 1.6rem;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #F59E0B, #D97706);
            border-radius: 10px;
            border: 2px solid #FCD34D;
            position: relative;
            overflow: visible;
        }
        
        .trophy-node.visible .trophy-icon {
            animation: trophyGlow 2s ease-in-out infinite;
        }
        
        .trophy-label {
            font-size: 0.55rem;
            font-weight: 700;
            letter-spacing: 1px;
            color: #FCD34D;
            text-transform: uppercase;
            text-shadow: 0 0 10px rgba(252, 211, 77, 0.5);
        }
        
        @keyframes trophyGlow {
            0%, 100% {
                box-shadow: 0 0 15px rgba(245, 158, 11, 0.5),
                            0 0 30px rgba(245, 158, 11, 0.3),
                            inset 0 0 10px rgba(255, 255, 255, 0.2);
            }
            50% {
                box-shadow: 0 0 25px rgba(245, 158, 11, 0.8),
                            0 0 50px rgba(245, 158, 11, 0.5),
                            inset 0 0 15px rgba(255, 255, 255, 0.3);
            }
        }
        
        /* ============================================
           RIGHT ZONE: CIP LEARNING
           ============================================ */
        .learning-zone {
            flex: 1;
            min-width: 0;
        }
        
        .learning-container {
            padding: 8px 0 4px 0;
            min-height: 280px;
            position: relative;
        }
        
        .learning-stage {
            position: relative;
            width: 100%;
            height: 240px;
        }
        
        /* Brain tagline */
        .brain-tagline {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, 65px);
            font-size: 0.85rem;
            font-weight: 600;
            font-style: italic;
            color: #A78BFA;
            opacity: 0;
            transition: opacity 0.6s ease;
            white-space: nowrap;
            text-align: center;
            text-shadow: 0 0 15px rgba(139, 92, 246, 0.3);
        }
        
        .brain-tagline.visible {
            opacity: 1;
        }
        
        .brain-tagline.pulse {
            animation: taglinePulse 1.5s ease-in-out 3;
        }
        
        .brain-tagline.bright {
            opacity: 1;
            color: #C4B5FD;
            text-shadow: 0 0 20px rgba(139, 92, 246, 0.5);
        }
        
        /* Input section (left side) */
        .input-section {
            position: absolute;
            left: 5px;
            top: 0;
            bottom: 40px;
            width: 70px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 8px 0;
        }
        
        .input-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .input-group-label {
            font-size: 0.55rem;
            font-weight: 700;
            letter-spacing: 1px;
            color: #3B82F6;
            text-transform: uppercase;
            margin-bottom: 2px;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .input-group-label.visible {
            opacity: 1;
        }
        
        .input-node {
            display: flex;
            align-items: center;
            gap: 3px;
            opacity: 0;
            transform: translateX(-15px);
            transition: opacity 0.5s ease, transform 0.5s ease;
        }
        
        .input-node.visible {
            opacity: 1;
            transform: translateX(0);
        }
        
        .input-icon {
            font-size: 1rem;
            width: 26px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1E293B;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .input-node.visible .input-icon {
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.2);
        }
        
        /* Learning arrows */
        .learn-arrow-container {
            position: absolute;
            display: flex;
            align-items: center;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .learn-arrow-container.visible {
            opacity: 1;
        }
        
        .contract-arrow-1 { left: 80px; top: 30px; transform: rotate(14deg); }
        .contract-arrow-2 { left: 80px; top: 52px; transform: rotate(7deg); }
        .contract-arrow-3 { left: 80px; top: 74px; transform: rotate(2deg); }
        
        .feedback-arrow-1 { left: 80px; bottom: 85px; transform: rotate(-2deg); }
        .feedback-arrow-2 { left: 80px; bottom: 63px; transform: rotate(-7deg); }
        .feedback-arrow-3 { left: 80px; bottom: 41px; transform: rotate(-14deg); }
        
        .learn-arrow-line {
            height: 2px;
            background: linear-gradient(90deg, #3B82F6, #8B5CF6);
            border-radius: 1px;
            width: 30px;
        }
        
        .learn-arrow-container.visible .learn-arrow-line {
            animation: arrowPulse 2s ease-in-out infinite, inputArrowGrow 2s ease-in-out infinite;
        }
        
        .learn-arrow-head {
            width: 0;
            height: 0;
            border-top: 3px solid transparent;
            border-bottom: 3px solid transparent;
            border-left: 5px solid #8B5CF6;
            filter: drop-shadow(0 0 2px rgba(139, 92, 246, 0.5));
            flex-shrink: 0;
        }
        
        .learn-arrow-container.visible .learn-arrow-head {
            animation: arrowHeadPulse 2s ease-in-out infinite;
        }
        
        /* Central brain */
        .brain-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -55%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        
        .brain-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at 30% 30%, #1E293B, #0F172A);
            border-radius: 50%;
            border: 2px solid #8B5CF6;
            opacity: 0;
            transition: all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        }
        
        .brain-icon.visible {
            opacity: 1;
        }
        
        .brain-icon.small { width: 50px; height: 50px; font-size: 1.4rem; }
        .brain-icon.large { width: 58px; height: 58px; font-size: 1.6rem; }
        .brain-icon.xl { width: 66px; height: 66px; font-size: 1.8rem; }
        .brain-icon.xxl { width: 74px; height: 74px; font-size: 2rem; }
        .brain-icon.xxxl { width: 82px; height: 82px; font-size: 2.2rem; }
        .brain-icon.xxxxl { width: 90px; height: 90px; font-size: 2.4rem; }
        
        .brain-label {
            font-size: 0.6rem;
            font-weight: 700;
            letter-spacing: 1px;
            color: #A78BFA;
            text-transform: uppercase;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .brain-label.visible {
            opacity: 1;
        }
        
        /* Output section (right side) */
        .output-section {
            position: absolute;
            right: 5px;
            top: 0;
            bottom: 40px;
            width: 60px;
            display: flex;
            flex-direction: column;
            justify-content: space-around;
            padding: 15px 0;
        }
        
        .output-node {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 3px;
            opacity: 0;
            transform: translateX(15px);
            transition: opacity 0.5s ease, transform 0.5s ease;
        }
        
        .output-node.visible {
            opacity: 1;
            transform: translateX(0);
        }
        
        .output-icon {
            font-size: 1rem;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1E293B;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .output-node.visible .output-icon {
            box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
        }
        
        .output-label {
            font-size: 0.5rem;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
        }
        
        /* Output arrows */
        .output-arrow-container {
            position: absolute;
            display: flex;
            align-items: center;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .output-arrow-container.visible {
            opacity: 1;
        }
        
        .faster-arrow { right: 70px; top: 35px; }
        .smarter-arrow { right: 70px; top: 50%; transform: translateY(-50%); }
        .safer-arrow { right: 70px; bottom: 55px; }
        
        .output-arrow-line {
            height: 2px;
            background: linear-gradient(90deg, #8B5CF6, #3B82F6);
            border-radius: 1px;
            width: 25px;
        }
        
        .output-arrow-container.visible .output-arrow-line {
            animation: arrowPulse 2s ease-in-out infinite;
        }
        
        .output-arrow-head {
            width: 0;
            height: 0;
            border-top: 3px solid transparent;
            border-bottom: 3px solid transparent;
            border-left: 5px solid #3B82F6;
            filter: drop-shadow(0 0 2px rgba(59, 130, 246, 0.5));
        }
        
        /* ============================================
           TIMES SQUARE CELEBRATION
           ============================================ */
        .times-square-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s ease;
        }
        
        .times-square-overlay.visible {
            opacity: 1;
            pointer-events: auto;
        }
        
        .countdown {
            font-size: 8rem;
            font-weight: 900;
            color: #FCD34D;
            text-shadow: 0 0 50px rgba(252, 211, 77, 0.8),
                         0 0 100px rgba(252, 211, 77, 0.5);
            opacity: 0;
            transform: scale(2);
            transition: opacity 0.3s ease, transform 0.3s ease;
        }
        
        .countdown.visible {
            opacity: 1;
            transform: scale(1);
        }
        
        .trophy-drop {
            position: absolute;
            top: -150px;
            font-size: 10rem;
            filter: drop-shadow(0 0 50px rgba(245, 158, 11, 0.8));
            transition: top 1.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        .trophy-drop.dropped {
            top: 30%;
        }
        
        .aligned-text {
            font-size: 5rem;
            font-weight: 900;
            letter-spacing: 15px;
            background: linear-gradient(90deg, #F59E0B, #FCD34D, #F59E0B);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            opacity: 0;
            transform: scale(0.5);
            transition: opacity 0.8s ease, transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
            text-shadow: none;
            filter: drop-shadow(0 0 30px rgba(245, 158, 11, 0.5));
        }
        
        .aligned-text.visible {
            opacity: 1;
            transform: scale(1);
        }
        
        .subtitle-text {
            font-size: 1.5rem;
            color: #A78BFA;
            margin-top: 20px;
            opacity: 0;
            transition: opacity 1s ease;
        }
        
        .subtitle-text.visible {
            opacity: 1;
        }
        
        /* Confetti */
        .confetti-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10000;
            overflow: hidden;
        }
        
        .confetti {
            position: absolute;
            width: 10px;
            height: 10px;
            opacity: 0;
        }
        
        .confetti.active {
            opacity: 1;
            animation: confettiFall 3s ease-out forwards;
        }
        
        @keyframes confettiFall {
            0% {
                transform: translateY(-100vh) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(720deg);
                opacity: 0;
            }
        }
        
        /* Firework bursts */
        .firework {
            position: absolute;
            width: 5px;
            height: 5px;
            border-radius: 50%;
            opacity: 0;
        }
        
        .firework.burst {
            animation: fireworkBurst 1s ease-out forwards;
        }
        
        @keyframes fireworkBurst {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            50% {
                transform: scale(20);
                opacity: 0.8;
            }
            100% {
                transform: scale(40);
                opacity: 0;
            }
        }
        
        /* Light rays */
        .light-rays {
            position: absolute;
            width: 100%;
            height: 100%;
            background: radial-gradient(ellipse at center, 
                rgba(245, 158, 11, 0.3) 0%, 
                transparent 70%);
            opacity: 0;
            animation: none;
        }
        
        .light-rays.active {
            animation: rayPulse 2s ease-in-out infinite;
        }
        
        @keyframes rayPulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.6; }
        }
        
        /* ============================================
           SHARED ANIMATIONS
           ============================================ */
        @keyframes arrowPulse {
            0%, 100% {
                box-shadow: 0 0 3px rgba(59, 130, 246, 0.4);
            }
            50% {
                box-shadow: 0 0 10px rgba(139, 92, 246, 0.8);
            }
        }
        
        @keyframes arrowGrow {
            0%, 100% { width: 14px; }
            50% { width: 22px; }
        }
        
        @keyframes inputArrowGrow {
            0%, 100% { width: 30px; }
            50% { width: 45px; }
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
    <div class="home-container">
        <!-- ========================================
             LEFT ZONE: CIP WORKFLOW
             ======================================== -->
        <div class="workflow-zone">
            <div class="workflow-container">
                <div class="workflow-title" id="workflowTitle" onclick="restartAllAnimations()">CIP Workflow</div>
                
                <!-- Row 1: INTAKE -->
                <div class="workflow-row">
                    <div class="row-label">Intake</div>
                    <div class="row-content">
                        <div class="node" id="node0">
                            <div class="node-icon">📄</div>
                            <div class="node-label">Contract</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow0">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node1">
                            <div class="node-icon">🧠</div>
                            <div class="node-label">CIP</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow1">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node2">
                            <div class="node-icon">🏷️</div>
                            <div class="node-label">Metadata</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow2">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node3">
                            <div class="node-icon">💾</div>
                            <div class="node-label">Store</div>
                        </div>
                    </div>
                </div>
                
                <!-- Row 2: ANALYZE (with ALIGNED trophy slot) -->
                <div class="workflow-row">
                    <div class="row-label">Analyze</div>
                    <div class="row-content">
                        <div class="node" id="node4">
                            <div class="node-icon">🚦</div>
                            <div class="node-label">Risk</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow3">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node5">
                            <div class="node-icon">📝</div>
                            <div class="node-label">Redlines</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow4">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node6">
                            <div class="node-icon">⚖️</div>
                            <div class="node-label">Compare</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow-trophy">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <!-- ALIGNED TROPHY -->
                        <div class="trophy-node" id="trophyNode">
                            <div class="trophy-icon">🏆</div>
                            <div class="trophy-label">Aligned</div>
                        </div>
                    </div>
                </div>
                
                <!-- Row 3: LEARN -->
                <div class="workflow-row">
                    <div class="row-label">Learn</div>
                    <div class="row-content">
                        <div class="node" id="node7">
                            <div class="node-icon">📋</div>
                            <div class="node-label">Report</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow5">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node8">
                            <div class="node-icon">🤝</div>
                            <div class="node-label">Negotiate</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow6">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node9">
                            <div class="node-icon">📤</div>
                            <div class="node-label">Handoff</div>
                        </div>
                        <div class="arrow-container">
                            <div class="arrow" id="arrow7">
                                <div class="arrow-line"></div>
                                <div class="arrow-head"></div>
                            </div>
                        </div>
                        <div class="node" id="node10">
                            <div class="node-icon">🔄</div>
                            <div class="node-label">Feedback</div>
                        </div>
                    </div>
                </div>
                
                <!-- Tagline -->
                <div class="workflow-tagline">
                    <span class="tagline-text" id="workflowTagline"></span>
                </div>
            </div>
        </div>
        
        <!-- ========================================
             RIGHT ZONE: CIP LEARNING
             ======================================== -->
        <div class="learning-zone">
            <div class="learning-container">
                <div class="learning-title" id="learningTitle" onclick="restartAllAnimations()">CIP Learning</div>
                
                <div class="learning-stage">
                    <!-- Input section -->
                    <div class="input-section">
                        <div class="input-group">
                            <div class="input-group-label" id="contractsLabel">Contracts</div>
                            <div class="input-node" id="contract1"><div class="input-icon">📄</div></div>
                            <div class="input-node" id="contract2"><div class="input-icon">📄</div></div>
                            <div class="input-node" id="contract3"><div class="input-icon">📄</div></div>
                        </div>
                        <div class="input-group">
                            <div class="input-group-label" id="feedbackLabel">Feedback</div>
                            <div class="input-node" id="feedback1"><div class="input-icon">💬</div></div>
                            <div class="input-node" id="feedback2"><div class="input-icon">💬</div></div>
                            <div class="input-node" id="feedback3"><div class="input-icon">💬</div></div>
                        </div>
                    </div>
                    
                    <!-- Input arrows -->
                    <div class="learn-arrow-container contract-arrow-1" id="contractArrow1">
                        <div class="learn-arrow-line"></div>
                        <div class="learn-arrow-head"></div>
                    </div>
                    <div class="learn-arrow-container contract-arrow-2" id="contractArrow2">
                        <div class="learn-arrow-line"></div>
                        <div class="learn-arrow-head"></div>
                    </div>
                    <div class="learn-arrow-container contract-arrow-3" id="contractArrow3">
                        <div class="learn-arrow-line"></div>
                        <div class="learn-arrow-head"></div>
                    </div>
                    
                    <div class="learn-arrow-container feedback-arrow-1" id="feedbackArrow1">
                        <div class="learn-arrow-line"></div>
                        <div class="learn-arrow-head"></div>
                    </div>
                    <div class="learn-arrow-container feedback-arrow-2" id="feedbackArrow2">
                        <div class="learn-arrow-line"></div>
                        <div class="learn-arrow-head"></div>
                    </div>
                    <div class="learn-arrow-container feedback-arrow-3" id="feedbackArrow3">
                        <div class="learn-arrow-line"></div>
                        <div class="learn-arrow-head"></div>
                    </div>
                    
                    <!-- Central brain -->
                    <div class="brain-container">
                        <div class="brain-icon" id="brainIcon">🧠</div>
                        <div class="brain-label" id="brainLabel">CIP</div>
                    </div>
                    
                    <!-- Brain tagline -->
                    <div class="brain-tagline" id="brainTagline"></div>
                    
                    <!-- Output arrows -->
                    <div class="output-arrow-container faster-arrow" id="fasterArrow">
                        <div class="output-arrow-line"></div>
                        <div class="output-arrow-head"></div>
                    </div>
                    <div class="output-arrow-container smarter-arrow" id="smarterArrow">
                        <div class="output-arrow-line"></div>
                        <div class="output-arrow-head"></div>
                    </div>
                    <div class="output-arrow-container safer-arrow" id="saferArrow">
                        <div class="output-arrow-line"></div>
                        <div class="output-arrow-head"></div>
                    </div>
                    
                    <!-- Output section -->
                    <div class="output-section">
                        <div class="output-node" id="fasterNode">
                            <div class="output-icon">⚡</div>
                            <div class="output-label">Faster</div>
                        </div>
                        <div class="output-node" id="smarterNode">
                            <div class="output-icon">🎯</div>
                            <div class="output-label">Smarter</div>
                        </div>
                        <div class="output-node" id="saferNode">
                            <div class="output-icon">🛡️</div>
                            <div class="output-label">Safer</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- ========================================
         TIMES SQUARE CELEBRATION OVERLAY
         ======================================== -->
    <div class="times-square-overlay" id="timesSquareOverlay">
        <div class="light-rays" id="lightRays"></div>
        <div class="countdown" id="countdown"></div>
        <div class="trophy-drop" id="trophyDrop">🏆</div>
        <div class="aligned-text" id="alignedText">ALIGNED</div>
        <div class="subtitle-text" id="subtitleText">Contract Intelligence Achieved</div>
    </div>
    
    <div class="confetti-container" id="confettiContainer"></div>

    <script>
        // ========================================
        // ELEMENT REFERENCES
        // ========================================
        
        // Workflow elements
        const workflowTitle = document.getElementById('workflowTitle');
        const workflowTagline = document.getElementById('workflowTagline');
        const trophyNode = document.getElementById('trophyNode');
        const arrowTrophy = document.getElementById('arrow-trophy');
        
        // Learning elements
        const learningTitle = document.getElementById('learningTitle');
        const brainIcon = document.getElementById('brainIcon');
        const brainLabel = document.getElementById('brainLabel');
        const brainTagline = document.getElementById('brainTagline');
        const contractsLabel = document.getElementById('contractsLabel');
        const feedbackLabel = document.getElementById('feedbackLabel');
        
        // Times Square elements
        const timesSquareOverlay = document.getElementById('timesSquareOverlay');
        const countdown = document.getElementById('countdown');
        const trophyDrop = document.getElementById('trophyDrop');
        const alignedText = document.getElementById('alignedText');
        const subtitleText = document.getElementById('subtitleText');
        const lightRays = document.getElementById('lightRays');
        const confettiContainer = document.getElementById('confettiContainer');
        
        // Taglines
        const workflowRowTaglines = [
            "Every contract, captured and cataloged",
            "Identify, manage and mitigate risk",
            "Insights that drive performance"
        ];
        const workflowFinalTagline = "Building contract management as a core competency";
        
        const learningTaglines = [
            "The more you use it, the better it gets",
            "Intelligence that grows with you",
            "Learning never stops",
            "Continuous improvement built-in",
            "Every interaction builds expertise",
            "Smarter with every contract"
        ];
        
        // State tracking
        let workflowComplete = false;
        let learningComplete = false;
        
        // ========================================
        // RESET FUNCTIONS
        // ========================================
        
        function resetWorkflow() {
            workflowTitle.classList.remove('visible');
            workflowTagline.classList.remove('visible', 'pulse', 'bright');
            workflowTagline.textContent = '';
            trophyNode.classList.remove('visible');
            arrowTrophy.classList.remove('visible');
            
            for (let i = 0; i <= 10; i++) {
                const node = document.getElementById(`node${i}`);
                if (node) node.classList.remove('visible');
            }
            for (let i = 0; i <= 7; i++) {
                const arrow = document.getElementById(`arrow${i}`);
                if (arrow) arrow.classList.remove('visible');
            }
        }
        
        function resetLearning() {
            learningTitle.classList.remove('visible');
            brainTagline.classList.remove('visible', 'pulse', 'bright');
            brainTagline.textContent = '';
            contractsLabel.classList.remove('visible');
            feedbackLabel.classList.remove('visible');
            
            for (let i = 1; i <= 3; i++) {
                document.getElementById(`contract${i}`).classList.remove('visible');
                document.getElementById(`feedback${i}`).classList.remove('visible');
                document.getElementById(`contractArrow${i}`).classList.remove('visible');
                document.getElementById(`feedbackArrow${i}`).classList.remove('visible');
            }
            
            brainIcon.classList.remove('visible', 'small', 'large', 'xl', 'xxl', 'xxxl', 'xxxxl');
            brainLabel.classList.remove('visible');
            
            document.getElementById('fasterArrow').classList.remove('visible');
            document.getElementById('smarterArrow').classList.remove('visible');
            document.getElementById('saferArrow').classList.remove('visible');
            document.getElementById('fasterNode').classList.remove('visible');
            document.getElementById('smarterNode').classList.remove('visible');
            document.getElementById('saferNode').classList.remove('visible');
        }
        
        function resetTimesSquare() {
            timesSquareOverlay.classList.remove('visible');
            countdown.classList.remove('visible');
            countdown.textContent = '';
            trophyDrop.classList.remove('dropped');
            trophyDrop.style.top = '-150px';
            alignedText.classList.remove('visible');
            subtitleText.classList.remove('visible');
            lightRays.classList.remove('active');
            confettiContainer.innerHTML = '';
        }
        
        function resetAll() {
            resetWorkflow();
            resetLearning();
            resetTimesSquare();
            workflowComplete = false;
            learningComplete = false;
        }
        
        // ========================================
        // HELPER FUNCTIONS
        // ========================================
        
        function showWorkflowTagline(text) {
            workflowTagline.classList.remove('visible', 'pulse', 'bright');
            setTimeout(() => {
                workflowTagline.textContent = text;
                workflowTagline.classList.add('visible');
            }, 200);
        }
        
        function showBrainTagline(index) {
            brainTagline.classList.remove('visible', 'pulse', 'bright');
            setTimeout(() => {
                brainTagline.textContent = learningTaglines[index];
                brainTagline.classList.add('visible');
            }, 200);
        }
        
        function setBrainSize(size) {
            brainIcon.classList.remove('small', 'large', 'xl', 'xxl', 'xxxl', 'xxxxl');
            brainIcon.classList.add(size);
        }
        
        function createConfetti() {
            const colors = ['#F59E0B', '#FCD34D', '#8B5CF6', '#3B82F6', '#10B981', '#EF4444'];
            for (let i = 0; i < 150; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + '%';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.animationDelay = Math.random() * 2 + 's';
                confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
                confettiContainer.appendChild(confetti);
                
                setTimeout(() => confetti.classList.add('active'), 100);
            }
        }
        
        function createFireworks() {
            const positions = [
                { x: '20%', y: '30%' },
                { x: '80%', y: '25%' },
                { x: '50%', y: '20%' },
                { x: '30%', y: '40%' },
                { x: '70%', y: '35%' }
            ];
            const colors = ['#F59E0B', '#FCD34D', '#8B5CF6', '#3B82F6', '#10B981'];
            
            positions.forEach((pos, i) => {
                setTimeout(() => {
                    const firework = document.createElement('div');
                    firework.className = 'firework';
                    firework.style.left = pos.x;
                    firework.style.top = pos.y;
                    firework.style.backgroundColor = colors[i];
                    confettiContainer.appendChild(firework);
                    
                    setTimeout(() => firework.classList.add('burst'), 50);
                    setTimeout(() => firework.remove(), 1500);
                }, i * 300);
            });
        }
        
        function checkBothComplete() {
            if (workflowComplete && learningComplete) {
                setTimeout(triggerTimesSquare, 500);
            }
        }
        
        // ========================================
        // TIMES SQUARE CELEBRATION
        // ========================================
        
        function triggerTimesSquare() {
            timesSquareOverlay.classList.add('visible');
            
            let delay = 500;
            
            // Countdown 3-2-1
            const countdownNums = ['3', '2', '1'];
            countdownNums.forEach((num, i) => {
                setTimeout(() => {
                    countdown.textContent = num;
                    countdown.classList.remove('visible');
                    void countdown.offsetWidth; // Force reflow
                    countdown.classList.add('visible');
                }, delay + i * 800);
            });
            
            delay += 2400;
            
            // Hide countdown
            setTimeout(() => {
                countdown.style.display = 'none';
            }, delay);
            
            delay += 200;
            
            // Trophy drop
            setTimeout(() => {
                trophyDrop.classList.add('dropped');
                lightRays.classList.add('active');
            }, delay);
            
            delay += 1500;
            
            // ALIGNED text
            setTimeout(() => {
                alignedText.classList.add('visible');
                createFireworks();
            }, delay);
            
            delay += 800;
            
            // Confetti
            setTimeout(() => {
                createConfetti();
            }, delay);
            
            delay += 500;
            
            // Subtitle
            setTimeout(() => {
                subtitleText.classList.add('visible');
            }, delay);
            
            // Auto-close after celebration
            setTimeout(() => {
                timesSquareOverlay.classList.remove('visible');
                setTimeout(resetTimesSquare, 500);
            }, delay + 4000);
        }
        
        // ========================================
        // WORKFLOW ANIMATION
        // ========================================
        
        function runWorkflowAnimation() {
            resetWorkflow();
            workflowComplete = false;
            
            let delay = 200;
            const nodeDelay = 500;
            const arrowDelay = 350;
            const rowPause = 400;
            
            // Title
            setTimeout(() => workflowTitle.classList.add('visible'), delay);
            delay += 800;
            
            // Row 1: INTAKE (nodes 0-3, arrows 0-2)
            for (let i = 0; i <= 3; i++) {
                setTimeout(() => {
                    document.getElementById(`node${i}`).classList.add('visible');
                }, delay);
                delay += nodeDelay;
                
                if (i < 3) {
                    setTimeout(() => {
                        document.getElementById(`arrow${i}`).classList.add('visible');
                    }, delay);
                    delay += arrowDelay;
                }
            }
            
            setTimeout(() => showWorkflowTagline(workflowRowTaglines[0]), delay);
            delay += rowPause + 600;
            
            // Row 2: ANALYZE (nodes 4-6, arrows 3-4)
            for (let i = 4; i <= 6; i++) {
                setTimeout(() => {
                    document.getElementById(`node${i}`).classList.add('visible');
                }, delay);
                delay += nodeDelay;
                
                if (i < 6) {
                    setTimeout(() => {
                        document.getElementById(`arrow${i - 1}`).classList.add('visible');
                    }, delay);
                    delay += arrowDelay;
                }
            }
            
            setTimeout(() => showWorkflowTagline(workflowRowTaglines[1]), delay);
            delay += rowPause + 600;
            
            // Row 3: LEARN (nodes 7-10, arrows 5-7)
            for (let i = 7; i <= 10; i++) {
                setTimeout(() => {
                    document.getElementById(`node${i}`).classList.add('visible');
                }, delay);
                delay += nodeDelay;
                
                if (i < 10) {
                    setTimeout(() => {
                        document.getElementById(`arrow${i - 2}`).classList.add('visible');
                    }, delay);
                    delay += arrowDelay;
                }
            }
            
            setTimeout(() => showWorkflowTagline(workflowRowTaglines[2]), delay);
            delay += 1200;
            
            // Final tagline
            setTimeout(() => showWorkflowTagline(workflowFinalTagline), delay);
            delay += 600;
            
            // Pulse
            setTimeout(() => workflowTagline.classList.add('pulse'), delay);
            delay += 4500;
            
            // Stay bright & mark complete
            setTimeout(() => {
                workflowTagline.classList.remove('pulse');
                workflowTagline.classList.add('bright');
                workflowComplete = true;
                checkBothComplete();
            }, delay);
        }
        
        // ========================================
        // LEARNING ANIMATION
        // ========================================
        
        function runLearningAnimation() {
            resetLearning();
            learningComplete = false;
            
            // Start after workflow gets going
            const startDelay = 15000;
            
            const inputDelay = 350;
            const arrowDelay = 400;
            const growDelay = 700;
            const readDelay = 1000;
            
            let delay = startDelay + 100;
            
            // Title
            setTimeout(() => learningTitle.classList.add('visible'), delay);
            delay += 500;
            
            // Labels
            setTimeout(() => {
                contractsLabel.classList.add('visible');
                feedbackLabel.classList.add('visible');
            }, delay);
            delay += 350;
            
            // Brain (small) + Tagline 1
            setTimeout(() => {
                brainIcon.classList.add('visible', 'small');
                brainLabel.classList.add('visible');
                showBrainTagline(0);
            }, delay);
            delay += readDelay + 500;
            
            // Contract 1 → Large + Tagline 2
            setTimeout(() => document.getElementById('contract1').classList.add('visible'), delay);
            delay += inputDelay;
            setTimeout(() => document.getElementById('contractArrow1').classList.add('visible'), delay);
            delay += arrowDelay;
            setTimeout(() => { setBrainSize('large'); showBrainTagline(1); }, delay);
            delay += readDelay;
            
            // Feedback 1 → XL + Tagline 3
            setTimeout(() => document.getElementById('feedback1').classList.add('visible'), delay);
            delay += inputDelay;
            setTimeout(() => document.getElementById('feedbackArrow1').classList.add('visible'), delay);
            delay += arrowDelay;
            setTimeout(() => { setBrainSize('xl'); showBrainTagline(2); }, delay);
            delay += readDelay;
            
            // Contract 2 → XXL + Tagline 4
            setTimeout(() => document.getElementById('contract2').classList.add('visible'), delay);
            delay += inputDelay;
            setTimeout(() => document.getElementById('contractArrow2').classList.add('visible'), delay);
            delay += arrowDelay;
            setTimeout(() => { setBrainSize('xxl'); showBrainTagline(3); }, delay);
            delay += readDelay;
            
            // Feedback 2 → XXXL + Tagline 5
            setTimeout(() => document.getElementById('feedback2').classList.add('visible'), delay);
            delay += inputDelay;
            setTimeout(() => document.getElementById('feedbackArrow2').classList.add('visible'), delay);
            delay += arrowDelay;
            setTimeout(() => { setBrainSize('xxxl'); showBrainTagline(4); }, delay);
            delay += readDelay;
            
            // Contract 3 → XXXXL + Tagline 6
            setTimeout(() => document.getElementById('contract3').classList.add('visible'), delay);
            delay += inputDelay;
            setTimeout(() => document.getElementById('contractArrow3').classList.add('visible'), delay);
            delay += arrowDelay;
            setTimeout(() => { setBrainSize('xxxxl'); showBrainTagline(5); }, delay);
            delay += readDelay;
            
            // Feedback 3 (brain stays XXXXL)
            setTimeout(() => document.getElementById('feedback3').classList.add('visible'), delay);
            delay += inputDelay;
            setTimeout(() => document.getElementById('feedbackArrow3').classList.add('visible'), delay);
            delay += 500;
            
            // Pause at max size
            delay += 2500;
            
            // Output arrows
            setTimeout(() => document.getElementById('fasterArrow').classList.add('visible'), delay);
            delay += 300;
            setTimeout(() => document.getElementById('smarterArrow').classList.add('visible'), delay);
            delay += 300;
            setTimeout(() => document.getElementById('saferArrow').classList.add('visible'), delay);
            delay += 350;
            
            // Output nodes
            setTimeout(() => document.getElementById('fasterNode').classList.add('visible'), delay);
            delay += 350;
            setTimeout(() => document.getElementById('smarterNode').classList.add('visible'), delay);
            delay += 350;
            setTimeout(() => document.getElementById('saferNode').classList.add('visible'), delay);
            delay += 600;
            
            // Tagline pulse
            setTimeout(() => brainTagline.classList.add('pulse'), delay);
            delay += 4500;
            
            // Stay bright & trigger ALIGNED trophy
            setTimeout(() => {
                brainTagline.classList.remove('pulse');
                brainTagline.classList.add('bright');
                
                // Show trophy arrow and trophy
                arrowTrophy.classList.add('visible');
                setTimeout(() => {
                    trophyNode.classList.add('visible');
                    learningComplete = true;
                    checkBothComplete();
                }, 400);
            }, delay);
        }
        
        // ========================================
        // MAIN CONTROL
        // ========================================
        
        function runAllAnimations() {
            resetAll();
            runWorkflowAnimation();
            runLearningAnimation();
        }
        
        function restartAllAnimations() {
            runAllAnimations();
        }
        
        // Start on load
        document.addEventListener('DOMContentLoaded', runAllAnimations);
        
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(runAllAnimations, 100);
        }
    </script>
</body>
</html>
'''


def render_home_animation(height: int = 340) -> None:
    """
    Render the unified CIP Home animation.
    
    Includes:
    - CIP Workflow (left zone)
    - CIP Learning (right zone)
    - ALIGNED Trophy (Row 2 Col 4)
    - Times Square Drop celebration
    
    Args:
        height: Height of the animation container in pixels
    """
    components.html(HOME_ANIMATION_HTML, height=height, scrolling=False)
