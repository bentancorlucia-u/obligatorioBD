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
        capacidad=None
    ):
        self.id_reserva = id_reserva
        self.nombre_sala = nombre_sala
        self.edificio = edificio
        self.fecha = fecha
        self.id_turno = id_turno
        self.estado = estado
        self.capacidad = capacidad  # se usa para validar el límite de personas
    
    def cancelar(self):
        # Cambia el estado de la reserva a cancelada solo si está activa
        if self.estado != "activa":
            return flash("Solo se pueden cancelar reservas activas", "warning")
        self.estado = "cancelada"

    def __repr__(self):
        return f"<Reserva {self.id_reserva} - {self.nombre_sala}, {self.edificio} ({self.fecha})>"

