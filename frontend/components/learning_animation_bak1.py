# components/learning_animation.py
"""
CIP Learning Animation Component
Shows how CIP gets smarter with more contracts and feedback.

Usage:
    from components.learning_animation import render_learning_animation
    render_learning_animation()
"""

import streamlit as st
import streamlit.components.v1 as components


LEARNING_HTML = '''
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
        
        .learning-container {
            padding: 8px 0 4px 0;
            min-height: 300px;
            position: relative;
        }
        
        .header-row {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 8px;
            min-height: 28px;
        }
        
        .learning-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #E2E8F0;
            opacity: 0;
            transform: translateY(-10px);
            transition: opacity 0.6s ease, transform 0.6s ease;
            cursor: pointer;
            flex-shrink: 0;
        }
        
        .learning-title:hover {
            color: #3B82F6;
        }
        
        .learning-title.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .learning-stage {
            position: relative;
            width: 100%;
            height: 260px;
        }
        
        /* Tagline UNDER brain */
        .brain-tagline {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, 70px);
            font-size: 0.95rem;
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
        
        @keyframes taglinePulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        
        /* Input section (left side) */
        .input-section {
            position: absolute;
            left: 5px;
            top: 0;
            bottom: 40px;
            width: 80px;
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
            font-size: 0.6rem;
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
            font-size: 1.1rem;
            width: 28px;
            height: 28px;
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
        
        /* Arrows pointing to brain */
        .arrow-container {
            position: absolute;
            display: flex;
            align-items: center;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .arrow-container.visible {
            opacity: 1;
        }
        
        /* Contract arrows (top half) */
        .contract-arrow-1 { left: 90px; top: 35px; transform: rotate(16deg); }
        .contract-arrow-2 { left: 90px; top: 60px; transform: rotate(9deg); }
        .contract-arrow-3 { left: 90px; top: 85px; transform: rotate(3deg); }
        
        /* Feedback arrows (bottom half) */
        .feedback-arrow-1 { left: 90px; bottom: 95px; transform: rotate(-3deg); }
        .feedback-arrow-2 { left: 90px; bottom: 70px; transform: rotate(-9deg); }
        .feedback-arrow-3 { left: 90px; bottom: 45px; transform: rotate(-16deg); }
        
        .arrow-line {
            height: 2px;
            background: linear-gradient(90deg, #3B82F6, #8B5CF6);
            border-radius: 1px;
            width: 35px;
        }
        
        .arrow-container.visible .arrow-line {
            animation: arrowPulse 2s ease-in-out infinite, inputArrowGrow 2s ease-in-out infinite;
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
        
        .arrow-container.visible .arrow-head {
            animation: arrowHeadPulse 2s ease-in-out infinite;
        }
        
        /* Central brain - COMPACT SIZES */
        .brain-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -55%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }
        
        .brain-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1E293B;
            border-radius: 50%;
            border: 2px solid rgba(139, 92, 246, 0.3);
            opacity: 0;
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 1rem;
            width: 32px;
            height: 32px;
        }
        
        .brain-icon.visible { opacity: 1; }
        
        /* Small */
        .brain-icon.small { 
            font-size: 1.2rem; 
            width: 38px; 
            height: 38px; 
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.2); 
        }
        /* Large */
        .brain-icon.large { 
            font-size: 1.5rem; 
            width: 48px; 
            height: 48px; 
            box-shadow: 0 0 18px rgba(139, 92, 246, 0.28); 
            border-color: rgba(139, 92, 246, 0.4); 
        }
        /* XL */
        .brain-icon.xl { 
            font-size: 1.9rem; 
            width: 60px; 
            height: 60px; 
            box-shadow: 0 0 26px rgba(139, 92, 246, 0.36); 
            border-color: rgba(139, 92, 246, 0.5); 
        }
        /* XXL */
        .brain-icon.xxl { 
            font-size: 2.3rem; 
            width: 74px; 
            height: 74px; 
            box-shadow: 0 0 36px rgba(139, 92, 246, 0.45); 
            border-color: rgba(139, 92, 246, 0.6); 
        }
        /* XXXL */
        .brain-icon.xxxl { 
            font-size: 2.8rem; 
            width: 90px; 
            height: 90px; 
            box-shadow: 0 0 50px rgba(139, 92, 246, 0.55), 0 0 80px rgba(59, 130, 246, 0.3);
            border-color: rgba(139, 92, 246, 0.7); 
        }
        /* XXXXL - Maximum size */
        .brain-icon.xxxxl { 
            font-size: 3.5rem; 
            width: 115px; 
            height: 115px; 
            box-shadow: 0 0 80px rgba(139, 92, 246, 0.75), 0 0 130px rgba(59, 130, 246, 0.5);
            border-color: #8B5CF6;
            border-width: 3px;
            animation: xxxxlPulse 2s ease-in-out infinite;
        }
        
        .brain-label {
            font-size: 0.6rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #8B5CF6;
            text-transform: uppercase;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .brain-label.visible { opacity: 1; }
        
        /* Output arrows (right side) */
        .output-arrow {
            position: absolute;
            display: flex;
            align-items: center;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .output-arrow.visible { opacity: 1; }
        
        .output-arrow.faster-arrow { right: 110px; top: 55px; transform: rotate(-16deg); }
        .output-arrow.smarter-arrow { right: 110px; top: 50%; transform: translateY(-50%); }
        .output-arrow.safer-arrow { right: 110px; bottom: 65px; transform: rotate(16deg); }
        
        .output-arrow .arrow-line { width: 28px; }
        .output-arrow.visible .arrow-line {
            animation: arrowPulse 2s ease-in-out infinite, outputArrowGrow 2s ease-in-out infinite;
        }
        
        /* Result nodes (right side) */
        .result-node {
            position: absolute;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 3px;
            opacity: 0;
            transform: scale(0.8);
            transition: opacity 0.5s ease, transform 0.5s ease;
            right: 8px;
        }
        
        .result-node.visible {
            opacity: 1;
            transform: scale(1);
        }
        
        .result-node.faster { top: 35px; }
        .result-node.smarter { top: 50%; transform: translateY(-50%); }
        .result-node.smarter.visible { transform: translateY(-50%) scale(1); }
        .result-node.safer { bottom: 45px; }
        
        .result-icon {
            font-size: 1.2rem;
            width: 38px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(59, 130, 246, 0.15));
            border-radius: 8px;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .result-node.visible .result-icon {
            box-shadow: 0 3px 12px rgba(16, 185, 129, 0.25);
            animation: resultGlow 2s ease-in-out infinite;
        }
        
        .result-label {
            font-size: 0.5rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #10B981;
            text-transform: uppercase;
        }
        
        /* Animations */
        @keyframes arrowPulse {
            0%, 100% { box-shadow: 0 0 2px rgba(59, 130, 246, 0.4); }
            50% { box-shadow: 0 0 6px rgba(139, 92, 246, 0.7); }
        }
        
        @keyframes inputArrowGrow {
            0%, 100% { width: 35px; }
            50% { width: 48px; }
        }
        
        @keyframes outputArrowGrow {
            0%, 100% { width: 28px; }
            50% { width: 40px; }
        }
        
        @keyframes arrowHeadPulse {
            0%, 100% { filter: drop-shadow(0 0 2px rgba(139, 92, 246, 0.4)); }
            50% { filter: drop-shadow(0 0 4px rgba(139, 92, 246, 0.8)); }
        }
        
        @keyframes xxxxlPulse {
            0%, 100% { 
                box-shadow: 0 0 80px rgba(139, 92, 246, 0.75), 0 0 130px rgba(59, 130, 246, 0.5);
            }
            50% { 
                box-shadow: 0 0 100px rgba(139, 92, 246, 0.9), 0 0 160px rgba(59, 130, 246, 0.65);
            }
        }
        
        @keyframes resultGlow {
            0%, 100% { box-shadow: 0 3px 12px rgba(16, 185, 129, 0.25); }
            50% { box-shadow: 0 3px 18px rgba(16, 185, 129, 0.4); }
        }
    </style>
</head>
<body>
    <div class="learning-container">
        <div class="header-row">
            <div class="learning-title" id="learningTitle" onclick="restartAnimation()">CIP Learning</div>
        </div>
        
        <div class="learning-stage">
            <!-- Tagline UNDER brain -->
            <div class="brain-tagline" id="brainTagline"></div>
            
            <!-- Input section (left) -->
            <div class="input-section">
                <!-- Contracts group (top) -->
                <div class="input-group">
                    <div class="input-group-label" id="contractsLabel">Contracts</div>
                    <div class="input-node" id="contract1"><div class="input-icon">📄</div></div>
                    <div class="input-node" id="contract2"><div class="input-icon">📄</div></div>
                    <div class="input-node" id="contract3"><div class="input-icon">📄</div></div>
                </div>
                
                <!-- Feedback group (bottom) -->
                <div class="input-group">
                    <div class="input-group-label" id="feedbackLabel">Feedback</div>
                    <div class="input-node" id="feedback1"><div class="input-icon">🔄</div></div>
                    <div class="input-node" id="feedback2"><div class="input-icon">🔄</div></div>
                    <div class="input-node" id="feedback3"><div class="input-icon">🔄</div></div>
                </div>
            </div>
            
            <!-- Arrows to brain -->
            <div class="arrow-container contract-arrow-1" id="contractArrow1">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            <div class="arrow-container contract-arrow-2" id="contractArrow2">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            <div class="arrow-container contract-arrow-3" id="contractArrow3">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            
            <div class="arrow-container feedback-arrow-1" id="feedbackArrow1">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            <div class="arrow-container feedback-arrow-2" id="feedbackArrow2">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            <div class="arrow-container feedback-arrow-3" id="feedbackArrow3">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            
            <!-- Central Brain -->
            <div class="brain-container">
                <div class="brain-icon" id="brainIcon">🧠</div>
                <div class="brain-label" id="brainLabel">CIP</div>
            </div>
            
            <!-- Output Arrows -->
            <div class="output-arrow faster-arrow" id="fasterArrow">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            <div class="output-arrow smarter-arrow" id="smarterArrow">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            <div class="output-arrow safer-arrow" id="saferArrow">
                <div class="arrow-line"></div><div class="arrow-head"></div>
            </div>
            
            <!-- Results (right side) -->
            <div class="result-node faster" id="fasterNode">
                <div class="result-icon">⚡</div>
                <div class="result-label">Faster</div>
            </div>
            <div class="result-node smarter" id="smarterNode">
                <div class="result-icon">🎯</div>
                <div class="result-label">Smarter</div>
            </div>
            <div class="result-node safer" id="saferNode">
                <div class="result-icon">🛡️</div>
                <div class="result-label">Safer</div>
            </div>
        </div>
    </div>

    <script>
        const title = document.getElementById('learningTitle');
        const brainTagline = document.getElementById('brainTagline');
        const brainIcon = document.getElementById('brainIcon');
        const brainLabel = document.getElementById('brainLabel');
        
        const contractsLabel = document.getElementById('contractsLabel');
        const feedbackLabel = document.getElementById('feedbackLabel');
        
        const contract1 = document.getElementById('contract1');
        const contract2 = document.getElementById('contract2');
        const contract3 = document.getElementById('contract3');
        const contractArrow1 = document.getElementById('contractArrow1');
        const contractArrow2 = document.getElementById('contractArrow2');
        const contractArrow3 = document.getElementById('contractArrow3');
        
        const feedback1 = document.getElementById('feedback1');
        const feedback2 = document.getElementById('feedback2');
        const feedback3 = document.getElementById('feedback3');
        const feedbackArrow1 = document.getElementById('feedbackArrow1');
        const feedbackArrow2 = document.getElementById('feedbackArrow2');
        const feedbackArrow3 = document.getElementById('feedbackArrow3');
        
        const fasterArrow = document.getElementById('fasterArrow');
        const smarterArrow = document.getElementById('smarterArrow');
        const saferArrow = document.getElementById('saferArrow');
        const fasterNode = document.getElementById('fasterNode');
        const smarterNode = document.getElementById('smarterNode');
        const saferNode = document.getElementById('saferNode');
        
        // Taglines that appear UNDER brain during growth (6 total)
        const growthTaglines = [
            "The more you use it, the better it gets",
            "Intelligence that grows with you",
            "Learning never stops",
            "Continuous improvement built-in",
            "Every interaction builds expertise",
            "Smarter with every contract"
        ];
        
        function resetAnimation() {
            title.classList.remove('visible');
            brainTagline.classList.remove('visible', 'pulse', 'bright');
            brainTagline.textContent = '';
            
            contractsLabel.classList.remove('visible');
            feedbackLabel.classList.remove('visible');
            
            contract1.classList.remove('visible');
            contract2.classList.remove('visible');
            contract3.classList.remove('visible');
            contractArrow1.classList.remove('visible');
            contractArrow2.classList.remove('visible');
            contractArrow3.classList.remove('visible');
            
            feedback1.classList.remove('visible');
            feedback2.classList.remove('visible');
            feedback3.classList.remove('visible');
            feedbackArrow1.classList.remove('visible');
            feedbackArrow2.classList.remove('visible');
            feedbackArrow3.classList.remove('visible');
            
            brainIcon.classList.remove('visible', 'small', 'large', 'xl', 'xxl', 'xxxl', 'xxxxl');
            brainLabel.classList.remove('visible');
            
            fasterArrow.classList.remove('visible');
            smarterArrow.classList.remove('visible');
            saferArrow.classList.remove('visible');
            fasterNode.classList.remove('visible');
            smarterNode.classList.remove('visible');
            saferNode.classList.remove('visible');
        }
        
        function setBrainSize(size) {
            brainIcon.classList.remove('small', 'large', 'xl', 'xxl', 'xxxl', 'xxxxl');
            brainIcon.classList.add(size);
        }
        
        function showBrainTagline(index) {
            brainTagline.classList.remove('visible', 'pulse', 'bright');
            setTimeout(() => {
                brainTagline.textContent = growthTaglines[index];
                brainTagline.classList.add('visible');
            }, 200);
        }
        
        function runAnimation() {
            resetAnimation();
            
            // Start delay: wait for CIP Workflow to finish (~15 seconds with taglines)
            const startDelay = 15000;
            
            // SLOWER timing values
            const inputDelay = 400;
            const arrowDelay = 500;
            const growDelay = 800;
            const readDelay = 1200;
            
            let delay = startDelay + 100;
            
            // 1. Title fades in
            setTimeout(() => {
                title.classList.add('visible');
            }, delay);
            delay += 600;
            
            // Show labels
            setTimeout(() => {
                contractsLabel.classList.add('visible');
                feedbackLabel.classList.add('visible');
            }, delay);
            delay += 400;
            
            // 2. Brain appears (Small) + Tagline 1 under brain
            setTimeout(() => {
                brainIcon.classList.add('visible', 'small');
                brainLabel.classList.add('visible');
                showBrainTagline(0);
            }, delay);
            delay += readDelay + 600;
            
            // 3. Contract #1 + arrow → brain grows to Large + Tagline 2
            setTimeout(() => { contract1.classList.add('visible'); }, delay);
            delay += inputDelay;
            setTimeout(() => { contractArrow1.classList.add('visible'); }, delay);
            delay += arrowDelay;
            setTimeout(() => { 
                setBrainSize('large'); 
                showBrainTagline(1);
            }, delay);
            delay += readDelay;
            
            // 4. Feedback #1 + arrow → brain grows to XL + Tagline 3
            setTimeout(() => { feedback1.classList.add('visible'); }, delay);
            delay += inputDelay;
            setTimeout(() => { feedbackArrow1.classList.add('visible'); }, delay);
            delay += arrowDelay;
            setTimeout(() => { 
                setBrainSize('xl'); 
                showBrainTagline(2);
            }, delay);
            delay += readDelay;
            
            // 5. Contract #2 + arrow → brain grows to XXL + Tagline 4
            setTimeout(() => { contract2.classList.add('visible'); }, delay);
            delay += inputDelay;
            setTimeout(() => { contractArrow2.classList.add('visible'); }, delay);
            delay += arrowDelay;
            setTimeout(() => { 
                setBrainSize('xxl'); 
                showBrainTagline(3);
            }, delay);
            delay += readDelay;
            
            // 6. Feedback #2 + arrow → brain grows to XXXL + Tagline 5
            setTimeout(() => { feedback2.classList.add('visible'); }, delay);
            delay += inputDelay;
            setTimeout(() => { feedbackArrow2.classList.add('visible'); }, delay);
            delay += arrowDelay;
            setTimeout(() => { 
                setBrainSize('xxxl'); 
                showBrainTagline(4);
            }, delay);
            delay += readDelay;
            
            // 7. Contract #3 + arrow → brain grows to XXXXL + Tagline 6 (final)
            setTimeout(() => { contract3.classList.add('visible'); }, delay);
            delay += inputDelay;
            setTimeout(() => { contractArrow3.classList.add('visible'); }, delay);
            delay += arrowDelay;
            setTimeout(() => { 
                setBrainSize('xxxxl'); 
                showBrainTagline(5);  // Final tagline: "Smarter with every contract"
            }, delay);
            delay += readDelay;
            
            // 8. Feedback #3 + arrow → brain STAYS XXXXL (no shrink)
            setTimeout(() => { feedback3.classList.add('visible'); }, delay);
            delay += inputDelay;
            setTimeout(() => { feedbackArrow3.classList.add('visible'); }, delay);
            delay += 600;
            
            // 9. PAUSE 3 seconds at maximum size
            delay += 3000;
            
            // 10. Output arrows appear (one at a time) - NO BRAIN SHRINK
            setTimeout(() => { fasterArrow.classList.add('visible'); }, delay);
            delay += 350;
            setTimeout(() => { smarterArrow.classList.add('visible'); }, delay);
            delay += 350;
            setTimeout(() => { saferArrow.classList.add('visible'); }, delay);
            delay += 450;
            
            // 11. FASTER → SMARTER → SAFER (one at a time)
            setTimeout(() => { fasterNode.classList.add('visible'); }, delay);
            delay += 400;
            setTimeout(() => { smarterNode.classList.add('visible'); }, delay);
            delay += 400;
            setTimeout(() => { saferNode.classList.add('visible'); }, delay);
            delay += 800;
            
            // 12. Final tagline pulses then stays bright (stays under brain)
            setTimeout(() => {
                brainTagline.classList.add('pulse');
            }, delay);
            delay += 4500; // 3 pulses × 1.5s
            
            // Stop pulsing, stay bright
            setTimeout(() => {
                brainTagline.classList.remove('pulse');
                brainTagline.classList.add('bright');
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


def render_learning_animation(height: int = 320) -> None:
    """
    Render the CIP Learning animation.
    
    Args:
        height: Height of the animation container in pixels
    """
    components.html(LEARNING_HTML, height=height, scrolling=False)
