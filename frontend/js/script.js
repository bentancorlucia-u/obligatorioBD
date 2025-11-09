document.addEventListener("DOMContentLoaded", () => {
  const salasPorEdificio = JSON.parse(document.getElementById("salas-data").textContent);
  const edificioSelect = document.getElementById("edificio");
  const salaSelect = document.getElementById("nombre_sala");

  edificioSelect.addEventListener("change", () => {
    const edificioSeleccionado = edificioSelect.value;
    const salas = salasPorEdificio[edificioSeleccionado] || [];

    salaSelect.innerHTML = "";
    salaSelect.disabled = salas.length === 0;

    if (salas.length === 0) {
      salaSelect.innerHTML = '<option value="">No hay salas disponibles</option>';
      return;
    }

    salaSelect.innerHTML = '<option value="" disabled selected>Seleccioná una sala</option>';
    salas.forEach(nombre => {
      const option = document.createElement("option");
      option.value = nombre;
      option.textContent = nombre;
      salaSelect.appendChild(option);
    });
  });
});
