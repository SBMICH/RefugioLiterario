// Menú en móvil
function toggleNav(button) {
    const nav = document.getElementById('main-nav');
    const abierto = nav.classList.toggle('open');
    button.setAttribute('aria-expanded', abierto);
}

// Cambiar entre inicio de sesión y registro
function toggleForm() {
    const login = document.getElementById('login-form');
    const registro = document.getElementById('register-form');
    login.hidden = !login.hidden;
    registro.hidden = !registro.hidden;
}

// Mostrar u ocultar el formulario de edición del perfil
function toggleEdit() {
    const info = document.getElementById('perfil-info');
    const form = document.getElementById('edit-form');
    info.hidden = !info.hidden;
    form.hidden = !form.hidden;
}

// Abrir la ficha de un libro del catálogo
function openBook(id) {
    const dialog = document.getElementById(id);
    if (dialog) dialog.showModal();
}

document.addEventListener('DOMContentLoaded', () => {
    // Cerrar la ficha al hacer clic fuera de ella
    document.querySelectorAll('dialog').forEach((dialog) => {
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) dialog.close();
        });
    });

    // Los avisos desaparecen solos
    document.querySelectorAll('.flash').forEach((flash) => {
        setTimeout(() => flash.classList.add('fade'), 5000);
        setTimeout(() => flash.remove(), 5600);
    });

    // Método de pago en "finalizar compra"
    const metodo = document.getElementById('metodo_pago');
    if (metodo) {
        metodo.addEventListener('change', () => {
            ['tarjeta_credito', 'paypal', 'transferencia'].forEach((m) => {
                const campos = document.getElementById(m + '_fields');
                if (campos) campos.style.display = metodo.value === m ? 'block' : 'none';
            });
        });
    }
});
