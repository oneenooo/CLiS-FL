# pylint: disable = C0114, C0115, C0116, C0103

import warnings
from time import sleep
from colorama import init, Fore
from utils.stats import count_clients, display_client_information, \
    draw_graph, count_rejected_clients, show_results
from utils.generation import generate_nodes, selected_to_dict, choose_dataset
from constants.model_constants import NUM_CLASSES, NUM_CHANNELS
from constants.federated_learning import ROUNDS, FINAL_ACCURACY
from distributedLearning.DistributedLearning import dist_learning
from clientSelection import RandomClientSelection
from utils.displays import display_author
from models.CNN.CNNMnist import CNNMnist
from models.CNN.CNNCifar import CNNCifar

# TODO : Adding cause of down.

# TODO : Consuming Battery depending on cpu power used.

# TODO : Memory consumed depending on the size of data.

# TODO : CPU consumed depending on memory usage.


warnings.filterwarnings("ignore", category=DeprecationWarning)
init(autoreset=True)

if __name__ == '__main__':
    display_author()  # * Display authors information

    # ! -------------------------------------------- Generation process ------------------------------------------------

    # ? Choose how many nodes you want to simulate.
    number_of_nodes = int(input(f"{Fore.LIGHTYELLOW_EX}How Many nodes do you want "
                                f"to simulate ?\n> "))

    # ? Specify the percentage of choice of the participant clients.
    selection_percentage = int(input(f"{Fore.LIGHTYELLOW_EX}What percentage "
                                     f"of participating clients do you want?\n> ")) / 100

    # ? Choosing the dataset ( 1 = MNIST, 2 = Fashion MNIST, 3 = CIFAR 100).
    dataset_id, train_dataset, test_dataset = choose_dataset()

    # ? Generate the chosen number of nodes.
    clients = generate_nodes(number_of_nodes=number_of_nodes, data=train_dataset)

    # ! ---------------------------------------------------- End ! -----------------------------------------------------

    # ! -------------------------------------------- Generic Model ----------------------------------------------------
    global_model = CNNCifar() if dataset_id == 3 else CNNMnist(
        num_channels=NUM_CHANNELS,
        num_classes=NUM_CLASSES)

    global_model.train()  # ? Generic model.

    global_weights = global_model.state_dict()

    # ! ---------------------------------------------------- End ! -----------------------------------------------------
    train_loss, train_accuracy = [], []
    total_energy = 0

    for epoch in range(ROUNDS):
        print(f"\n{Fore.LIGHTYELLOW_EX}Global Training Round : {epoch + 1}\n")

        sleep(2)

        global_model.train()

    # ! -------------------------------------------- Client selection process ------------------------------------------
        # ? Call Random client selection module to select random clients.
        selected_clients = RandomClientSelection(nodes=clients, K=selection_percentage,
                                                 debug_mode=False).random_client_selection()

        # ? Convert the output of random clients to list.
        selected_clients_list = selected_to_dict(selected_clients=selected_clients)

        # ? Get the number of weak, mid and powerful nodes. ;;:
        number_weak_nodes, number_mid_nodes, number_powerful_nodes = count_clients(
            selected_clients=selected_clients)

        # ? Display some stats about selected clients.
        display_client_information(selected_clients_list=selected_clients_list,
                                   selected_clients=selected_clients,
                                   number_weak_nodes=number_weak_nodes,
                                   number_mid_nodes=number_mid_nodes,
                                   number_powerful_nodes=number_powerful_nodes,
                                   K=selection_percentage)

    # ! -------------------------------------------- End of client selection process -----------------------------------

    # ! -------------------------------------------- Start Distributed Learning  ---------------------------------------

        # ? Begin training on each client.

        loss_avg, list_acc, clients_acc, energy = dist_learning(train_dataset=train_dataset,
                                                                selected_clients=selected_clients,
                                                                global_model=global_model,
                                                                global_round=epoch)

        global_acc = sum(list_acc) / len(list_acc)

        print(f"Global accuracy : {global_acc * 100} %")

        train_accuracy.append(global_acc)
        if loss_avg is not None:
            train_loss.append(loss_avg)
        total_energy = total_energy + energy

        if global_acc >= FINAL_ACCURACY / 100:
            print(f"{Fore.LIGHTGREEN_EX}[+] Global accuracy reached !! "
                  f"No more rounds for FL ( Round : {epoch + 1} )")
            break

    # ! ---------------------------------------------------- End ! -----------------------------------------------------

    # ! ---------------------------------------------------- Results ---------------------------------------------------

    # ? Print loss and the accuracy of each node.
    show_results(train_loss=train_loss, clients_acc=clients_acc)

    METHOD = "Vanila FL"

    number_rejected_clients = count_rejected_clients(clients)

    accuracy_data, energy_data, down_data = {METHOD: 100 * train_accuracy[-1]}, \
                                            {METHOD: total_energy}, \
                                            {METHOD: number_rejected_clients}

    draw_graph(accuracy_data=accuracy_data, energy_data=energy_data, down_data=down_data)

    # ! ---------------------------------------------------- End ! -----------------------------------------------------
