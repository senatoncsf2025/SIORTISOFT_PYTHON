document.addEventListener('DOMContentLoaded', function () {
    // ==============================
    // Toggle entre Consulta y Registro
    // ==============================
    const btnConsulta = document.getElementById('btnConsulta');
    const btnRegistro = document.getElementById('btnRegistro');
    const formConsulta = document.getElementById('formConsulta');
    const formRegistro = document.getElementById('formRegistro');

    function mostrarFormulario(formMostrar, formOcultar) {
        if (formMostrar) {
            formMostrar.classList.remove('d-none');
        }
        if (formOcultar) {
            formOcultar.classList.add('d-none');
        }
    }

    if (btnConsulta) {
        btnConsulta.addEventListener('click', function () {
            mostrarFormulario(formConsulta, formRegistro);
        });
    }

    if (btnRegistro) {
        btnRegistro.addEventListener('click', function () {
            mostrarFormulario(formRegistro, formConsulta);
        });
    }

    // ==============================
    // Vehículo - Registro
    // ==============================
    const vehiculoRegistro = document.getElementById('trae_vehiculo');
    const vehiculoFieldsRegistro = document.getElementById('vehiculoFields');

    if (vehiculoRegistro && vehiculoFieldsRegistro) {
        function toggleVehiculoRegistro() {
            vehiculoFieldsRegistro.classList.toggle(
                'd-none',
                vehiculoRegistro.value !== '1'
            );
        }

        toggleVehiculoRegistro();
        vehiculoRegistro.addEventListener('change', toggleVehiculoRegistro);
    }

    // ==============================
    // Computador - Registro
    // ==============================
    const pcRegistro = document.getElementById('trae_pc');
    const pcFieldsRegistro = document.getElementById('pcFields');

    if (pcRegistro && pcFieldsRegistro) {
        function togglePcRegistro() {
            pcFieldsRegistro.classList.toggle(
                'd-none',
                pcRegistro.value !== '1'
            );
        }

        togglePcRegistro();
        pcRegistro.addEventListener('change', togglePcRegistro);
    }

    // ==============================
    // Vehículo - Consulta
    // ==============================
    const vehiculoConsulta = document.getElementById('trae_vehiculo_consulta');
    const vehiculoFieldsConsulta = document.getElementById('vehiculoFieldsConsulta');

    if (vehiculoConsulta && vehiculoFieldsConsulta) {
        function toggleVehiculoConsulta() {
            vehiculoFieldsConsulta.classList.toggle(
                'd-none',
                vehiculoConsulta.value !== '1'
            );
        }

        toggleVehiculoConsulta();
        vehiculoConsulta.addEventListener('change', toggleVehiculoConsulta);
    }

    // ==============================
    // Computador - Consulta
    // ==============================
    const pcConsulta = document.getElementById('trae_pc_consulta');
    const pcFieldsConsulta = document.getElementById('pcFieldsConsulta');

    if (pcConsulta && pcFieldsConsulta) {
        function togglePcConsulta() {
            pcFieldsConsulta.classList.toggle(
                'd-none',
                pcConsulta.value !== '1'
            );
        }

        togglePcConsulta();
        pcConsulta.addEventListener('change', togglePcConsulta);
    }
});