from flask import flash

class Reserva:
    def __init__(
        self,
        id_reserva,
        nombre_sala,
        edificio,
        fecha,
        id_turno,
        estado="activa",
        participantes=None,
        capacidad=None
    ):
        self.id_reserva = id_reserva
        self.nombre_sala = nombre_sala
        self.edificio = edificio
        self.fecha = fecha
        self.id_turno = id_turno
        self.estado = estado
        self.participantes = participantes or []
        self.capacidad = capacidad  # se usa para validar el límite de personas

    def agregar_participante(self, participante):
        """Agrega un participante si no está ya en la reserva y hay espacio."""
        if any(p.ci == participante.ci for p in self.participantes):
            flash(f"El participante {participante.ci} ya está en la reserva.", "warning")
            return

        if self.capacidad is not None and len(self.participantes) >= self.capacidad:
            flash(f"La sala '{self.nombre_sala}' ya alcanzó su capacidad máxima ({self.capacidad}).", "error")
            return

        self.participantes.append(participante)
        flash(f"Participante {participante.nombre} {participante.apellido} agregado correctamente.", "success")

    def eliminar_participante(self, ci_participante):
        """Elimina un participante por su cédula."""
        original_len = len(self.participantes)
        self.participantes = [p for p in self.participantes if p.ci != ci_participante]
        if len(self.participantes) < original_len:
            flash(f"Participante {ci_participante} eliminado correctamente.", "success")
        else:
            flash(f"No se encontró al participante {ci_participante} en la reserva.", "warning")

    def listar_participantes(self):
        """Devuelve una lista con los nombres de los participantes."""
        return [f"{p.nombre} {p.apellido}" for p in self.participantes]

    def __repr__(self):
        return f"<Reserva {self.id_reserva} - {self.nombre_sala}, {self.edificio} ({self.fecha})>"

