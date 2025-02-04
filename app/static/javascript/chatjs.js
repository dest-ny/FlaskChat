var socket = io()

const chat = document.getElementById("chat")
const formChat = document.getElementById("formChat")
const mensajeInput = document.getElementById("mensajeInput")
const usrList = document.getElementById("usrList")

function removeOptions(selectElement) {
    var i, L = selectElement.options.length - 1;
    for(i = L; i >= 0; i--) {
       selectElement.remove(i);
    }
}

socket.on('estado', function(data){
    
    chat.textContent += data['nombre'] + " " + data['msg'] + "\n"
    let arr = data['usuarios']
    console.log(arr)
    removeOptions(usrList)
    arr.forEach(element => {
        console.log(element)
        let opcion = document.createElement("option")
        opcion.text = element
        usrList.add(opcion)
    });
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
