function toggleForm() {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const title = document.getElementById("form-title");

    if (loginForm.style.display === "none") {
        loginForm.style.display = "block";
        registerForm.style.display = "none";
        title.textContent = "Iniciar Sesión";
    } else {
        loginForm.style.display = "none";
        registerForm.style.display = "block";
        title.textContent = "Registrarse";
    }
}

function toggleEdit() {
    var perfilInfo = document.getElementById('perfil-info');
    var editForm = document.getElementById('edit-form');
    var editButton = document.getElementById('edit-button');

    if (editForm.style.display === 'none') {
        perfilInfo.style.display = 'none';
        editForm.style.display = 'block';
        editButton.textContent = 'Cancelar Edición';
    } else {
        perfilInfo.style.display = 'block';
        editForm.style.display = 'none';
        editButton.textContent = 'Editar Perfil';
    }
}

function toggleEdit() {
  var perfilInfo = document.getElementById('perfil-info');
  var editForm = document.getElementById('edit-form');
  var editButton = document.getElementById('edit-button');

  if (editForm.style.display === 'none') {
    perfilInfo.style.display = 'none';
    editForm.style.display = 'block';
    editButton.textContent = 'Cancelar';
  } else {
    perfilInfo.style.display = 'block';
    editForm.style.display = 'none';
    editButton.textContent = 'Editar Perfil';
  }
}