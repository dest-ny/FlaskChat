var socket = io()

const chat = document.getElementById("chat")
const formChat = document.getElementById("formChat")
const mensajeInput = document.getElementById("mensajeInput")

socket.on('estado', function(data){
    chat.textContent += data['nombre'] + " " + data['msg'] + "\n"
});

socket.on('mensaje', function(data){
    console.log("Mensaje recibido!")
    chat.value += `<${data['sender']}> ${data['msg']}\n`
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
