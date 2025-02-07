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

socket.on('mensaje', function(data){
    chat_listamensajes.innerHTML += data
    scrollChat()
});

socket.on('usuarios_online', function(data){
    const user_container = document.getElementById("users_container")
    user_container.innerHTML = data
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