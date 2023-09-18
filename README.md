# Documentation for the server side implementation
The implementation is basically divided in two parts.

Client side JS and server side (python - Flask)

The ideia is to get the gameboard image drawn by pygame in python and send it to the client's side as a canvas drawing
and capture keystrokes and send them to the server.

##  Client side
 The client side implementation uses websockets to make the communication.
 When the subject reaches the page /[SUBJECT_ID]

 1. The socket io code opens up the connection and the server receives the 'connect' event.
 2. The javascript code is executed to setup the key listener.
 3. We setup an auto focus feature to keep the focus on the canvas element
 4. We send the first event to join a new game `create_join`.
 5. We register for all events of `game_board_update`
 6. We start the animate function that keeps drawing on the screen the latest updated game board.

## Server side

The code is basically divided in two sections, the game loop and the Flask app code

### The Flask app code

This is the only html page mapping for requests coming into the server
```
@app.route('/<subject_name>')
```

This is the event that is creator at ```1```
```
@socketio.on('connect')
```

This is the event sent on step ```4```
```
@socketio.on('create_join')
```

This is the event that gets received on each keystroke
```
@socketio.on('action')
```

### The game loop

The game loop uses the instance for the Game Enviroment that was instanciated and associated to the user's socket id in step 4 
This instance of the implementation uses the number of episodes from the command line and keeps the game loop running while the number of steps is not reached. As soon as the first `game_episode_start` the game If the step returns None the episode is over and we loop to the next one in case there is anyone left.

The image is generated py pygame and is saved as base64 string and sent over the websocket as an event to the clients, so they update the canvas unit.
This could be impemented in a more efficient way, sending the raw image bytes and handling those bytes to canvas compatible image, and maybe avoiding sending equal images sending them only when they differ.

## The events

This is the list events in chronological order

1. 'connect', not issued explicitly but is received on the server side.
2. 'create_join' issued once the game html page is fully loaded
3. 'game_episode_start' the event that gives the information for the episode number.
4. 'action' issued on the client side on every keystroke that is mapped to an action
5. 'game_board_update' on every step the gameboard is sent to the client.
6. 'game_ended' event is sent after the number of episodes is reached and the client is then redirected to the final url link (passed as argument to the server.)
