var socket = io()

socket.on('connect', function(){
    socket.emit('evento', {data:'Connected!'})
    console.log('Me he conectado!')
});