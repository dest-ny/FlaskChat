var socket = io()

const formChat = document.getElementById("chat__form")
const chat_listamensajes = document.getElementById("chat_listamensajes")
const mensajeInput = document.getElementById("mensajeInput")

socket.on('estado', function(data){
    //chat.textContent += data['nombre'] + " " + data['msg'] + "\n"
    //let arr = data['usuarios']
    chat_listamensajes.innerHTML += data
    scrollChat()
});

socket.on('disconnect', function(){
    alert("Desconectado del chat!")
    location.reload()
})

socket.on('mensaje', function(data){
    chat_listamensajes.innerHTML += data
    scrollChat()
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
                ${usuario.role == 10 ? `
                    <span class="decorator">⭐</span>
                    ` : ""}
            </div>
            ${role >= 5 && usuario.name != nombre? `
            <div class="user__buttons">
                <button class="ban-button">VETAR</button>
            </div>
            ` : ""}
        </div> `;
        users_wrapper.appendChild(li);
    });
});

if(formChat){
    formChat.addEventListener("submit", async (event) =>{
        event.preventDefault()
        if(mensajeInput && mensajeInput.value.trim() === "") {
            console.log("Mensaje inválido!")
            mensajeInput.style.border = "1px solid rgb(255, 47, 0)"
            return
        }

        mensajeInput.style.border = ""

        socket.emit("mensaje", mensajeInput.value)
        mensajeInput.value = ""
    });
}

function scrollChat(){
    const sala = document.getElementById("chat_sala")
    const scroll = sala.scrollHeight;

    const scrollBottom = () => {
        const scrollOptions = {
            top: scroll,
            behaviour: "smoorth",
        };
        sala.scrollTo(scrollOptions);
    }

    setTimeout(scrollBottom, 100);
}