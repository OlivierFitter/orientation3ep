// ─── MENU MOBILE ──────────────────────────────────────────────
const toggle = document.getElementById('navToggle');
const links  = document.getElementById('navLinks');
if (toggle && links) {
    toggle.addEventListener('click', () => links.classList.toggle('open'));
}

// ─── COOKIE BANNER ────────────────────────────────────────────
function showCookieBanner() {
    if (!localStorage.getItem('cookieConsent')) {
        const banner = document.getElementById('cookieBanner');
        if (banner) banner.style.display = 'block';
    }
}
function acceptCookies() {
    localStorage.setItem('cookieConsent', 'accepted');
    document.getElementById('cookieBanner').style.display = 'none';
}
function refuseCookies() {
    localStorage.setItem('cookieConsent', 'refused');
    document.getElementById('cookieBanner').style.display = 'none';
}
document.addEventListener('DOMContentLoaded', showCookieBanner);

// ─── FAQ ACCORDÉON ────────────────────────────────────────────
document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
        const item = btn.closest('.faq-item');
        const isOpen = item.classList.contains('open');
        document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
        if (!isOpen) item.classList.add('open');
    });
});
