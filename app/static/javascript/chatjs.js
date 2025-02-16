var socket = io()

const formChat = document.getElementById("chat__form")
const chat_listamensajes = document.getElementById("chat_listamensajes")
const chat_sala = document.getElementById("chat_sala")
const mensajeInput = document.getElementById("mensajeInput")

const limit = 50
let offset = 0
let loading = false
let hasLoaded = false
let allMessagesLoaded = false

function createMessage(message){
    return `
            <span><strong>${message.name}</strong></span> 
            <span>${message.content}</span>
            <span>${message.fecha_formateada}</span>
        `
}
function loadMessages() {
    if (loading || allMessagesLoaded) return;
    loading = true

    let loadingMessage = document.createElement("div")
    loadingMessage.className = "chat__loading"
    loadingMessage.innerHTML = "<span>Cargando mensajes...</span>"
    chat_listamensajes.prepend(loadingMessage);

    fetch(`/load_messages?offset=${offset}`)
        .then(response => response.json())
        .then(messages => {
            chat_listamensajes.removeChild(loadingMessage);
            if (messages && messages.length > 0) {
                messages.forEach(message => {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'chat__msg';
                    if (message.name === document.body.dataset.name) {
                        messageElement.classList.add('chat__mymsg');
                    }
                    messageElement.innerHTML = createMessage(message);
                    chat_listamensajes.prepend(messageElement);
                });
                offset += limit;
            }
            if(messages === undefined || messages.length < limit){
                allMessagesLoaded = true
            }
            loading = false;
        })
        .catch(error => {
            console.error('Error cargando mensajes:', error);
            loading = false;
        });
}

chat_sala.addEventListener('scroll', function() {
    if (chat_sala.scrollTop === 0) {
        loadMessages();
    }else if(chat_sala.scrollTop + chat_sala.clientHeight >= chat_sala.scrollHeight){
        let messageElements = chat_listamensajes.querySelectorAll(".chat__msg")
        if (messageElements.length > limit) {
            while (messageElements.length > limit) {
                messageElements = chat_listamensajes.querySelectorAll(".chat__msg")
                chat_listamensajes.removeChild(messageElements[0]);
            }
        }
        offset = limit
        allMessagesLoaded = false
    }
})

socket.on('connect', function(){
    loadMessages()
})

socket.on('estado', function(statusMSG){
    if(statusMSG){
        const messageElement = document.createElement("div")
        messageElement.className = "chat__notif"
        messageElement.classList.add(statusMSG.category)
        messageElement.innerHTML = `<span><strong><span>${statusMSG.name}</span></strong> <span>${statusMSG.content}</span></span>`
        chat_listamensajes.appendChild(messageElement)
        scrollChat()
    }
});

socket.on('disconnect', function(){
    alert("Desconectado del chat!")
    location.reload()
})

socket.on('mensaje', function(message){
    if(message){
        const messageElement = document.createElement("div")
        messageElement.className = "chat__msg"
        messageElement.innerHTML = createMessage(message)
        chat_listamensajes.appendChild(messageElement)
        scrollChat()
    }
});

socket.on('usuarios_online', function(data){
    const users_wrapper = document.getElementById("users_wrapper")
    const users_count = document.getElementById("users_online")
    let usuarios = data;
    let nombre = document.body.dataset.name || ""
    let role = parseInt(document.body.dataset.role || "0");

    users_count.textContent=usuarios.length
    users_wrapper.innerHTML = ""
    usuarios.forEach(usuario => {
        let li = document.createElement("li")
        li.innerHTML = `
        <div class="user__element">
            <div class="user__identifier">
                <span class="username">${usuario.name}</span>
                ${usuario.role >= 10 ? `
                    <span class="decorator">⭐</span>
                    ` : 
                    usuario.role >= 5 ? `
                    <span class="decorator">🛡️</span>
                    ` : ""
                }
            </div>
            ${role >= 5 && usuario.name != nombre && usuario.role < role ? `
            <div class="user__buttons">
                <button class="user_button" onclick="timeout_user(${usuario.id})">TIMEOUT</button>
                ${role >= 10 && usuario.name != nombre ? `
                <button class="user_button" onclick="ban_user(${usuario.id})">BAN</button>
                ` : ""}
            </div>
            ` : ""}
        </div> `;
        users_wrapper.appendChild(li);
        console.log(role + " | " + usuario.name + " | " + (role >= 10 && usuario.name != nombre))
    });
});

socket.on("force_disconnect", function(name){
    if (!name || name === document.body.dataset.name) {
        socket.disconnect();
    }
});
if(formChat){
    formChat.addEventListener("submit", async (event) =>{
        event.preventDefault()
        if(mensajeInput && mensajeInput.value.trim() === "") {
            mensajeInput.style.border = "2px solid rgb(255, 47, 0)"
            return
        }

        mensajeInput.style.border = ""

        socket.emit("mensaje", mensajeInput.value)
        mensajeInput.value = ""
    });
}

function scrollChat(){
    const sala = document.getElementById("chat_sala")

    const scrollBottom = () => {
        const scroll = sala.scrollHeight;
        const scrollOptions = {
            top: scroll,
            behaviour: "smooth",
        };
        sala.scrollTo(scrollOptions);
    }

    setTimeout(scrollBottom, 100);
}

function timeout_user(userId){
    let duration = prompt("Indica la duración del timeout (minutos): ", '60')
    if(duration === null) return;
    duration = parseInt(duration)

    if(isNaN(duration) || duration <= 0) return;

    socket.emit("timeout_user", {"user" : userId, "duration": duration})
}

function ban_user(userId){
    let okay = confirm("Desea vetar al usuario para siempre?")
    if(!okay) return;
    let duration = -1

    socket.emit("timeout_user", {"user" : userId, "duration": duration})
}