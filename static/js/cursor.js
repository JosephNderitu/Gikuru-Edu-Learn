
document.addEventListener('DOMContentLoaded', function() {
    // Only enable custom cursor on desktop
    if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
        const cursorDot = document.querySelector('.cursor-dot');
        const cursorOutline = document.querySelector('.cursor-dot-outline');
        
        let mouseX = 0, mouseY = 0;
        let outlineX = 0, outlineY = 0;
        
        // Mouse position tracking
        document.addEventListener('mousemove', function(e) {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });
        
        // Animation loop
        function animateCursor() {
            // Smooth movement for dot (fast)
            let dotX = mouseX;
            let dotY = mouseY;
            
            // Smooth movement for outline (slow, with lag)
            outlineX += (mouseX - outlineX) * 0.1;
            outlineY += (mouseY - outlineY) * 0.1;
            
            cursorDot.style.left = dotX + 'px';
            cursorDot.style.top = dotY + 'px';
            
            cursorOutline.style.left = outlineX + 'px';
            cursorOutline.style.top = outlineY + 'px';
            
            requestAnimationFrame(animateCursor);
        }
        
        animateCursor();
        
        // Interactive elements hover effects
        const interactiveElements = document.querySelectorAll(
            'a, button, input, select, textarea, [role="button"], .hover-effect, .cursor-interactive'
        );
        
        interactiveElements.forEach(el => {
            // Hover effect
            el.addEventListener('mouseenter', function() {
                if (this.tagName === 'A') {
                    cursorOutline.classList.add('cursor-link');
                } else if (this.tagName === 'BUTTON') {
                    cursorOutline.classList.add('cursor-hover');
                } else if (this.tagName === 'INPUT' || this.tagName === 'TEXTAREA' || this.tagName === 'SELECT') {
                    cursorOutline.classList.add('cursor-text');
                }
            });
            
            el.addEventListener('mouseleave', function() {
                cursorOutline.classList.remove('cursor-hover', 'cursor-click', 'cursor-text', 'cursor-link');
            });
            
            // Click effect
            el.addEventListener('mousedown', function() {
                cursorOutline.classList.add('cursor-click');
            });
            
            el.addEventListener('mouseup', function() {
                cursorOutline.classList.remove('cursor-click');
            });
        });
        
        // Cursor trail effect
        const createTrail = () => {
            const trail = document.createElement('div');
            trail.className = 'cursor-trail';
            
            // Random color for trail
            const colors = [
                '#3b82f6', '#8b5cf6', '#ec4899', '#ef4444', '#f59e0b', '#10b981'
            ];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            
            trail.style.background = `radial-gradient(circle, ${randomColor}, transparent)`;
            trail.style.left = mouseX + 'px';
            trail.style.top = mouseY + 'px';
            
            document.body.appendChild(trail);
            
            // Animate trail
            let opacity = 0.6;
            let size = 6;
            
            const animateTrail = () => {
                opacity -= 0.02;
                size += 0.5;
                
                trail.style.opacity = opacity;
                trail.style.width = size + 'px';
                trail.style.height = size + 'px';
                
                if (opacity <= 0) {
                    trail.remove();
                } else {
                    requestAnimationFrame(animateTrail);
                }
            };
            
            animateTrail();
        };
        
        // Create trail on mouse move (throttled)
        let trailTimeout;
        document.addEventListener('mousemove', function() {
            if (!trailTimeout) {
                createTrail();
                trailTimeout = setTimeout(() => {
                    trailTimeout = null;
                }, 16); // ~60fps
            }
        });
        
        // Cursor effects on scroll
        let scrollTimeout;
        window.addEventListener('scroll', function() {
            cursorOutline.style.transform = 'translate(-50%, -50%) scale(0.8)';
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                cursorOutline.style.transform = 'translate(-50%, -50%) scale(1)';
            }, 100);
        });
        
        // Cursor effects on page load
        window.addEventListener('load', function() {
            cursorOutline.style.transform = 'translate(-50%, -50%) scale(1.5)';
            setTimeout(() => {
                cursorOutline.style.transform = 'translate(-50%, -50%) scale(1)';
            }, 500);
        });
        
        // Disable cursor when leaving window
        document.addEventListener('mouseleave', function() {
            cursorDot.style.opacity = '0';
            cursorOutline.style.opacity = '0';
        });
        
        document.addEventListener('mouseenter', function() {
            cursorDot.style.opacity = '1';
            cursorOutline.style.opacity = '1';
        });
    }
});