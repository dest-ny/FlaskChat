document.addEventListener('DOMContentLoaded', function(){
    const role = parseInt(document.body.dataset.role || '0')
    if(role < 10) return

    const devbar = document.getElementById('dev-bar')
    const togglebtn = document.getElementById('toggle-devbar')
    const cnctbtn = document.getElementById('connect-socket')
    const socketStatus = document.getElementById('socket-status')
    const updateinfobtn = document.getElementById('update-info')
    const searchUserInput = document.getElementById('search-username');
    const searchUserBtn = document.getElementById('search-user');
    const userResultsList = document.getElementById('user-results-list');
    const userInfoSection = document.getElementById('user-info_section');
    const clearMessagesBtn = document.getElementById('clear-messages');

    clearMessagesBtn.addEventListener('click', function(){
        socket.emit("clear_messages")
    })

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
                responsetime.textContent = endtime + "ms"
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

    if (searchUserBtn && searchUserInput && userResultsList) {
        searchUserBtn.addEventListener('click', function() {
            searchUsers();
        });

        searchUserInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchUsers();
            }
        });
    }

    function searchUsers() {
        const searchTerm = searchUserInput.value.trim();
        if (!searchTerm) return;

        fetch(`/search_users?termino=${encodeURIComponent(searchTerm)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la búsqueda');
                }
                return response.json();
            })
            .then(users => {
                displayUserResults(users);
            })
            .catch(error => {
                console.error('Error searching users:', error);
            });
    }

    function displayUserResults(users) {
        userResultsList.innerHTML = '';
        
        if (!users || users.length === 0 || Object.keys(users).length === 0) {
            userResultsList.innerHTML = '<li>No se encontraron usuarios</li>';
            return;
        }
        Object.values(users).forEach(user => {
            const li = document.createElement('li');
            li.textContent = `[ ${user.id} ] ${user.name}`;
            li.dataset.userId = user.id;
            li.addEventListener('click', function() {
                displayUserDetails(user);
            });
            userResultsList.appendChild(li);
        });
    }

    function displayUserDetails(user) {
        userInfoSection.innerHTML = '';
        
        const userHeader = document.createElement('h4');
        userHeader.textContent = user.name;
        
        const userDetails = document.createElement('div');
        userDetails.classList.add('user-details');
        
        let bannedUntilText = 'No';
        if (user.banned_until) {
            const bannedDate = new Date(user.banned_until);
            if (bannedDate > new Date()) {
                bannedUntilText = 'Sí, hasta ' + bannedDate.toLocaleString();
            }
        }
        
        userDetails.innerHTML = `
            <p><strong>ID:</strong> ${user.id}</p>
            <p><strong>Rol:</strong> ${user.role}</p>
            <p><strong>Online:</strong> ${user.online ? 'Sí' : 'No'}</p>
            <p><strong>Mensajes:</strong> ${user.message_count || 0}</p>
            <p><strong>Baneado?:</strong> ${bannedUntilText}</p>
        `;
        
        const actionButtons = document.createElement('div');
        actionButtons.classList.add('user-actions');
        
        const setRoleBtn = document.createElement('button');
        setRoleBtn.textContent = 'Cambiar Rol';
        setRoleBtn.addEventListener('click', function() {
            const newRole = prompt("Indica el nuevo rol para el usuario \n(0-normal, 5-moderador,10-admin):", user.role);
            if (newRole !== null) {
                fetch(`/change_role`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user: user.id, role: parseInt(newRole) })
                })
                .then(response => response.json())  
                .then(data => {
                    if(data.success){
                        user.role = parseInt(newRole)
                        displayUserDetails(user)
                    }
                })
                .catch(error => {
                    console.error('Error al cambiar el rol:', error);
                })
            }
        })
        
        const unbanBtn = document.createElement('button');
        unbanBtn.textContent = 'Desbanear';
        unbanBtn.addEventListener('click', function() {
            fetch(`/unban_user`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user: user.id })
            })
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    user.banned_until = null
                    displayUserDetails(user)
                }
            })
            .catch(error => {
                console.error('Error al desbanear el usuario:', error);
            })
        })

        actionButtons.appendChild(setRoleBtn);
        actionButtons.appendChild(unbanBtn);
        
        userInfoSection.appendChild(userHeader);
        userInfoSection.appendChild(userDetails);
        userInfoSection.appendChild(actionButtons);
    }
})