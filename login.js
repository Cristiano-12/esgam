document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const studentIDInput = document.getElementById('studentID');
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('togglePassword');
    const eyeIcon = document.getElementById('eyeIcon');

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
        togglePasswordBtn.addEventListener('click', ()=> {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            eyeIcon.innerHTML = isPassword ? eyeClosedSVG : eyeOpenSVG;
        })
    }

    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            event.preventDefault();

            const studentID = studentIDInput.value.trim();
            const password = passwordInput.value.trim();

            if (studentID === '123456' && password === '654321'){
                localStorage.setItem('studentId', studentID);
                window.location.href = "portal.html";
            } else {
                alert("Alguma credencial incorreta! Por favor dirija-se a direcao");
            }
        })
    }
});
