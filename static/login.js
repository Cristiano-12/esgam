document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const studentIDInput = document.getElementById('studentID');
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('toggle-password');
    const eyeIcon = document.getElementById('eyeIcon');
    const menuBtn = document.getElementById('menu-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');
    const logoutBtn = document.getElementById('logout-btn');

    if (loginForm) {
        loginForm.reset();
    }

    if (studentIDInput) {
        studentIDInput.value = '';
    }

    if (passwordInput) {
        passwordInput.value = '';
    }

    const eyeOpenSVG = `
    <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0z"></path>
    <circle cx="12" cy="12" r="3"></circle>
    `;

    const eyeClosedSVG = `
        <path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.226 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-19.876 0z"></path>
        <path d="M14.084 8.414a3 3 0 0 0-4.242 4.243"></path>
        <path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"></path>
        <line x1="2" y1="2" x2="22" y2="22" stroke="currentColor" stroke-width="2"></line>
    `;

    if (togglePasswordBtn && passwordInput && eyeIcon) {
        togglePasswordBtn.addEventListener('click', () => {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            eyeIcon.innerHTML = isPassword ? eyeClosedSVG : eyeOpenSVG;
        });
    }

    if (menuBtn && dropdownMenu) {
        menuBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            window.location.href = '/logout';
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            window.location.href = '/logout';
        });
    }

    document.querySelectorAll('[maxlength]').forEach((field) => {
        const wrapper = field.closest('.input-field, .form-group');
        if (!wrapper) return;

        const maxLength = Number(field.getAttribute('maxlength'));
        if (!maxLength) return;

        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.setAttribute('aria-live', 'polite');
        wrapper.appendChild(counter);

        const updateCounter = () => {
            const current = field.value.length;
            counter.textContent = `${current}/${maxLength}`;
            counter.classList.toggle('is-warning', current >= maxLength * 0.9);
        };

        field.addEventListener('input', updateCounter);
        updateCounter();
    });
});


document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[type="file"]').forEach(function (input) {
        var indicador = document.createElement('small');
        indicador.className = 'file-indicator';
        indicador.textContent = 'Nenhum ficheiro selecionado';
        input.insertAdjacentElement('afterend', indicador);

        input.addEventListener('change', function () {
            if (!input.files || input.files.length === 0) {
                indicador.textContent = 'Nenhum ficheiro selecionado';
                indicador.classList.remove('has-file');
                return;
            }
            var nomes = Array.prototype.map.call(input.files, function (f) { return f.name; });
            indicador.textContent = nomes.length > 1
                ? nomes.length + ' ficheiros selecionados: ' + nomes.join(', ')
                : nomes[0];
            indicador.classList.add('has-file');
        });
    });
});


(function () {
    
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            try {
                sessionStorage.setItem('controleScrollY', String(window.scrollY || 0));
                var card = form.closest('.card');
                if (card) {
                    var h = card.querySelector('h2');
                    if (h) sessionStorage.setItem('controleScrollTarget', h.textContent.trim());
                }
            } catch (e) {}
        });
    });

    function restaurarScroll() {
        try {
            var target = sessionStorage.getItem('controleScrollTarget');
            var y = sessionStorage.getItem('controleScrollY');
            sessionStorage.removeItem('controleScrollTarget');
            sessionStorage.removeItem('controleScrollY');
            if (target) {
                var headings = document.querySelectorAll('.card h2');
                for (var i = 0; i < headings.length; i++) {
                    if (headings[i].textContent.trim() === target) {
                        headings[i].scrollIntoView({ block: 'center', behavior: 'auto' });
                        return;
                    }
                }
            }
            if (y !== null) window.scrollTo(0, parseInt(y, 10) || 0);
        } catch (e) {}
    }

    function fecharFlash(el) {
        if (!el || !el.parentNode) return;
        el.style.transition = 'opacity .3s ease';
        el.style.opacity = '0';
        setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 300);
    }

    document.querySelectorAll('.flash-close').forEach(function (btn) {
        if (btn.closest('form')) return; // botão X de pendência (submit)
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            fecharFlash(btn.closest('.flash'));
        });
    });

    // Auto-esconder flashes de mensagem (não as caixas de pendência)
    document.querySelectorAll('.flash').forEach(function (flash) {
        if (flash.closest('[style*="padding:22px"]')) return;
        setTimeout(function () { fecharFlash(flash); }, 6000);
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', restaurarScroll);
    } else {
        restaurarScroll();
    }
})();