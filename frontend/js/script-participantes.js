document.addEventListener("DOMContentLoaded", () => {
  const programasPorFacultad = JSON.parse(document.getElementById("programas-data").textContent);
  const facultadSelect = document.getElementById("facultad");
  const programaSelect = document.getElementById("programa");

  facultadSelect.addEventListener("change", () => {
    const facultadSeleccionada = facultadSelect.value;
    const programas = programasPorFacultad[facultadSeleccionada] || [];

    programaSelect.innerHTML = "";
    programaSelect.disabled = programas.length === 0;

    if (programas.length === 0) {
      programaSelect.innerHTML = '<option value="">No hay programas disponibles</option>';
      return;
    }

    programaSelect.innerHTML = '<option value="" disabled selected>Seleccioná un programa</option>';
    programas.forEach(nombre => {
      const option = document.createElement("option");
      option.value = nombre;
      option.textContent = nombre;
      programaSelect.appendChild(option);
    });
  });

});