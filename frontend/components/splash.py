"""
CIP Splash Screen Component
File: frontend/components/splash.py

COPY THIS ENTIRE FILE - DO NOT MODIFY
"""

import streamlit as st
import streamlit.components.v1 as components

# SPLASH ONLY - NO DASHBOARD MOCKUP
SPLASH_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        html, body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0F172A;
            color: #E2E8F0;
            height: 100%;
            overflow: hidden;
        }
        
        .splash {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #0F172A;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .splash::before {
            content: '';
            position: absolute;
            width: 800px;
            height: 800px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
            border-radius: 50%;
            animation: ambientPulse 2.4s ease-in-out infinite;
        }
        
        @keyframes ambientPulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.2); opacity: 0.8; }
        }
        
        .splash-text {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 900px;
            z-index: 1;
            opacity: 0;
            animation: fadeIn 0.6s ease-out forwards;
        }
        
        @keyframes fadeIn { to { opacity: 1; } }
        
        .letter {
            font-size: 52px;
            font-weight: 700;
            color: white;
            transition: color 0.2s ease, opacity 0.3s ease, transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-block;
            min-width: 10px;
        }
        
        .letter.space { width: 20px; }
        
        .letter.critical { color: #EF4444; text-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }
        .letter.high { color: #F97316; text-shadow: 0 0 20px rgba(249, 115, 22, 0.5); }
        .letter.moderate { color: #FBBF24; text-shadow: 0 0 20px rgba(251, 191, 36, 0.5); }
        .letter.low { color: #10B981; text-shadow: 0 0 20px rgba(16, 185, 129, 0.5); }
        
        .letter.cip-letter { font-weight: 800; }
        
        .letter.gradient {
            background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: none;
        }
        
        .letter.vanish { opacity: 0; transform: scale(0.5); }
        
        .splash-tagline {
            position: absolute;
            top: calc(50% + 60px);
            left: 50%;
            transform: translate(-50%, 100px);
            color: rgba(255,255,255,0.6);
            font-size: 16px;
            font-weight: 500;
            letter-spacing: 4px;
            text-transform: uppercase;
            opacity: 0;
            transition: opacity 0.6s ease-out, transform 0.6s ease-out;
            z-index: 1;
        }

        .splash-tagline.visible { opacity: 1; transform: translate(-50%, 0); }
        
    </style>
</head>
<body>
    <div class="splash" id="splash">
        <div class="splash-text" id="splashText"></div>
        <div class="splash-tagline" id="tagline">Contract Intelligence Platform</div>
    </div>

    <script>
        const splashText = document.getElementById('splashText');
        const tagline = document.getElementById('tagline');
        
        const fullText = "Contract Intelligence Platform";
        const riskColors = ['critical', 'high', 'moderate', 'low'];
        
        // CORRECT positions: C=0, I=9, P=22
        const cipPositions = { 'C': 0, 'I': 9, 'P': 22 };
        
        let letters = [];
        let charIndex = 0;
        let skipPressed = false;
        
        // Create letter spans
        for (let i = 0; i < fullText.length; i++) {
            const char = fullText[i];
            const span = document.createElement('span');
            span.className = 'letter';
            span.textContent = char;
            
            if (char === ' ') {
                span.classList.add('space');
            } else {
                const isCIP = (i === cipPositions['C'] || i === cipPositions['I'] || i === cipPositions['P']);
                if (isCIP) span.classList.add('cip-letter');
                charIndex++;
            }
            
            letters.push({
                element: span,
                isCIP: span.classList.contains('cip-letter'),
                char: char
            });
            
            splashText.appendChild(span);
        }
        
        const nonCIPLetters = letters.filter(l => !l.isCIP && l.char !== ' ');
        const cipLetters = letters.filter(l => l.isCIP);
        
        function shuffle(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
            return array;
        }
        
        const shuffledNonCIP = shuffle([...nonCIPLetters]);
        
        // SPED UP 40% (multiply by 0.6)
        const INITIAL_DELAY = 900;      // Was 1500
        const CYCLE_DURATION = 480;     // Was 800
        const LETTER_STAGGER = 180;     // Was 300
        
        setTimeout(startAnimation, INITIAL_DELAY);
        
        function startAnimation() {
            if (skipPressed) return;
            
            letters.forEach((letter, idx) => {
                if (letter.char === ' ') return;
                cycleColors(letter.element, letter.isCIP, idx * 30);  // Was 50
            });
            
            shuffledNonCIP.forEach((letter, idx) => {
                setTimeout(() => {
                    if (skipPressed) return;
                    setTimeout(() => {
                        if (skipPressed) return;
                        letter.element.classList.add('vanish');
                    }, CYCLE_DURATION * 4);
                }, idx * LETTER_STAGGER);
            });
            
            const vanishComplete = (shuffledNonCIP.length * LETTER_STAGGER) + (CYCLE_DURATION * 4) + 300;  // Was 500
            setTimeout(glideCIPToCenter, vanishComplete);
        }
        
        function cycleColors(element, isCIP, delay) {
            let colorIndex = 0;
            setTimeout(() => {
                const interval = setInterval(() => {
                    if (skipPressed) { clearInterval(interval); return; }
                    riskColors.forEach(c => element.classList.remove(c));
                    element.classList.add(riskColors[colorIndex]);
                    colorIndex++;
                    if (isCIP) {
                        if (colorIndex >= riskColors.length) colorIndex = 0;
                    } else {
                        if (colorIndex >= riskColors.length) clearInterval(interval);
                    }
                }, CYCLE_DURATION);
            }, delay);
        }
        
        function glideCIPToCenter() {
            if (skipPressed) return;
            
            cipLetters.forEach(letter => {
                riskColors.forEach(c => letter.element.classList.remove(c));
                letter.element.classList.add('gradient');
            });
            
            const cipData = cipLetters.map(letter => {
                const rect = letter.element.getBoundingClientRect();
                return { element: letter.element, startX: rect.left, startY: rect.top };
            });
            
            letters.forEach(l => {
                if (l.char === ' ' || !l.isCIP) {
                    l.element.style.transition = 'opacity 0.3s ease';  // Was 0.5s
                    l.element.style.opacity = '0';
                }
            });
            
            // VERTICALLY CENTERED
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;
            const finalFontSize = 80;
            const letterWidths = [50, 20, 50];
            const gap = 30;
            const totalWidth = letterWidths[0] + gap + letterWidths[1] + gap + letterWidths[2];
            const startX = centerX - (totalWidth / 2);
            
            const positions = [
                startX,
                startX + letterWidths[0] + gap,
                startX + letterWidths[0] + gap + letterWidths[1] + gap
            ];
            
            cipData.forEach((data, idx) => {
                const el = data.element;
                el.style.position = 'fixed';
                el.style.left = data.startX + 'px';
                el.style.top = data.startY + 'px';
                el.style.margin = '0';
            });
            
            setTimeout(() => {
                cipData.forEach((data, idx) => {
                    const el = data.element;
                    el.style.transition = 'all 0.9s cubic-bezier(0.25, 0.1, 0.25, 1)';  // Was 1.5s
                    el.style.left = positions[idx] + 'px';
                    el.style.top = (centerY - finalFontSize / 2) + 'px';
                    el.style.fontSize = finalFontSize + 'px';
                });
            }, 60);  // Was 100
            
            setTimeout(() => {
                if (skipPressed) return;
                tagline.classList.add('visible');
            }, 1080);  // Was 1800
        }
        
        function handleSkip() {
            if (!skipPressed) {
                skipPressed = true;
                // Signal parent (Streamlit) that splash is complete
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*');
            }
        }
        
        document.addEventListener('keydown', handleSkip);
        document.addEventListener('click', handleSkip);
    </script>
</body>
</html>
'''


def show_splash_screen():
    """
    Show splash screen ONLY if not already shown.
    Returns True if splash is being displayed, False if already complete.
    """
    # Skip if already completed
    if st.session_state.get('splash_complete', False):
        return False
    
    # Hide Streamlit UI during splash
    st.markdown("""
        <style>
            header, footer, [data-testid="stSidebar"], 
            [data-testid="stHeader"], #MainMenu, .stDeployButton {
                display: none !important;
            }
            .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Show splash animation
    components.html(SPLASH_HTML, height=500, scrolling=False)
    
    # Style button: transparent background, light grey text, no border
    st.markdown("""
        <style>
            div.stButton > button {
                background: transparent !important;
                border: none !important;
                color: #94A3B8 !important;
            }
            div.stButton > button:hover {
                background: transparent !important;
                color: #E2E8F0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Enter button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Enter CIP", use_container_width=True):
            st.session_state.splash_complete = True
            st.rerun()
    
    return True


def init_splash():
    """Initialize splash state"""
    if 'splash_complete' not in st.session_state:
        st.session_state.splash_complete = False
