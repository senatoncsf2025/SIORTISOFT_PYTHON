document.addEventListener('DOMContentLoaded', () => {

    // ==============================
    // Toggle entre Consulta y Registro
    // ==============================
    const btnConsulta = document.getElementById('btnConsulta');
    const btnRegistro = document.getElementById('btnRegistro');
    const formConsulta = document.getElementById('formConsulta');
    const formRegistro = document.getElementById('formRegistro');

    if (btnConsulta && formConsulta && formRegistro) {
        btnConsulta.addEventListener('click', () => {
            formConsulta.classList.remove('d-none');
            formRegistro.classList.add('d-none');
        });
    }

    if (btnRegistro && formConsulta && formRegistro) {
        btnRegistro.addEventListener('click', () => {
            formRegistro.classList.remove('d-none');
            formConsulta.classList.add('d-none');
        });
    }


    // ==============================
    // Vehículo
    // ==============================
    const vehiculo = document.getElementById('trae_vehiculo');
    const vehiculoFields = document.getElementById('vehiculoFields');

    if (vehiculo && vehiculoFields) {

        const toggleVehiculo = () => {
            vehiculoFields.classList.toggle('d-none', vehiculo.value !== '1');
        };

        toggleVehiculo();
        vehiculo.addEventListener('change', toggleVehiculo);
    }


    // ==============================
    // Computador
    // ==============================
    const pc = document.getElementById('trae_pc');
    const pcFields = document.getElementById('pcFields');

    if (pc && pcFields) {

        const togglePC = () => {
            pcFields.classList.toggle('d-none', pc.value !== '1');
        };

        togglePC();
        pc.addEventListener('change', togglePC);
    }

});