document.addEventListener('DOMContentLoaded', function(){
    const role = parseInt(document.body.dataset.role || '0')
    if(role < 10) return

    const devbar = document.getElementById('dev-bar')
    const togglebtn = document.getElementById('toggle-devbar')
    const cnctbtn = document.getElementById('connect-socket')
    const socketStatus = document.getElementById('socket-status')
    const updateinfobtn = document.getElementById('update-info')

    togglebtn.addEventListener('click', function(){
        devbar.classList.toggle('collapsed')
        togglebtn.textContent = devbar.classList.contains('collapsed') ? '▲' : '▼'
    })

    devbar.classList.add('collapsed');
    togglebtn.textContent = '▲';

    cnctbtn.addEventListener('click', function(){
        if(socket.connected){
            socket.disconnect()
        }else{
            socket.connect()
        }
    })
    
    function updateSocketStatus(isConnected) {
        if (socketStatus && cnctbtn) {
            socketStatus.textContent = isConnected ? 'Conectado' : 'Desconectado'
            socketStatus.className = isConnected ? '' : 'disconnected'
            cnctbtn.textContent = isConnected ? 'Desconectar' : 'Conectar'
        }
    }

    socket.on('connect', function() {
        updateSocketStatus(true);
    });

    socket.on('disconnect', function() {
        updateSocketStatus(false);
    });

    function actualizarInfo() {
        const starttime = performance.now()
        fetch('/get_info').then(response => response.json())
        .then(content => {
            const endtime = (performance.now() - starttime).toFixed(2) || 0
            const usercount = document.getElementById('usercount')
            const messagecount = document.getElementById('messagecount')
            const responsetime = document.getElementById('ping')
            const memoryusage = document.getElementById("memoryusage")
            const cpuload = document.getElementById("serverload")
            if(usercount)
                usercount.textContent = content.users
            if(messagecount)
                messagecount.textContent = content.messages
            if(responsetime)
                responsetime.textContent = (endtime-1000) + "ms"
            if(cpuload)
                cpuload.textContent = content.cpu + "%"
            if(memoryusage)
                memoryusage.textContent = content.memory + "%" 
        })
    }

    updateinfobtn.addEventListener('click', function(){
        actualizarInfo()
    })

    actualizarInfo()
})