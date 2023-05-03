import socket
import random
import time

# define host and port
HOST = 'localhost'   # use localhost or '' for all available interfaces
PORT = 12345

# define number of rounds and number of players
rounds_number = 3
while True:
    try:
        players_number = int(input("Number of players: "))
        if players_number > 0:
            break
        else:
            print("Please enter a positive integer.")
    except ValueError:
        print("Invalid input. Please enter a positive integer.")


# notes: to send and receive we should convert to string
# then we have to encod at sender side and decode at receiver side


# ask for player name
def get_player_name(client_socket):
    client_socket.send("Enter your name ".encode())
    name = client_socket.recv(1024).decode().strip()
    return name


# create a socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    # bind the socket to a specific address and port
    server_socket.bind((HOST, PORT))

    # listen for incoming connections
    server_socket.listen(players_number)

    print(f"Server is listening on {HOST}:{PORT}")

    # create a list to hold player sockets and scores
    player_sockets = []
    # cumulative scores
    player_scores = [0] * players_number
    # rtt of each round
    current_round = [0] * players_number
    player_names = []

    # accept new connections
    for i in range(players_number):
        client, address = server_socket.accept()
        print(f"New connection from {address}")

        # add new connection to player_sockets
        player_sockets.append(client)

        # call name function to ask for names
        name = get_player_name(client)
        player_names.append(name)

        # send welcome message
        welcome_message = f"Welcome to the game, {name}! You are player {i+1}.\n The rules of this game are simple: \nYou will be given a number, try to send it as fast as possible!"
        client.send(welcome_message.encode())

    results = f"You won :D \n"
    results2 = f"You lost :( \n"
    results3 = f"It's a tie! \n"

    disconnection_occurred = False # Flag for connection errors
    
    # play the game for the specified number of rounds
    for i in range(rounds_number):
        print(f"\nRound {i+1}\n----------")

        # generate a random number from 0 to 9
        number = random.randint(0, 9)
        print(f"The number is: {number}\n")

        # wait 3 seconds before sending the number
        time.sleep(3)

        # for each player, we send the number, receive a response, calculate rtt
        # then we check if the answer is correct, then save the rtt to compare it later
        for j, client in enumerate(player_sockets):
            # we try to send the number, if the connection is lost
            # we send an error message and break out of the loop to
            # end the game
            try:
                client.send(str(number).encode())
                # start the timer
                start_time = time.time()
                # get a response from the connected clients
                response = client.recv(1024).decode().strip()
                # stop timer
                end_time = time.time()
                # rtt here calculates the time between sending the number and receiving an answer
                rtt = end_time - start_time
                # check if the response is correct
                if response == str(number):
                    print(f"{player_names[j]}: {rtt:.5f} s")
                    current_round[j] = rtt
                # if number isn't correct we take rtt as a very big value (100)
                # so while comparing the player is disqualified
                # the player won't get a message that he's disqualified
                # he'll just get a result that he lost
                else:
                    print(f"Player {j+1} disqualified")
                    current_round[j] = 100
            # connection error
            except (ConnectionAbortedError, ConnectionResetError, ConnectionError):
                disconnection_occurred = True  # Update the flag when a disconnection occurs
                print(f"Player {j+1} disconnected")
                for k, other_client in enumerate(player_sockets):
                    if k != j:
                        other_client.send(
                            "Game has ended due to a disconnection \nPlease close this window".encode())
                    other_client.close()
                # closing the server, hence all connection and breaking out of the players loop
                server_socket.close()
                break
            # break out of rounds loop
            if server_socket._closed:
                break
        
        round_scores = [0] * players_number
        # calculate the round results
        if len(set(current_round)) == 1:
            # if more than one player had the same time
            for j in range(players_number):
                # result3 is a tie
                player_sockets[j].send(results3.encode())
                print(f"Player {j+1}: 1")
                # update round score
                round_scores[j] = 1
        else:
            # choose winner as the one with the minimum rtt
            # set the index of the winner as round_winner
            # give him a current round score of 1
            round_winner = current_round.index(min(current_round))
            round_scores[round_winner] = 1
            print(f"\nRound Scores:")
            # Create a list of tuples with player names and round scores
            name_round_score_list = list(zip(player_names, round_scores))
            # Sort the list in descending order based on the round scores
            name_round_score_list.sort(key=lambda x: x[1], reverse=True)

            for name, score in name_round_score_list:
                print(f"{name}: {score}")

            # Send the results to each player
            if i < rounds_number - 1:  # To make sure this isn't the last round
                for j in range(players_number):
                    if round_scores[j] == 1:
                        # results is "you won"
                        player_sockets[j].send(results.encode())
                    else:
                        # results2 is "you lost"
                        player_sockets[j].send(results2.encode())

            # update the overall scores
            # add current round scores to players score 
            player_scores = [a + b for a,b in zip(player_scores, round_scores)]

            # print the updated overall scores
            print(f"\nOverall Scores:")
            sorted_scores = sorted(zip(player_names, player_scores), key=lambda x: x[1], reverse=True)
            overall_scores_str = "Overall Scores:\n"
            for name, score in sorted_scores:
                overall_scores_str += f"{name}: {score}\n"
                print(f"{name}: {score}")

            # Send the overall scores to the clients
            for client in player_sockets:
                client.send(overall_scores_str.encode())




    # send the final scores to each player
    # find the winner
    if not disconnection_occurred:  # Add this condition before sending final scores
        max_score = max(player_scores)

        # note that player_sockets and player_scores share the same indexing
        for j, client in enumerate(player_sockets):
            try:
                if player_scores[j] == max_score:
                    client.send("Congratulations! You won the game!".encode())
                else:
                    client.send("Better luck next time!".encode())
            # if we encounter an error while sending to players, print connection lost
            except OSError:
                print(f"Connection to Player {j+1} lost")
            finally:
                # close the client connection
                client.close()
        # close server
        server_socket.close()
